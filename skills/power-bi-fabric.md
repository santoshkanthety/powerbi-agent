---
name: Power BI Fabric
description: Manage Microsoft Fabric / Power BI Service workspaces and datasets via powerbi-agent — authenticate, list workspaces, list datasets, trigger refreshes. Invoke when the user mentions Fabric, Power BI Service, workspace, dataset refresh, or publishing to the cloud.
tools: powerbi-agent CLI (pbi-agent)
---

# Skill: Fabric / Power BI Service Operations

## Trigger
Activate when the user mentions Microsoft Fabric, Power BI Service, workspaces, cloud datasets, or dataset refresh. Requires Azure authentication.

## Authentication

```bash
# Interactive device-code / browser login (run this first)
pbi-agent fabric login
```

## Commands

```bash
# List workspaces the authenticated user can access
pbi-agent fabric workspaces

# List semantic models (datasets) in a workspace (defaults to "My Workspace" if omitted)
pbi-agent fabric datasets
pbi-agent fabric datasets --workspace "Finance Analytics"
pbi-agent fabric datasets -w "00000000-1111-2222-3333-444444444444"

# Trigger a dataset refresh (returns immediately by default)
pbi-agent fabric refresh "Sales Model"

# Wait for the refresh to complete before returning
pbi-agent fabric refresh "Sales Model" --workspace "Finance Analytics" --wait
```

## Guidance
- `--workspace` accepts either a workspace **name** or a **GUID**.
- `--wait` polls until the refresh terminates (Completed / Failed / Cancelled). Use for CI pipelines; skip for interactive triggering.
- Refreshes require the dataset's scheduled refresh credentials to be configured in the service — this CLI does not set credentials.
- For dataset names with spaces or special chars, always quote them.

## Common Failures
- **"Not authenticated"** → run `pbi-agent fabric login` first
- **"Workspace not found"** → run `pbi-agent fabric workspaces` to verify the exact name/ID
- **Refresh returns 400 / credentials missing** → configure dataset credentials in the Power BI Service UI; powerbi-agent only triggers refreshes
- **Token expired** → re-run `pbi-agent fabric login`
