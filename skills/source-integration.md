# Skill: Source Integration & Data Model Development

## Trigger
Activate when the user mentions: data source, connect source, ingest data, database connection, API connection, CSV upload, web scrape, source connector, raw data model, normalize, Bronze ingestion, source mapping, data model development, config tool, pbi-agent ui, configuration tool, rule engine, pipeline setup, source to Bronze, multi-source

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
