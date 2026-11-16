"""
Builds Power BI (star schema) and Tableau (flat) tables from the REAL data in data/f1_real.db.
Run after ingest_real_data.py:   python src/build_bi_exports_real.py
Output: data/bi_real/*.csv
"""
import os
import sqlite3
import sys
import pandas as pd

DB, OUT = "data/f1_real.db", "data/bi_real"
if not os.path.exists(DB):
    sys.exit("data/f1_real.db not found - run src/ingest_real_data.py first.")
os.makedirs(OUT, exist_ok=True)
con = sqlite3.connect(DB)
def rd(q): return pd.read_sql(q, con)


drv, cons, cir, rac = rd("SELECT * FROM drivers"), rd(
    "SELECT * FROM constructors"), rd("SELECT * FROM circuits"), rd("SELECT * FROM races")
res, spr, qua = rd("SELECT * FROM race_results"), rd(
    "SELECT * FROM sprint_results"), rd("SELECT * FROM qualifying")
pit, lap = rd("SELECT * FROM pit_stops"), rd("SELECT * FROM lap_times")
pts = rd("SELECT race_id, driver_id, constructor_id, SUM(points) AS points FROM v_points GROUP BY race_id, driver_id, constructor_id")

# ------------------------------------------------------------------ dimensions
dim_driver = drv.assign(driver_name=drv.first_name + " " + drv.last_name)
dim_constructor = cons.rename(
    columns={"name": "constructor_name", "nationality": "constructor_nationality"})
dim_circuit = cir.rename(
    columns={"name": "circuit_name", "country": "circuit_country"})
rac["race_date"] = pd.to_datetime(rac["race_date"])
dim_race = rac.merge(dim_circuit[[
                     "circuit_id", "circuit_name", "circuit_country"]], on="circuit_id", how="left")
dim_race["race_label"] = dim_race.season.astype(
    str) + " R" + dim_race["round"].astype(str).str.zfill(2) + " " + dim_race.race_name
dim_race["has_sprint"] = dim_race.race_id.isin(spr.race_id).astype(int)
days = pd.date_range(f"{rac.race_date.dt.year.min()}-01-01",
                     f"{rac.race_date.dt.year.max()}-12-31")
dim_date = pd.DataFrame({"date": days, "year": days.year, "quarter": days.quarter, "month_num": days.month,
                         "month_name": days.strftime("%b"), "day_of_week": days.strftime("%a")})

# ------------------------------------------------------------------ championship standings after every round


def standings(entity):
    """Cumulative points and championship position after each round, for every season (Grand Prix + sprint points)."""
    rows = []
    for season, g in pts.merge(rac[["race_id", "season", "round"]], on="race_id").groupby("season"):
        rounds = sorted(rac.loc[rac.season == season, "round"])
        pv = g.pivot_table(index=entity, columns="round", values="points",
                           aggfunc="sum", fill_value=0).reindex(columns=rounds, fill_value=0)
        cum = pv.cumsum(axis=1)
        a = pv.reset_index().melt(id_vars=entity, var_name="round", value_name="round_points")
        b = cum.reset_index().melt(id_vars=entity, var_name="round", value_name="cum_points")
        m = a.merge(b, on=[entity, "round"])
        m["season"] = season
        m["championship_pos"] = m.groupby("round").cum_points.rank(
            method="min", ascending=False).astype(int)
        rows.append(m)
    out = pd.concat(rows, ignore_index=True)
    out["round"] = out["round"].astype(int)
    return out.merge(rac[["race_id", "season", "round"]], on=["season", "round"])


fact_driver_standings = standings("driver_id")
fact_constructor_standings = standings("constructor_id")

# ------------------------------------------------------------------ facts
r = res.merge(spr[["race_id", "driver_id", "points"]].rename(
    columns={"points": "sprint_points"}), on=["race_id", "driver_id"], how="left")
r["sprint_points"] = r.sprint_points.fillna(0)
r["total_points"] = r.points + r.sprint_points
r["is_classified"] = r.position_text.astype(
    str).str.fullmatch(r"\d+").astype(int)
r["is_win"] = (r.position == 1).astype(int)
r["is_podium"] = (r.position <= 3).astype(int)
r["is_points_finish"] = (r.points > 0).astype(int)
r["is_dnf"] = (r.position_text == "R").astype(int)
r["is_pole"] = (r.grid == 1).astype(int)
r["places_gained"] = (
    r.grid - r.position).where((r.grid > 0) & (r.is_classified == 1))
fact_race_results = r

q = qua.copy()
q["gap_to_pole_pct"] = 100 * (q.best_s - q.groupby("race_id").best_s.transform(
    "min")) / q.groupby("race_id").best_s.transform("min")
fact_qualifying = q

team_of = res[["race_id", "driver_id", "constructor_id"]]
fact_pit_stops = pit.merge(team_of, on=["race_id", "driver_id"], how="left")

fact_lap_times = pd.DataFrame()
if len(lap):
    l = lap.merge(team_of, on=["race_id", "driver_id"], how="left")
    pit_in = pit[["race_id", "driver_id", "lap"]].drop_duplicates().rename(
        columns={"lap": "lap_number"}).assign(is_pit_lap=1)
    pit_out = pit_in.assign(lap_number=pit_in.lap_number +
                            1).rename(columns={"is_pit_lap": "is_pit_out_lap"})
    l = l.merge(pit_in, on=["race_id", "driver_id", "lap_number"], how="left").merge(
        pit_out, on=["race_id", "driver_id", "lap_number"], how="left")
    l[["is_pit_lap", "is_pit_out_lap"]] = l[[
        "is_pit_lap", "is_pit_out_lap"]].fillna(0).astype(int)
    race_median = l.groupby("race_id").lap_time_s.transform("median")
    # "clean" lap = not lap 1, not a pit in/out lap, and within 107% of the race's median lap (drops safety-car laps)
    l["is_clean_lap"] = ((l.lap_number > 1) & (l.is_pit_lap == 0) & (
        l.is_pit_out_lap == 0) & (l.lap_time_s <= 1.07 * race_median)).astype(int)
    clean_median = l[l.is_clean_lap == 1].groupby(
        "race_id").lap_time_s.median().rename("race_clean_median_s")
    l = l.merge(clean_median, on="race_id", how="left")
    l["pace_delta_s"] = l.lap_time_s - l.race_clean_median_s
    fact_lap_times = l

# ------------------------------------------------------------------ Tableau flat tables
race_cols = ["race_id", "season", "round", "race_date", "race_label",
             "race_name", "circuit_name", "circuit_country", "has_sprint"]
flat_results = (fact_race_results.merge(dim_race[race_cols], on="race_id")
                .merge(dim_driver[["driver_id", "driver_name", "code", "nationality"]].rename(columns={"nationality": "driver_nationality"}), on="driver_id")
                .merge(dim_constructor[["constructor_id", "constructor_name"]], on="constructor_id")
                .merge(fact_driver_standings[["race_id", "driver_id", "cum_points", "championship_pos"]]
                       .rename(columns={"cum_points": "driver_cum_points", "championship_pos": "driver_championship_pos"}),
                       on=["race_id", "driver_id"], how="left"))
flat_driver_standings = (fact_driver_standings.merge(dim_driver[["driver_id", "driver_name", "code"]], on="driver_id")
                         .merge(dim_race[["race_id", "race_label", "race_date"]], on="race_id"))
flat_constructor_standings = (fact_constructor_standings.merge(dim_constructor[["constructor_id", "constructor_name"]], on="constructor_id")
                              .merge(dim_race[["race_id", "race_label", "race_date"]], on="race_id"))
flat_qualifying = (fact_qualifying.merge(dim_race[["race_id", "season", "round", "race_label"]], on="race_id")
                   .merge(dim_driver[["driver_id", "driver_name", "code"]], on="driver_id")
                   .merge(dim_constructor[["constructor_id", "constructor_name"]], on="constructor_id"))
flat_pit_stops = (fact_pit_stops.merge(dim_race[["race_id", "season", "round", "race_label"]], on="race_id")
                  .merge(dim_driver[["driver_id", "driver_name", "code"]], on="driver_id")
                  .merge(dim_constructor[["constructor_id", "constructor_name"]], on="constructor_id", how="left"))
flat_lap_times = pd.DataFrame()
if len(fact_lap_times):
    flat_lap_times = (fact_lap_times.merge(dim_race[["race_id", "season", "round", "race_label", "circuit_name"]], on="race_id")
                      .merge(dim_driver[["driver_id", "driver_name", "code"]], on="driver_id")
                      .merge(dim_constructor[["constructor_id", "constructor_name"]], on="constructor_id", how="left"))

out = {  # Power BI star schema
    "dim_driver": dim_driver, "dim_constructor": dim_constructor, "dim_circuit": dim_circuit, "dim_race": dim_race, "dim_date": dim_date,
    "fact_race_results": fact_race_results, "fact_sprint_results": spr, "fact_qualifying": fact_qualifying,
    "fact_pit_stops": fact_pit_stops, "fact_lap_times": fact_lap_times,
    "fact_driver_standings": fact_driver_standings, "fact_constructor_standings": fact_constructor_standings,
    # Tableau flat tables
    "flat_results": flat_results, "flat_driver_standings": flat_driver_standings, "flat_constructor_standings": flat_constructor_standings,
    "flat_qualifying": flat_qualifying, "flat_pit_stops": flat_pit_stops, "flat_lap_times": flat_lap_times,
}
for name, df in out.items():
    if len(df):
        df.to_csv(f"{OUT}/{name}.csv", index=False)
        print(f"{name}: {len(df):,} rows")
    else:
        print(f"{name}: empty - skipped")
