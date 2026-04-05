# Skill: Time Series Data — Consolidation, Gaps, Normalisation & Binning

## Trigger
Activate when the user mentions: time series, gaps in data, missing dates, sparse data, irregular intervals, binning, time buckets, rounding timestamps, 5-minute intervals, hourly buckets, normalise time, fill gaps, spine, date spine, continuous axis, aggregation over time, interval aggregation, IoT, sensor data, event data, tick data

## What You Know

You have handled time series at every scale — from financial tick data (microsecond resolution) to IoT sensor streams (millions of events per day) to monthly business KPIs. You know how to identify gaps, normalise irregular timestamps to clean intervals, and build the aggregation patterns Power BI needs to work correctly.

## Step 1: Identify Gaps in Time Series

### In Spark (Silver layer)
```python
from pyspark.sql.functions import col, lag, datediff, unix_timestamp
from pyspark.sql.window import Window

w = Window.partitionBy("sensor_id").orderBy("event_time")

df_gaps = df \
    .withColumn("prev_time", lag("event_time").over(w)) \
    .withColumn("gap_seconds",
        unix_timestamp("event_time") - unix_timestamp("prev_time")) \
    .filter(col("gap_seconds") > 300)  # flag gaps > 5 minutes

df_gaps.select("sensor_id", "prev_time", "event_time", "gap_seconds").show()
```

### In DAX (Report layer — detect missing date rows)
```dax
-- Count days with zero transactions (gaps in your date table)
Days With No Sales =
CALCULATE(
    COUNTROWS(dim_date),
    FILTER(
        dim_date,
        CALCULATE([Total Sales]) = 0 || ISBLANK(CALCULATE([Total Sales]))
    )
)

-- Flag a gap period in a line chart (show as dashed or zero)
Sales Filled =
IF(ISBLANK([Total Sales]), 0, [Total Sales])
```

### In Power Query / M
```m
// Generate a complete date spine (no gaps) and left-join your data onto it
let
    StartDate = #date(2020, 1, 1),
    EndDate = Date.From(DateTime.LocalNow()),
    DayCount = Duration.Days(EndDate - StartDate) + 1,
    DateList = List.Dates(StartDate, DayCount, #duration(1,0,0,0)),
    DateTable = Table.FromList(DateList, Splitter.SplitByNothing(), {"Date"}),
    MergedWithData = Table.NestedJoin(DateTable, "Date", YourData, "TransactionDate", "Data", JoinKind.LeftOuter)
in
    MergedWithData
```

## Step 2: Binning to Rounded Intervals

### Round timestamps to fixed intervals (Spark)
```python
from pyspark.sql.functions import (
    col, floor, from_unixtime, unix_timestamp, date_trunc
)

INTERVAL_MINUTES = 15  # Change to 5, 30, 60 as needed

df_binned = df.withColumn(
    "time_bin",
    from_unixtime(
        floor(unix_timestamp("event_time") / (INTERVAL_MINUTES * 60)) * (INTERVAL_MINUTES * 60)
    ).cast("timestamp")
)
```

### Aggregate to binned intervals
```python
df_agg = df_binned.groupBy("sensor_id", "time_bin").agg(
    F.avg("temperature").alias("avg_temp"),
    F.max("temperature").alias("max_temp"),
    F.min("temperature").alias("min_temp"),
    F.count("*").alias("reading_count"),
    F.first("status").alias("first_status"),
    F.last("status").alias("last_status"),
)
```

### Binning in DAX (dynamic bucket sizes)
```dax
-- Bin sales into $500 buckets
Sales Bucket =
VAR BucketSize = 500
VAR RawValue = [Total Sales per Customer]
RETURN
    FLOOR(RawValue, BucketSize) & " – " & (FLOOR(RawValue, BucketSize) + BucketSize - 1)

-- Age binning
Age Group =
SWITCH(
    TRUE(),
    Customer[Age] < 18,  "Under 18",
    Customer[Age] < 25,  "18–24",
    Customer[Age] < 35,  "25–34",
    Customer[Age] < 45,  "35–44",
    Customer[Age] < 55,  "45–54",
    Customer[Age] < 65,  "55–64",
    "65+"
)
```

## Step 3: Fill Gaps — Create a Complete Time Spine

### Full-resolution Date×Dimension spine (Spark)
```python
# Cross join date spine with all sensor IDs to create a complete grid
date_spine = spark.range(0, 8760).select(  # 8760 hours in a year
    (F.to_timestamp("2024-01-01") + F.expr("INTERVAL id HOURS")).alias("hour_bin")
)

sensors = df.select("sensor_id").distinct()
spine = date_spine.crossJoin(sensors)

# Left join actual readings onto the spine
full_df = spine.join(df_hourly, on=["hour_bin", "sensor_id"], how="left")

# Forward-fill missing values (LOCF — Last Observation Carried Forward)
w = Window.partitionBy("sensor_id").orderBy("hour_bin").rowsBetween(Window.unboundedPreceding, 0)
full_df = full_df.withColumn("temp_filled", F.last("temperature", ignorenulls=True).over(w))
```

## Step 4: Normalisation

### Z-Score normalisation (per sensor, per day)
```python
from pyspark.sql.functions import stddev, mean

stats = df.groupBy("sensor_id").agg(
    mean("value").alias("mu"),
    stddev("value").alias("sigma")
)

df_norm = df.join(stats, "sensor_id") \
    .withColumn("z_score", (col("value") - col("mu")) / col("sigma"))
```

### Min-Max normalisation to [0, 1]
```python
from pyspark.sql.functions import min as spark_min, max as spark_max

bounds = df.groupBy("sensor_id").agg(
    spark_min("value").alias("min_v"),
    spark_max("value").alias("max_v")
)
df_scaled = df.join(bounds, "sensor_id") \
    .withColumn("scaled", (col("value") - col("min_v")) / (col("max_v") - col("min_v")))
```

## CLI Commands
```bash
# Detect gaps in a Delta table time series column
pbi-agent fabric detect-gaps \
  --table "bronze.iot_temperature" \
  --time-col "event_time" \
  --partition-col "sensor_id" \
  --max-gap-seconds 300

# Bin a column and write aggregated table to Silver
pbi-agent fabric bin-time \
  --table "bronze.iot_temperature" \
  --time-col "event_time" \
  --interval-minutes 15 \
  --agg "avg:temperature,max:temperature,count:*" \
  --output "silver.iot_temp_15min"
```
