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


def get(path):
    url = f"{BASE}/{path}?limit=100"
    for attempt in range(4):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "F1RaceAnalytics/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.load(r)["MRData"]
            time.sleep(0.6)  # stay well under the API rate limit
            return data
        except Exception as e:
            print(f"  retry {attempt + 1}/4 for {path}: {e}")
            time.sleep(2 ** attempt)
    sys.exit(
        f"Could not fetch {url}. Check your internet connection or try again later.")


def main():
    # Which season is "current"? (Falls back one year if no races have been scored yet.)
    season = int(get("current/driverstandings.json")
                 ["StandingsTable"]["season"])
    dlist = get(
        f"{season}/driverstandings.json")["StandingsTable"]["StandingsLists"]
    if not dlist:
        season -= 1
        dlist = get(
            f"{season}/driverstandings.json")["StandingsTable"]["StandingsLists"]
    clist = get(
        f"{season}/constructorstandings.json")["StandingsTable"]["StandingsLists"]
    if not dlist or not clist:
        sys.exit("The API returned no standings data.")
    print(f"Season used for team/driver strength: {season}")

    constructors = []
    for row in clist[0]["ConstructorStandings"]:
        c = row["Constructor"]
        constructors.append(dict(constructorId=c["constructorId"], name=c["name"], nationality=c["nationality"],
                                 points=float(row["points"]), position=int(row["position"]), wins=int(row["wins"])))

    prior_ids = {d["driverId"] for d in get(
        f"{season - 1}/drivers.json")["DriverTable"]["Drivers"]}
    drivers = []
    for row in dlist[0]["DriverStandings"]:
        d = row["Driver"]
        teams = row.get("Constructors") or []
        drivers.append(dict(driverId=d["driverId"], code=d.get("code"), number=d.get("permanentNumber"),
                            givenName=d["givenName"], familyName=d["familyName"],
                            dateOfBirth=d["dateOfBirth"], nationality=d["nationality"],
                            constructorId=teams[-1]["constructorId"] if teams else None,
                            points=float(row["points"]), position=int(row["position"]),
                            rookie=d["driverId"] not in prior_ids))

    calendars = {}
    for year in (season - 1, season):
        races = get(f"{year}/races.json")["RaceTable"]["Races"]
        calendars[str(year)] = [dict(round=int(r["round"]), raceName=r["raceName"],
                                     circuitId=r["Circuit"]["circuitId"], circuitName=r["Circuit"]["circuitName"],
                                     locality=r["Circuit"]["Location"]["locality"],
                                     country=r["Circuit"]["Location"]["country"], date=r["date"]) for r in races]

    ref = dict(season=season, source=BASE, fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
               constructors=constructors, drivers=drivers, calendars=calendars)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(ref, f, indent=2)
    print(f"Saved {len(constructors)} teams, {len(drivers)} drivers, "
          f"{sum(len(v) for v in calendars.values())} races to {OUT}")


if __name__ == "__main__":
    main()
