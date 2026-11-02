"""
Builds the simulation world (teams, drivers, circuits, calendar) from real data saved by
fetch_f1_reference.py. Car and driver strength come from the current championship standings.
"""
import json
from datetime import date
import numpy as np

REF_PATH = "data/reference/reference.json"
