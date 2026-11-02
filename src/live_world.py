"""
Builds the simulation world (teams, drivers, circuits, calendar) from real data saved by
fetch_f1_reference.py. Car and driver strength come from the current championship standings.
"""
import json
from datetime import date
import numpy as np

REF_PATH = "data/reference/reference.json"
# circuitId -> (lap length km, base lap time s, rain probability, overtaking ease 0-1)
# The API does not provide these, so they are approximate values kept here.
KNOWN = {
    "bahrain": (5.41, 95.0, 0.02, 0.50), "jeddah": (6.17, 90.5, 0.01, 0.40),
    "albert_park": (5.28, 80.5, 0.20, 0.50), "suzuka": (5.81, 91.5, 0.25, 0.35),
    "shanghai": (5.45, 96.0, 0.20, 0.60), "miami": (5.41, 90.0, 0.12, 0.55),
    "imola": (4.91, 77.0, 0.18, 0.30), "monaco": (3.34, 72.5, 0.15, 0.05),
    "villeneuve": (4.36, 73.5, 0.25, 0.65), "catalunya": (4.66, 78.0, 0.10, 0.35),
    "red_bull_ring": (4.32, 66.0, 0.20, 0.60), "silverstone": (5.89, 88.0, 0.30, 0.55),
    "hungaroring": (4.38, 78.5, 0.20, 0.25), "spa": (7.00, 105.0, 0.40, 0.60),
    "zandvoort": (4.26, 72.0, 0.20, 0.25), "monza": (5.79, 82.0, 0.10, 0.70),
    "baku": (6.00, 103.0, 0.08, 0.60), "marina_bay": (4.94, 96.0, 0.25, 0.30),
    "americas": (5.51, 95.0, 0.10, 0.55), "rodriguez": (4.30, 78.0, 0.10, 0.45),
    "interlagos": (4.31, 70.5, 0.35, 0.60), "vegas": (6.20, 94.0, 0.02, 0.70),
    "losail": (5.38, 84.0, 0.01, 0.50), "yas_marina": (5.28, 86.0, 0.01, 0.45),
}


def build_world(rng, nrng, rid):
    ref = json.load(open(REF_PATH))

    # ---- constructors: car pace and reliability from championship position ----
    teams = sorted(ref["constructors"], key=lambda t: t["position"])
    n = len(teams)
    total_pts = sum(t["points"] for t in teams)
    top_pts = max(t["points"] for t in teams) or 1
    constructors, cid, tpts = [], {}, {}
    for i, t in enumerate(teams):
        delta = 1.6 * \
            (1 - t["points"] / top_pts) if total_pts > 0 else 1.6 * \
            i / max(1, n - 1)
        row = dict(constructor_id=rid(), name=t["name"], nationality=t["nationality"],
                   car_pace_delta=round(delta, 3),
                   reliability=round(0.97 - 0.09 * i / max(1, n - 1), 3),
                   base_budget_musd=int(250 - delta * 70 + rng.randint(-10, 10)))
        constructors.append(row)
        cid[t["constructorId"]] = row["constructor_id"]
        tpts[t["constructorId"]] = t["points"]

    # ---- drivers: skill from share of the team's points (beating your teammate = faster) ----
    load = {k: 0 for k in cid}
    for d in ref["drivers"]:
        if d.get("constructorId") in cid:
            load[d["constructorId"]] += 1
    drivers = []
    for d in ref["drivers"]:
        team = d.get("constructorId")
        if team not in cid:                      # driver with no team in the standings
            team = min(load, key=load.get)
            load[team] += 1
        share = d["points"] / tpts[team] if tpts[team] > 0 else 0.5
        skill = float(np.clip((0.5 - share) * 0.8, -
                      0.3, 0.3) + nrng.normal(0, 0.05))
        drivers.append(dict(
            driver_id=rid(), first_name=d["givenName"], last_name=d["familyName"],
            code=d.get("code") or d["familyName"][:3].upper(),
            driver_number=int(d.get("number") or rng.randint(2, 98)),
            nationality=d["nationality"], date_of_birth=d["dateOfBirth"],
            skill=round(skill, 3), aggression=round(rng.uniform(0.2, 0.9), 2),
            constructor_id=cid[team], rookie=bool(d.get("rookie"))))

    # ---- circuits (unique across both seasons) and race calendar ----
    circuits, circ_by_key, races = [], {}, []
    for year in sorted(ref["calendars"], key=int):
        for r in sorted(ref["calendars"][year], key=lambda x: x["round"]):
            key = r["circuitId"]
            if key not in circ_by_key:
                if key in KNOWN:
                    km, base, rain, ot = KNOWN[key]
                else:                             # unknown track: plausible random values
                    km = round(rng.uniform(4.0, 6.5), 2)
                    base = round(km * 17.5 + rng.uniform(-6, 6), 1)
                    rain, ot = round(rng.uniform(0.05, 0.30), 2), round(
                        rng.uniform(0.25, 0.60), 2)
                row = dict(circuit_id=rid(), name=r["circuitName"], country=r["country"], length_km=km,
                           laps=int(round(305 / km)), base_lap_time_s=base, pit_loss_s=round(rng.uniform(18, 26), 1),
                           rain_probability=rain, overtaking_ease=ot, tyre_wear_factor=round(rng.uniform(0.7, 1.4), 2))
                circuits.append(row)
                circ_by_key[key] = row
            c = circ_by_key[key]
            races.append(dict(race_id=rid(), season=int(year), round=r["round"], circuit_id=c["circuit_id"],
                              race_date=date.fromisoformat(r["date"]), _c=c))
    return constructors, drivers, circuits, races
