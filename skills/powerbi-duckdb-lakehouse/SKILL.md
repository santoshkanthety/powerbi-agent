---
name: powerbi-duckdb-lakehouse
description: Query Fabric lakehouse Delta tables, warehouse data and OneLake Parquet with DuckDB — locally or inside a Fabric notebook — for data profiling, freshness and quality checks, and reconciling a semantic model against its source without paying Spark cold-start or capacity cost. Use when the user mentions: DuckDB, duckdb, query Delta locally, read Parquet without Spark, profile lakehouse data, data freshness check, data quality check, row count reconciliation, compare model to source, cheap lakehouse query, delta_scan, OneLake Parquet, local SQL over OneLake.
license: MIT
---

# DuckDB over lakehouse and OneLake data

DuckDB is an in-process SQL engine that reads Parquet and Delta directly. Pointed at OneLake,
it answers most of the questions people reach for Spark to answer — row counts, distincts,
null rates, min/max dates, a reconciliation against what the semantic model reports — with no
cluster, no cold start, and **no capacity consumption**.

That last point is the reason this skill exists. A freshness check that costs nothing can run
on every delivery; one that opens a Spark session and smooths CU forward for 24 hours cannot.

Reach for DuckDB first. Reach for `powerbi-spark-livy` only when the volume or the
transformation genuinely needs distributed compute.

## Where it runs

| Location | Use when |
|---|---|
| **Local** (your machine, this CLI) | Profiling, reconciliation, quality gates, anything in a delivery loop. Needs OneLake access from the host. |
| **Inside a Fabric notebook** | Data is large enough that pulling it to the host is the bottleneck, but small enough that Spark is overkill. Still cheaper than a Spark session on the same notebook. |

## Setup

```bash
pip install duckdb        # or: uv pip install duckdb
```

Extensions, loaded per connection:

```python
import duckdb

con = duckdb.connect()
con.execute("INSTALL azure; LOAD azure;")   # ABFSS / OneLake access
con.execute("INSTALL delta; LOAD delta;")   # Delta log awareness — not just the Parquet files
```

`INSTALL` needs network access once; on an air-gapped build host, pre-seed the extension
directory and skip `INSTALL`.

### Authentication to OneLake

Use the Azure credential chain rather than a key or a SAS token:

```python
con.execute("""
    CREATE SECRET onelake (
        TYPE azure,
        PROVIDER credential_chain,
        CHAIN 'cli;env;managed_identity',
        ACCOUNT_NAME 'onelake'
    );
""")
```

That picks up `az login` locally and a managed identity in a hosted runtime. Confirm the exact
clause names against the DuckDB azure extension docs for your installed version — the secret
syntax has changed across DuckDB releases and a wrong clause fails with a parse error rather
than an auth error.

Never embed an account key, a SAS token or a bearer token in SQL — it lands in query logs and
in whatever file you saved the script to.

## Reading lakehouse data

OneLake paths follow the ABFSS shape:

```
abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<item>.Lakehouse/Tables/<schema>/<table>
abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<item>.Lakehouse/Files/<path>
```

```sql
-- Delta table, honouring the transaction log (correct row counts after updates/deletes)
SELECT count(*) FROM delta_scan(
  'abfss://analytics@onelake.dfs.fabric.microsoft.com/bronze.Lakehouse/Tables/dbo/orders'
);

-- Raw Parquet, including globs and Hive-style partitions
SELECT count(*) FROM read_parquet(
  'abfss://analytics@onelake.dfs.fabric.microsoft.com/bronze.Lakehouse/Files/raw/orders/**/*.parquet',
  hive_partitioning = true
);
```

**Use `delta_scan`, not `read_parquet`, on a Delta table.** Reading the underlying Parquet
files directly ignores the transaction log, so deleted and superseded rows come back and your
count is wrong — and wrong in the direction that looks like a genuine data discrepancy. This
is the single most common error in this workflow.

Warehouse tables are reachable the same way through the warehouse item's OneLake path, or over
the SQL endpoint with a SQL client when you need warehouse semantics rather than file reads.

## The three jobs this does well

### 1. Profiling

```sql
SELECT
    count(*)                                        AS rows,
    count(DISTINCT customer_id)                     AS customers,
    count(*) FILTER (WHERE customer_id IS NULL)     AS null_customer,
    min(order_date)                                 AS first_order,
    max(order_date)                                 AS last_order,
    sum(amount)                                     AS total_amount
FROM delta_scan('abfss://.../Tables/dbo/orders');
```

Run this before designing a star schema, not after. Cardinality, null rates and date range
decide the grain, the partitioning and whether a column belongs in a dimension —
`powerbi-star-schema-modeling`.

### 2. Freshness and quality gates

```sql
-- Freshness: is the source newer than the model's last refresh?
SELECT max(order_date) AS source_max FROM delta_scan('abfss://.../Tables/dbo/orders');

-- Referential integrity before it becomes a blank row in a report
SELECT count(*) AS orphans
FROM delta_scan('abfss://.../Tables/dbo/orders')      o
LEFT JOIN delta_scan('abfss://.../Tables/dbo/customer') c USING (customer_id)
WHERE c.customer_id IS NULL;

-- Duplicate grain
SELECT order_id, count(*) AS n
FROM delta_scan('abfss://.../Tables/dbo/orders')
GROUP BY order_id HAVING count(*) > 1 LIMIT 20;
```

These are the checks that belong in a delivery gate (`powerbi-testing-validation`). Because
they cost nothing, they can run on every change rather than once at UAT.

### 3. Reconciling a model against its source

The question that ends most "the number is wrong" escalations: does the model agree with the
lakehouse?

```bash
# Source side — DuckDB over the lakehouse
#   SELECT sum(amount) FROM delta_scan('abfss://.../Tables/dbo/orders') WHERE year(order_date)=2026

# Model side — DAX over the semantic model
pbi-agent dax query "EVALUATE ROW(\"Total\", CALCULATE([Total Sales], 'Date'[Year] = 2026))"
```

Compare the two. A mismatch is one of: a Power Query filter or type coercion
(`powerbi-power-query`), a relationship dropping rows, measure logic, or an incremental
refresh partition that never reloaded (`powerbi-refresh-semantic-model`). Narrow it by
reconciling at successively finer grain — year, then month, then one key — rather than
guessing.

## Limits — know them before promising

- **Single machine, single process.** Memory-bound. A wide join across two multi-hundred-GB
  fact tables belongs in Spark. Set `SET memory_limit` and `SET threads` explicitly on a
  shared host rather than letting it take everything.
- **Egress.** Local reads pull bytes out of OneLake across the network. Project the columns
  you need and push filters into the scan; `SELECT *` over a wide fact table is slow for a
  reason that is not DuckDB's fault.
- **Read-only, by policy here.** DuckDB can write Parquet and Delta, but a lakehouse table's
  writer should be the pipeline that owns it, not an ad-hoc profiling script. Write to a local
  file or a scratch path, and never to a bronze/silver/gold table without explicit
  confirmation naming the table.
- **Delta feature coverage** varies by extension version — column mapping, deletion vectors
  and newer protocol features may not be supported. If a `delta_scan` count disagrees with
  Spark's, suspect the extension version before suspecting the data.
- **Not a semantic layer.** DuckDB answers what is in the source. It does not and cannot tell
  you what a measure means — that is the model's job.

## Related skills

| Need | Skill |
|---|---|
| Distributed compute, real transforms | `powerbi-spark-livy`, `powerbi-fabric-pipelines` |
| Layer design the profile informs | `powerbi-medallion-architecture`, `powerbi-star-schema-modeling` |
| Turning checks into a delivery gate | `powerbi-testing-validation` |
| Why source and model disagree | `powerbi-power-query`, `powerbi-refresh-semantic-model` |
| Cost of the Spark alternative | `powerbi-fabric-capacity` |
| Non-OneLake sources | `powerbi-source-integration` |
