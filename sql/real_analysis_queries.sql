-- Starter analysis queries for the REAL F1 data (SQLite 3.25+)

-- 1. Championship standings per season (drivers)
SELECT r.season, RANK() OVER (PARTITION BY r.season ORDER BY SUM(x.points) DESC) AS pos,
       d.first_name || ' ' || d.last_name AS driver, SUM(x.points) AS points,
       SUM(x.position = 1) AS wins
FROM race_results x JOIN races r USING (race_id) JOIN drivers d USING (driver_id)
GROUP BY r.season, d.driver_id ORDER BY r.season, pos;

-- 2. How much does the starting grid decide the race? Win and podium rate by grid slot
SELECT grid, COUNT(*) AS starts, ROUND(100.0 * SUM(position = 1) / COUNT(*), 1) AS win_pct,
       ROUND(100.0 * SUM(position <= 3) / COUNT(*), 1) AS podium_pct
FROM race_results WHERE grid BETWEEN 1 AND 10 GROUP BY grid ORDER BY grid;

-- 3. Same question by circuit: average finishing position of front-row starters
SELECT c.name AS circuit, COUNT(*) AS front_row_starts, ROUND(AVG(x.position), 2) AS avg_finish_from_front_row
FROM race_results x JOIN races r USING (race_id) JOIN circuits c USING (circuit_id)
WHERE x.grid IN (1, 2) AND x.position_text GLOB '[0-9]*'
GROUP BY c.circuit_id HAVING front_row_starts >= 4 ORDER BY avg_finish_from_front_row DESC;

-- 4. Reliability: retirement rate by constructor and season
SELECT r.season, k.name AS constructor, COUNT(*) AS entries, SUM(x.position_text = 'R') AS retirements,
       ROUND(100.0 * SUM(x.position_text = 'R') / COUNT(*), 1) AS retirement_pct
FROM race_results x JOIN races r USING (race_id) JOIN constructors k USING (constructor_id)
GROUP BY r.season, k.constructor_id ORDER BY r.season, retirement_pct DESC;

-- 5. Overperformers: average places gained vs grid (classified finishers, grid > 0)
SELECT d.first_name || ' ' || d.last_name AS driver, COUNT(*) AS races,
       ROUND(AVG(x.grid - x.position), 2) AS avg_places_gained
FROM race_results x JOIN drivers d USING (driver_id)
WHERE x.grid > 0 AND x.position_text GLOB '[0-9]*'
GROUP BY d.driver_id HAVING races >= 20 ORDER BY avg_places_gained DESC LIMIT 15;

-- 6. Qualifying pace: average gap to pole (%) by constructor and season
WITH gap AS (
  SELECT q.race_id, q.constructor_id,
         100.0 * (q.best_s - MIN(q.best_s) OVER (PARTITION BY q.race_id)) / MIN(q.best_s) OVER (PARTITION BY q.race_id) AS gap_pct
  FROM qualifying q WHERE q.best_s IS NOT NULL)
SELECT r.season, k.name AS constructor, ROUND(AVG(g.gap_pct), 3) AS avg_gap_to_pole_pct
FROM gap g JOIN races r USING (race_id) JOIN constructors k USING (constructor_id)
GROUP BY r.season, k.constructor_id ORDER BY r.season, avg_gap_to_pole_pct;

-- 7. Pit stop performance by constructor (stops between 15 and 40 s to ignore red-flag and penalty outliers)
SELECT r.season, k.name AS constructor, COUNT(*) AS stops, ROUND(AVG(p.duration_s), 2) AS avg_stop_s
FROM pit_stops p JOIN races r USING (race_id)
JOIN race_results x ON x.race_id = p.race_id AND x.driver_id = p.driver_id
JOIN constructors k ON k.constructor_id = x.constructor_id
WHERE p.duration_s BETWEEN 15 AND 40
GROUP BY r.season, k.constructor_id HAVING stops >= 20 ORDER BY r.season, avg_stop_s;

-- 8. Does stopping more help? Places gained by number of pit stops (classified finishers)
SELECT x.pit_stops_n, COUNT(*) AS driver_races, ROUND(AVG(x.grid - x.position), 2) AS avg_places_gained
FROM (SELECT r.race_id, r.driver_id, r.grid, r.position, r.position_text,
             (SELECT COUNT(*) FROM pit_stops p WHERE p.race_id = r.race_id AND p.driver_id = r.driver_id) AS pit_stops_n
      FROM race_results r) x
WHERE x.grid > 0 AND x.position_text GLOB '[0-9]*' AND x.pit_stops_n > 0
GROUP BY x.pit_stops_n ORDER BY x.pit_stops_n;

-- 9. Teammate qualifying head-to-head (self join)
SELECT r.season, a.code AS driver_a, b.code AS driver_b,
       SUM(qa.position < qb.position) AS a_ahead, SUM(qa.position > qb.position) AS b_ahead
FROM qualifying qa JOIN qualifying qb ON qa.race_id = qb.race_id AND qa.constructor_id = qb.constructor_id AND qa.driver_id < qb.driver_id
JOIN races r ON r.race_id = qa.race_id
JOIN drivers a ON a.driver_id = qa.driver_id JOIN drivers b ON b.driver_id = qb.driver_id
GROUP BY r.season, a.driver_id, b.driver_id HAVING COUNT(*) >= 8 ORDER BY r.season;

-- 10. Race pace from lap data (needs --laps): average lap time excluding laps slower than 107% of the driver's best
WITH best AS (SELECT race_id, driver_id, MIN(lap_time_s) AS best_s FROM lap_times GROUP BY race_id, driver_id)
SELECT r.season, r.round, d.code, ROUND(AVG(l.lap_time_s), 3) AS avg_clean_lap_s
FROM lap_times l JOIN best b USING (race_id, driver_id) JOIN races r USING (race_id) JOIN drivers d USING (driver_id)
WHERE l.lap_time_s <= 1.07 * b.best_s GROUP BY l.race_id, l.driver_id ORDER BY r.season, r.round, avg_clean_lap_s LIMIT 20;