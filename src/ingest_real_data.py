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
