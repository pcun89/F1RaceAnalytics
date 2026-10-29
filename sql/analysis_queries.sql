-- F1 analysis queries (SQLite 3.25+ / most work in Postgres with minor tweaks)

-- 1. Final driver championship standings per season
SELECT season, RANK() OVER (PARTITION BY season ORDER BY SUM(points) DESC) AS pos,
       d.first_name || ' ' || d.last_name AS driver, SUM(points) AS points,
       SUM(finish_position = 1) AS wins
FROM race_results rr JOIN races r USING (race_id) JOIN drivers d USING (driver_id)
GROUP BY season, d.driver_id ORDER BY season, pos;

-- 2. Running points total per driver (window function)
SELECT r.season, r.round, d.code,
       SUM(rr.points) OVER (PARTITION BY r.season, d.driver_id ORDER BY r.round) AS cumulative_points
FROM race_results rr JOIN races r USING (race_id) JOIN drivers d USING (driver_id)
ORDER BY r.season, r.round, cumulative_points DESC;

-- 3. Constructor standings
SELECT r.season, c.name AS constructor, SUM(rr.points) AS points
FROM race_results rr JOIN races r USING (race_id) JOIN constructors c ON c.constructor_id = rr.constructor_id
GROUP BY r.season, c.constructor_id ORDER BY r.season, points DESC;

-- 4. Win rate by starting grid position
SELECT grid_position, COUNT(*) AS starts, SUM(finish_position = 1) AS wins,
       ROUND(100.0 * SUM(finish_position = 1) / COUNT(*), 1) AS win_pct
FROM race_results GROUP BY grid_position ORDER BY grid_position LIMIT 10;

-- 5. Biggest overtakers: average positions gained (finishers only)
SELECT d.code, ROUND(AVG(positions_gained), 2) AS avg_pos_gained, COUNT(*) AS finishes
FROM race_results rr JOIN drivers d USING (driver_id)
WHERE status IN ('Finished','Lapped') GROUP BY d.driver_id HAVING finishes >= 20
ORDER BY avg_pos_gained DESC;

-- 6. Tyre degradation: avg green-flag lap delta by compound and tyre age (dry races)
SELECT l.tyre_compound, l.tyre_age_laps, ROUND(AVG(l.lap_time_s - c.base_lap_time_s), 3) AS avg_delta_to_base_s, COUNT(*) AS laps
FROM lap_times l JOIN races r USING (race_id) JOIN circuits c USING (circuit_id)
WHERE l.safety_car = 0 AND l.is_pit_lap = 0 AND l.lap_number > 1 AND r.weather <> 'Wet'
GROUP BY l.tyre_compound, l.tyre_age_laps HAVING laps >= 30 ORDER BY l.tyre_compound, l.tyre_age_laps;

-- 7. Average pit stop duration by constructor (ignores missing values and slow-stop outliers)
SELECT c.name, ROUND(AVG(p.pit_duration_s), 2) AS avg_stop_s, COUNT(*) AS stops
FROM pit_stops p JOIN drivers d USING (driver_id) JOIN constructors c ON c.constructor_id = d.constructor_id
WHERE p.pit_duration_s IS NOT NULL AND p.pit_duration_s < 5 GROUP BY c.constructor_id ORDER BY avg_stop_s;

-- 8. Retirement (DNF) rate by constructor
SELECT c.name, COUNT(*) AS entries, SUM(status NOT IN ('Finished','Lapped')) AS dnfs,
       ROUND(100.0 * SUM(status NOT IN ('Finished','Lapped')) / COUNT(*), 1) AS dnf_pct
FROM race_results rr JOIN constructors c USING (constructor_id) GROUP BY c.constructor_id ORDER BY dnf_pct DESC;

-- 9. Wet vs dry performance: average finish position by driver
SELECT d.code, SUM(r.weather='Wet') AS wet_races,
       ROUND(AVG(CASE WHEN r.weather='Wet' THEN rr.finish_position END), 2) AS avg_finish_wet,
       ROUND(AVG(CASE WHEN r.weather<>'Wet' THEN rr.finish_position END), 2) AS avg_finish_dry
FROM race_results rr JOIN races r USING (race_id) JOIN drivers d USING (driver_id)
GROUP BY d.driver_id ORDER BY d.code;

-- 10. Teammate qualifying head-to-head (self join)
SELECT a.code AS driver_a, b.code AS driver_b,
       SUM(qa.qualifying_position < qb.qualifying_position) AS a_ahead,
       SUM(qa.qualifying_position > qb.qualifying_position) AS b_ahead
FROM qualifying qa JOIN qualifying qb ON qa.race_id = qb.race_id AND qa.driver_id < qb.driver_id
JOIN drivers a ON a.driver_id = qa.driver_id
JOIN drivers b ON b.driver_id = qb.driver_id AND a.constructor_id = b.constructor_id
GROUP BY a.driver_id, b.driver_id;

-- 11. Races with the most on-track position gains, using LAG (pit laps excluded)
WITH x AS (
  SELECT race_id, driver_id, lap_number, position, is_pit_lap,
         LAG(position) OVER (PARTITION BY race_id, driver_id ORDER BY lap_number) AS prev_pos
  FROM lap_times)
SELECT r.season, r.round, SUM(prev_pos > position AND is_pit_lap = 0) AS positions_gained_on_track
FROM x JOIN races r USING (race_id) GROUP BY race_id ORDER BY positions_gained_on_track DESC LIMIT 10;

-- 12. Fastest laps ranked relative to circuit base time
SELECT r.season, r.round, d.code, rr.fastest_lap_time_s,
       RANK() OVER (PARTITION BY r.season ORDER BY rr.fastest_lap_time_s / c.base_lap_time_s) AS relative_rank
FROM race_results rr JOIN races r USING (race_id) JOIN circuits c USING (circuit_id) JOIN drivers d USING (driver_id)
WHERE rr.fastest_lap_award = 1 ORDER BY r.season, relative_rank LIMIT 10;    
