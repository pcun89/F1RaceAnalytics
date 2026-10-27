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
