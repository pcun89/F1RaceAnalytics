"""
Formula 1 race simulator -> relational synthetic dataset (CSV).
Two seasons, 24 races each, 10 fictional teams, 20 drivers.
Tables: constructors, drivers, circuits, races, qualifying, race_results, lap_times, pit_stops
All IDs are random unique numeric values.
Usage: python src/f1_simulator.py [seed] [output_dir]
"""
import random
import sys
import csv
import os
from datetime import date, timedelta
import numpy as np

SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 42
OUT = sys.argv[2] if len(sys.argv) > 2 else "data/raw"
os.makedirs(OUT, exist_ok=True)
rng = random.Random(SEED)
nrng = np.random.default_rng(SEED)
used = set()


def rid(lo=100000, hi=999999):
    while True:
        v = rng.randint(lo, hi)
        if v not in used:
            used.add(v); return v
        