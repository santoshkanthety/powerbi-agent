# Skill: Source Integration & Data Model Development

## Trigger
Activate when the user mentions: data source, connect source, ingest data, database connection, API connection, CSV upload, web scrape, source connector, raw data model, normalize, Bronze ingestion, source mapping, data model development, config tool, pbi-agent ui, configuration tool, rule engine, pipeline setup, source to Bronze, multi-source, PostgreSQL, postgres, JDBC, RDS, Aurora, Azure Database for PostgreSQL, Cloud SQL, read replica, DirectQuery postgres, incremental refresh postgres

## What You Know

You have integrated 50+ source systems into enterprise data platforms — from SAP ERP to Salesforce CRM, REST APIs to flat file drops, web scrapes to real-time streams. You know the full journey from "we have data in X" to "it's landed, clean, and queryable in OneLake."

## The Configuration Tool

powerbi-agent includes a browser-based configuration tool for designing the full pipeline visually:

```bash
# Launch the web UI (opens browser automatically)
pbi-agent ui

# Specify a project and port
pbi-agent ui --project my-platform --port 9000
```

The UI covers:
1. **Data Sources** — connect DB, API, CSV, web scrape
2. **Rule Engine** — quality checks and transformations
3. **Data Model** — Bronze/Silver/Gold table designer
4. **Fabric Pipeline** — workspace, lakehouse, refresh config

## Source Type Patterns

### Database Sources
```python
# Supported: SQL Server, PostgreSQL, MySQL, Oracle, Snowflake, SQLite
# Connection: JDBC or pyodbc
# Key settings:
#   - Load strategy: full_load | incremental | cdc
#   - Watermark column: the "modified_date" equivalent
#   - Schema + table list (or empty for all tables)

# Best practices:
# - Prefer incremental over full_load for tables > 100K rows
# - Use Key Vault for credentials, never hardcode
# - Test connection before scheduling pipeline
```

---

## PostgreSQL

PostgreSQL is fully supported across all Power BI / Fabric integration paths. Choose the right approach based on data volume and latency requirements.

### Connection Modes — Decision Guide

| Scenario | Recommended Mode |
|---|---|
| Small tables (<1M rows), low latency | DirectQuery |
| Large tables (>1M rows), fast dashboards | Import (scheduled refresh) |
| Fabric Lakehouse as intermediary | Copy Activity (Fabric Pipeline) → OneLake → DirectLake |
| Real-time streaming data | Eventstream → Lakehouse → DirectLake |

### Power BI Desktop — Direct Connection

```
Get Data → Database → PostgreSQL Database
  Server:   db.example.com          (or db.example.com:5432)
  Database: prod_db
  Data Connectivity mode:
    • Import     — loads data into model (recommended for most cases)
    • DirectQuery — live queries to PostgreSQL (use only for <10M rows and fast server)
```

**Credential setup (first time only):**
```
Connection settings → Database credentials
  Authentication type: Database
  User name: readonly_user          ← always use a dedicated read-only account
  Password:  [stored in credential manager, not in the .pbix file]
```

### Native Query (SQL Pushdown)

Use Native Query to push complex SQL directly to PostgreSQL instead of loading whole tables:

```
Get Data → PostgreSQL → Advanced Options → SQL Statement:

SELECT
  o.order_id,
  o.order_date,
  o.revenue,
  c.region,
  c.segment
FROM public.orders o
JOIN public.customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= CURRENT_DATE - INTERVAL '365 days'
  AND o.order_status != 'cancelled'
```

> **Important**: Native Query disables query folding for subsequent Power Query steps. Apply all filters in the SQL, then do minimal M transformations after.

### Power Query M — Parameterised Connection

```m
// Parameterise host and database for environment switching (dev/prod)
let
    PgHost     = "db.example.com",
    PgDatabase = "prod_db",
    Source     = PostgreSQL.Database(PgHost, PgDatabase,
                     [Query = "SELECT * FROM public.orders
                               WHERE updated_at >= #datetimezone(2024,1,1,0,0,0,0,0)"]),
    Typed = Table.TransformColumnTypes(Source, {
        {"order_id",   Int64.Type},
        {"order_date", type date},
        {"revenue",    type number}
    })
in
    Typed
```

### SSL / TLS (RDS, Azure Database for PostgreSQL, Cloud SQL)

Managed PostgreSQL services require SSL. Configure in Power BI Desktop:

```
Get Data → PostgreSQL → Advanced Options
  Additional connection string properties:
    sslmode=require
```

For Azure Database for PostgreSQL — Flexible Server:
```
Server: myserver.postgres.database.azure.com
Additional: sslmode=require;Trust Server Certificate=false
```

### Incremental Refresh with PostgreSQL

Incremental refresh requires a `RangeStart` / `RangeEnd` Power Query parameter pattern. PostgreSQL supports this via query folding when using the native connector:

```m
// In Power Query — use RangeStart / RangeEnd parameters (set as Date/Time)
let
    Source = PostgreSQL.Database("db.example.com", "prod_db"),
    orders = Source{[Schema="public", Item="orders"]}[Data],
    // This WHERE clause folds to PostgreSQL — enables incremental refresh
    Filtered = Table.SelectRows(orders, each
        [order_date] >= RangeStart and [order_date] < RangeEnd
    )
in
    Filtered
```

Then in the dataset settings → Incremental refresh:
```
Archive data starting: 3 years before refresh date
Incrementally refresh data starting: 7 days before refresh date
Detect data changes: updated_at   ← optional, PostgreSQL supports this
```

### Fabric Pipeline — PostgreSQL → OneLake (for large tables)

For tables > 5M rows, ingest via Fabric Pipeline into a Lakehouse first, then connect Power BI via DirectLake:

```
Fabric Pipeline:
  Source:      PostgreSQL (JDBC)
    Host:      db.example.com
    Port:      5432
    Database:  prod_db
    Table:     public.orders
    Query:     SELECT * FROM public.orders WHERE updated_at > @{pipeline().parameters.watermark}
  Sink:        Lakehouse → Files → bronze/orders/
  Format:      Parquet (auto-converted to Delta on shortcut)

Next step: Create a Delta table in the Lakehouse from the Parquet files
           Then attach a Power BI Semantic Model via DirectLake
```

```bash
# CLI: configure PostgreSQL source in pbi-agent UI
pbi-agent ui   # then add PostgreSQL source in Sources tab

# Test connection
pbi-agent source test-connection --type postgres \
  --host db.example.com --port 5432 --database prod_db

# Ingest to Bronze lakehouse via Fabric pipeline
pbi-agent fabric ingest --source postgres \
  --table public.orders \
  --target bronze.pg_orders \
  --mode incremental \
  --watermark updated_at
```

### Performance Rules for PostgreSQL in Power BI

| Rule | Detail |
|---|---|
| **Use a read replica** | Never point Power BI at your primary write node |
| **Create covering indexes** | Index every column used in `WHERE` / `JOIN` in your M query |
| **Avoid VOLATILE functions in SQL** | Prevents query folding (e.g. `NOW()` — use parameters instead) |
| **Enable query folding** | Check: right-click a step → "View Native Query" — if greyed out, folding is broken |
| **Import over DirectQuery** | For dashboards with >100K rows, Import + scheduled refresh outperforms DirectQuery |
| **Connection pool size** | Set `Max connections` to match your pg_hba.conf limit (default 100) |

### REST API Sources
```python
# Supported patterns: offset pagination, cursor, Link header
# Auth: bearer token, API key, OAuth2, basic
# Key settings:
#   - Watermark field: the "updatedAt" equivalent in the API response
#   - Page size: match API limits (typically 100–1000)

# Example — paginated REST ingestion:
import httpx

def ingest_api(base_url, token, watermark_value, page_size=100):
    headers = {"Authorization": f"Bearer {token}"}
    page, all_records = 0, []
    while True:
        resp = httpx.get(f"{base_url}?since={watermark_value}&limit={page_size}&offset={page*page_size}",
                         headers=headers, timeout=30)
        data = resp.json().get("data", [])
        if not data:
            break
        all_records.extend(data)
        page += 1
    return all_records
```

### CSV Sources
```python
# Best for: historical data loads, one-time migrations, partner file drops
# Key considerations:
#   - Validate encoding before load (UTF-8, Latin-1, CP1252)
#   - Infer or specify schema (never trust auto-detect for production)
#   - Watch for: BOM markers, mixed line endings, quoted commas

from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
df = spark.read \
    .option("header", "true") \
    .option("inferSchema", "false") \          # Always false — define schema
    .option("encoding", "UTF-8") \
    .option("quote", '"') \
    .option("escape", '"') \
    .schema(your_defined_schema) \
    .csv("abfss://bronze@.../files/upload.csv")
```

### Web Scrape Sources
```python
# Use only when no API exists and you have permission
# Rate limit: always respect robots.txt and add delays
# Key libraries: requests-html, playwright, beautifulsoup4

from bs4 import BeautifulSoup
import httpx, time

def scrape_table(url, css_selector, max_pages=10):
    records = []
    for page in range(1, max_pages + 1):
        resp = httpx.get(f"{url}?page={page}",
                         headers={"User-Agent": "powerbi-agent/1.0"})
        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select(css_selector)
        if not rows:
            break
        records.extend([row.get_text(strip=True) for row in rows])
        time.sleep(1.0)   # Rate limit
    return records
```

## Raw Storage Data Model — Design Principles

### Normalization for Bronze (3NF is NOT the goal here)
Bronze is NOT normalized. It mirrors the source exactly:
- One Bronze table per source entity/endpoint
- No joins, no derived columns
- Add only `_ingested_at`, `_source_system`, `_file_name` metadata columns
- Store as Delta with append/merge — never truncate

### Silver: Light Normalization (2NF–3NF)
- Remove repeating groups and partial dependencies
- Standardize data types across sources
- Apply business key → surrogate key mapping
- This is where SCD Type 2 lives

### Gold: De-normalize for Analytics (Kimball)
- Flatten for Power BI performance
- Star schema over normalized schema
- See `star-schema-modeling` skill for full guidance

## Rule Engine Design

Design rules in this order:
```
1. Structural checks (schema, data types) → fail_pipeline on error
2. Not-null on critical keys              → fail_pipeline on error
3. Uniqueness on business keys            → quarantine duplicates
4. Format/regex validation                → flag_and_pass for soft errors
5. Range checks                           → flag_and_pass for out-of-bounds
6. Transformations (trim, cast, rename)   → apply silently
7. Derivations (hash keys, flags)         → apply silently
```

## CLI Commands for Source Management
```bash
# Launch config UI
pbi-agent ui --project my-platform

# Test a database connection
pbi-agent source test-connection --source-id abc123 --project my-platform

# Run a one-off CSV upload
pbi-agent source upload sales_2024.csv --target bronze.raw_sales --project my-platform

# Preview first 100 rows of a source
pbi-agent source preview --source-id abc123 --limit 100

# Run all rules against a table
pbi-agent rules run --table bronze.raw_crm_customer --project my-platform
```
