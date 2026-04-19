---
name: Power BI DAX
description: Execute and validate DAX queries and expressions against a connected Power BI Desktop model via powerbi-agent. Invoke when the user mentions DAX, asks to run a query, test a formula, use EVALUATE / CALCULATE / SUMMARIZECOLUMNS, or validate an expression before saving as a measure.
tools: powerbi-agent CLI (pbi-agent)
---

# Skill: Run and Validate DAX

## Trigger
Activate when the user wants to run a DAX query, test a DAX expression, validate syntax, explore model data via DAX, or aggregate values from the connected Power BI Desktop model.

## Prerequisites
Must have an active connection — run `pbi-agent connect` first if DAX commands fail with "no connection".

## Commands

```bash
# Run a DAX query (default table output)
pbi-agent dax query "EVALUATE TOPN(10, Sales)"

# Pick output format
pbi-agent dax query "EVALUATE VALUES('Product'[Category])" --format json
pbi-agent dax query "EVALUATE Sales" --format csv

# Constrain to a specific table context
pbi-agent dax query "CALCULATE(SUM(Sales[Amount]))" --table Sales

# Pin the SSAS port (skip auto-detect)
pbi-agent dax query "EVALUATE INFO.TABLES()" --port 56123

# Validate an expression without executing
pbi-agent dax validate "CALCULATE(SUM(Sales[Amount]), YEAR(Sales[Date])=2024)"
```

## Shell Quoting Notes
Multi-line DAX (VAR / RETURN) passed as a shell argument loses line breaks and breaks parsing. For multi-line expressions:
- Prefer inline single-expression form: `DIVIDE([A] - [B], [B])` instead of `VAR x = [A] VAR y = [B] RETURN ...`
- If VAR/RETURN is required, test the single-line collapsed form first (`VAR x = ... RETURN ...` on one line — DAX accepts whitespace separators)

## Common Exploration Patterns

```bash
# Inventory the model
pbi-agent dax query "EVALUATE INFO.TABLES()"
pbi-agent dax query "EVALUATE INFO.MEASURES()"
pbi-agent dax query "EVALUATE INFO.RELATIONSHIPS()"

# Preview a table
pbi-agent dax query "EVALUATE TOPN(10, Sales)"

# Row count
pbi-agent dax query "EVALUATE ROW(\"Count\", COUNTROWS(Sales))"

# Group-by aggregation
pbi-agent dax query "EVALUATE SUMMARIZECOLUMNS(Products[Category], \"Total\", SUM(Sales[Amount]))"
```

## Common Failures
- **"No active connection"** → run `pbi-agent connect`
- **Syntax error on VAR/RETURN** → collapse to single-line DIVIDE / inline form, or test with `pbi-agent dax validate` first
- **Table not found** → run `pbi-agent model tables` to verify the exact name (case-sensitive)
