---
name: powerbi-spark-livy
description: Execute PySpark or Python on Fabric Spark compute through the Livy API without creating a notebook artifact — ephemeral sessions, Delta table read/write in a lakehouse, batch job submission, and the token and lifecycle rules that keep sessions from leaking capacity. Use when the user mentions: Livy, Livy API, run PySpark in Fabric, execute Python on Fabric compute, Spark without a notebook, ephemeral Spark session, submit code to Fabric Spark, Spark session state, livyapi, Spark batch job, read Delta table from Fabric compute, scratch Spark query.
license: MIT
---

# Executing Spark on Fabric without a notebook

The Livy endpoint on a Fabric lakehouse runs arbitrary PySpark or Python on Fabric Spark
compute as an **ephemeral session** — no notebook artifact is created, nothing is persisted
in the workspace, and the session is yours to delete. It is the right tool for profiling a
Delta table, checking a silver-layer row count, validating a transform before it becomes a
pipeline, or answering "is the data even there" without leaving a notebook behind in a
governed workspace.

It is the wrong tool for anything scheduled or reviewed. If the code should run again
tomorrow, it belongs in a notebook or a Spark job definition under source control —
`powerbi-fabric-pipelines`.

## Prerequisites

| Requirement | Check |
|---|---|
| Azure CLI signed in | `az account show` |
| A lakehouse in the target workspace | the session runs against it; `fab ls "<ws>.Workspace"` |
| Fabric capacity (F SKU or trial) | Spark draws CU — see below |
| Workspace Contributor or above | session creation is a write operation |

## Authentication — the one thing people get wrong

The Livy API needs a token scoped to the Fabric service, acquired through Azure CLI:

```python
import json
import subprocess

result = subprocess.run(
    ["az", "account", "get-access-token", "--resource", "https://api.fabric.microsoft.com"],
    capture_output=True,
    text=True,
    check=True,
)
token = json.loads(result.stdout)["accessToken"]
```

Two rules:

- **A `fab auth` token is not interchangeable here.** It will authenticate the call and then
  fail on OneLake storage access from inside the Spark session, which surfaces as a confusing
  permission error on the first `spark.read`, not on session creation.
- **Never print, log or echo the token**, and never pass it on a command line — process
  arguments are readable by other users on the host. Pass it in the `Authorization` header
  from in-process variables only.

## Session lifecycle

```
1. POST   .../livyapi/versions/<ver>/sessions                 {"kind": "pyspark"}
2. GET    .../sessions/{id}                 poll until state == "idle"   (~30–90 s cold)
3. POST   .../sessions/{id}/statements      {"code": "...", "kind": "pyspark"}
4. GET    .../sessions/{id}/statements/{n}  poll until state == "available"
5. DELETE .../sessions/{id}                 ALWAYS — in a finally block
```

The base URL is the lakehouse's Livy endpoint in the target workspace. Resolve it from the
workspace and lakehouse IDs rather than hardcoding it, and confirm the API version against
[the Fabric Livy API docs](https://learn.microsoft.com/fabric/data-engineering/api-livy-overview)
before first use — it is versioned in the path.

### Step 5 is not optional

An abandoned session holds Spark compute and keeps drawing CU until it times out. Every
helper you write must delete the session in a `finally`, and the deletion must run even when
a statement raised. If a run is interrupted, list sessions and clean up before starting
another — leaked sessions are a common cause of a capacity that is "mysteriously" busy.

```python
session_id = create_session(token)
try:
    wait_for_idle(token, session_id)
    out = run_statement(token, session_id, code)
finally:
    delete_session(token, session_id)
```

### Polling

Cold-start is 30–90 seconds; a warm pool is faster. Poll with a bounded backoff and a hard
deadline, and fail loudly on timeout — a helper that returns success because it stopped
waiting is worse than one that errors. Distinguish the states: `starting`, `idle`, `busy`,
`error`, `dead` on sessions; `waiting`, `running`, `available`, `error`, `cancelled` on
statements. A statement that reaches `available` can still carry a Python traceback in its
output — check the output payload's status, not just the HTTP status.

## Working with lakehouse data

Inside the session, Spark is already wired to the lakehouse the session was created against:

```python
# Delta tables in the attached lakehouse
df = spark.sql("SELECT * FROM silver.orders WHERE order_date >= '2026-01-01'")
df.printSchema()
print(df.count())

# Files, by ABFSS path
raw = spark.read.parquet("abfss://<workspace>@onelake.dfs.fabric.microsoft.com/<lakehouse>.Lakehouse/Files/raw/")
```

Cross-lakehouse reads work by full ABFSS path, provided the caller has access.

**Bound everything.** A session is interactive compute on a shared capacity, so treat each
statement the way you would treat an ad-hoc production query: `LIMIT` on exploration,
`count()` on a filtered frame rather than a full table, `.explain()` before an expensive
join. Returning a large result through the Livy statement payload is also slow and
truncation-prone — aggregate in Spark and return the summary, or write to a table and read
it from elsewhere.

### Writes

Writing is possible and that is exactly why it needs a rule: **never write to a lakehouse
table from an ephemeral session without explicit confirmation naming the table and the
mode.** `overwrite` on a silver or gold table destroys data no one asked you to touch, and
there is no notebook artifact recording that it happened. Scratch writes belong in a
clearly-named scratch schema.

## Batch jobs

The same endpoint accepts batch submissions for a packaged job rather than interactive
statements. Use batch when the work is long-running and you do not need a REPL; the same
lifecycle discipline applies, including cleanup. Anything recurring should instead be a
Spark job definition in the workspace, under source control.

## Capacity cost

A Spark session is background-class consumption on the capacity and is smoothed over 24
hours, which means a session you ran this afternoon can be part of tomorrow morning's
throttling. Before opening a session on a shared or production capacity, state the expected
cost and get a yes — `powerbi-fabric-capacity` has the statement shape and the throttling
stages. Session cost is driven by node size, node count and *wall-clock duration*, so an idle
session you forgot to delete costs the same as one doing work.

## When to use something else

| Situation | Better tool |
|---|---|
| Recurring transform | notebook or Spark job definition — `powerbi-fabric-pipelines` |
| Light SQL over lakehouse/warehouse data, no Spark needed | `powerbi-duckdb-lakehouse` — no capacity cost, no cold start |
| Medallion layer design rather than execution | `powerbi-medallion-architecture` |
| Data quality or freshness check | `powerbi-duckdb-lakehouse` first; Spark only if the volume demands it |
| Semantic model questions | `powerbi-dax-mastery`, not Spark |

## Related skills

`powerbi-fabric-cli` · `powerbi-fabric-capacity` · `powerbi-duckdb-lakehouse` ·
`powerbi-medallion-architecture` · `powerbi-fabric-pipelines` · `powerbi-data-transformation`
