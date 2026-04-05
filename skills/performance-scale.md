# Skill: Performance & Scale — Enterprise-Grade Power BI

## Trigger
Activate when the user mentions: slow report, performance, DirectQuery, DirectLake, Import mode, aggregations, composite model, large dataset, timeout, query performance, DAX Studio, Performance Analyzer, V-Order, OPTIMIZE, memory, Premium, Fabric capacity, large model

## What You Know

You have optimised Power BI semantic models from sub-optimal 10-second page loads down to sub-second. You understand the full query path from DAX → xmVelocity → Formula Engine → Storage Engine → source data, and where to intervene at each layer.

## Storage Mode Decision Framework

```
Data volume & refresh needs → Choose mode:

< 1GB model, needs latest data always?  → Import Mode (default, fastest for users)
> 1GB, PII/live data required?          → DirectLake (Fabric only, best of both)
Operational live data, < 1M rows?       → DirectQuery (last resort)
Mixed: history in Import + live in DQ?  → Composite Model
> 10GB, Premium/Fabric?                 → Large Dataset Storage + Import
```

### Import Mode Optimisation
1. **Remove unused columns** — every column consumes memory
2. **Remove unused tables** — check with DAX Studio dependencies
3. **Reduce cardinality** — high-cardinality text columns kill compression
4. **Correct data types** — INT not TEXT for numeric IDs, DATE not DATETIME when time not needed
5. **Disable auto date/time** — creates hidden tables for every date column (massive size increase)

```bash
# Analyse model size and column cardinality
pbi-agent model analyse-size --port 12345
pbi-agent model unused-columns --threshold 0
```

### DirectLake Mode (Fabric Only)
DirectLake reads directly from OneLake Delta tables — no import, no DirectQuery latency.

**Requirements for optimal DirectLake:**
```
✅ Delta tables with V-Order enabled (OPTIMIZE ... VORDER)
✅ Parquet file sizes 128MB–1GB
✅ Row group sizes ~1M rows
✅ Fabric capacity F64 or above for large models
✅ No unsupported DAX functions (check compatibility list)
```

**Fallback to DirectQuery** — triggers when:
- Query hits a non-Delta source
- Delta table is mid-update (transaction in progress)
- Model uses functions not supported in DirectLake

```bash
# Check if your Delta tables are DirectLake-ready
pbi-agent fabric validate-delta --lakehouse "Analytics" --table "fact_sales"

# Check V-Order status and optimize
pbi-agent fabric optimize-delta --table "fact_sales" --vorder
```

## DAX Performance Patterns

### Profile Before Optimising
Always measure first:
1. **Performance Analyzer** (Power BI Desktop) — shows per-visual query times
2. **DAX Studio** — copy the slow query, run Server Timings tab
3. Look at: FE (Formula Engine) vs SE (Storage Engine) ratio
   - High FE time → rewrite DAX logic
   - High SE time → data model structure issue (cardinality, relationships)

### Common Slow DAX Patterns & Fixes

```dax
-- ❌ SLOW: FILTER on large fact table row-by-row
Slow = CALCULATE([Total Sales], FILTER(Sales, Sales[Amount] > 1000))

-- ✅ FAST: Use KEEPFILTERS for columnar filter
Fast = CALCULATE([Total Sales], KEEPFILTERS(Sales[Amount] > 1000))

-- ❌ SLOW: Nested CALCULATE with ALL inside FILTER
Slow2 = CALCULATE([Sales], FILTER(ALL(Customer), [Customer Rank] <= 10))

-- ✅ FAST: Pre-filter with TOPN
Fast2 = CALCULATE([Sales], TOPN(10, ALL(Customer[Name]), [Sales]))

-- ❌ SLOW: Computing same sub-expression multiple times
Slow3 =
    IF([Total Sales] > 1000000,
       [Total Sales] * 0.1,
       [Total Sales] * 0.05)

-- ✅ FAST: Variable for shared sub-expression
Fast3 =
VAR sales = [Total Sales]
RETURN IF(sales > 1000000, sales * 0.1, sales * 0.05)
```

## Aggregation Tables (Pre-Aggregation Pattern)

For fact tables > 50M rows, create aggregation tables:
```sql
-- Gold layer: agg_sales_monthly
CREATE TABLE agg_sales_monthly AS
SELECT
    date_key / 100 AS year_month,  -- YYYYMM
    product_key,
    geography_key,
    SUM(sales_amount)   AS total_sales,
    SUM(quantity)       AS total_qty,
    COUNT(*)            AS transaction_count
FROM fact_sales
GROUP BY date_key / 100, product_key, geography_key;
```

Then configure as an Aggregation in Power BI:
- Maps `agg_sales_monthly[total_sales]` → `fact_sales[sales_amount]` (SUM)
- Power BI automatically routes queries to the agg table when possible

## Capacity Sizing Guide (Fabric)

| Model Size | Row Count | Recommended Capacity |
|---|---|---|
| < 1 GB | Any | F2 / F4 |
| 1–10 GB | < 100M rows | F8 / F16 |
| 10–50 GB | 100M–1B rows | F32 / F64 |
| 50–400 GB | > 1B rows | F64 / F128 |
| > 400 GB | Enterprise | F256+ |

## Refresh Optimisation
```
Large fact tables: Incremental refresh (keep 3 years, refresh last 7 days)
Dimension tables: Full refresh (typically small, fast)
Aggregation tables: Refresh after fact table refresh completes
Hot cache: Pin frequently-queried pages via API to pre-warm cache
```

```bash
# Configure incremental refresh policy
pbi-agent model set-incremental-refresh \
  --table "fact_sales" \
  --rolling-window-years 3 \
  --incremental-days 7
```
