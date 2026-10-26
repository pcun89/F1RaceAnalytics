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


# ---------- constructors (car pace delta s/lap, reliability) ----------
team_defs = [("Apex Dynamics", "United Kingdom", 0.00, 0.97), ("Scuderia Valtorri", "Italy", 0.12, 0.95),
             ("Nordhaus Racing", "Germany", 0.25,
              0.96), ("Falcon Works", "United States", 0.40, 0.94),
             ("Kestrel GP", "United Kingdom", 0.60,
              0.93), ("Aurora Motorsport", "France", 0.75, 0.92),
             ("Sakura Racing", "Japan", 0.95,
              0.93), ("Iberia Speed", "Spain", 1.15, 0.90),
             ("Maple Leaf Racing", "Canada", 1.35, 0.89), ("Outback GP", "Australia", 1.55, 0.88)]
constructors = []
for n, c, d, r in team_defs:
    constructors.append(dict(constructor_id=rid(), name=n, nationality=c, car_pace_delta=d, reliability=r,
                             base_budget_musd=int(250-d*70+rng.randint(-10, 10))))
# ---------- drivers ----------
first = ["Lucas", "Mateo", "Oskar", "Hiro", "Daniel", "Felix", "Andre", "Rafael", "Jonas", "Theo", "Marco",
         "Noah", "Kai", "Luca", "Ivan", "Sergio", "Callum", "Pierre", "Leon", "Tomas", "Elias", "Diego", "Max", "Ethan"]
last = ["Hartmann", "Moretti", "Lindqvist", "Tanaka", "Okafor", "Duval", "Santos", "Kowalski", "Brennan", "Alvarez", "Rossi",
        "Fischer", "Novak", "Mercer", "Castillo", "Yamada", "Larsen", "Dubois", "Reyes", "Whitfield", "Berg", "Costa", "Ito", "Navarro"]
nats = ["United Kingdom", "Germany", "Italy", "France", "Spain", "Netherlands", "Japan",
        "Australia", "Canada", "Brazil", "Finland", "Denmark", "Mexico", "Thailand", "United States"]
rng.shuffle(first)
rng.shuffle(last)
drivers = []
nums = rng.sample(range(2, 99), 20)
for i in range(20):
    # s/lap, negative = faster
    skill = float(np.clip(nrng.normal(0, 0.25), -0.5, 0.6))
    drivers.append(dict(driver_id=rid(), first_name=first[i], last_name=last[i],
                        driver_number=nums[i], nationality=rng.choice(nats),
                        date_of_birth=date(
                            1986, 1, 1)+timedelta(days=rng.randint(0, 365*15)),
                        skill=round(skill, 3), aggression=round(rng.uniform(0.2, 0.9), 2),
                        constructor_id=constructors[i//2]["constructor_id"],
                        rookie=rng.random() < 0.2))
for d in drivers:
    d["code"] = (d["last_name"][:3]).upper()
