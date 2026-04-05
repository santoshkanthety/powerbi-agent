<div align="center">

# powerbi-agent

### Your AI co-pilot for the entire Microsoft Fabric & Power BI stack

*From raw data to board-ready analytics — guided by 20 years of enterprise data expertise*

[![PyPI](https://img.shields.io/pypi/v/powerbi-agent?color=blue&label=pip%20install)](https://pypi.org/project/powerbi-agent/)
[![Python](https://img.shields.io/pypi/pyversions/powerbi-agent)](https://pypi.org/project/powerbi-agent/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/santoshkanthety/powerbi-agent?style=social)](https://github.com/santoshkanthety/powerbi-agent)

**Created by [Santosh Kanthety](https://github.com/santoshkanthety)**
*Enterprise Data Architect · 20+ years delivering data platforms*

</div>

---

## The Problem

You open Power BI. You have data in OneLake, a business question, and a deadline.

Between you and the answer: medallion design decisions, Delta table optimisation, Kimball-correct star schemas, 400 lines of DAX, RLS for 3,000 users, report layout, and a Fabric refresh pipeline.

You know all of this. But it takes time — and time is the one thing you don't have.

---

## The Solution

**powerbi-agent** gives Claude Code the deep institutional knowledge of an enterprise data architect. Install once. Then just *ask*.

```
You:    "Build a YTD vs Prior Year Sales measure with fiscal year ending June"
Claude: pbi-agent model add-measure "Sales FYTD" \
          "CALCULATE([Total Sales], DATESYTD(Date[Date], '06/30'))" \
          --table Sales --format-string "#,0"
        ✓ Measure added. Formula validated. Description set.
```

No tab-switching. No documentation hunting. No syntax errors at 11pm.

---

## The Full Journey — Automated

```
┌─────────────────────────────────────────────────────────────────────┐
│                    The Data Platform Journey                        │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Ingest  │  Bronze  │  Silver  │   Gold   │  Model   │   Report    │
│          │          │          │          │          │             │
│ Sources  │  Delta   │  Clean   │  Star    │  DAX +   │  PBIR +     │
│ CRM/ERP  │  Raw     │  SCD2    │  Schema  │  RLS +   │  Visuals +  │
│ Files    │  Layer   │  Tests   │  Agg.    │  Docs    │  Themes     │
└──────────┴──────────┴──────────┴──────────┴──────────┴─────────────┘
    ↑            ↑          ↑          ↑          ↑           ↑
 Skill:     Medallion   Pipelines  Star Schema   DAX       Report
 Ingest     Arch.       & ETL      Modeling    Mastery   Authoring
```

---

## Install in 60 Seconds

```bash
# 1. Install
pip install "powerbi-agent[desktop,fabric]"

# 2. Register with Claude Code (one-time)
pbi-agent skills install

# 3. Connect to Power BI Desktop
pbi-agent connect

# 4. Ask Claude anything
```

> Need to check your setup? Run `pbi-agent doctor`

---

## What Claude Can Now Do

<table>
<tr>
<td width="50%">

### Data Architecture
- Design medallion layers (Bronze / Silver / Gold)
- Build Kimball star & snowflake schemas
- Configure DirectLake V-Order optimisation
- Set up incremental refresh policies

### Data Engineering
- Incremental + CDC pipeline patterns
- SCD Type 1, 2, 6 transformations
- Union/append across source systems
- Time series gap detection & binning
- Hash key generation for light joins

### Analytics & DAX
- Time intelligence (YTD, YoY, MTD, Rolling)
- Dynamic ranking and segmentation
- Running totals and Pareto
- Measure dependency tracing
- Performance profiling

</td>
<td width="50%">

### Reports & Visuals
- Page structure and layout guidance
- Visual selection for your data story
- Conditional formatting rules
- Bookmarks, drillthrough, tooltips
- Mobile layout configuration

### Security & Governance
- Dynamic RLS (user-based, hierarchy)
- Object-level security (OLS)
- Fabric workspace access control
- Data catalog + Purview integration
- Measure lineage and glossary

### Quality & Delivery
- DAX regression testing
- Pipeline reconciliation
- UAT checklist generation
- Model audit (missing docs, orphans)
- Project delivery frameworks

</td>
</tr>
</table>

---

## Real Conversations

### "My report is slow"
```
You:    "The Executive Dashboard takes 8 seconds to load — fix it"

Claude: Running Performance Analyzer...
        → fact_sales has 450M rows, no aggregations
        → 3 measures using row-context FILTER on fact table

        pbi-agent model analyse-size
        pbi-agent fabric optimize-delta --table gold.fact_sales --vorder
        pbi-agent model add-aggregation --table agg_sales_monthly

        Result: Page load reduced from 8.2s → 0.9s
```

### "Set up RLS for our sales team"
```
You:    "We have 200 sales reps, each should see only their region's data"

Claude: I'll implement dynamic RLS using USERPRINCIPALNAME().

        pbi-agent security add-role "RegionFilter" \
          --filter "Geography[Region] IN CALCULATETABLE(VALUES(UserAccess[region]), \
            UserAccess[email] = USERPRINCIPALNAME())"

        pbi-agent security test-rls --role RegionFilter \
          --user alice@company.com

        ✓ RLS applied. 200 users mapped. 5 test profiles passed.
```

### "Build a Bronze ingestion for our CRM"
```
You:    "Load Salesforce contacts into Bronze with incremental updates"

Claude: Using watermark pattern on LastModifiedDate.

        pbi-agent fabric pipeline-create \
          --source salesforce.Contact \
          --target bronze.raw_crm_contact \
          --pattern incremental \
          --watermark-col LastModifiedDate

        ✓ Pipeline created. Watermark table initialised. First load: 847,230 rows.
```

---

## Skill Library

14 domain skills installed directly into Claude Code:

| | Skill | Expertise |
|---|---|---|
| 🏗️ | **medallion-architecture** | Bronze/Silver/Gold design, DirectLake readiness |
| ⭐ | **star-schema-modeling** | Kimball, SCD Types, surrogate keys, date dimensions |
| 📐 | **dax-mastery** | Time intelligence, ranking, performance, evaluation context |
| 🔄 | **fabric-pipelines** | Incremental load, CDC, Spark patterns, orchestration |
| 📊 | **report-authoring** | Layout, visual selection, bookmarks, accessibility |
| 🔐 | **security-rls** | Dynamic RLS, OLS, hierarchy security, test coverage |
| 🏷️ | **data-catalog-lineage** | Purview, endorsement, impact analysis, business glossary |
| 📖 | **measure-glossary** | Formula visibility, dependency tracing, auto-documentation |
| ⚡ | **performance-scale** | DirectLake, V-Order, aggregations, capacity sizing |
| ⏱️ | **time-series-data** | Gap detection, binning, normalisation, spine generation |
| 🔀 | **data-transformation** | Union/append, type conversion, hash keys, schema drift |
| 🧪 | **testing-validation** | DAX regression, pipeline reconciliation, UAT templates |
| 📋 | **project-management** | Delivery phases, RAID logs, sprint templates, go-live |
| 🔌 | **power-bi-connect** | Desktop instance detection, diagnostics |

---

## CLI Reference

```
pbi-agent [command]

  connect       Connect to Power BI Desktop
  dax           Run and validate DAX queries
  model         Inspect and modify semantic model
  report        Work with report pages and visuals
  fabric        Power BI Service and Fabric operations
  skills        Manage Claude Code skill installation
  doctor        Diagnose environment issues
```

Run `pbi-agent [command] --help` for subcommands.

---

## Contributing

This project is built for the community — data engineers, BI developers, architects, and Power BI enthusiasts.

**You don't need to write Python to contribute.** The most impactful contributions are better skill documentation — more patterns, more anti-patterns, more real-world examples from your experience.

```bash
git clone https://github.com/santoshkanthety/powerbi-agent
cd powerbi-agent
pip install -e ".[dev]"
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guide.
Issues tagged [`good first issue`](https://github.com/santoshkanthety/powerbi-agent/issues?q=label%3A%22good+first+issue%22) are a great place to start.

---

## Roadmap

- **v0.2** — Power Query / M skill + PQTest.exe integration
- **v0.3** — Tabular Editor C# script generation
- **v0.4** — Deneb / Vega-Lite visual authoring
- **v0.5** — Auto-generated model documentation (HTML/PDF)
- **v1.0** — Full multi-agent workflow: ingest → model → test → refresh → validate → deploy

---

<div align="center">

Built by **[Santosh Kanthety](https://github.com/santoshkanthety)** from 20 years in the trenches.
Open-sourced for the community.

*If this saves you time, give it a ⭐ — it helps others find it.*

---

*See [ATTRIBUTIONS.md](ATTRIBUTIONS.md) for full license and credit information.*
*powerbi-agent is not affiliated with or endorsed by Microsoft Corporation.*

</div>
