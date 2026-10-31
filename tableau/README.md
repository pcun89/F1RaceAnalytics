# Tableau

## 1. Connect

Run the Python scripts first, then connect to the flat tables in `data/bi/` (Text file connector):

| File | Use for |
| --- | --- |
| flat_race_results.csv | Standings, wins, grid vs finish, reliability (already has cumulative points and championship position) |
| flat_constructor_standings.csv | Constructor championship by round |
| flat_lap_times.csv | Race pace, position battle, tyre degradation |
| flat_pit_stops.csv | Pit stop and strategy analysis |
| flat_qualifying.csv | Qualifying and teammate comparisons |

To combine sources, relate them in the Data Model tab on `race_id` + `driver_id`.

## 2. Calculated fields

See [`calculated_fields.md`](calculated_fields.md).

## 3. Dashboards

See [`dashboard_specs.md`](dashboard_specs.md): Championship, Race Pace, Strategy, Reliability.

## 4. Publish

Save the workbook as `tableau/f1_dashboard.twbx`. Publish to Tableau Public for a shareable link and add it to the main README. Put screenshots in `tableau/screenshots/`.
