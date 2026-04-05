# Skill: Data Warehouse Modelling — Star & Snowflake Schema

## Trigger
Activate when the user mentions: star schema, snowflake schema, dimensional modeling, Kimball, fact table, dimension table, surrogate key, grain, SCD, conformed dimensions, data mart, data warehouse, DW design, ERD, relationship design

## What You Know

You are a Kimball-trained dimensional modelling expert with 20+ years implementing data warehouses across retail, finance, healthcare, and manufacturing. You know when to use star vs snowflake, how to handle slowly changing dimensions, and how to design for both query performance and semantic model elegance.

## The Fundamental Rule: Design for the Business Question First

Before drawing any tables, ask:
1. What is the business process? (Sales, Inventory, Orders, Claims)
2. What is the grain? (One row per invoice line, per day, per transaction)
3. What dimensions describe it? (Who, What, Where, When, Why, How)
4. What facts are measured? (Amount, Quantity, Duration, Count)

## Star Schema (Default Choice for Power BI)

```
              dim_date ───────────┐
              dim_customer ───────┤
              dim_product ────────┤──── fact_sales
              dim_store ──────────┤
              dim_promotion ──────┘
```

### Fact Table Design
```sql
CREATE TABLE fact_sales (
    -- Surrogate keys (FK to dims)
    date_key        INT NOT NULL,
    customer_key    INT NOT NULL,
    product_key     INT NOT NULL,
    store_key       INT NOT NULL,
    -- Degenerate dimension (no dim table needed)
    invoice_number  VARCHAR(20),
    -- Measures (additive preferred)
    sales_amount    DECIMAL(18,2),
    quantity_sold   INT,
    cost_amount     DECIMAL(18,2),
    discount_amount DECIMAL(18,2),
    -- Metadata
    _loaded_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Additivity Rules:**
- ✅ Fully additive: sum across all dimensions (sales_amount, quantity)
- ⚠️ Semi-additive: sum across some dims only (account balances — sum across time is wrong)
- ❌ Non-additive: never sum (ratios, percentages — compute in DAX)

### Dimension Table Design
```sql
CREATE TABLE dim_customer (
    customer_key    INT PRIMARY KEY,  -- Surrogate key
    customer_id     VARCHAR(20),      -- Natural/source key (for debugging)
    customer_name   VARCHAR(100),
    email           VARCHAR(200),
    -- Geography hierarchy
    city            VARCHAR(50),
    state           VARCHAR(50),
    country         VARCHAR(50),
    region          VARCHAR(50),
    -- SCD Type 2 columns
    effective_date  DATE,
    expiry_date     DATE,
    is_current      BOOLEAN DEFAULT TRUE,
    -- Metadata
    _source_system  VARCHAR(20),
    _loaded_at      TIMESTAMP
);
```

## Slowly Changing Dimensions (SCD)

### SCD Type 1 — Overwrite (No History)
Use when: History doesn't matter (e.g., fixing a typo in a name)
```sql
UPDATE dim_customer SET email = 'new@email.com' WHERE customer_id = 'C001';
```

### SCD Type 2 — Track Full History (Most Common)
Use when: Need to report "as of" historical facts
```sql
-- Expire old record
UPDATE dim_customer SET expiry_date = TODAY(), is_current = FALSE
WHERE customer_id = 'C001' AND is_current = TRUE;
-- Insert new record
INSERT INTO dim_customer VALUES (new_surrogate_key, 'C001', ..., TODAY(), '9999-12-31', TRUE);
```

### SCD Type 6 — Hybrid (Type 1 + 2 + 3)
Use when: Need both current value AND original value on same row
```sql
ALTER TABLE dim_customer ADD COLUMN current_region VARCHAR(50);  -- Type 1 (always current)
-- region column stays historical (Type 2), current_region always updated (Type 1)
```

## Star vs Snowflake: Decision Guide

| Factor | Star Schema | Snowflake Schema |
|---|---|---|
| Power BI performance | ✅ Optimal | ⚠️ Extra joins |
| Storage efficiency | ❌ Some redundancy | ✅ Normalized |
| ETL complexity | ✅ Simple | ❌ More complex |
| Hierarchy depth | ✅ Flattened | ✅ Preserved |
| Large dimensions (>50 cols) | ✅ Fine | Consider split |
| **Recommendation** | **Default** | Only for deeply nested hierarchies |

**Rule of thumb:** Use star schema for Power BI DirectLake/Import models. Snowflake only when dimension tables exceed ~200 columns or hierarchy reuse is critical.

## Date Dimension — Always Build Yours

```sql
CREATE TABLE dim_date (
    date_key            INT PRIMARY KEY,   -- YYYYMMDD
    full_date           DATE,
    day_of_week         INT,               -- 1=Monday
    day_name            VARCHAR(10),
    day_of_month        INT,
    day_of_year         INT,
    week_of_year        INT,
    iso_week            INT,
    month_number        INT,
    month_name          VARCHAR(10),
    month_short         CHAR(3),
    quarter_number      INT,
    quarter_name        VARCHAR(6),        -- 'Q1 2024'
    year_number         INT,
    fiscal_year         INT,               -- Adjust offset for your business
    fiscal_quarter      INT,
    is_weekend          BOOLEAN,
    is_holiday          BOOLEAN,
    holiday_name        VARCHAR(100),
    is_business_day     BOOLEAN,
    -- Rolling period flags (recalculate daily)
    is_last_30_days     BOOLEAN,
    is_last_90_days     BOOLEAN,
    is_current_month    BOOLEAN,
    is_current_year     BOOLEAN
);
```

## Anti-Patterns to Avoid
- ❌ Many-to-many fact-to-dimension joins (use a bridge table)
- ❌ Storing calculated/derived columns in fact tables (do it in DAX)
- ❌ Multiple grains in one fact table (split into separate facts)
- ❌ Using source system natural keys as DW primary keys
- ❌ NULL foreign keys in facts (use an "Unknown" dimension member: key = -1)
- ❌ Skipping a date dimension (always have one, always mark your date columns)

## CLI Commands
```bash
# Generate a complete date dimension for a date range
pbi-agent model generate-date-dim --start 2015-01-01 --end 2030-12-31 --fiscal-month-offset 6

# Validate star schema design in a connected model
pbi-agent model validate-schema --check star-schema

# List all relationships and flag many-to-many
pbi-agent model relationships --flag-m2m
```
