---
name: powerbi-paginated-reports
description: Author, validate, deploy and export Power BI paginated reports (RDL) — Report Builder, RDL structure, datasets and parameters, pixel-perfect pagination for print and regulatory output, deployment to a Fabric or Power BI workspace, and the Export To File REST API for scheduled PDF/Excel delivery. Use when the user mentions: paginated report, RDL, .rdl, Report Builder, SSRS report, pixel perfect, print-ready report, invoice or statement report, multi-page table, export to PDF, export to file API, RDL parameters, tablix, subreport, migrate SSRS to Power BI.
license: MIT
---

# Paginated reports (RDL)

Paginated reports are the right answer to a narrow but unavoidable set of requirements:
output that must paginate predictably, print to a fixed layout, carry a regulatory format, or
leave the platform as a PDF or Excel file on a schedule. An interactive Power BI report cannot
do those things well, and trying to make it do them is how teams end up with a report nobody
trusts and a page that prints across four sheets.

Decide the format before building anything:

| Requirement | Build |
|---|---|
| Explore, filter, cross-highlight, drill | interactive report — `powerbi-create-pbi-report` |
| Print to a fixed page size; page headers/footers; page breaks you control | paginated (RDL) |
| A table of thousands of rows the user will read or export in full | paginated |
| Invoice, statement, remittance, compliance filing, regulator submission | paginated |
| Scheduled PDF or XLSX to an inbox or a file share | paginated + Export To File API |
| Both — a dashboard that drills to a printable detail | interactive, with a paginated report as the drillthrough target |

Say this out loud when a user asks for "a report that prints properly". The format choice is
the decision that determines whether the rest of the work succeeds.

## Prerequisites

| Requirement | Notes |
|---|---|
| **Power BI Report Builder** | Windows. The authoring tool. [Download](https://www.microsoft.com/download/details.aspx?id=58158) — also the source of the TOM and ADOMD assemblies `pbi-agent` uses for Desktop work |
| Workspace on **Fabric capacity or Premium / PPU** | Paginated reports do not run in a Pro-only workspace |
| Build permission on the data source | Semantic model, SQL, or whatever the dataset queries |
| `fab` CLI | For deploy, export and workspace plumbing — `powerbi-fabric-cli` |

## RDL structure

An `.rdl` file is XML. That matters: it is diffable, scriptable and reviewable, so paginated
reports belong in source control alongside the PBIP projects. The parts that carry the design:

| Element | What it is | Where people go wrong |
|---|---|---|
| **DataSource** | the connection | hardcoded server/workspace that breaks on deploy — parameterise or rebind at deploy time |
| **DataSet** | one query + its field list | one giant dataset feeding every region of the page; split by region so a slow query does not block the whole render |
| **ReportParameters** | user or caller input | no default and no available-values list, so the report cannot render unattended or be exported by API |
| **Tablix** | table / matrix / list | the single most common source of pagination defects — see below |
| **PageHeader / PageFooter** | repeats per physical page | referencing a dataset field (not allowed outside the body) instead of a report variable or parameter |
| **Report page setup** | size, orientation, margins | body width wider than page width minus margins — the cause of blank alternating pages |
| **Subreport** | another RDL rendered inline | executed once *per row* when placed in a detail group; a reliable way to make a report take ten minutes |

### Pagination defects, and their causes

These account for most "the report prints wrong" tickets:

- **Blank pages between every page.** Body width exceeds page width minus left and right
  margins. Shrink the body, not the margins, and check after any column width change.
- **Headers that do not repeat.** `RepeatColumnHeaders` alone is not enough on a tablix —
  the static row in the row-group hierarchy needs `KeepWithGroup` and `RepeatOnNewPage` set.
- **Page breaks in the wrong place.** Set the break on the *group*, not on the tablix, and
  decide explicitly whether the page number resets.
- **Totals on the wrong grain.** A tablix total aggregates the dataset rows in scope; pass the
  scope explicitly in the aggregate rather than relying on the default.
- **Interactive sort that does nothing in PDF.** Expected — interactive features do not survive
  a static render. Sort in the dataset query.

## Datasets and parameters

- **Push work to the source.** Filter in the dataset query, not in the tablix filter. A tablix
  filter retrieves every row and then discards it, so the query cost is unchanged and the
  render cost grows.
- **Against a semantic model, write DAX, not a wrapped SQL query.** `powerbi-dax-mastery`
  applies unchanged. Bound the result — a paginated report over an unbounded `EVALUATE` on a
  real fact table is a capacity incident, not a slow report.
- **Every parameter needs a default and a valid-values source** if the report will ever be
  exported by API or scheduled. A parameter with no default blocks unattended rendering.
- **Parameterise the data source** for dev → test → prod, or rebind at deploy. Never ship an
  RDL whose connection points at a developer's workspace.
- **Multi-value parameters** need the query to handle an empty selection, which is the case
  nobody tests.

## Deploy

```bash
# Upload / overwrite an RDL into a workspace
fab import "<workspace>.Workspace/<report-name>.PaginatedReport" -i ./reports/Statement.rdl -f

# Confirm it landed, and what it is bound to
fab ls "<workspace>.Workspace"
fab get "<workspace>.Workspace/<report-name>.PaginatedReport"
```

Confirm the exact item type and import flags with `fab import --help` for the installed `fab`
version before a first deploy — item type names have changed across releases. Create any
output directory before an export: `fab export` does not create intermediate directories.

Deploy rules:

- Deploy to a dev workspace first. A paginated report overwrite is immediate and has no
  built-in version history.
- Rebind the data source as part of the deploy, verified — not assumed.
- `-f` suppresses the overwrite prompt. Only use it once you have confirmed what you are
  overwriting, and never when sensitivity labels are in play.

## Scheduled export (Export To File)

The Export To File REST API renders a paginated report server-side to PDF, XLSX, DOCX, PPTX,
CSV, XML or an image, with parameter values supplied per call. This is how a monthly statement
run or a regulator submission gets automated.

The pattern is asynchronous — three calls, and the middle one is a poll:

1. `POST .../reports/{reportId}/ExportTo` with the format and parameter values → returns an
   export id
2. `GET  .../reports/{reportId}/exports/{exportId}` → poll until the status reports success;
   it carries a percent-complete and a retry-after
3. `GET  .../reports/{reportId}/exports/{exportId}/file` → download the bytes

Confirm the current request shape against
[Export To File for paginated reports](https://learn.microsoft.com/power-bi/developer/embedded/export-paginated-report)
before writing the client — the payload has gained options over time.

Implementation rules that matter more than the endpoint:

- **Honour the retry-after and cap the poll.** A fixed-interval poll with no deadline either
  hammers the API or hangs forever.
- **Fail loudly.** An export helper that reports success because polling stopped is worse than
  one that raises. Check the terminal status explicitly; `Failed` carries a reason — surface it.
- **Keep the bearer token out of the process list and the logs.** No tokens in command-line
  arguments, no tokens echoed on error. Acquire in-process and pass in the header.
- **Exports consume capacity**, and a month-end run of hundreds of statements is a background
  load smoothed over the following day. Estimate it first — `powerbi-fabric-capacity`.
- **Cap concurrency.** Parallel exports are the fastest way to throttle a capacity that was
  otherwise healthy.

## Migrating from SSRS

An on-premises SSRS RDL usually uploads and runs, which makes the real work easy to
underestimate. What actually needs attention:

| Area | What changes |
|---|---|
| Data sources | Shared data sources and shared datasets do not come across the same way; rebind each report |
| Authentication | Stored credentials and Windows auth give way to Entra ID and, for on-prem sources, a gateway |
| Unsupported features | Custom assemblies and some expression surface do not run in the service — find these by rendering, not by reading |
| Subscriptions | SSRS subscriptions become Power BI subscriptions or an Export To File job; email delivery semantics differ |
| Row-level security | Enforced by the semantic model or the source, not by the report — check it still holds (`powerbi-security-rls`) |

Migrate a representative sample first — the longest report, the one with subreports, and the
one with the most parameters. Those three find most of the problems.

## Related skills

| Need | Skill |
|---|---|
| Interactive report instead | `powerbi-create-pbi-report`, `powerbi-report-design` |
| Workspace / item deploy plumbing | `powerbi-fabric-cli` |
| DAX in the dataset | `powerbi-dax-mastery`, `powerbi-dax-performance` |
| Cost of a scheduled export run | `powerbi-fabric-capacity` |
| RLS behaviour under a paginated report | `powerbi-security-rls` |
| Delivery and UAT of the output | `powerbi-testing-validation` |
