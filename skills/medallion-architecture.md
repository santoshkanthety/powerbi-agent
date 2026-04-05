# Skill: Medallion Architecture Design & Setup

## Trigger
Activate when the user mentions: medallion, bronze, silver, gold, lakehouse, data lake, data architecture, layer design, raw layer, curated layer, semantic layer, OneLake

## What You Know

You embody the experience of a 20+ year data architect who has designed and delivered enterprise medallion architectures on Microsoft Fabric and Azure Data Lake. You know every trade-off, every failure mode, and every shortcut worth taking.

### The Three-Layer Medallion Pattern

```
OneLake
├── Bronze/  (Raw Ingestion)
│   ├── crm/
│   ├── erp/
│   └── files/
├── Silver/  (Cleaned & Conformed)
│   ├── dim_customer/
│   ├── dim_product/
│   └── fact_sales/
└── Gold/    (Business-Ready)
    ├── semantic_model/
    ├── finance_reporting/
    └── marketing_analytics/
```

### Bronze Layer — Raw Zone
- **Never transform, never filter** — store exactly as received
- Partition by ingestion date: `year=YYYY/month=MM/day=DD/`
- Store as Parquet or Delta — never CSV (no schema enforcement)
- Preserve source system identifiers and timestamps
- Add metadata columns: `_ingested_at`, `_source_system`, `_file_name`
- Retain for minimum 7 years (audit trail, replays)

### Silver Layer — Conformed Zone
- Apply data quality rules: nulls, duplicates, referential integrity
- Standardize data types (e.g., all dates as UTC timestamps)
- Resolve naming conflicts across source systems
- Implement slowly changing dimensions (SCD Type 1, 2, 6)
- Add surrogate keys — never expose natural keys to Gold
- Validate with Great Expectations or Fabric Data Quality

### Gold Layer — Business Zone
- Optimized for analytical consumption
- Star Schema preferred for Power BI (see star-schema skill)
- Pre-aggregated rollup tables for large fact tables (>100M rows)
- Semantic layer aligned to business vocabulary
- RLS policies applied at this layer
- Delta tables with V-Order optimization for Power BI DirectLake

## Fabric-Specific Guidance

### DirectLake Performance — Gold Layer Rules
- Enable V-Order on all Delta tables: `OPTIMIZE table VORDER`
- Target file size: 128MB–1GB per Parquet file
- Partition only when cardinality > 10M rows and filter patterns are clear
- Avoid over-partitioning — it kills DirectLake scan performance

### Lakehouse vs Warehouse vs Eventhouse
| Scenario | Use |
|---|---|
| Delta tables, notebooks, ML | Lakehouse |
| SQL-only analytics, stored procs | Data Warehouse |
| Real-time streaming, KQL | Eventhouse |
| Mixed: Power BI + notebooks | Lakehouse (primary) |

### Naming Conventions (enforce consistently)
```
Bronze:  raw_<source>_<entity>
Silver:  stg_<entity> (staging), int_<entity> (intermediate)
Gold:    dim_<entity>, fact_<entity>, agg_<entity>_<grain>
```

## CLI Commands
```bash
# Scaffold medallion folder structure in a Fabric workspace
pbi-agent fabric medallion-init --workspace "My Workspace" --layers bronze,silver,gold

# Validate Delta table readiness for DirectLake
pbi-agent fabric validate-delta --table gold.fact_sales

# Check V-Order optimization status
pbi-agent fabric check-vorder --lakehouse "Analytics"
```

## Anti-Patterns to Avoid
- ❌ Transforming data in Bronze (replay becomes impossible)
- ❌ Natural keys as join keys in Gold (breaks SCDs)
- ❌ CSV in any layer (schema drift nightmare)
- ❌ Partitioning on high-cardinality columns (e.g., CustomerID)
- ❌ Storing aggregations in Silver (that's Gold's job)
- ❌ Using Gold for raw ML feature stores (keep a separate feature layer)
