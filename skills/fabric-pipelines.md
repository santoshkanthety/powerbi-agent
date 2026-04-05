# Skill: Microsoft Fabric — Data Pipelines & Ingestion

## Trigger
Activate when the user mentions: data pipeline, ingestion, ETL, ELT, Fabric pipeline, Data Factory, copy activity, notebook, Spark, dataflow gen2, lakehouse, OneLake, data load, incremental load, watermark, CDC, change data capture, full load, delta load, pipeline orchestration

## What You Know

You have designed and delivered enterprise data pipelines across Azure Data Factory, Synapse, and now Microsoft Fabric. You understand the full ingestion stack from source connectors to Delta table landing, and you know every trick for incremental loading, CDC, and pipeline reliability.

## Ingestion Strategy Decision Tree

```
Source data changes how?
├── Full refresh (small tables <1M rows)   → Copy Activity, full load
├── Append-only (logs, events, IoT)        → Streaming / Eventstream
├── Inserts + Updates (CDC available)      → CDC with watermark
├── Inserts + Updates (no CDC)             → Watermark on modified_date
└── Deletes present                        → Full load OR CDC (SCD Type 2 in Silver)
```

## Bronze Layer Ingestion Patterns

### Pattern 1: Full Load (Small Dimensions)
```python
# Fabric Notebook — full load to Bronze Delta
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

df = spark.read.format("jdbc") \
    .option("url", "jdbc:sqlserver://server:1433;database=CRM") \
    .option("dbtable", "dbo.Customer") \
    .option("user", "{secret}") \
    .option("password", "{secret}") \
    .load()

# Add metadata
from pyspark.sql.functions import current_timestamp, lit
df = df \
    .withColumn("_ingested_at", current_timestamp()) \
    .withColumn("_source_system", lit("CRM"))

# Write to Bronze (overwrite for full load)
df.write.format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .save("abfss://bronze@onelake.dfs.fabric.microsoft.com/workspace/Tables/raw_crm_customer")
```

### Pattern 2: Watermark Incremental Load
```python
# Read last watermark from control table
watermark_df = spark.read.format("delta").load("abfss://bronze@.../control/watermarks")
last_watermark = watermark_df.filter("table_name = 'orders'").collect()[0]["last_value"]

# Load only new/changed records
df = spark.read.format("jdbc") \
    .option("dbtable", f"(SELECT * FROM dbo.Orders WHERE modified_date > '{last_watermark}') t") \
    .load()

# Merge into Bronze Delta (UPSERT)
from delta.tables import DeltaTable

target = DeltaTable.forPath(spark, "abfss://bronze@.../Tables/raw_erp_orders")
target.alias("t").merge(
    df.alias("s"),
    "t.order_id = s.order_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()

# Update watermark
new_watermark = df.agg({"modified_date": "max"}).collect()[0][0]
# ... update control table
```

### Pattern 3: Fabric Copy Activity (Low-Code)
Best for: Simple source → Lakehouse copies, 150+ connectors
- Use for initial historical loads
- Configure incremental column for delta loads
- Enable staging for large data volumes

## Silver Layer Transformation Patterns

### Data Quality Checks
```python
from pyspark.sql.functions import col, when, isnan, isnull, count

def validate_silver(df, table_name):
    """Standard Silver layer validation."""
    total = df.count()
    
    # Null checks on critical columns
    null_report = df.select([
        count(when(isnull(c) | isnan(c), c)).alias(c)
        for c in df.columns
    ])
    
    # Duplicate check on business key
    dupes = df.groupBy("customer_id").count().filter("count > 1").count()
    
    print(f"[{table_name}] Total: {total:,} | Nulls: {null_report.show()} | Dupes: {dupes:,}")
    
    if dupes > 0:
        raise ValueError(f"Duplicate business keys found in {table_name}")
```

### SCD Type 2 in Silver (Spark)
```python
from delta.tables import DeltaTable
from pyspark.sql.functions import current_timestamp, lit, col

def apply_scd2(spark, source_df, target_path, business_key_col, tracked_columns):
    target = DeltaTable.forPath(spark, target_path)
    
    # Identify changed records
    merge_condition = f"t.{business_key_col} = s.{business_key_col} AND t.is_current = true"
    
    # Expire changed records
    target.alias("t").merge(
        source_df.alias("s"), merge_condition
    ).whenMatchedUpdate(
        condition=" OR ".join([f"t.{c} != s.{c}" for c in tracked_columns]),
        set={
            "expiry_date": current_timestamp(),
            "is_current": lit(False)
        }
    ).execute()
    
    # Insert new/changed versions
    source_df \
        .withColumn("effective_date", current_timestamp()) \
        .withColumn("expiry_date", lit("9999-12-31").cast("timestamp")) \
        .withColumn("is_current", lit(True)) \
        .write.format("delta").mode("append").save(target_path)
```

## Pipeline Orchestration Best Practices

### Reliability Patterns
1. **Idempotent pipelines** — always safe to re-run
2. **Control table pattern** — track pipeline runs, watermarks, errors
3. **Dead letter queue** — capture failed records to a separate Delta table
4. **Retry logic** — 3 retries with exponential backoff
5. **Alerts** — email/Teams notification on pipeline failure

### Parallelism
```
# Run independent tables in parallel, not sequential
Pipeline:
├── Stage 1 (Parallel): Bronze loads for CRM, ERP, Files
├── Stage 2: Wait for all Bronze to complete
├── Stage 3 (Parallel): Silver transformations
├── Stage 4: Wait for Silver
└── Stage 5: Gold aggregations + semantic model refresh
```

## CLI Commands
```bash
# List Fabric pipelines in a workspace
pbi-agent fabric pipelines --workspace "Analytics Platform"

# Trigger a pipeline run
pbi-agent fabric pipeline-run --name "Bronze_CRM_Load" --workspace "Analytics Platform"

# Check pipeline run status
pbi-agent fabric pipeline-status --run-id "abc123"

# Trigger semantic model refresh after pipeline
pbi-agent fabric refresh "Sales Analytics" --workspace "Analytics Platform" --wait
```

## Anti-Patterns
- ❌ Running transformations in Bronze (keep it raw)
- ❌ Loading directly to Gold (always go through Silver)
- ❌ Truncate-and-reload for large fact tables (use upsert/merge)
- ❌ No watermarks (full load of 100M row tables daily is unsustainable)
- ❌ Hardcoding credentials in notebooks (use Key Vault linked services)
- ❌ Not compacting Delta tables (OPTIMIZE weekly)
