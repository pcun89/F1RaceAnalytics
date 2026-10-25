"""
Ingests REAL Formula 1 data from the Jolpica F1 API (Ergast-compatible) into SQLite + CSV.

Usage:
  python src/ingest_real_data.py                          # last 5 seasons through the current one
  python src/ingest_real_data.py --seasons 2021-2025 --laps
  python src/ingest_real_data.py --seasons 2026 --refresh # re-pull a season that is still in progress

Raw API pages are cached in data/cache/, so re-runs are fast and an interrupted run can resume.
Lap times take one request series per race, so they are optional (--laps) and slow to pull.
"""
import argparse
import csv
import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

BASE = "https://api.jolpi.ca/ergast/f1"
CACHE, CSV_DIR, DB, SCHEMA = "data/cache", "data/real", "data/f1_real.db", "sql/schema_real.sql"
PAGE = 100
_last_call = 0.0
# ---------------------------------------------------------------- HTTP + cache


def http_json(url):
    """GET one API page. Polite pacing, retries, and rate-limit (429) handling."""
    global _last_call
    for attempt in range(6):
        time.sleep(max(0.0, 0.5 - (time.time() - _last_call)))
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "F1RaceAnalytics/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                _last_call = time.time()
                return json.load(r)["MRData"]
        except urllib.error.HTTPError as e:
            _last_call = time.time()
            if e.code == 404:
                return None
            if e.code == 429:
                delay = int(e.headers.get("Retry-After")
                            or 0) or 30 * (attempt + 1)
                print(f"  rate limited - waiting {delay}s")
                time.sleep(delay)
            else:
                time.sleep(2 ** attempt)
        except Exception:
            time.sleep(2 ** attempt)
    sys.exit(
        f"Giving up on {url}. Re-run the script; pages already downloaded are cached.")


def get_page(path, offset, refresh):
    fp = os.path.join(CACHE, re.sub(
        r"[^A-Za-z0-9]+", "_", path).strip("_") + f"_{offset}.json")
    if not refresh and os.path.exists(fp):
        return json.load(open(fp))
    data = http_json(
        f"{BASE}/{path}?limit={PAGE}&offset={offset}") or {"total": "0"}
    if int(data.get("total", 0)) > 0:                     # never cache empty answers
        os.makedirs(CACHE, exist_ok=True)
        json.dump(data, open(fp, "w"))
    return data


def pages(path, refresh):
    offset = 0
    while True:
        d = get_page(path, offset, refresh)
        yield d
        offset += PAGE
        if offset >= int(d.get("total", 0)):
            break


def collect(path, refresh, key):
    """Merge a paginated race-level list (e.g. 'Results') back together, keyed by (season, round)."""
    races = {}
    for d in pages(path, refresh):
        for r in d.get("RaceTable", {}).get("Races", []):
            slot = races.setdefault(
                (int(r["season"]), int(r["round"])), dict(r, **{key: []}))
            slot[key].extend(r.get(key, []))
    return races


def collect_laps(path, refresh):
    """A lap's timings can be split across pages, so merge by lap number."""
    laps = {}
    for d in pages(path, refresh):
        for r in d.get("RaceTable", {}).get("Races", []):
            for lap in r.get("Laps", []):
                laps.setdefault(int(lap["number"]), []).extend(lap["Timings"])
    return laps
# ---------------------------------------------------------------- parsing helpers


def to_int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def secs(t):
    """'1:26.123' -> 86.123 ; '23.456' -> 23.456 ; missing/invalid -> None"""
    if not t:
        return None
    try:
        v = 0.0
        for part in str(t).split(":"):
            v = v * 60 + float(part)
        return round(v, 3)
    except ValueError:
        return None
# ---------------------------------------------------------------- ingest one season


def ingest_season(season, with_laps, refresh, T, skipped):
    results = collect(f"{season}/results.json", refresh, "Results")
    if not results:
        print(f"{season}: no results published yet - skipped")
        return
    quali = collect(f"{season}/qualifying.json", refresh, "QualifyingResults")
    print(f"{season}: {len(results)} races with results")

    def add_people(d, c):
        T["drivers"][d["driverId"]] = dict(
            driver_id=d["driverId"], code=d.get("code"), driver_number=to_int(d.get("permanentNumber")),
            first_name=d["givenName"], last_name=d["familyName"],
            date_of_birth=d.get("dateOfBirth"), nationality=d.get("nationality"))
        T["constructors"][c["constructorId"]] = dict(
            constructor_id=c["constructorId"], name=c["name"], nationality=c.get("nationality"))

    for (yr, rnd), race in sorted(results.items()):
        race_id = yr * 100 + rnd
        circ, loc = race["Circuit"], race["Circuit"]["Location"]
        T["circuits"][circ["circuitId"]] = dict(
            circuit_id=circ["circuitId"], name=circ["circuitName"], locality=loc.get(
                "locality"),
            country=loc.get("country"), latitude=loc.get("lat"), longitude=loc.get("long"))
        T["races"][race_id] = dict(
            race_id=race_id, season=yr, round=rnd, race_name=race[
                "raceName"], circuit_id=circ["circuitId"],
            race_date=race["date"], total_laps=max([to_int(r["laps"]) or 0 for r in race["Results"]] or [0]))

        for r in race["Results"]:
            add_people(r["Driver"], r["Constructor"])
            fl = r.get("FastestLap") or {}
            T["race_results"].append(dict(
                race_id=race_id, driver_id=r["Driver"]["driverId"], constructor_id=r["Constructor"]["constructorId"],
                car_number=to_int(r.get("number")), grid=to_int(r.get("grid")), position=to_int(r.get("position")),
                position_text=r.get("positionText"), points=float(r.get("points", 0)), laps=to_int(r.get("laps")),
                status=r.get("status"), finish_time_ms=to_int((r.get("Time") or {}).get("millis")),
                fastest_lap_rank=to_int(fl.get("rank")), fastest_lap_number=to_int(fl.get("lap")),
                fastest_lap_s=secs((fl.get("Time") or {}).get("time"))))

        for q in quali.get((yr, rnd), {}).get("QualifyingResults", []):
            add_people(q["Driver"], q["Constructor"])
            q1, q2, q3 = secs(q.get("Q1")), secs(
                q.get("Q2")), secs(q.get("Q3"))
            T["qualifying"].append(dict(
                race_id=race_id, driver_id=q["Driver"]["driverId"], constructor_id=q["Constructor"]["constructorId"],
                position=to_int(q.get("position")), q1_s=q1, q2_s=q2, q3_s=q3,
                best_s=min([t for t in (q1, q2, q3) if t is not None], default=None)))

        stops = collect(f"{yr}/{rnd}/pitstops.json", refresh,
                        "PitStops").get((yr, rnd), {}).get("PitStops", [])
        for p in stops:
            if p["driverId"] not in T["drivers"]:
                skipped["pit_stops"] += 1
                continue
            T["pit_stops"].append(dict(
                race_id=race_id, driver_id=p["driverId"], stop_number=to_int(p["stop"]), lap=to_int(p["lap"]),
                local_time=p.get("time"), duration_s=secs(p.get("duration"))))

        if with_laps:
            for lap_no, timings in sorted(collect_laps(f"{yr}/{rnd}/laps.json", refresh).items()):
                for t in timings:
                    if t["driverId"] not in T["drivers"]:
                        skipped["lap_times"] += 1
                        continue
                    T["lap_times"].append(dict(
                        race_id=race_id, driver_id=t["driverId"], lap_number=lap_no,
                        position=to_int(t.get("position")), lap_time_s=secs(t.get("time"))))


# ---------------------------------------------------------------- output
TABLES = ["circuits", "constructors", "drivers", "races",
          "race_results", "qualifying", "pit_stops", "lap_times"]


def rows_of(T, name):
    return list(T[name].values()) if isinstance(T[name], dict) else T[name]


def write_outputs(T):
    os.makedirs(CSV_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(DB), exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript(open(SCHEMA).read())
    for name in TABLES:
        rows = rows_of(T, name)
        if not rows:
            continue
        cols = list(rows[0].keys())
        with open(f"{CSV_DIR}/{name}.csv", "w", newline="") as f:      # CSVs for Power BI / Tableau
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        con.executemany(                                                # upsert = safe to re-run
            f"INSERT OR REPLACE INTO {name} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})",
            [tuple(r[c] for c in cols) for r in rows])
    con.commit()
    return con


# ---------------------------------------------------------------- data quality checks
CHECKS = [  # (label, SQL returning a count of problems, severity)
    ("races without any results",
     "SELECT COUNT(*) FROM races r WHERE NOT EXISTS (SELECT 1 FROM race_results x WHERE x.race_id=r.race_id)", "FAIL"),
    ("races with no winner (no position 1)",
     "SELECT COUNT(*) FROM races r WHERE NOT EXISTS (SELECT 1 FROM race_results x WHERE x.race_id=r.race_id AND x.position=1)", "FAIL"),
    ("duplicate finishing positions within a race",
     "SELECT COUNT(*) FROM (SELECT race_id, position FROM race_results GROUP BY race_id, position HAVING COUNT(*)>1)", "FAIL"),
    ("results pointing at a missing driver or constructor",
     "SELECT COUNT(*) FROM race_results x WHERE x.driver_id NOT IN (SELECT driver_id FROM drivers) "
     "OR x.constructor_id NOT IN (SELECT constructor_id FROM constructors)", "FAIL"),
    ("negative points",
     "SELECT COUNT(*) FROM race_results WHERE points < 0", "FAIL"),
    ("races with an unusual number of entries (<16 or >26)",
     "SELECT COUNT(*) FROM (SELECT race_id FROM race_results GROUP BY race_id HAVING COUNT(*)<16 OR COUNT(*)>26)", "WARN"),
    ("races with no qualifying data",
     "SELECT COUNT(*) FROM races r WHERE NOT EXISTS (SELECT 1 FROM qualifying q WHERE q.race_id=r.race_id)", "WARN"),
    ("pit stops outside 10-120 s",
     "SELECT COUNT(*) FROM pit_stops WHERE duration_s < 10 OR duration_s > 120", "WARN"),
    ("lap times outside 40-300 s",
     "SELECT COUNT(*) FROM lap_times WHERE lap_time_s < 40 OR lap_time_s > 300", "WARN"),
    ("races with pit stops but no lap data (only meaningful with --laps)",
     "SELECT COUNT(*) FROM races r WHERE EXISTS (SELECT 1 FROM pit_stops p WHERE p.race_id=r.race_id) "
     "AND NOT EXISTS (SELECT 1 FROM lap_times l WHERE l.race_id=r.race_id)", "INFO"),
]


def run_checks(con):
    print("\nData quality checks")
    failed = False
    for label, sql, level in CHECKS:
        n = con.execute(sql).fetchone()[0]
        status = "PASS" if n == 0 else level
        failed |= (status == "FAIL")
        print(f"  [{status:4}] {label}: {n}")
    return failed

# ---------------------------------------------------------------- main


def parse_seasons(text):
    out = []
    for part in text.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += range(int(a), int(b) + 1)
        else:
            out.append(int(part))
    return sorted(set(out))


def main(argv=None):
    now = datetime.now().year
    ap = argparse.ArgumentParser(
        description="Ingest real F1 data from the Jolpica API")
    ap.add_argument(
        "--seasons", default=f"{now - 4}-{now}", help="e.g. 2021-2025, 2026, or 2019,2023")
    ap.add_argument("--laps", action="store_true",
                    help="also pull lap times (many requests per race)")
    ap.add_argument("--refresh", action="store_true",
                    help="ignore the cache (use for a season in progress)")
    args = ap.parse_args(argv)

    T = {name: ({} if name in ("circuits", "constructors",
                "drivers", "races") else []) for name in TABLES}
    skipped = {"pit_stops": 0, "lap_times": 0}
    for season in parse_seasons(args.seasons):
        ingest_season(season, args.laps, args.refresh, T, skipped)
    if not T["races"]:
        sys.exit("No race data was loaded.")

    con = write_outputs(T)
    print("\nRows loaded:", {n: len(rows_of(T, n)) for n in TABLES})
    if any(skipped.values()):
        print("Skipped rows with unknown drivers:", skipped)
    sys.exit(1 if run_checks(con) else 0)


if __name__ == "__main__":
    main()
