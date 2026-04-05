# Skill: Data Catalog, Lineage & Governance

## Trigger
Activate when the user mentions: data catalog, lineage, data governance, Microsoft Purview, data dictionary, metadata, data discovery, impact analysis, endorsement, certified, promoted, scan, data map, business glossary, column-level lineage, table lineage, sensitivity label, data quality score

## What You Know

You have implemented enterprise data governance programs covering Purview, Power BI endorsement workflows, and column-level lineage in organizations with 500+ data assets. You know how to build governance that data teams actually use.

## Microsoft Purview Integration

### Scanning Power BI Assets
Purview auto-scans registered Power BI tenants and captures:
- Workspace → Dataset → Report → Dashboard lineage
- Column-level lineage from data sources to Power BI columns
- Sensitivity labels propagation
- Data quality scores

### Business Glossary
Build a living glossary that maps business terms to technical columns:
```
Business Term: "Active Customer"
Definition: A customer with at least one transaction in the last 12 months
Owner: Sales Analytics Team
Technical Mapping:
  - dim_customer[customer_status] = 'Active'
  - fact_sales: customer appears in last 365 days
Related Terms: "Churned Customer", "Customer LTV"
```

## Power BI Endorsement Workflow

### Three Levels
```
Promoted   → Dataset owner can set; signals quality but informal
Certified  → Requires Power BI Admin approval; enterprise-grade standard
No label   → Exploratory or deprecated
```

### Certification Criteria (enforce these before certifying)
```
☐ Data refreshes on schedule (no failures in last 30 days)
☐ RLS applied where data is sensitive
☐ Descriptions on all tables and key measures
☐ Data dictionary linked in dataset description
☐ Tested by more than one business user
☐ Naming conventions followed (dim_, fact_, agg_)
☐ Source system documented in dataset metadata
☐ Owner and support contact named
```

### Promoting via CLI
```bash
# Endorse a dataset as Promoted
pbi-agent fabric endorse --dataset "Sales Analytics" --level promoted

# Submit for certification (requires admin approval)
pbi-agent fabric endorse --dataset "Sales Analytics" --level certified --justification "Meets all certification criteria as of 2024-Q4 review"
```

## Column-Level Lineage

### Documenting in TMDL/Model
Add descriptions directly to model objects — they appear in Purview automatically:
```bash
# Add description to a measure
pbi-agent model set-description --measure "Total Sales" \
  --description "Sum of Sales[Amount] for all non-cancelled orders. Source: ERP.dbo.Sales. Refreshed daily."

# Add description to a table
pbi-agent model set-description --table "dim_customer" \
  --description "One row per customer. SCD Type 2. Source: CRM_Salesforce. Tracks email, region, segment."
```

### Lineage Tracing
```
OneLake Bronze (raw_crm_contact)
  ↓ Silver ETL (Spark notebook: silver_customer_transform)
  ↓ dim_customer (Gold Delta table)
  ↓ Semantic Model: Sales Analytics
  ↓ Power BI Report: Customer 360 Dashboard
  ↓ Power BI App: Executive Suite
```

## Impact Analysis
Before changing a source column or table, always run impact analysis:
```bash
# What Power BI assets are impacted if we rename this column?
pbi-agent lineage impact --source-table "dbo.Customer" --source-column "CustomerEmail"

# Show all downstream consumers of a Delta table
pbi-agent lineage downstream --lakehouse "Analytics" --table "dim_customer"
```

## Data Dictionary Template
Each certified dataset must have a living data dictionary:

| Column | Business Name | Description | Type | Example | Owner | PII? | Source |
|---|---|---|---|---|---|---|---|
| cust_id | Customer ID | Unique CRM ID | INT | 10234 | CRM Team | No | CRM.dbo.Customer.id |
| email | Email Address | Primary contact | VARCHAR | a@b.com | CRM Team | Yes | CRM.dbo.Customer.email |
| ltv_usd | Customer LTV | 12-month purchase value | DECIMAL | 4500.00 | Analytics | No | Calculated |

## Governance Maturity Model
```
Level 1 (Ad Hoc):      No catalog, no endorsements, no lineage
Level 2 (Managed):     Purview connected, key datasets endorsed, basic lineage
Level 3 (Defined):     Business glossary, column-level lineage, impact analysis
Level 4 (Optimized):   Automated quality scores, certification workflow, full lineage
```

Assess current state with:
```bash
pbi-agent governance maturity-check --workspace "Analytics Platform"
```
