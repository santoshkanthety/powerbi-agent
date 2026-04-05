# Skill: Project & Product Management — Data Platform Delivery

## Trigger
Activate when the user mentions: project plan, sprint, milestone, delivery, roadmap, stakeholder, requirements, scope, backlog, user story, epic, data product, product management, agile, kanban, release plan, go-live, risk, RAID log, data platform delivery, data project, BI delivery, analytics delivery, change management, business case

## What You Know

You have delivered enterprise data platforms from inception to production — managing stakeholders, scope, teams of 5–30 people, budgets, and the inevitable last-minute requirement changes. You know what kills data projects and how to prevent it.

## The Data Product Mindset

Think of every analytical output as a **data product**, not a report. A data product has:
- An **owner** (accountable person, not just a team)
- **Consumers** (who uses it and how)
- A **SLA** (refresh frequency, availability, acceptable error rate)
- A **lifecycle** (v1, v2, deprecation)
- **Feedback loops** (usage metrics, consumer satisfaction)

## Project Phases — Data Platform Delivery

```
Phase 1: Discovery & Design (2–4 weeks)
  ├── Stakeholder interviews (business requirements)
  ├── Source system analysis (data availability, quality)
  ├── Data model design (star schema, grain decisions)
  ├── Architecture decision (Fabric, medallion, DirectLake)
  └── Delivery plan + RAID log

Phase 2: Foundation (2–4 weeks)
  ├── Fabric workspace setup + access control
  ├── Medallion architecture scaffolding
  ├── CI/CD pipeline setup (GitHub/ADO)
  └── Source connections + Bronze ingestion

Phase 3: Core Delivery (4–8 weeks, sprints of 2 weeks)
  ├── Silver transformations (cleansing, SCD, type alignment)
  ├── Gold layer (star schema, aggregations)
  ├── Semantic model (DAX measures, RLS, descriptions)
  └── MVP report (executive summary + 1–2 operational views)

Phase 4: Hardening & UAT (2–3 weeks)
  ├── Data quality tests + reconciliation
  ├── Performance tuning (V-Order, aggregations, Incremental Refresh)
  ├── RLS testing (all user profiles)
  └── UAT with business stakeholders

Phase 5: Go-Live & Hypercare (2–4 weeks)
  ├── Production deployment
  ├── User training and onboarding
  ├── Hypercare period (daily check-ins, fast bug fixes)
  └── Handover documentation
```

## Agile Delivery for Data Projects

### Epic → Story → Task structure
```
Epic: Sales Analytics Data Product
  Story: Bronze ingestion from CRM
    Task: Set up Fabric lakehouse connection to Salesforce
    Task: Create Bronze ingestion notebook
    Task: Validate Bronze row counts match source
  Story: Silver customer dimension
    Task: Design dim_customer schema (SCD Type 2)
    Task: Build Silver transformation notebook
    Task: Write pytest test suite for dim_customer
  Story: Total Sales measure
    Task: Implement [Total Sales] DAX measure
    Task: Write DAX test for known CY2023 value
    Task: Add measure description and format string
```

### Story Points — Data Project Calibration
```
1 pt  → Simple column rename, measure description update
2 pt  → New measure with 1 dependency, simple table column
3 pt  → New measure with time intelligence, SCD implementation
5 pt  → New data source integration, complex DAX pattern
8 pt  → Full Silver table with quality tests, new Fabric connection
13 pt → End-to-end data product (source → Gold → semantic model)
```

## RAID Log (Risks, Assumptions, Issues, Dependencies)

```markdown
## RAID Log — Sales Analytics Platform

### Risks
| ID | Risk | Probability | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | CRM API rate limiting delays Bronze loads | Medium | High | Implement retry + incremental windows | Data Eng |
| R2 | Historical data quality issues > 2019 | High | Medium | Scope to 2020+ initially; backfill in Phase 2 | PM |

### Assumptions
| ID | Assumption | If Wrong... | Owner |
|---|---|---|---|
| A1 | Source CRM data has consistent email format | Data normalisation effort increases by 2 sprints | Data Eng |
| A2 | Business users will test during UAT sprint | Go-live delayed by minimum 1 sprint | PM |

### Issues
| ID | Issue | Severity | Resolution | Owner | Due |
|---|---|---|---|---|---|
| I1 | ERP database has no modified_date column | High | Full load only; re-assess CDC options | Data Eng | Sprint 2 |

### Dependencies
| ID | Dependency | Provider | Due | Risk if Missed |
|---|---|---|---|---|
| D1 | Fabric workspace provisioned | IT Admin | Sprint 1 | All development blocked |
| D2 | CRM API credentials | CRM team | Sprint 1 | Bronze ingestion blocked |
```

## Stakeholder Communication Templates

### Weekly Status Update
```
## Analytics Platform — Week 12 Status

**Overall Status:** 🟢 ON TRACK

**This Week:**
- ✅ Silver customer dimension completed + tested
- ✅ DAX measures: [Total Sales], [Sales YTD], [YoY%] done
- ⚠️ ERP connection delayed — IT provisioning issue (see Risk R2)

**Next Week:**
- Bronze ingestion: Orders fact table
- Silver transformation: fact_orders
- Begin UAT preparation checklist

**Open Issues:**
- I1: ERP modified_date column missing → full load approach agreed

**Ask of Stakeholders:**
- Business team: Please confirm UAT start date (currently planned Week 15)
```

## Go-Live Checklist
```
☐ All pipelines running on schedule with no failures for 5+ days
☐ UAT signed off by business sponsor
☐ RLS tested for all user profiles (incl. edge cases)
☐ Performance: all report pages load < 3 seconds
☐ Incremental refresh configured on fact tables
☐ Alerts configured for pipeline failures (email + Teams)
☐ Support runbook documented (common issues + resolution steps)
☐ Training session delivered to end users
☐ Rollback plan documented
☐ Go-live communication sent to all stakeholders
```

## Data Product Metrics (Post Go-Live)
Track these to demonstrate value:
```bash
# Report usage stats from Power BI Service
pbi-agent fabric usage-report --workspace "Analytics Platform" --days 30

# Check pipeline success rate
pbi-agent fabric pipeline-health --workspace "Analytics Platform" --days 14
```

- **Adoption**: Daily active users / target users
- **Reliability**: Pipeline success rate (target: >99%)
- **Performance**: Average page load time (target: <3s)
- **Quality**: Data reconciliation pass rate (target: 100%)
- **Satisfaction**: Monthly user NPS survey
