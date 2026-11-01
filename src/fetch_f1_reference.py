"""
Pulls the CURRENT Formula 1 teams, drivers, standings and race calendars from the
Jolpica F1 API (free, no key, Ergast-compatible) and saves them to data/reference/reference.json.

Usage: python src/fetch_f1_reference.py
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

BASE = "https://api.jolpi.ca/ergast/f1"
OUT = "data/reference/reference.json"
