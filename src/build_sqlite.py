"""Loads data/raw into a SQLite database (data/f1.db) using sql/schema.sql.
Usage: python src/build_sqlite.py"""
import sqlite3
import pandas as pd
import os
DB = "data/f1.db"
if os.path.exists(DB):
    os.remove(DB)
con = sqlite3.connect(DB)
con.executescript(open("sql/schema.sql").read())
for t in ["constructors", "circuits", "drivers", "races", "qualifying", "race_results", "pit_stops", "lap_times"]:
    df = pd.read_csv(f"data/raw/{t}.csv")
    df.to_sql(t, con, if_exists="append", index=False)
    print(t, len(df))
con.commit()
con.close()