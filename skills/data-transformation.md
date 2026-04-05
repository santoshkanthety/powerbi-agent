# Skill: Data Transformation — Union, Append, Type Conversion & Light Joins

## Trigger
Activate when the user mentions: union, append, stack tables, combine datasets, convert data types, cast, type mismatch, key generation, surrogate key, hash key, join key, light join, merge, schema alignment, homogenise, data harmonisation, Power Query union, Spark union, M append, combine queries

## What You Know

You have harmonised data from dozens of source systems — different date formats, inconsistent key strategies, null handling, schema drift. You know every trick for making mismatched data play nicely, and you know when a "light join" is the right move vs a full dimensional join.

## Unioning / Appending Data

### Spark — Union Multiple Sources (with schema alignment)
```python
from pyspark.sql.functions import col, lit, current_timestamp
from functools import reduce

def union_with_schema_alignment(dfs: list) -> "DataFrame":
    """Union DataFrames with different schemas — fills missing columns with null."""
    # Find superset of all columns
    all_cols = list({col for df in dfs for col in df.columns})

    aligned = []
    for df in dfs:
        missing = [c for c in all_cols if c not in df.columns]
        for c in missing:
            df = df.withColumn(c, lit(None))
        aligned.append(df.select(all_cols))

    return reduce(lambda a, b: a.union(b), aligned)


# Usage: combine CRM + ERP + CSV contacts into one Bronze table
crm_df   = spark.read.format("delta").load(".../raw_crm_contact")
erp_df   = spark.read.format("delta").load(".../raw_erp_contact")
csv_df   = spark.read.option("header", True).csv(".../files/contacts.csv")

# Tag each source before unioning
crm_df  = crm_df.withColumn("_source_system", lit("CRM"))
erp_df  = erp_df.withColumn("_source_system", lit("ERP"))
csv_df  = csv_df.withColumn("_source_system", lit("CSV"))

combined = union_with_schema_alignment([crm_df, erp_df, csv_df])
```

### Power Query / M — Append Queries
```m
// Append CRM and ERP contact tables
let
    CRM_Contacts  = Excel.Workbook(...){[Name="CRM"]}[Data],
    ERP_Contacts  = Csv.Document(...),
    // Align schemas before appending
    CRM_Aligned   = Table.SelectColumns(CRM_Contacts, {"Name","Email","Phone","Source"}),
    ERP_Aligned   = Table.SelectColumns(ERP_Contacts, {"Name","Email","Phone","Source"}),
    Combined      = Table.Combine({CRM_Aligned, ERP_Aligned})
in
    Combined
```

## Type Conversion — The Right Way

### Spark Type Casting
```python
from pyspark.sql.functions import col, to_date, to_timestamp, regexp_replace, trim

df_typed = df \
    # String → Date (handle multiple formats)
    .withColumn("order_date",
        F.coalesce(
            to_date("order_date_raw", "yyyy-MM-dd"),
            to_date("order_date_raw", "dd/MM/yyyy"),
            to_date("order_date_raw", "MM-dd-yyyy")
        )
    ) \
    # String → Decimal (strip currency symbols first)
    .withColumn("amount",
        regexp_replace(trim(col("amount_str")), r"[£$€,]", "").cast("decimal(18,2)")
    ) \
    # String → Boolean (normalise yes/no/true/false/1/0)
    .withColumn("is_active",
        col("active_flag").isin("1", "true", "yes", "Y", "TRUE").cast("boolean")
    ) \
    # String → Integer ID (handle NULLs gracefully)
    .withColumn("customer_id",
        F.when(col("cust_id").isNotNull() & (col("cust_id") != ""),
               col("cust_id").cast("int"))
        .otherwise(lit(None).cast("int"))
    )
```

### Power Query / M — Type Conversion
```m
let
    Source = ...,
    // Convert multiple columns at once
    TypedTable = Table.TransformColumnTypes(Source, {
        {"OrderDate",    type date},
        {"Amount",       type number},
        {"CustomerID",   Int64.Type},
        {"IsActive",     type logical},
        {"Description",  type text}
    }),
    // Safe number parse (handles null/blank)
    SafeAmounts = Table.TransformColumns(TypedTable, {
        {"Amount", each if _ = null or _ = "" then null else Number.From(_), type number}
    })
in
    SafeAmounts
```

## Key Generation — Light Joins

### When to use a "light join" (hash key)
Use hash surrogate keys when:
- You need to join across sources without a master customer/product ID
- ETL must be idempotent (re-runnable without duplicating rows)
- Natural keys from multiple systems need to resolve to the same entity

```python
from pyspark.sql.functions import sha2, concat_ws, upper, trim, col

# Deterministic surrogate key: hash of business key fields
df = df.withColumn(
    "customer_key",
    sha2(
        concat_ws("|",
            upper(trim(col("first_name"))),
            upper(trim(col("last_name"))),
            upper(trim(col("email")))
        ),
        256
    )
)
# Same input → same hash → safe to join across sources without a lookup table
```

### Mapping/Lookup Join (Silver layer)
```python
# Load surrogate key mapping table (generated once in Silver)
key_map = spark.read.format("delta").load(".../silver/customer_key_map")

# Light join: enrich fact table with surrogate keys
fact_enriched = fact_df.join(
    key_map.select("natural_key", "customer_key"),
    fact_df["cust_id"] == key_map["natural_key"],
    how="left"
).drop("natural_key")

# Flag any unresolved keys for investigation
unresolved = fact_enriched.filter(col("customer_key").isNull())
if unresolved.count() > 0:
    unresolved.write.format("delta").mode("append").save(".../silver/unresolved_keys")
```

## Schema Drift Handling
```python
# Auto-merge schema when source adds new columns (Bronze only)
df.write.format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save(target_path)

# Detect schema drift before Silver transformation
def check_schema_drift(expected_cols: list, actual_df):
    missing = [c for c in expected_cols if c not in actual_df.columns]
    extra   = [c for c in actual_df.columns if c not in expected_cols]
    if missing:
        raise ValueError(f"Missing columns in source: {missing}")
    if extra:
        print(f"[WARNING] New columns detected (not yet in Silver): {extra}")
```

## CLI Commands
```bash
# Union two Delta tables with automatic schema alignment
pbi-agent fabric union-tables \
  --source1 "bronze.raw_crm_customer" \
  --source2 "bronze.raw_erp_customer" \
  --output "silver.stg_customer_combined" \
  --source-tag-col "_source_system"

# Generate hash surrogate keys on a Silver table
pbi-agent fabric generate-keys \
  --table "silver.stg_customer" \
  --key-cols "first_name,last_name,email" \
  --output-col "customer_key"

# Profile data types and suggest corrections
pbi-agent fabric profile-types --table "bronze.raw_crm_customer"
```
