# Power BI

## 1. Load data

1. Run the Python scripts first so `data/bi/` exists.
2. **Get Data > Text/CSV**, and load these files from `data/bi/`:
   `dim_constructor`, `dim_driver`, `dim_circuit`, `dim_race`, `dim_date`, `fact_race_results`, `fact_lap_times`, `fact_pit_stops`, `fact_qualifying`.
3. Set `dim_date[date]` and `dim_race[race_date]` to **Date**, then **Mark as date table** on `dim_date`.

## 2. Model (star schema)

Create these relationships (all one-to-many, single direction, dimension to fact):

| From (one) | To (many) |
| --- | --- |
| dim_driver[driver_id] | fact_race_results, fact_lap_times, fact_pit_stops, fact_qualifying |
| dim_constructor[constructor_id] | fact_race_results, dim_driver |
| dim_race[race_id] | fact_race_results, fact_lap_times, fact_pit_stops, fact_qualifying |
| dim_circuit[circuit_id] | dim_race |
| dim_date[date] | dim_race[race_date] |

Hide the foreign keys in the report view and put the measures from `dax_measures.dax` in a table called `_Measures`.

## 3. Report pages

| Page | Visuals |
| --- | --- |
| Championship | Line chart of cumulative points by round (legend = driver, filter season); standings table with Points, Wins, Podiums; constructor bar chart; season slicer |
| Race Pace | Line chart of lap time by lap (one race, legend = driver); avg green-lap time by constructor; weather slicer |
| Strategy | Stint length by tyre compound; tyre age vs avg lap delta (degradation curves); pit stop duration by constructor |
| Reliability and Grid | DNF rate by constructor; win rate by grid position; positions gained by driver; matrix of finish position by driver x race |

Tips: add a drill-through page from driver to a driver profile, bookmarks for a season toggle, and a tooltip page with a mini points trend.

## 4. Publish

Save as `powerbi/f1_dashboard.pbix`, export page screenshots to `powerbi/screenshots/`, and publish to the Power BI Service for a shareable link.
