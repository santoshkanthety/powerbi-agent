---
name: powerbi-fabric-capacity
description: Read and reason about Microsoft Fabric capacity consumption — CU accounting, smoothing, bursting, the four throttling stages, F-SKU sizing, and querying the Fabric Capacity Metrics semantic model with DAX to attribute CU seconds to items and operations. Estimate the capacity cost of an action before running it. Use when the user mentions: capacity, CU, capacity units, Fabric Capacity Metrics, throttling, interactive delay, interactive rejection, background rejection, smoothing, bursting, F2 F64 F256, P1 P2 P3, capacity overload, who is using the capacity, cost of a refresh, autoscale, pause capacity, resize capacity.
license: MIT
---

# Fabric capacity: CU accounting and cost-before-action

A Fabric capacity is a shared, metered pool. Every query, refresh, pipeline run, Spark job
and Fabric App request draws capacity units (CU) from it, and a capacity pushed past its
limit does not fail loudly — it throttles everyone on it, including reports nobody touched.

Two jobs:

1. **Attribute** consumption — what is actually burning CU, per item and operation.
2. **Estimate before acting** — say what an action will cost the capacity *before* running it.

## Estimate before you act

Before any operation that draws meaningful CU on a shared or production capacity, tell the
user the expected impact in one line, then wait for a yes. Treat these as triggering it:

- A full semantic model refresh, or any refresh of an import model over ~1 GB
- A Direct Lake model reframe or a large table reload
- A Spark job, notebook run or Livy session (see `powerbi-spark-livy`)
- A pipeline backfill, or any ETL over more than one partition
- Standing up a Fabric App on a shared capacity (see `powerbi-fabric-apps`)
- A bulk `fab` operation across many items
- A DAX query without a row bound against a large fact table

Shape of the statement, with real numbers where you have them:

> Full refresh of `Sales Analytics` (4.2 GB import, 18 partitions). Last comparable refresh
> consumed ~3,100 CU seconds — about 2.2 % of the F64 daily budget, running ~11 minutes.
> Current capacity utilisation is 71 %. Safe now; it would be marginal during the 08:00
> business-hours peak. Proceed?

When you have no prior measurement, say that rather than inventing a figure: name the
comparable operation you would measure, offer to measure it, and give the order of magnitude.

## CU mechanics

| Concept | What it means in practice |
|---|---|
| **CU second** | The unit everything is billed in. A capacity's SKU number is its CU-per-second allowance; an F64 has 64 CU/s, so 5,529,600 CU seconds per day. |
| **Smoothing** | Consumption is spread forward rather than charged at the instant it happens — interactive operations over a short window, background operations (refreshes, pipelines, Spark) over 24 hours. This is why a heavy refresh shows up as a flat shelf across the next day, not a spike, and why yesterday's work can throttle you today. |
| **Bursting** | A single operation may consume faster than the SKU allows, finishing sooner; the excess is smoothed forward. Bursting makes operations fast and overage debt invisible until it throttles. |
| **Overage / carry-forward** | Smoothed future consumption that exceeds the allowance. The throttling stage is a function of *how far forward* the overage reaches, not of instantaneous load. |

### The four stages

| Future smoothed overage | Effect |
|---|---|
| under 10 minutes | nothing — normal bursting |
| 10 to 60 minutes | **interactive delay** — interactive requests are held, adding seconds to every report interaction |
| 60 minutes to 24 hours | **interactive rejection** — interactive requests fail; reports and apps error for users |
| over 24 hours | **background rejection** — refreshes and jobs are refused too |

Read the consequence out of this: by the time users complain about slow reports, the
capacity is already in interactive delay, and the cause is usually a background job that
finished hours ago. Diagnose backwards from the metrics app, not from the report.

### SKUs

F-SKU CU/s equals the SKU number: F2 = 2, F8 = 8, F64 = 64, F256 = 256, up to F2048.
Legacy Premium maps at P1 = F64 = 64 CU/s, P2 = 128, P3 = 256. An F64 or larger lifts the
per-user Pro licence requirement for *consuming* content in that workspace; below F64, every
consumer still needs Pro.

F SKUs can be paused (billing stops, content is unavailable) and resized. Resizing is the
honest answer more often than optimisation is — but measure first, because a capacity that
throttles from one unbounded nightly query does not need to be bigger.

## Reading the Capacity Metrics app

Install **Microsoft Fabric Capacity Metrics** from AppSource into a workspace you control.
It ships a semantic model, and that model is queryable over XMLA — which means
`powerbi-agent` can read it directly instead of screenshotting a report page.

```bash
# The metrics app's semantic model is a dataset like any other
pbi-agent fabric workspaces
pbi-agent fabric datasets --workspace "Fabric Capacity Metrics"
```

**Discover the schema before writing DAX against it.** The metrics model's table and column
names change between app versions; a query written from memory will fail or, worse, return
a plausible wrong number. Enumerate first:

```bash
pbi-agent model tables                       # against the metrics model via XMLA
pbi-agent model measures --format json
```

Then build the query from what is actually there. The shape you are looking for is almost
always: a capacity dimension, a time-point or date table, an item dimension, an operation
dimension, and measures over CU seconds and duration. Typical questions, expressed against
whatever those are named in your version:

- Total CU seconds by item, descending, for a date range → the one query that answers "what
  is burning the capacity"
- CU seconds by operation type → separates interactive query load from background refresh load
- Utilisation percentage by time point → finds the peak and whether it crossed a throttling
  stage
- Throttling / overage measures by time point → confirms which stage was reached and when
- Storage by workspace → the other half of the bill, and not smoothed

The metrics app only retains a rolling window (commonly 14 days). If the user needs trend
over quarters, extract to a lakehouse on a schedule — a one-off query cannot recover data
the app has already dropped. Say this before someone asks for a six-month chart.

**Keep the app's model warm.** Its semantic model goes idle, and an XMLA query against a
cold model can fail or time out on first contact. Query it, let the first attempt warm it,
and retry once before reporting a failure.

## Attribution in practice

A disciplined investigation, in order:

1. **Confirm the stage.** Was there interactive delay / rejection, and in which window?
   Without this you are optimising something that was never the problem.
2. **Split background from interactive** for that window. Background overage points at a
   refresh, pipeline or Spark job; interactive points at report or app query load.
3. **Rank items by CU seconds** in the window *and* the 24 hours before it — smoothing means
   the culprit may have finished long before the symptom.
4. **Rank operations within the top item.** One unbounded DAX query, one non-folding Power
   Query step, or one full refresh of a model that should be incremental explains most cases.
5. **Fix the cause, in this order:** incremental refresh over full; query folding over local
   evaluation (`powerbi-power-query`); bounded queries and aggregations
   (`powerbi-dax-performance`); Direct Lake over import where the data is already in OneLake
   (`powerbi-performance-scale`); schedule separation so background work lands off-peak.
   Resizing the capacity is the last step, not the first.
6. **Re-measure.** State the before and after in CU seconds, not in adjectives.

## Fabric Apps on a capacity

A Fabric App's services — SQL database, GraphQL data API, static hosting, Functions — all
draw CU from the workspace's capacity, and every `executeQuery` through a
`fabric-semanticmodel` connector is an interactive query against the model on top of
whatever the reports are already doing. Before standing one up on a production capacity:

- Say that the app's traffic is interactive load, so it competes directly with report users
  and shares their throttling stages.
- Insist on bounded queries and result reuse in the app (`powerbi-fabric-apps` covers both).
- Prefer a separate capacity, or a dev capacity, for anything with unknown traffic.

## Guardrails

- **Never pause, resize, or reassign a capacity without explicit confirmation.** Pausing makes
  every item on it unavailable; resizing changes the bill. Name the capacity and the current
  SKU in the confirmation.
- **Never move a workspace between capacities** to dodge throttling without saying what else
  shares the destination.
- Read-only investigation needs no confirmation. Say which capacity you are reading.
- Admin-level metrics require capacity admin rights. If a read fails on permissions, report
  the missing right — do not try a different path to the same data.

## Related skills

| Need | Skill |
|---|---|
| Workspace and item plumbing, `fab` commands | `powerbi-fabric-cli` |
| Refresh strategy, incremental refresh | `powerbi-refresh-semantic-model` |
| Query cost at the model level | `powerbi-dax-performance`, `powerbi-performance-scale` |
| Folding and ETL cost | `powerbi-power-query`, `powerbi-fabric-pipelines` |
| Spark and Livy session cost | `powerbi-spark-livy` |
| Apps drawing on the same capacity | `powerbi-fabric-apps` |
| Tenant settings around capacity and metrics | `powerbi-audit-tenant-settings` |
