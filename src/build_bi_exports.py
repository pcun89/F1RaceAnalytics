"""Builds BI-ready tables (star schema for Power BI + flat tables for Tableau) from data/raw.
Usage: python src/build_bi_exports.py [raw_dir] [out_dir]"""
import sys
import os
import pandas as pd  # pyright: ignore[reportMissingImports]

RAW = sys.argv[1] if len(sys.argv) > 1 else "data/raw"
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/bi"
os.makedirs(OUT, exist_ok=True)
def rd(n): return pd.read_csv(f"{RAW}/{n}.csv")


con, drv, cir, rac = rd("constructors"), rd(
    "drivers"), rd("circuits"), rd("races")
qua, res, pit, lap = rd("qualifying"), rd(
    "race_results"), rd("pit_stops"), rd("lap_times")
rac["race_date"] = pd.to_datetime(rac["race_date"])
# ---------- dimensions ----------
dim_constructor = con.rename(
    columns={"name": "constructor_name", "nationality": "constructor_nationality"})
dim_driver = drv.assign(driver_name=drv.first_name + " " + drv.last_name)
dim_driver = dim_driver.merge(
    dim_constructor[["constructor_id", "constructor_name"]], on="constructor_id")
dim_circuit = cir.rename(
    columns={"name": "circuit_name", "country": "circuit_country"})
dim_race = rac.merge(
    dim_circuit[["circuit_id", "circuit_name", "circuit_country"]], on="circuit_id")
dim_race["race_label"] = dim_race.season.astype(
    str) + " R" + dim_race["round"].astype(str).str.zfill(2) + " " + dim_race.circuit_name
dates = pd.date_range(rac.race_date.min().replace(
    month=1, day=1), rac.race_date.max().replace(month=12, day=31))
dim_date = pd.DataFrame({"date": dates})
dim_date["year"] = dates.year
dim_date["quarter"] = dates.quarter
dim_date["month_num"] = dates.month
dim_date["month_name"] = dates.strftime("%b")
dim_date["day_of_week"] = dates.strftime("%a")
# ---------- facts / flat tables ----------
r = res.merge(dim_race[["race_id", "season", "round", "race_date", "race_label",
              "circuit_name", "circuit_country", "weather", "total_laps"]], on="race_id")
r = r.merge(dim_driver[["driver_id", "driver_name", "code",
            "driver_number", "nationality"]], on="driver_id")
r = r.merge(dim_constructor[["constructor_id",
            "constructor_name"]], on="constructor_id")
r["is_win"] = (r.finish_position == 1).astype(int)
r["is_podium"] = (r.finish_position <= 3).astype(int)
r["is_points_finish"] = (r.points > 0).astype(int)
r["is_dnf"] = (~r.status.isin(["Finished", "Lapped"])).astype(int)
r["is_pole"] = (r.grid_position == 1).astype(int)
r = r.sort_values(["driver_id", "season", "round"])
r["driver_cum_points"] = r.groupby(["driver_id", "season"]).points.cumsum()
r["driver_championship_pos"] = r.groupby(["season", "round"]).driver_cum_points.rank(
    method="min", ascending=False).astype(int)
ct = r.groupby(["constructor_id", "constructor_name", "season", "round"],
               as_index=False).points.sum().sort_values(["constructor_id", "season", "round"])
ct["constructor_cum_points"] = ct.groupby(
    ["constructor_id", "season"]).points.cumsum()
ct["constructor_championship_pos"] = ct.groupby(
    ["season", "round"]).constructor_cum_points.rank(method="min", ascending=False).astype(int)

l = lap.merge(dim_race[["race_id", "season", "round",
              "race_label", "circuit_name", "weather"]], on="race_id")
l = l.merge(dim_driver[["driver_id", "code",
            "driver_name", "constructor_name"]], on="driver_id")
l["is_green_lap"] = ((l.safety_car == 0) & (
    l.is_pit_lap == 0) & (l.lap_number > 1)).astype(int)
p = pit.merge(dim_race[["race_id", "season", "round",
              "race_label", "circuit_name"]], on="race_id")
p = p.merge(dim_driver[["driver_id", "code",
            "driver_name", "constructor_name"]], on="driver_id")
q = qua.merge(dim_race[["race_id", "season", "round", "race_label"]], on="race_id").merge(
    dim_driver[["driver_id", "code", "driver_name", "constructor_name"]], on="driver_id")

out = {
    # Power BI star schema
    "dim_constructor": dim_constructor, "dim_driver": dim_driver, "dim_circuit": dim_circuit,
    "dim_race": dim_race, "dim_date": dim_date,
    "fact_race_results": res, "fact_lap_times": lap, "fact_pit_stops": pit, "fact_qualifying": qua,
    # Tableau flat tables
    "flat_race_results": r, "flat_constructor_standings": ct, "flat_lap_times": l, "flat_pit_stops": p, "flat_qualifying": q,
}
for k, v in out.items():
    v.to_csv(f"{OUT}/{k}.csv", index=False)
    print(f"{k}: {len(v):,} rows")