# Skill: Testing & Validation — Power BI & Fabric Data Quality

## Trigger
Activate when the user mentions: testing, test, unit test, DAX test, data quality, validate, assertion, reconciliation, UAT, user acceptance testing, regression test, data test, test pipeline, PQTest, Great Expectations, data contract, row count, sum check, null check, business logic test, source vs target, reconcile

## What You Know

You have shipped data platforms where a wrong number costs real money. You know that untested models will fail at the worst time — during a board presentation. You build testing into the pipeline, not as an afterthought.

## The Four Levels of Testing

```
Level 1: Source Data Tests       → Does the input data look right?
Level 2: Pipeline Tests          → Did the transformation produce correct output?
Level 3: Semantic Model Tests    → Do DAX measures return expected values?
Level 4: Report Tests            → Do visuals display what the business expects?
```

## Level 1: Source Data Quality Tests

### Using Great Expectations (Python)
```python
import great_expectations as gx

context = gx.get_context()
suite = context.add_expectation_suite("bronze.raw_crm_customer")

# Define expectations
suite.expect_column_values_to_not_be_null("customer_id")
suite.expect_column_values_to_be_unique("customer_id")
suite.expect_column_values_to_not_be_null("email")
suite.expect_column_values_to_match_regex("email", r"^[^@]+@[^@]+\.[^@]+$")
suite.expect_column_values_to_be_between("age", min_value=0, max_value=120)
suite.expect_table_row_count_to_be_between(min_value=10000, max_value=5000000)

# Run validation
results = context.run_validation_operator(
    "action_list_operator",
    assets_to_validate=[batch]
)
```

### Lightweight Spark Assertions
```python
def assert_no_nulls(df, col_name, table_name):
    count = df.filter(col(col_name).isNull()).count()
    assert count == 0, f"[{table_name}] {count} NULL values in {col_name}"

def assert_unique(df, col_name, table_name):
    total = df.count()
    distinct = df.select(col_name).distinct().count()
    assert total == distinct, f"[{table_name}] Duplicates on {col_name}: {total - distinct}"

def assert_row_count_in_range(df, min_rows, max_rows, table_name):
    count = df.count()
    assert min_rows <= count <= max_rows, \
        f"[{table_name}] Row count {count:,} outside expected range [{min_rows:,}, {max_rows:,}]"
```

## Level 2: Pipeline / ETL Tests

### Reconciliation Test (Source vs Target)
```python
def reconcile_sum(source_df, target_df, metric_col, group_cols, table_name):
    """Verify aggregated sum matches between source and target."""
    src_agg = source_df.groupBy(*group_cols).agg(F.sum(metric_col).alias("src_sum"))
    tgt_agg = target_df.groupBy(*group_cols).agg(F.sum(metric_col).alias("tgt_sum"))

    diff = src_agg.join(tgt_agg, group_cols) \
        .withColumn("variance", col("src_sum") - col("tgt_sum")) \
        .filter(col("variance") != 0)

    if diff.count() > 0:
        diff.show()
        raise AssertionError(f"[{table_name}] Sum reconciliation failed — {diff.count()} group(s) have variance")
    print(f"✓ [{table_name}] Sum reconciliation passed")
```

### Pipeline Test Suite
```python
# tests/test_silver_customer.py
import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local").getOrCreate()

def test_no_duplicate_customer_keys(spark):
    df = spark.read.format("delta").load("silver/dim_customer")
    total = df.count()
    distinct = df.select("customer_key").distinct().count()
    assert total == distinct, f"Duplicate customer_key: {total - distinct} rows"

def test_scd2_only_one_current_per_customer(spark):
    df = spark.read.format("delta").load("silver/dim_customer")
    dupes = df.filter("is_current = true") \
              .groupBy("customer_id").count() \
              .filter("count > 1")
    assert dupes.count() == 0, "Multiple is_current=true rows per customer"

def test_no_null_effective_dates(spark):
    df = spark.read.format("delta").load("silver/dim_customer")
    nulls = df.filter("effective_date IS NULL").count()
    assert nulls == 0
```

## Level 3: DAX / Semantic Model Tests

### DAX Test Patterns
```bash
# Run a DAX assertion — compare measure to known expected value
pbi-agent dax test \
  --measure "[Total Sales]" \
  --filter "Date[Year] = 2023, Geography[Country] = 'USA'" \
  --expected 45823750.00 \
  --tolerance 0.01  # 1% tolerance

# Regression test: compare before/after model change
pbi-agent model regression-test \
  --baseline "snapshots/model_v1_results.csv" \
  --measures "Total Sales, Sales YTD, Sales YoY%"
```

### DAX Test Library (create once, run always)
```dax
-- Test: Sales YoY% should be BLANK when no prior year data
Test_YoY_Blank_No_PY =
VAR Result = CALCULATE([Sales YoY%], Date[Year] = MIN(Date[Year]))
RETURN IF(ISBLANK(Result), "PASS", "FAIL: Expected BLANK, got " & Result)

-- Test: Running total should always be >= current period value
Test_Running_Total_Monotonic =
VAR Current = [Total Sales]
VAR Running = [Running Total Sales]
RETURN IF(Running >= Current, "PASS", "FAIL: Running total < current")
```

## Level 4: Report / UAT Testing

### UAT Checklist Template
```markdown
## UAT Test Case: Executive Sales Dashboard

**Tester:** [Name]
**Date:** [Date]
**Environment:** Dev / UAT / Prod

| Test # | Scenario | Steps | Expected | Actual | Pass/Fail |
|---|---|---|---|---|---|
| 1 | Total Sales KPI | Select FY2024, All Regions | $45.8M | | |
| 2 | YoY growth | Select FY2024 vs FY2023 | +12.3% | | |
| 3 | Regional filter | Select EMEA only | Shows only EMEA data | | |
| 4 | Drill-through | Click on a product → drill | Opens product detail page | | |
| 5 | RLS - EMEA user | Login as EMEA.user@company.com | Only EMEA data visible | | |
| 6 | Mobile view | Open on mobile device | Layout renders correctly | | |
| 7 | Export to Excel | Click Export → Excel | Correct data exported | | |
```

## CLI Commands
```bash
# Run full data quality test suite on a Delta table
pbi-agent test delta --table "silver.dim_customer" --suite standard

# Run DAX regression tests comparing two model versions
pbi-agent test dax-regression --before baseline.csv --after current --tolerance 0.005

# Generate a UAT test template for a specific report
pbi-agent report generate-uat --report "Sales Dashboard" --output uat_checklist.md

# Run model audit (measures, descriptions, orphans)
pbi-agent model audit --all --output audit_report.html
```
