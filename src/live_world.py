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
