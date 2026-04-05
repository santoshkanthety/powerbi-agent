# Skill: Measure Lineage & Semantic Model Glossary

## Trigger
Activate when the user mentions: measure lineage, measure description, formula documentation, DAX glossary, business glossary, measure visibility, what does this measure do, measure dependency, measure catalogue, document measures, annotate measures, formula visibility, where is this measure used, measure impact, self-documenting model

## What You Know

You have audited Power BI models with 500+ measures where nobody knew what half of them did. You know how to build self-documenting semantic models where every measure is traceable from business question to DAX formula to source column.

## The Three Layers of Measure Documentation

```
1. Description       → What does this measure do in business terms?
2. Formula lineage   → Which columns/tables/other measures does it depend on?
3. Glossary entry    → How is the business term defined for non-technical users?
```

## Adding Descriptions to Measures

### Via CLI (batch approach)
```bash
# Set description on a specific measure
pbi-agent model set-description \
  --measure "Total Sales" \
  --description "Sum of all completed order line amounts (excl. cancelled, returned). Source: fact_sales[sales_amount]. Refreshed: daily at 6am UTC."

# Bulk import descriptions from a CSV
pbi-agent model import-descriptions --file descriptions.csv
```

### descriptions.csv format
```csv
object_type,table,name,description
measure,Sales,"Total Sales","Sum of completed order amounts. Source: fact_sales[sales_amount]."
measure,Sales,"Sales YTD","Year-to-date sales using DATESYTD. Resets 1 Jan."
measure,Sales,"Sales YoY%","(Total Sales - Sales PY) / Sales PY. Blank if no prior year data."
table,,dim_customer,"One row per customer. SCD Type 2. Source: CRM Salesforce."
column,dim_customer,customer_segment,"Customer tier: Platinum / Gold / Silver / Bronze based on LTV."
```

### Via TMDL (source-controlled models)
```yaml
# In tables/Sales/measures/Total Sales.tmdl
measure 'Total Sales' = SUM(Sales[Amount])
    formatString: "#,0"
    description: """
        Sum of all completed order line amounts (excl. cancelled, returned).
        Source: fact_sales[sales_amount].
        Calculation: SUM of Amount where OrderStatus = 'Completed'.
        Refreshed: daily at 6am UTC.
        Owner: Sales Analytics Team.
    """
```

## Measure Lineage — Dependency Tracing

### Detect measure-to-measure dependencies
```bash
# Show the full dependency tree for a measure
pbi-agent model lineage --measure "Sales YoY%"
```

Output:
```
Sales YoY%
├── [Total Sales]
│   └── fact_sales[sales_amount]
└── [Sales PY]
    ├── [Total Sales]
    │   └── fact_sales[sales_amount]
    └── dim_date[Date]           ← SAMEPERIODLASTYEAR dependency
```

### Impact analysis — "what breaks if I change this column?"
```bash
# List all measures that reference a specific column
pbi-agent model impact --table "fact_sales" --column "sales_amount"
```

Output:
```
Column: fact_sales[sales_amount]
Used in 12 measure(s):
  - [Total Sales]          → direct SUM
  - [Sales YTD]            → via [Total Sales]
  - [Sales YoY%]           → via [Total Sales] and [Sales PY]
  - [Gross Margin]         → direct reference
  - [Gross Margin %]       → via [Gross Margin] and [Total Sales]
  ... (7 more)
Used in 2 calculated column(s):
  - fact_sales[Amount Bucket]
  - fact_sales[High Value Flag]
```

## Business Glossary Generation

Generate a living glossary from your model automatically:
```bash
# Export full model glossary as Markdown
pbi-agent model export-glossary --format markdown --output glossary.md

# Export as HTML (embed in SharePoint or Teams Wiki)
pbi-agent model export-glossary --format html --output glossary.html

# Export as Excel (for business stakeholders to review)
pbi-agent model export-glossary --format excel --output glossary.xlsx
```

### Glossary Markdown output example
```markdown
## Sales Metrics

### Total Sales
- **Formula:** `SUM(fact_sales[sales_amount])`
- **Definition:** Sum of all completed order line amounts, excluding cancelled and returned orders.
- **Unit:** USD (base currency)
- **Source Table:** `fact_sales`
- **Source Column:** `sales_amount`
- **Owner:** Sales Analytics Team
- **Last Verified:** 2024-11-15

### Sales YoY%
- **Formula:** `DIVIDE([Total Sales] - [Sales PY], [Sales PY])`
- **Definition:** Percentage growth in Total Sales vs the same period in the prior year.
- **Returns BLANK when:** No prior year data exists for the selected period.
- **Depends on:** [Total Sales], [Sales PY], dim_date[Date]
- **Owner:** Sales Analytics Team
```

## Measure Quality Checklist
```bash
# Find all measures missing descriptions
pbi-agent model audit --check missing-descriptions

# Find measures with identical expressions (potential duplicates)
pbi-agent model audit --check duplicate-expressions

# Find orphaned measures (not used in any report)
pbi-agent model audit --check unused-measures

# Full model audit report
pbi-agent model audit --all --output model-audit.html
```

Audit output:
```
✗  47 measures missing descriptions
✗   3 duplicate measure expressions found
⚠  12 measures not used in any published report
✓  All tables have descriptions
✓  All date columns marked as Date Table
```

## Best Practice: Self-Documenting Model Standard
```
Every measure MUST have:
  ☐ Description (business definition, not the formula restated)
  ☐ Format string
  ☐ Home table assignment (logical grouping)
  ☐ Display folder (group related measures)
  ☐ Owner annotation in description

Every table MUST have:
  ☐ Description (what it contains, source system, grain, refresh frequency)

Every key column MUST have:
  ☐ Description (what the value represents, how it was derived)
```
