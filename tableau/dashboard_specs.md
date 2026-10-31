# Dashboard specs (1400 x 900, fixed size)

## 1. Championship

- Line chart: Round (columns), driver_cum_points (rows), Driver Name (color); filter Season. Label line ends only.
- Bar chart: season points by driver (sorted desc), colored by constructor.
- Bump chart: Round vs driver_championship_pos (reversed axis) for the top 8 drivers.
- KPI tiles: leader, wins, points gap to P2 for the selected season.
- Filters: Season, Constructor (apply the season filter to all sheets).

## 2. Race Pace

- Line chart: Lap Number vs Lap Time for the selected race (flat_lap_times), color by driver.
- Box plot: Green Lap Time by constructor.
- Position chart: Lap Number vs Position (reversed) per driver.
- Filters: Season, Race Label (single value), Weather.

## 3. Strategy

- Gantt chart: Driver on rows, Lap Number on columns, stint segments colored by tyre_compound.
- Line chart: Tyre Age vs Lap Delta to Race Median, color = compound (degradation curves).
- Bar chart: Avg Clean Pit Duration by constructor.
- Histogram: pit stop duration distribution.
- Filters: Season, Compound, Under Safety Car.

## 4. Reliability and Grid

- Bar chart: DNF Rate by constructor.
- Column chart: Win Rate by Grid Position.
- Heatmap: Driver x Race Label colored by Finish Position.
- Scatter: Avg Grid Position vs Avg Finish Position by driver, with trend line.
- Filters: Season, Weather.

## Design tips

- Dark theme with one fixed color per constructor across all dashboards.
- Dashboard actions: click a driver to highlight and filter other sheets.
- Tooltips with driver, team, points, wins.
