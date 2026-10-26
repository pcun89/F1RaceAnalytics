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
# ---------- circuits ----------
circ_defs = [("Sakhir Desert Circuit", "Bahrain", 5.41, 95.0, 0.02, 0.5), ("Jeddah Corniche", "Saudi Arabia", 6.17, 90.5, 0.01, 0.4),
             ("Melbourne Park", "Australia", 5.28, 80.5, 0.20,
              0.5), ("Suzuka Hills", "Japan", 5.81, 91.5, 0.25, 0.35),
             ("Shanghai International", "China", 5.45, 96.0, 0.20,
              0.6), ("Miami Marina", "United States", 5.41, 90.0, 0.12, 0.55),
             ("Imola Autodromo", "Italy", 4.91, 77.0, 0.18,
              0.3), ("Monaco Harbour", "Monaco", 3.34, 72.5, 0.15, 0.05),
             ("Montreal Island", "Canada", 4.36, 73.5, 0.25,
              0.65), ("Barcelona Catalunya", "Spain", 4.66, 78.0, 0.10, 0.35),
             ("Red Bull Alpine Ring", "Austria", 4.32, 66.0, 0.20,
              0.6), ("Silverstone Plains", "United Kingdom", 5.89, 88.0, 0.30, 0.55),
             ("Hungaroring", "Hungary", 4.38, 78.5, 0.20,
              0.25), ("Spa Ardennes", "Belgium", 7.00, 105.0, 0.40, 0.6),
             ("Zandvoort Dunes", "Netherlands", 4.26, 72.0, 0.20,
              0.25), ("Monza Park", "Italy", 5.79, 82.0, 0.10, 0.7),
             ("Baku Old City", "Azerbaijan", 6.00, 103.0, 0.08,
              0.6), ("Marina Bay Night", "Singapore", 4.94, 96.0, 0.25, 0.3),
             ("Austin Americas", "United States", 5.51, 95.0, 0.10,
              0.55), ("Mexico City Altitude", "Mexico", 4.30, 78.0, 0.10, 0.45),
             ("Sao Paulo Interlagos", "Brazil", 4.31, 70.5, 0.35,
              0.6), ("Las Vegas Strip", "United States", 6.20, 94.0, 0.02, 0.7),
             ("Lusail Desert", "Qatar", 5.38, 84.0, 0.01, 0.5), ("Yas Marina", "United Arab Emirates", 5.28, 86.0, 0.01, 0.45)]
circuits = []
for n, c, km, bt, rain, ot in circ_defs:
    circuits.append(dict(circuit_id=rid(), name=n, country=c, length_km=km,
                         laps=int(round(305/km)), base_lap_time_s=bt, pit_loss_s=round(rng.uniform(18, 26), 1),
                         rain_probability=rain, overtaking_ease=ot,
                         tyre_wear_factor=round(rng.uniform(0.7, 1.4), 2)))

# ---------- calendar: 2 seasons ----------
races = []
for season in (2024, 2025):
    # (kept so the random stream stays identical)
    start = date(season, 3, 2)+timedelta(days=rng.randint(0, 6))
    for rnd, c in enumerate(circuits, 1):
        dt = date(season, 3, 3)+timedelta(days=int((rnd-1)*(250/23)))
        dt += timedelta(days=(6-dt.weekday()) % 7)  # move to Sunday
        races.append(dict(race_id=rid(), season=season, round=rnd,
                     circuit_id=c["circuit_id"], race_date=dt, _c=c))

COMP = {"SOFT": (0.0, 0.085, 18), "MEDIUM": (0.45, 0.05, 28),
        "HARD": (0.9, 0.032, 40)}  # offset, deg/lap, life (laps)
quali = []
results = []
laps = []
pits = []
pts = [25, 18, 15, 12, 10, 8, 6, 4, 2, 1]
form = {d["driver_id"]: 0.0 for d in drivers}
cdrift = {c["constructor_id"]: 0.0 for c in constructors}
cmap = {c["constructor_id"]: c for c in constructors}

for race in races:
    c = race.pop("_c")
    wet = rng.random() < c["rain_probability"]
    race["weather"] = "Wet" if wet else rng.choices(
        ["Dry", "Cloudy", "Hot"], [0.55, 0.3, 0.15])[0]
    race["air_temp_c"] = round(float(np.clip(nrng.normal(26, 6), 10, 42)), 1)
    race["track_temp_c"] = round(race["air_temp_c"]+rng.uniform(5, 18),
                                 1) if not wet else round(race["air_temp_c"]+rng.uniform(0, 4), 1)
    race["humidity_pct"] = None if rng.random() < 0.05 else int(
        np.clip(nrng.normal(85 if wet else 50, 12), 20, 98))
    race["attendance"] = int(nrng.normal(110000, 25000)
                             ) if rng.random() > 0.04 else None
    L = c["laps"]
    for k in cdrift:
        cdrift[k] = 0.9*cdrift[k]+nrng.normal(0, 0.04)
    for k in form:
        form[k] = 0.85*form[k]+nrng.normal(0, 0.06)
    # qualifying
    qs = []
    for d in drivers:
        t = c["base_lap_time_s"]-2.5+cmap[d["constructor_id"]]["car_pace_delta"]*1.1 + \
            d["skill"]*1.1+cdrift[d["constructor_id"]] + \
            form[d["driver_id"]]+nrng.normal(0, 0.18)
        if wet:
            t += 7
        qs.append((t, d))
    qs.sort(key=lambda x: x[0])
    grid = {}
    for pos, (t, d) in enumerate(qs, 1):
        gp = pos
        if rng.random() < 0.06:
            gp = min(20, pos+rng.randint(3, 10))  # grid penalty
        grid[d["driver_id"]] = [pos, gp, t]
    order = sorted(grid.items(), key=lambda kv: (kv[1][1], kv[1][0]))
    for gpos, (did, v) in enumerate(order, 1):
        v[1] = gpos
    for did, (qp, gp, t) in grid.items():
        quali.append(dict(qualifying_id=rid(), race_id=race["race_id"], driver_id=did, qualifying_position=qp,
                          best_lap_time_s=None if rng.random() < 0.02 else round(t, 3), grid_position=gp, grid_penalty=int(gp != qp)))
    # safety cars
    sc_laps = set()
    n_sc = np.random.default_rng(rng.randint(
        0, 10**9)).poisson(0.9+(0.8 if wet else 0)+(0.8 if c["overtaking_ease"] < 0.15 else 0))
    for _ in range(min(n_sc, 3)):
        s = rng.randint(3, max(4, L-8))
        dur = rng.randint(3, 5)
        sc_laps.update(range(s, min(L, s+dur)))
    race["safety_car_laps"] = len(sc_laps)
    # driver state
    st = {}
    for d in drivers:
        did = d["driver_id"]
        gp = grid[did][1]
        rel = cmap[d["constructor_id"]]["reliability"]
        dnf_lap = None
        dnf_reason = None
        if rng.random() > rel**0.6:
            dnf_lap = rng.randint(1, L-1)
            dnf_reason = rng.choice(
                ["Engine", "Gearbox", "Hydraulics", "Brakes", "Power Unit", "Suspension", "Overheating"])
        elif rng.random() < 0.03+0.05*d["aggression"]*(2 if wet else 1)*0.5+(0.02 if gp > 10 else 0):
            dnf_lap = rng.randint(1, L-1)
            dnf_reason = rng.choice(["Collision", "Accident", "Spun off"])
        # strategy
        if wet:
            stops = sorted(rng.sample(range(8, L-8), rng.choice([1, 2])))
            comps = ["INTERMEDIATE"] + \
                [rng.choice(["INTERMEDIATE", "INTERMEDIATE", "WET"])
                 for _ in stops]
        else:
            ns = rng.choices([1, 2, 3], [0.3, 0.55, 0.15])[0]
            if c["tyre_wear_factor"] > 1.15:
                ns = max(ns, 2)
            cuts = sorted(rng.sample(range(10, L-8), ns)) if L > 25 else [L//2]
            stops = cuts
            start_c = rng.choices(["SOFT", "MEDIUM", "HARD"], [
                                  0.4, 0.45, 0.15] if gp <= 10 else [0.2, 0.4, 0.4])[0]
            comps = [start_c]
            for _ in stops:
                comps.append(rng.choice(
                    [k for k in ["SOFT", "MEDIUM", "HARD"] if k != comps[-1]] or ["HARD"]))
        st[did] = dict(d=d, cum=0.3*(gp-1), grid=gp, dnf=dnf_lap, reason=dnf_reason, stops=stops, comps=comps,
                       cidx=0, tyre_age=0, laps_done=0, pitcount=0, best=None, out=False)
    prev_order = sorted(st, key=lambda k: st[k]["grid"])
    for lap in range(1, L+1):
        sc = lap in sc_laps
        lap_records = {}
        for did in list(st):
            s = st[did]
            if s["out"]:
                continue
            d = s["d"]
            if s["dnf"] == lap:
                s["out"] = True
                s["laps_done"] = lap-1
                continue
            comp = s["comps"][s["cidx"]]
            off, deg, life = COMP.get(comp, (0.0, 0.06, 25))
            if comp == "INTERMEDIATE":
                off, deg = (0.0, 0.04)
            if comp == "WET":
                off, deg = (1.5, 0.03)
            age = s["tyre_age"]
            over = max(0, age-life)
            tyre = off+deg*c["tyre_wear_factor"]*age+0.02*over**1.6
            fuel = 0.035*(L-lap)  # lighter car = faster
            base = c["base_lap_time_s"] + \
                (10 if wet else 0)+(1.0 if lap == 1 else 0)
            lt = base+cmap[d["constructor_id"]]["car_pace_delta"]+cdrift[d["constructor_id"]] + \
                d["skill"]+form[did]+tyre+fuel + \
                float(nrng.normal(0, 0.22 if not wet else 0.6))
            # dirty air
            idx = prev_order.index(did)
            if idx > 0 and not sc:
                ahead = prev_order[idx-1]
                if not st[ahead]["out"] and -0.5 < s["cum"]-st[ahead]["cum"] < 1.0:
                    lt += (1-c["overtaking_ease"])*0.35
            if sc:
                lt = c["base_lap_time_s"]*1.35+float(nrng.normal(0, 0.5))
            pitted = False
            if s["pitcount"] < len(s["stops"]) and lap == s["stops"][s["pitcount"]]:
                pitted = True
                dur = float(np.clip(nrng.normal(2.5, 0.5), 1.9, 4.5)) if rng.random(
                ) > 0.04 else float(rng.uniform(5, 12))
                loss = c["pit_loss_s"]*(0.55 if sc else 1.0)+(dur-2.5)
                lt += loss
                pits.append(dict(pit_stop_id=rid(), race_id=race["race_id"], driver_id=did, stop_number=s["pitcount"]+1, lap=lap,
                                 pit_duration_s=None if rng.random() < 0.03 else round(dur, 2), tyre_from=comp, tyre_to=s["comps"][s["cidx"]+1],
                                 under_safety_car=int(sc)))
                s["pitcount"] += 1
                s["cidx"] += 1
                s["tyre_age"] = -1
            s["tyre_age"] += 1
            s["cum"] += lt
            if not sc and not pitted and (s["best"] is None or lt < s["best"][0]):
                s["best"] = (lt, lap)
            lap_records[did] = (lt, comp, pitted, s["tyre_age"])
        # safety car bunches the field
        if sc:
            order = sorted([k for k in st if not st[k]["out"]],
                           key=lambda k: st[k]["cum"])
            for i, k in enumerate(order):
                st[k]["cum"] = st[order[0]]["cum"]+0.8*i
        order = sorted([k for k in st if not st[k]["out"]],
                       key=lambda k: st[k]["cum"])
        outs = [k for k in st if st[k]["out"]]
        prev_order = order+sorted(outs, key=lambda k: -st[k]["laps_done"])
        for pos, did in enumerate(order, 1):
            lt, comp, pitted, age = lap_records[did]
            laps.append(dict(lap_id=rid(10**7, 10**8-1), race_id=race["race_id"], driver_id=did, lap_number=lap, position=pos,
                             lap_time_s=round(lt, 3), tyre_compound=comp, tyre_age_laps=age, is_pit_lap=int(pitted),
                             safety_car=int(sc), cumulative_time_s=round(st[did]["cum"], 3),
                             gap_to_leader_s=round(st[did]["cum"]-st[order[0]]["cum"], 3)))
        for k in st:
            if not st[k]["out"]:
                st[k]["laps_done"]=lap