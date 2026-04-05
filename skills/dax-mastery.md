# Skill: DAX Mastery

## Trigger
Activate when the user mentions: DAX, measure, calculated column, calculate, filter context, row context, time intelligence, SUMX, CALCULATE, ALL, ALLEXCEPT, RANKX, TREATAS, YTD, YoY, MTD, rolling average, running total, DAX error, formula, expression, context transition

## What You Know

You are a DAX expert who has written thousands of production measures for Fortune 500 companies. You understand evaluation context deeply, know every time intelligence pattern, and can diagnose slow measures by reading a query plan.

## Core Principles

### Rule 1: Measures vs Calculated Columns
- **Measure** = computed at query time, respects filter context → use for everything aggregated
- **Calculated column** = computed at refresh time, stored in model → use ONLY for row-level attributes you cannot get via relationships
- ❌ Never create a calculated column for something you can compute in a measure

### Rule 2: Understanding Evaluation Context
```dax
-- Filter context = the filters applied by slicers, rows/columns, visual filters
-- Row context = "current row" inside SUMX, FILTER, ADDCOLUMNS iterations

-- This FAILS (CALCULATE needed for context transition):
Wrong Measure = SUMX(Sales, Sales[Amount] * [Margin %])  -- [Margin %] is a measure

-- This WORKS:
Correct Measure = SUMX(Sales, Sales[Amount] * CALCULATE([Margin %]))
```

### Rule 3: CALCULATE is the Engine of DAX
```dax
-- CALCULATE(expression, [filter1], [filter2], ...)
-- It does TWO things:
-- 1. Evaluates expression in a NEW filter context
-- 2. Merges/overrides the current filter context

Total Sales = SUM(Sales[Amount])

Sales USA = CALCULATE([Total Sales], Geography[Country] = "USA")

-- ALL() removes filters; ALLEXCEPT() removes all except listed columns
Sales All Products = CALCULATE([Total Sales], ALL(Product))

-- KEEPFILTERS() adds rather than replaces
Sales High Value = CALCULATE([Total Sales], KEEPFILTERS(Sales[Amount] > 1000))
```

## Time Intelligence Patterns

### Prerequisites: Always mark your date table
- One row per date, no gaps
- Date column as primary key
- Mark as Date Table in Power BI

```dax
-- ── Year-to-Date ──────────────────────────────
Sales YTD = CALCULATE([Total Sales], DATESYTD(Date[Date]))

-- Fiscal YTD (fiscal year ends June 30)
Sales FYTD = CALCULATE([Total Sales], DATESYTD(Date[Date], "06/30"))

-- ── Prior Year ────────────────────────────────
Sales PY = CALCULATE([Total Sales], SAMEPERIODLASTYEAR(Date[Date]))

-- ── Year-over-Year Growth ─────────────────────
Sales YoY% = DIVIDE([Total Sales] - [Sales PY], [Sales PY])

-- ── Rolling 12 Months ─────────────────────────
Sales R12M =
CALCULATE(
    [Total Sales],
    DATESINPERIOD(Date[Date], LASTDATE(Date[Date]), -12, MONTH)
)

-- ── Month-to-Date ─────────────────────────────
Sales MTD = CALCULATE([Total Sales], DATESMTD(Date[Date]))

-- ── Prior Month ───────────────────────────────
Sales PM =
CALCULATE(
    [Total Sales],
    DATEADD(Date[Date], -1, MONTH)
)

-- ── Week-over-Week ────────────────────────────
Sales WoW% =
VAR CurrentWeek = [Total Sales]
VAR PriorWeek   = CALCULATE([Total Sales], DATEADD(Date[Date], -7, DAY))
RETURN DIVIDE(CurrentWeek - PriorWeek, PriorWeek)
```

## Advanced Patterns

### Running Total
```dax
Running Total =
CALCULATE(
    [Total Sales],
    FILTER(
        ALL(Date[Date]),
        Date[Date] <= MAX(Date[Date])
    )
)
```

### Ranking with Ties
```dax
Product Rank =
RANKX(
    ALL(Product[Product Name]),
    [Total Sales],
    ,
    DESC,
    DENSE  -- or SKIP for gaps
)
```

### Pareto / Top N %
```dax
Is Top 80% =
VAR CurrentProduct = SELECTEDVALUE(Product[Product Name])
VAR CurrentSales   = [Total Sales]
VAR AllSales       = CALCULATE([Total Sales], ALL(Product))
VAR CumulativeRank =
    CALCULATE(
        [Total Sales],
        FILTER(
            ALL(Product[Product Name]),
            [Total Sales] >= CurrentSales
        )
    )
RETURN
    IF(DIVIDE(CumulativeRank, AllSales) <= 0.8, "Top 80%", "Remaining 20%")
```

### Dynamic Segmentation (no calculated column needed)
```dax
Customer Segment =
SWITCH(
    TRUE(),
    [Customer LTV] >= 10000, "Platinum",
    [Customer LTV] >= 5000,  "Gold",
    [Customer LTV] >= 1000,  "Silver",
    "Bronze"
)
```

### TREATAS — Virtual Relationships
```dax
-- Use when you can't create a physical relationship
Budget vs Actual =
CALCULATE(
    SUM(Budget[Amount]),
    TREATAS(VALUES(Date[Year]), Budget[Year])
)
```

## Performance Rules
1. **Avoid row-by-row FILTER on large tables** — use relationship filtering instead
2. **Use variables (VAR)** — avoids recalculating the same expression multiple times
3. **DIVIDE() not `/`** — handles divide-by-zero gracefully
4. **Avoid bidirectional relationships** — they create ambiguity and slow queries
5. **SUMX on large tables** — always profile in DAX Studio first
6. **Avoid calculated columns on fact tables** — blows up model size

## CLI Commands
```bash
# Run a DAX query and display results
pbi-agent dax query "EVALUATE SUMMARIZECOLUMNS(Date[Year], \"Sales\", [Total Sales])"

# Validate a measure expression
pbi-agent dax validate "CALCULATE([Total Sales], SAMEPERIODLASTYEAR(Date[Date]))"

# List all measures with their expressions
pbi-agent model measures

# Add a new measure
pbi-agent model add-measure "Sales YTD" "CALCULATE([Total Sales], DATESYTD(Date[Date]))" --table Sales --format-string "#,0"
```
