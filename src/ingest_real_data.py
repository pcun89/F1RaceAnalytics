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
