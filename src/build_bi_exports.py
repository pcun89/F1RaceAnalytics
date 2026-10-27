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
