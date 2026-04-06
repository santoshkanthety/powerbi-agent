---
name: powerbi-data-governance-traceability
description: End-to-end data governance traceability for Power BI and Microsoft Fabric - GDPR/CCPA compliance, Purview lineage, sensitivity labels, retention, consent, and audit-ready evidence packages
triggers:
  - governance traceability
  - data lineage chain
  - GDPR
  - CCPA
  - HIPAA
  - data retention
  - right to erasure
  - data subject request
  - DSR
  - consent tracking
  - regulatory compliance
  - data classification
  - impact assessment
  - DPIA
  - breach detection
  - data residency
  - sovereignty
  - sensitivity label
  - Microsoft Purview
  - traceability report
  - evidence package
---

# Data Governance & Traceability in Power BI / Fabric

## The Traceability Stack

Full traceability in Fabric means you can answer: *"For any metric in a report — which source tables feed it, who can see it, how long is it kept, and can I prove it to a regulator?"*

```
Source System (SQL Server / Snowflake / API)
  └─ Fabric Lakehouse (Bronze → Silver → Gold)
       └─ Semantic Model (Power BI Dataset)
            └─ Report / Dashboard
                 └─ Export / Embed → Consumer recorded in Purview
```

All hops tracked by **Microsoft Purview** when connected to Fabric workspace.

## Data Classification with Sensitivity Labels

Microsoft Purview Sensitivity Labels propagate from data source → dataset → report → export.

```bash
# CLI: apply sensitivity label to a dataset
pbi-agent model set-label --workspace "Analytics" --dataset "Sales Model" --label "Confidential"

# List all datasets and their current sensitivity labels
pbi-agent model list-labels --workspace "Analytics"
```

```python
# Power BI REST API: assign sensitivity label
import httpx, os

token = os.environ["FABRIC_TOKEN"]
headers = {"Authorization": f"Bearer {token}"}

# Apply "Confidential" label to a dataset
httpx.post(
    "https://api.powerbi.com/v1.0/myorg/datasets/{datasetId}/Default.SetLabels",
    headers=headers,
    json={"datasetId": "{datasetId}", "sensitivity": "Confidential"}
)
```

### Label Hierarchy

| Label | Use Case | Power BI Behaviour |
|-------|---------|-------------------|
| Public | Marketing content | No restrictions |
| Internal | Internal dashboards | Watermark on exports |
| Confidential | PII, business metrics | Encrypted export; logged |
| Highly Confidential | Financial, HR, legal | Export blocked; alert on access |

## Microsoft Purview Integration

Connect Purview to scan and catalog all Fabric / Power BI assets:

```bash
# After connecting Purview to your Fabric workspace:

# 1. Trigger a manual scan
pbi-agent catalog purview-scan --workspace "Production"

# 2. View lineage for a report
pbi-agent catalog lineage --report "Revenue Dashboard" --workspace "Production"

# 3. Find all reports using a specific column
pbi-agent catalog impact --dataset "Sales Model" --column "customer_email"
```

Key Purview capabilities for Power BI:
- Automatic scan of all datasets, dataflows, reports, dashboards
- Column-level lineage from SQL source → Fabric table → DAX measure → report visual
- Business glossary terms linked to Power BI tables and columns
- Data quality scores surfaced in Purview Data Catalog

## GDPR Right-to-Erasure Workflow

```python
import httpx, os

def erase_subject_from_fabric(subject_email: str) -> dict:
    """
    Execute GDPR erasure across Fabric Lakehouse tables and invalidate
    cached Power BI reports containing subject data.
    """
    token    = os.environ["FABRIC_TOKEN"]
    headers  = {"Authorization": f"Bearer {token}"}
    evidence = {"subject": subject_email, "actions": []}

    # Step 1: Identify lakehouses containing this subject
    affected_tables = [
        {"lakehouse": "silver", "table": "customers",     "key_col": "email"},
        {"lakehouse": "silver", "table": "orders",        "key_col": "customer_email"},
        {"lakehouse": "gold",   "table": "customer_360",  "key_col": "email"},
    ]

    for item in affected_tables:
        # Delete via Fabric REST API (Spark SQL on Lakehouse)
        # In practice: run a Fabric notebook via API
        resp = httpx.post(
            f"https://api.fabric.microsoft.com/v1/workspaces/{{workspaceId}}/notebooks/erasure/jobs/instances",
            headers=headers,
            json={"parameters": {"subject_email": subject_email, **item}}
        )
        evidence["actions"].append({
            "type": "delete",
            "target": f"{item['lakehouse']}.{item['table']}",
            "status": resp.status_code
        })

    # Step 2: Trigger full dataset refresh (to flush cached PII from reports)
    httpx.post(
        "https://api.powerbi.com/v1.0/myorg/datasets/{datasetId}/refreshes",
        headers=headers
    )
    evidence["actions"].append({"type": "dataset_refresh", "target": "Sales Model"})

    return evidence
```

```bash
# CLI: erasure request
pbi-agent fabric erasure --subject customer@example.com --evidence-output erasure_2025.json
```

## Data Subject Access Request (DSAR)

```python
def compile_dsar_report(subject_email: str) -> dict:
    """Compile all Power BI / Fabric data held about a subject."""
    report = {"subject": subject_email, "data_found": []}

    # Query each Fabric lakehouse table
    tables_to_check = [
        "silver.customers", "silver.orders", "silver.support_tickets"
    ]

    for table in tables_to_check:
        # Run via Fabric notebook API or direct lakehouse query
        # Pseudocode: actual implementation via Fabric REST API
        results = spark.sql(f"SELECT * FROM {table} WHERE email = '{subject_email}'")
        if results.count() > 0:
            report["data_found"].append({
                "source": table,
                "records": results.toPandas().to_dict(orient="records")
            })

    return report
```

## Column-Level Lineage Documentation

```bash
# Show full lineage chain for a DAX measure
pbi-agent model lineage --dataset "Sales Model" --measure "Total Revenue"

# Expected output:
# Total Revenue (DAX measure)
#   └─ orders[revenue] (Power BI column)
#        └─ silver.orders.revenue (Fabric Lakehouse)
#             └─ bronze.raw_orders.revenue_str (Bronze raw)
#                  └─ orders_api (Source API)
```

Track measure → column → lakehouse → source in CLAUDE.md or Purview glossary:

```markdown
## Measure: Total Revenue
**Formula**: `SUMX(Orders, Orders[Revenue])`
**Lineage**: `orders_api → bronze.raw_orders → silver.orders → Orders[Revenue]`
**Owner**: analytics@company.com
**GDPR**: Contains transaction amounts (not PII). Retention: 7 years.
**Certified**: Yes — endorsed by Finance team 2025-01-15
```

## Retention Policy Enforcement

```bash
# Apply retention labels via Purview (propagates to Power BI exports)
pbi-agent catalog retention --workspace "Production" --label "7-Year-Finance"

# List datasets with no retention label
pbi-agent catalog audit --workspace "Production" --check no-retention-label
```

Key retention triggers in Power BI:
- Report exports inherit the dataset's sensitivity/retention label
- Purview applies retention labels to Fabric OneLake files
- Power BI activity log captures all export events for audit

## Governance Maturity Assessment

```bash
# Run a full governance audit
pbi-agent catalog audit --workspace "Production" --output governance_report.md

# Checks performed:
# ✓ All datasets have a sensitivity label
# ✓ All datasets are endorsed (Promoted / Certified)
# ✓ All datasets have an owner assigned
# ✓ All certified datasets connected to Purview
# ✓ RLS applied to all customer-facing reports
# ✓ Column-level lineage captured in Purview
# ✓ Export audit log enabled for Confidential datasets
```

## Audit-Ready Evidence Package

For regulatory audits (GDPR, SOC2, ISO 27001):

```bash
# Generate evidence package
pbi-agent catalog evidence --workspace "Production" \
  --regulation GDPR \
  --period 2025-01-01:2025-12-31 \
  --output gdpr_evidence_2025.zip

# Package contains:
# - All sensitivity label assignments + timestamps
# - Purview lineage screenshots
# - RLS rule definitions
# - Access audit log (who accessed what, when)
# - Erasure execution logs
# - Retention label assignments
```

## Governance Traceability Checklist

- [ ] All datasets have a Purview sensitivity label applied
- [ ] Purview workspace scan scheduled (weekly minimum)
- [ ] Column-level lineage visible in Purview for all certified datasets
- [ ] RLS applied to all reports with customer or employee data
- [ ] Erasure procedure documented and tested
- [ ] DSAR report generation tested with a test subject
- [ ] Retention labels applied to all Fabric OneLake tables
- [ ] Power BI activity log exported to Fabric for long-term retention
- [ ] Dataset endorsement status reviewed quarterly

## CLI Reference

```bash
pbi-agent catalog lineage --report "Revenue Dashboard"       # Full report lineage
pbi-agent catalog impact --dataset "Sales" --column email    # Column impact analysis
pbi-agent catalog audit --workspace Production               # Governance audit
pbi-agent fabric erasure --subject user@example.com          # GDPR erasure
pbi-agent model list-labels --workspace Production           # Sensitivity labels
pbi-agent catalog evidence --workspace Production --regulation GDPR
```
