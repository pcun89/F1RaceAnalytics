-- Schema for REAL F1 data ingested from the Jolpica API (natural text keys from the API)
CREATE TABLE IF NOT EXISTS circuits (
    circuit_id TEXT PRIMARY KEY, name TEXT NOT NULL, locality TEXT, country TEXT, latitude REAL, longitude REAL);
CREATE TABLE IF NOT EXISTS constructors (
    constructor_id TEXT PRIMARY KEY, name TEXT NOT NULL, nationality TEXT);
CREATE TABLE IF NOT EXISTS drivers (
    driver_id TEXT PRIMARY KEY, code TEXT, driver_number INTEGER, first_name TEXT, last_name TEXT,
    date_of_birth DATE, nationality TEXT);
CREATE TABLE IF NOT EXISTS races (
    race_id INTEGER PRIMARY KEY,                       -- season*100 + round, e.g. 202507
    season INTEGER NOT NULL, round INTEGER NOT NULL, race_name TEXT,
    circuit_id TEXT REFERENCES circuits(circuit_id), race_date DATE, total_laps INTEGER,
    UNIQUE (season, round));
CREATE TABLE IF NOT EXISTS race_results (
    race_id INTEGER REFERENCES races(race_id), driver_id TEXT REFERENCES drivers(driver_id),
    constructor_id TEXT REFERENCES constructors(constructor_id),
    car_number INTEGER, grid INTEGER,                  -- grid 0 = started from the pit lane
    position INTEGER, position_text TEXT,              -- position_text: number, or R / D / W / N / F / E
    points REAL, laps INTEGER, status TEXT, finish_time_ms INTEGER,
    fastest_lap_rank INTEGER, fastest_lap_number INTEGER, fastest_lap_s REAL,
    PRIMARY KEY (race_id, driver_id));
CREATE TABLE IF NOT EXISTS qualifying (
    race_id INTEGER REFERENCES races(race_id), driver_id TEXT REFERENCES drivers(driver_id),
    constructor_id TEXT REFERENCES constructors(constructor_id),
    position INTEGER, q1_s REAL, q2_s REAL, q3_s REAL, best_s REAL,
    PRIMARY KEY (race_id, driver_id));
CREATE TABLE IF NOT EXISTS pit_stops (
    race_id INTEGER REFERENCES races(race_id), driver_id TEXT REFERENCES drivers(driver_id),
    stop_number INTEGER, lap INTEGER, local_time TEXT, duration_s REAL,
    PRIMARY KEY (race_id, driver_id, stop_number));
CREATE TABLE IF NOT EXISTS lap_times (
    race_id INTEGER REFERENCES races(race_id), driver_id TEXT REFERENCES drivers(driver_id),
    lap_number INTEGER, position INTEGER, lap_time_s REAL,
    PRIMARY KEY (race_id, driver_id, lap_number));
CREATE INDEX IF NOT EXISTS idx_real_results_driver ON race_results(driver_id);
CREATE INDEX IF NOT EXISTS idx_real_results_team ON race_results(constructor_id);
CREATE INDEX IF NOT EXISTS idx_real_races_season ON races(season);