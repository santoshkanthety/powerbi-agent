---
name: Power BI Model
description: Inspect and modify the connected Power BI Desktop semantic model using powerbi-agent — list tables, measures, relationships, and add new measures. Invoke when the user asks about the data model, wants a measure list, needs to add a measure, or is exploring table structure and relationships.
tools: powerbi-agent CLI (pbi-agent)
---

# Skill: Inspect and Modify the Semantic Model

## Trigger
Activate when the user wants to inspect tables / measures / relationships, asks "what's in the model", wants to add a measure, or requests an overview of the data model.

## Prerequisites
Requires an active connection — run `pbi-agent connect` first if any command fails with "no connection".

## Commands

```bash
# Model overview (name, tables, measures, relationships counts)
pbi-agent model info

# List all tables
pbi-agent model tables

# List all measures across the model
pbi-agent model measures

# Filter measures to a single table
pbi-agent model measures --table Sales

# List relationships
pbi-agent model relationships

# Add a new measure (replaces if the name exists)
pbi-agent model add-measure "Total Sales" "SUM(Sales[Amount])" --table Sales

# Add a measure with a format string
pbi-agent model add-measure "YoY Growth" "[Total Sales] / [PY Sales] - 1" \
    --table Sales --format-string "0.0%"

# Pin an SSAS port (skip auto-detect)
pbi-agent model info --port 56123
```

## Guidance
- `add-measure` **overwrites** an existing measure with the same name — confirm with the user before replacing.
- Table names are case-sensitive; verify with `pbi-agent model tables` before `--table` references.
- For complex DAX with VAR/RETURN, validate via `pbi-agent dax validate` before calling `add-measure`.
- To inspect a single measure's DAX expression, use `pbi-agent dax query "EVALUATE FILTER(INFO.MEASURES(), [Name] = \"My Measure\")"`.

## Common Failures
- **"No active connection"** → run `pbi-agent connect`
- **Table not found** → verify with `pbi-agent model tables` (exact case)
- **Measure expression invalid** → validate first: `pbi-agent dax validate "<expr>"`
