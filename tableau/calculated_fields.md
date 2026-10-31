# Calculated fields

Set `race_date` to Date, and `season` and `round` to discrete dimensions.

**Win Rate**

```
SUM([is_win]) / COUNT([result_id])
```

**DNF Rate**

```
SUM([is_dnf]) / COUNT([result_id])
```

**Avg Positions Gained (finishers)**

```
AVG(IF [is_dnf] = 0 THEN [positions_gained] END)
```

**Season Points (LOD)**

```
{ FIXED [season], [driver_name] : SUM([points]) }
```

**Driver Season Rank**

```
RANK_DENSE(SUM([points]))
```

**Green Lap Time** (flat_lap_times)

```
IF [is_green_lap] = 1 THEN [lap_time_s] END
```

**Lap Delta to Race Median** (flat_lap_times)

```
[lap_time_s] - { FIXED [race_id] : MEDIAN(IF [is_green_lap] = 1 THEN [lap_time_s] END) }
```

**Clean Pit Duration** (flat_pit_stops)

```
IF [pit_duration_s] < 5 THEN [pit_duration_s] END
```

**Slow Stop Flag**

```
IF [pit_duration_s] >= 5 THEN "Slow stop" ELSE "Normal" END
```

