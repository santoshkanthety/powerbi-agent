<div align="center">

![powerbi-agent banner](docs/assets/banner.svg)

<br/>

[![PyPI](https://img.shields.io/pypi/v/powerbi-agent?style=for-the-badge&color=00e5ff&labelColor=030509&label=PyPI)](https://pypi.org/project/powerbi-agent/)
[![Python](https://img.shields.io/pypi/pyversions/powerbi-agent?style=for-the-badge&color=00b4d8&labelColor=030509)](https://pypi.org/project/powerbi-agent/)
[![License](https://img.shields.io/badge/License-MIT-00ff88?style=for-the-badge&labelColor=030509)](LICENSE)
[![Stars](https://img.shields.io/github/stars/santoshkanthety/powerbi-agent?style=for-the-badge&color=ffd700&labelColor=030509)](https://github.com/santoshkanthety/powerbi-agent/stargazers)
[![CI](https://img.shields.io/github/actions/workflow/status/santoshkanthety/powerbi-agent/ci.yml?style=for-the-badge&color=00e5ff&labelColor=030509&label=CI)](https://github.com/santoshkanthety/powerbi-agent/actions)

</div>

---

```
╔══════════════════════════════════════════════════════════════════╗
║  MISSION BRIEFING                                                ║
║                                                                  ║
║  You have data in the wild. Databases, APIs, CSV drops,          ║
║  web feeds. It needs to become board-ready Power BI analytics.   ║
║                                                                  ║
║  Between you and that goal:  medallion architecture decisions,   ║
║  Delta table optimization, Kimball star schemas, 400 lines of    ║
║  DAX, RLS for 5,000 users, PBIR report layouts, Fabric pipelines ║
║                                                                  ║
║  You know all of this.  It takes time.                           ║
║  POWERBI·AGENT gives that time back.                             ║
╚══════════════════════════════════════════════════════════════════╝
```

---

## `> SYSTEM_OVERVIEW`

![Architecture](docs/assets/architecture.svg)

---

## `> INITIALIZE_SEQUENCE`

**Three commands. Full stack online.**

```bash
# STEP 1 ── Install
pip install "powerbi-agent[desktop,fabric,ui]"

# STEP 2 ── Register 15 skills with Claude Code  (one-time)
pbi-agent skills install

# STEP 3 ── Connect to Power BI Desktop
pbi-agent connect
```

> **Verify the grid is live:**
> ```bash
> pbi-agent doctor
> ```

<details>
<summary><code>► What pbi-agent doctor checks</code></summary>

```
┌──────────────────────────────────────────────────┬────────┐
│ Check                                            │ Status │
├──────────────────────────────────────────────────┼────────┤
│ Python version (>=3.10)                          │   ✓    │
│ Operating System (Windows)                       │   ✓    │
│ Power BI Desktop installed                       │   ✓    │
│ pythonnet (for Desktop integration)              │   ✓    │
│ azure-identity (for Fabric integration)          │   ✓    │
│ Connection config                                │   ✓    │
│ Claude Code skills installed                     │   ✓    │
└──────────────────────────────────────────────────┴────────┘
All checks passed. You're good to go.
```
</details>

---

## `> WEB_CONFIG_TOOL`

**Design your entire pipeline visually. No YAML. No JSON editing.**

```bash
pbi-agent ui                          # Opens at http://localhost:8765
pbi-agent ui --project my-platform   # Named project
pbi-agent ui --port 9000 --no-open   # Headless mode
```

```
┌─────────────────────────────────────────────────────────┐
│  ██ POWERBI·AGENT  │ Config Tool          Project: demo │
├────────────┬────────────────────────────────────────────┤
│ Dashboard  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────────┐  │
│ ─────────  │  │ 4   │  │ 12  │  │ 8   │  │ Analytics│  │
│ INGEST     │  │Srcs │  │Rules│  │Tbls │  │Workspace │  │
│  Sources   │  └─────┘  └─────┘  └─────┘  └─────────┘  │
│            │                                            │
│ TRANSFORM  │  Sources→Bronze→Silver→Gold→Model→Reports  │
│  Rules     │  ══════════════════════════════════════►   │
│  Model     │                                            │
│            │  [ Add Source ] [ Add Rule ] [ Fabric → ]  │
│ DELIVER    │                                            │
│  Fabric    └────────────────────────────────────────────┘
└────────────┘
```

| Page | What You Configure |
|---|---|
| **Data Sources** | DB connections (SQL Server, PostgreSQL, Oracle, Snowflake), REST APIs (OAuth/Bearer/API Key), CSV uploads, web scrapers — each with load strategy, watermark column, Bronze target |
| **Rule Engine** | Quality checks (not\_null, unique, regex, range), transformations (cast, rename, derive, fill\_null) — each rule has an action: fail\_pipeline / quarantine / drop\_row / flag\_and\_pass |
| **Data Model** | Bronze/Silver/Gold table designer — column definitions, PK/FK relationships, PII flags, SCD type, partition column |
| **Fabric & Power BI** | Workspace, lakehouse, DirectLake toggle, incremental refresh windows, cron schedule — go-live readiness checklist |

---

## `> PIPELINE_SEQUENCE`

**The exact order. Every time.**

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  01. CONFIGURE    pbi-agent ui                                      │
│      ─────────    Add sources · Build rule engine · Design model    │
│                                                                     │
│  02. CONNECT      pbi-agent fabric login                            │
│      ────────     Authenticate with Microsoft Fabric / Azure        │
│                                                                     │
│  03. INGEST       Ask Claude:                                       │
│      ───────      "Run the Bronze ingestion for all sources"        │
│                                                                     │
│  04. TRANSFORM    Ask Claude:                                       │
│      ──────────   "Apply Silver transformations and run tests"      │
│                                                                     │
│  05. MODEL        pbi-agent model info                              │
│      ─────        pbi-agent model measures                          │
│                   pbi-agent model add-measure "Total Sales" ...     │
│                                                                     │
│  06. SECURE       pbi-agent security roles                          │
│      ──────       pbi-agent security test-rls --user alice@...      │
│                                                                     │
│  07. REPORT       pbi-agent report pages report.pbix                │
│      ──────       pbi-agent report add-page "Executive Summary"     │
│                                                                     │
│  08. REFRESH      pbi-agent fabric refresh "Sales Analytics" --wait │
│      ───────                                                        │
│                                                                     │
│  09. AUDIT        pbi-agent model audit --all                       │
│      ─────                                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## `> COMMAND_REFERENCE`

<details>
<summary><code>► connect — Link to Power BI Desktop</code></summary>

```bash
pbi-agent connect                     # Auto-detect first instance
pbi-agent connect --list              # List all open PBI instances
pbi-agent connect --port 59856        # Specify SSAS port manually
```
</details>

<details>
<summary><code>► dax — Query and validate DAX</code></summary>

```bash
# Run a DAX query — results as rich table
pbi-agent dax query "EVALUATE TOPN(10, Products, [Total Sales])"

# Run with output format options
pbi-agent dax query "EVALUATE VALUES(Date[Year])" --format json
pbi-agent dax query "EVALUATE SUMMARIZECOLUMNS(...)" --format csv

# Validate a DAX expression before adding it
pbi-agent dax validate "CALCULATE([Total Sales], SAMEPERIODLASTYEAR(Date[Date]))"
pbi-agent dax validate "SUMX(FILTER(Sales, Sales[Amount] > 1000), Sales[Amount])"
```

**Ask Claude instead:**
```
"Run a DAX query showing top 10 products by sales for 2024"
"Validate this RANKX expression before I add it to the model"
"What's wrong with my time intelligence measure?"
```
</details>

<details>
<summary><code>► model — Semantic model operations</code></summary>

```bash
# Inspect
pbi-agent model info                          # Model summary
pbi-agent model tables                        # All tables with counts
pbi-agent model measures                      # All measures
pbi-agent model measures --table Sales        # Filtered by table
pbi-agent model relationships                 # All relationships
pbi-agent model relationships --flag-m2m      # Flag many-to-many

# Build
pbi-agent model add-measure "Total Sales" \
  "SUM(fact_sales[sales_amount])" \
  --table Sales \
  --format-string "#,0"

pbi-agent model add-measure "Sales YTD" \
  "CALCULATE([Total Sales], DATESYTD(Date[Date]))" \
  --table Sales \
  --format-string "#,0"

pbi-agent model add-measure "Sales YoY%" \
  "DIVIDE([Total Sales] - [Sales PY], [Sales PY])" \
  --table Sales \
  --format-string "0.0%"

# Document
pbi-agent model set-description \
  --measure "Total Sales" \
  --description "Sum of completed order amounts. Source: fact_sales. Refreshed daily."

# Audit
pbi-agent model audit --check missing-descriptions
pbi-agent model audit --check duplicate-expressions
pbi-agent model audit --check unused-measures
pbi-agent model audit --all --output audit.html

# Lineage
pbi-agent model lineage --measure "Sales YoY%"
pbi-agent model impact --table "fact_sales" --column "sales_amount"
pbi-agent model export-glossary --format markdown --output glossary.md
```
</details>

<details>
<summary><code>► report — Report pages and visuals</code></summary>

```bash
# Inspect
pbi-agent report info  report.pbix              # Full structure tree
pbi-agent report pages report.pbix              # List all pages
pbi-agent report visuals report.pbix            # Visual types used

# Build
pbi-agent report add-page "Executive Summary" report.pbix
pbi-agent report add-page "Operations"        report.pbix

# Validate
pbi-agent report validate --check design-standards report.pbix

# Generate UAT checklist
pbi-agent report generate-uat --report "Sales Dashboard" --output uat.md
```
</details>

<details>
<summary><code>► fabric — Microsoft Fabric & Power BI Service</code></summary>

```bash
# Auth
pbi-agent fabric login

# Explore
pbi-agent fabric workspaces
pbi-agent fabric datasets --workspace "Analytics Platform"

# Operate
pbi-agent fabric refresh "Sales Analytics" \
  --workspace "Analytics Platform" \
  --wait                                        # Blocks until complete

# Validate DirectLake readiness
pbi-agent fabric validate-delta \
  --lakehouse "Analytics" \
  --table "fact_sales"

# Optimize Delta tables for DirectLake
pbi-agent fabric optimize-delta \
  --table "gold.fact_sales" \
  --vorder

# Endorsement
pbi-agent fabric endorse \
  --dataset "Sales Analytics" \
  --level certified \
  --justification "Passed all UAT checks, Q4 2024"
```
</details>

<details>
<summary><code>► security — RLS, OLS and governance</code></summary>

```bash
# Inspect roles
pbi-agent security roles

# Add dynamic RLS role
pbi-agent security add-role "RegionFilter" \
  --filter "[Region] IN CALCULATETABLE(VALUES(UserAccess[region]), \
    UserAccess[email] = USERPRINCIPALNAME())"

# Test RLS as a specific user
pbi-agent security test-rls \
  --role "RegionFilter" \
  --user "alice@company.com"

# Validate all users in UserAccess have coverage
pbi-agent security validate-coverage \
  --table UserAccess \
  --email-col email
```
</details>

<details>
<summary><code>► skills — Claude Code skill management</code></summary>

```bash
pbi-agent skills install              # Register all 15 skills
pbi-agent skills install --force      # Overwrite existing
pbi-agent skills list                 # Show install status
pbi-agent skills uninstall            # Remove all skills
```
</details>

<details>
<summary><code>► ui — Web configuration tool</code></summary>

```bash
pbi-agent ui                          # http://localhost:8765
pbi-agent ui --port 9000              # Custom port
pbi-agent ui --project my-platform   # Named project
pbi-agent ui --no-open                # Don't open browser
```
</details>

---

## `> NATURAL_LANGUAGE_INTERFACE`

**Once skills are installed, Claude Code understands Power BI natively.**

```
╔══════════════════════════ DATA ARCHITECTURE ══════════════════════════╗

  "Design a medallion architecture for a retail company — CRM in
   Salesforce, ERP in SAP, nightly file drops from 3rd-party vendors"

  → Claude designs Bronze/Silver/Gold layer structure,
    recommends partition strategy, SCD types, and DirectLake config

╠══════════════════════════════ DAX ════════════════════════════════════╣

  "Add a rolling 12-month revenue measure with a June fiscal year end"

  pbi-agent model add-measure "Revenue R12M FYTD" \
    "CALCULATE([Total Revenue], DATESINPERIOD(Date[Date],
       LASTDATE(Date[Date]), -12, MONTH))" \
    --table Revenue --format-string "$#,0"

╠══════════════════════════ PERFORMANCE ════════════════════════════════╣

  "The Executive Dashboard takes 9 seconds to load — fix it"

  → Performance Analyzer run, bottleneck identified (450M row fact table,
    no aggregations, FILTER on fact table in 3 measures)
  pbi-agent fabric optimize-delta --table gold.fact_sales --vorder
  pbi-agent model add-aggregation --table agg_sales_monthly
  → Page load: 9.2s → 0.8s

╠══════════════════════════ SECURITY ═══════════════════════════════════╣

  "Set up RLS for 300 sales reps — each sees only their territory"

  pbi-agent security add-role "TerritoryFilter" \
    --filter "[Territory] IN CALCULATETABLE(VALUES(UserAccess[territory]),
       UserAccess[email] = USERPRINCIPALNAME())"
  pbi-agent security test-rls --role TerritoryFilter --user rep@co.com
  → ✓ RLS applied · 300 users mapped · 5 test profiles passed

╠═══════════════════════════ GOVERNANCE ════════════════════════════════╣

  "Generate the full model glossary and find all orphaned measures"

  pbi-agent model export-glossary --format markdown --output glossary.md
  pbi-agent model audit --check unused-measures
  → 47 measures documented · 12 orphans flagged for review

╚═══════════════════════════════════════════════════════════════════════╝
```

---

## `> SKILL_MATRIX`

**15 domain skills loaded into Claude Code by `pbi-agent skills install`:**

```
┌─────────────────────────┬──────────────────────────────────────────────────┐
│ SKILL                   │ TRIGGERS ON                                      │
├─────────────────────────┼──────────────────────────────────────────────────┤
│ medallion-architecture  │ medallion · bronze · silver · gold · lakehouse   │
│ star-schema-modeling    │ star schema · Kimball · SCD · dimension · fact    │
│ dax-mastery             │ DAX · CALCULATE · time intelligence · YTD · YoY  │
│ fabric-pipelines        │ pipeline · ingestion · ETL · watermark · Spark   │
│ source-integration      │ source · connect · ingest · CSV · API · scrape   │
│ report-authoring        │ report · visual · chart · page · bookmark        │
│ security-rls            │ RLS · OLS · row-level security · USERPRINCIPALNAME│
│ data-catalog-lineage    │ catalog · lineage · Purview · glossary · impact   │
│ measure-glossary        │ measure description · formula · dependency        │
│ performance-scale       │ slow · DirectLake · aggregations · V-Order        │
│ time-series-data        │ time series · gaps · binning · intervals · spine  │
│ data-transformation     │ union · append · type cast · hash key · schema    │
│ testing-validation      │ test · validate · UAT · reconciliation            │
│ project-management      │ delivery · roadmap · sprint · RAID · go-live      │
│ power-bi-connect        │ connect · local instance · no connection           │
│ data-governance-trace.. │ GDPR · CCPA · lineage · retention · erasure       │
│ cyber-security          │ tenant hardening · MFA · embed token · exfiltrat. │
└─────────────────────────┴──────────────────────────────────────────────────┘
```

---

## `> PROJECT_STRUCTURE`

```
powerbi-agent/
│
├── src/powerbi_agent/
│   ├── cli.py              ◄── Click CLI · connect · dax · model · report
│   ├── connect.py          ◄── SSAS auto-detection via workspace port files
│   ├── dax.py              ◄── DAX execution via ADOMD.NET (pythonnet)
│   ├── model.py            ◄── TOM read/write (measures · tables · RLS)
│   ├── report.py           ◄── PBIR JSON manipulation (no Desktop needed)
│   ├── fabric.py           ◄── Power BI REST API · workspace · refresh
│   ├── doctor.py           ◄── Environment health checks
│   └── web/                ◄── FastAPI config tool (pbi-agent ui)
│       ├── app.py
│       ├── models/config.py    ◄── Pydantic models for all config entities
│       ├── routes/             ◄── sources · rules · model · pipeline · api
│       └── templates/          ◄── Tailwind CSS + HTMX pages
│
├── skills/                 ◄── 15 Claude Code skill markdown files
│   ├── medallion-architecture.md
│   ├── star-schema-modeling.md
│   ├── dax-mastery.md
│   └── ...
│
├── docs/assets/            ◄── SVG diagrams and visual assets
├── tests/                  ◄── pytest suite (no PBI Desktop required)
├── .github/workflows/ci.yml
├── pyproject.toml
├── CONTRIBUTING.md
└── ATTRIBUTIONS.md         ◄── License credits (pbi-cli MIT, data-goblin GPL-3.0)
```

---

## `> INSTALL_OPTIONS`

```bash
# Core CLI only
pip install powerbi-agent

# + Power BI Desktop integration (pythonnet / TOM / ADOMD)
pip install "powerbi-agent[desktop]"

# + Microsoft Fabric / Power BI Service (azure-identity)
pip install "powerbi-agent[fabric]"

# + Web configuration tool (FastAPI / uvicorn / Jinja2)
pip install "powerbi-agent[ui]"

# Everything
pip install "powerbi-agent[desktop,fabric,ui]"
```

---

## `> CONTRIBUTE`

```
The grid is open. All skill levels welcome.

No Python required to contribute:
  · Improve a skill file in skills/  (pure Markdown)
  · Add a real-world DAX pattern
  · Report a bug with reproduction steps
  · Suggest a new CLI command

With Python:
  · Add CLI commands or Fabric API coverage
  · Improve error messages and UX
  · Write tests

SETUP:
  git clone https://github.com/santoshkanthety/powerbi-agent
  cd powerbi-agent
  pip install -e ".[dev]"
  pytest
```

[![Issues](https://img.shields.io/github/issues/santoshkanthety/powerbi-agent?style=for-the-badge&color=00e5ff&labelColor=030509)](https://github.com/santoshkanthety/powerbi-agent/issues)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-00ff88?style=for-the-badge&labelColor=030509)](https://github.com/santoshkanthety/powerbi-agent/pulls)

---

## `> ROADMAP`

```
v0.2  ── Power Query / M skill + PQTest.exe integration
v0.3  ── Tabular Editor C# script generation via Claude
v0.4  ── Deneb / Vega-Lite visual authoring
v0.5  ── Auto-generated model documentation (HTML / PDF export)
v1.0  ── Full multi-agent workflow:
          ingest → transform → model → test → refresh → validate → deploy
```

---

## `> ATTRIBUTIONS`

Inspired by and building on:
- **[pbi-cli](https://github.com/MinaSaad1/pbi-cli)** (Mina Saad) — MIT · direct .NET TOM/ADOMD interop pattern
- **[power-bi-agentic-development](https://github.com/data-goblin/power-bi-agentic-development)** (Kurt Buhler) — GPL-3.0 · agentic skill architecture concept

No code was copied from either project. See [ATTRIBUTIONS.md](ATTRIBUTIONS.md) for full license details.

*Not affiliated with or endorsed by Microsoft Corporation.*

---

<div align="center">

```
╔══════════════════════════════════════════════════╗
║                                                  ║
║   Built by  SANTOSH KANTHETY                     ║
║   20+ years delivering enterprise data platforms ║
║                                                  ║
║   github.com/santoshkanthety/powerbi-agent       ║
║   linkedin.com/in/YOUR_LINKEDIN_HANDLE           ║
║                                                  ║
║   If this saves you time — give it a ★           ║
║                                                  ║
╚══════════════════════════════════════════════════╝
```

</div>
