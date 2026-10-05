---
name: powerbi-fabric-apps
description: Build, run and deploy Microsoft Fabric Apps with the Rayfin SDK and CLI — TypeScript decorator data models, Fabric SSO, GraphQL/DAB data API, storage, Functions, static hosting, and the fabric-semanticmodel connector that executes DAX against a Power BI semantic model from a custom app. Use when the user mentions: Fabric App, Fabric Apps, Rayfin, rayfin CLI, rayfin up, rayfin init, rayfin dev, rayfin connector, data app, backend as a service on Fabric, custom app on a semantic model, app on top of Power BI data, GraphQL on Fabric, Fabric SQL database app, appbackends, deploy an app to a Fabric workspace.
license: MIT
---

# Fabric Apps with the Rayfin SDK

Fabric Apps (preview) is a managed backend-as-a-service inside Microsoft Fabric. You
declare the data model as TypeScript classes with decorators; Rayfin provisions the SQL
database, Entra SSO, a GraphQL data API, file storage, Functions and static hosting, and
deploys all of it as one Fabric item with `npx rayfin up`.

For powerbi-agent the headline use is the **`fabric-semanticmodel` connector**: an app that
executes DAX against an existing Power BI semantic model with delegated user identity, so
you can ship a bespoke analytical front end on a model you already govern — without
embedding, without a service principal, and without the Execute Queries REST API in your
own code.

## Rule zero: route, don't improvise

**Never write Rayfin API code from memory.** The decorator set, the client generics, the
connector packages and the deployment surface are version-locked per project, and they move
fast in preview. Remembered signatures are routinely wrong against the installed version.

Order of authority, highest first:

1. `.agents/skills/rayfin/SKILL.md` in the project — the version-matched skill the CLI
   installs. If it exists, it wins over this file for every in-project specific.
2. `rayfin docs` CLI and the package READMEs under `node_modules/@microsoft/rayfin-*`.
3. `AGENTS.md` at the project root, when the template ships a capability router.
4. Microsoft Learn: [Fabric Apps overview](https://learn.microsoft.com/fabric/apps/overview),
   [CLI reference](https://learn.microsoft.com/fabric/apps/cli-reference).

This skill owns **getting there and the Power BI bridge**. Once you are inside a project,
load `.agents/skills/rayfin/SKILL.md` and follow it.

If you can reach none of those sources, say so and stop. Do not offer a "general approach"
or placeholder code — fabricated Rayfin APIs are the specific failure this discipline exists
to prevent.

## Prerequisites

| Requirement | Check |
|---|---|
| Node.js 20+ | `node --version` |
| Rayfin CLI | `npx rayfin --version` (installs on demand; or `npm i @microsoft/rayfin-cli`) |
| Fabric capacity on the target workspace | `fab ls` then check the workspace capacity, or the portal |
| Tenant setting **Fabric Apps (preview)** enabled | Fabric admin portal → Tenant settings |
| Tenant setting **Semantic Model Execute Queries REST API** enabled | only for the `fabric-semanticmodel` connector |
| Contributor / Member / Admin on the workspace | `fab acl ls` or the portal |
| Build + Read on the semantic model | only for the `fabric-semanticmodel` connector |
| Supported region | [region availability](https://learn.microsoft.com/fabric/admin/region-availability) — Fabric Apps is not in every region |

Fabric Apps consumes CUs from the assigned capacity. Before standing one up on a shared
production capacity, read `powerbi-fabric-capacity` and tell the user the expected impact.

## Is this already a Rayfin project?

Check **before** scaffolding, even when the user says "new app". A directory is a Rayfin
project if either is true:

- `rayfin/rayfin.yml` exists
- `package.json` depends on any `@microsoft/rayfin-*` package

| Situation | Do this |
|---|---|
| Already a Rayfin project | Load `.agents/skills/rayfin/SKILL.md`, continue in place |
| Existing non-Rayfin app here | Add Rayfin in place: `npx -y -p @microsoft/rayfin-cli@latest rayfin init --project-name <name>` |
| Empty directory | Scaffold (below) |

Never create a nested or sibling project inside one that already exists.

## Scaffold

Agents run non-interactively (stdin is not a TTY), so use the `npx -y` form —
`npm create` can mishandle piped stdin and strip flags, and `--project-name` is required
non-interactively.

```bash
# Analytical app on a semantic model — the Power BI case. Use this template.
npm create @microsoft/rayfin@latest -- "<app-name>" --template dataapp --workspace "<workspace-name>"

# Minimal app, no framework opinions
npx -y @microsoft/create-rayfin@latest --project-name <app-name> --template blankapp

# Add Rayfin to a directory that already has source
npx -y -p @microsoft/rayfin-cli@latest rayfin init --project-name <app-name> [directory]

# See what the installed CLI offers before choosing
npx rayfin init --list-templates
```

`create-rayfin` creates a child directory named from a slugified `--project-name`, so `cd`
into it. An in-place `rayfin init` scaffolds into the current directory.

For the gallery of community templates and how to author one, see
`powerbi-fabric-app-templates`.

Then read `AGENTS.md` (if present) and `.agents/skills/rayfin/SKILL.md` before writing a
line of app code.

## Project shape

```
<app>/
├── rayfin/
│   ├── rayfin.yml           # services, auth, static hosting, connectors — the contract
│   ├── .env                 # deployment properties; never commit secrets
│   ├── .deployments.json    # recorded deployments: fabricWorkspaceId, fabricItemId,
│   │                        #   hostingUrl, fabricDeepLink, deployedAt
│   ├── data/                # TypeScript entity classes — the schema source of truth
│   ├── connectors/<name>/   # generated connector schema (schema.ts, connectorConfig)
│   └── functions/           # Functions package (optional)
├── .agents/skills/rayfin/   # version-locked in-project skill — authoritative
├── AGENTS.md                # capability router, when the template ships one
└── src/                     # frontend
```

`rayfin/.deployments.json` is how any tool (including Kurt Buhler's `/fabric-app-pane` mod)
knows where an app is deployed. Read it rather than asking the user for IDs.

## Data model

Entities are plain TypeScript classes with decorators from `@microsoft/rayfin-core`.
Verify the decorator set against the in-project skill — this shape is the documented
pattern, not a guarantee for your installed version:

```typescript
import { entity, role, text, boolean, date, uuid } from '@microsoft/rayfin-core';

@entity()
@role('authenticated', '*', {
  policy: (claims, item) => claims.sub.eq(item.user_id),
})
export class Todo {
  @uuid() id!: string;
  @text({ min: 1, max: 100 }) title!: string;
  @boolean() isCompleted!: boolean;
  @date() createdAt!: Date;
  @date({ optional: true }) dueDate?: Date;
  @text() user_id!: string;
}
```

Rayfin derives the table definitions, the GraphQL endpoints, the row-level authorization
rules and the type-safe client methods from this.

**The code is the only safe place to change schema.** The child SQL database is editable in
the Fabric portal, and editing it there causes schema conflicts that break the app. Change
`rayfin/data/`, then `npx rayfin up db apply`.

## The Power BI bridge: `fabric-semanticmodel`

This is the connector that makes Fabric Apps interesting to a Power BI practice. It gives
the app typed, delegated, read-only DAX execution against a semantic model.

```bash
# 1. Find the model (omit --workspace-id to search the project's recorded workspaces)
npx rayfin connector search --workspace-id <workspace-id> --type fabric-semanticmodel --json

# 2. Add it
npx rayfin connector add \
  --type fabric-semanticmodel \
  --workspace-id <workspace-id> \
  --item-id <semantic-model-item-id> \
  --name salesModel \
  --operations executeQuery

# 3. Run the npm install command the CLI prints — verbatim. It is version-matched.

# 4. Inspect without changing anything; --url accepts a portal URL and derives both IDs
npx rayfin connector inspect --name salesModel --entity Sales --rows 10
npx rayfin connector inspect --url "https://app.powerbi.com/groups/<ws>/datasets/<id>"
npx rayfin connector inspect --name salesModel --query ./queries/top-products.dax

# 5. Smoke-test an operation from the terminal before wiring the UI
npx rayfin connector invoke salesModel executeQuery --input '{"query":"EVALUATE ROW(\"n\", 1)"}'
```

`connector add` writes to `rayfin/rayfin.yml`:

```yaml
connectors:
  - name: salesModel
    type: fabric-semanticmodel
    config:
      workspaceId: "<workspace-id>"
      itemId: "<semantic-model-item-id>"
    auth:
      type: delegated
    version: "1"
    operations:
      - name: executeQuery
```

Keep the generated `version` value. Do not hand-edit `workspaceId` / `itemId` when a
`connector` subcommand can set them.

Client side — one data-access path, the connector client:

```typescript
const result = await client.connectors.salesModel.executeQuery({
  query: 'EVALUATE TOPN(10, Sales)',
});

if (result.status === 'success') {
  render(result.table.columns, result.table.rows);
} else {
  showError(result.error.category, result.error.message);
}
```

Always branch on `status` before touching `table`. A failed query must surface an error
state — never substitute mock data for a connector failure.

### DAX inside a Fabric App

The DAX discipline does not change because the host is a web app. `powerbi-dax-mastery` and
`powerbi-dax-performance` still apply, plus:

- **Query the model metadata before writing DAX.** Never guess table, column or measure
  names. `pbi-agent model tables` / `model measures` against the model (or
  `rayfin connector inspect --entity`) first.
- **Bound every result set.** `TOPN`, an explicit row cap, or a filtered `SUMMARIZECOLUMNS`.
  An unbounded `EVALUATE Sales` on a real fact table will take the app down, not just slow it.
- **Reuse results.** Each `executeQuery` is a capacity-billed query against the model. Cache
  per interaction rather than per component render.
- **Apply the model's format strings** to cards, axes, tooltips, data labels and grid cells,
  so the app agrees with the reports built on the same model.
- **Delegated auth only.** RLS on the model is enforced because the caller is the signed-in
  user. Never add a service principal, a stored token, or a direct call to the Execute
  Queries REST API to work around a permission error — fix the permission.

Other connector types are available; `npx rayfin connector types -v` lists what the
installed CLI supports (lakehouse, warehouse, SQL database in Fabric, semantic model).

## Local development

```bash
npx rayfin dev                              # full stack locally
npx rayfin dev --workspace "<ws-name>"      # first run, names the backend workspace
npx rayfin dev --skip-db-apply              # don't auto-apply schema
npx rayfin dev functions apply              # local Functions host (default port 7071)
npx rayfin env --framework vite             # emit .env.local from rayfin/.env
npx rayfin env --framework nextjs --show    # preview without writing
```

Local dev may use email/password auth. **Deployed apps are Fabric SSO only** — no other
provider is available after deployment. Do not build a sign-in flow that assumes otherwise.

## Deploy

```bash
npx rayfin login                            # and: rayfin login status / rayfin logout
npx rayfin up --dry-run --verbose           # always first: validates and resolves the workspace
npx rayfin up --workspace-id <id> --yes     # non-interactive deploy
npx rayfin up --exclude-services functions  # skip functions or staticHosting
npx rayfin up status --json
npx rayfin up list                          # every recorded deployment
npx rayfin up switch --list                 # then: rayfin up switch <workspace>
```

Targeted re-deploys, when only one service changed:

| Command | Deploys |
|---|---|
| `npx rayfin up db apply` | DAB config / schema to the remote item |
| `npx rayfin up staticapp deploy [--skip-build]` | built frontend assets |
| `npx rayfin up functions deploy [--skip-build]` | Functions |
| `npx rayfin up connector apply [--name <n>]` | declared GraphQL connector config |

**`--force` on `rayfin up` allows destructive data-schema changes.** Treat it the way you
treat `DROP`: name the entity and the column, say what data is lost, and get an explicit yes
before running it. Never add `--force` to clear an error you have not diagnosed.

`--capacity-id` cannot be combined with `--workspace`, `--workspace-id` or `--workspace-uri`.

## Deployed topology

One backend endpoint fronts every service:

```
https://<your-app>-app.rayfin.windows.net/
  /api/graphql    data API, used by the Rayfin client
  /auth           authentication
  /storage        file storage
```

Child items appear under the Fabric app in the portal: the SQL database (read-only there),
authentication, and static content. Item permissions do **not** inherit from workspace
roles — a user needs **Run and interact** to use the app, **Edit** to deploy to it,
**Reshare** to grant access.

## Agent context files

```bash
npx rayfin init ai-files status --json      # up-to-date / update-available / user-modified / missing / …
npx rayfin init ai-files install --yes      # idempotent; preserves user config
npx rayfin init ai-files install --force skill:rayfin
npx rayfin init ai-files install --dry-run
```

This manages `AGENTS.md`, `.mcp.json` and `.agents/skills/rayfin/SKILL.md`. `--force` never
overwrites `AGENTS.md`. Run `status` at the start of any session in an existing project: a
`user-modified` or stale in-project skill is the usual cause of code that compiles against
the wrong Rayfin version.

## Security

You own, and Fabric does not:

- **No secrets in the repo, in `rayfin/.env` commits, or in frontend assets** — regardless
  of the `assetAccess` setting. Static assets are shipped to the browser.
- **What authenticated users can see and do.** SSO proves identity; your `@role` policies
  and your queries decide authorization.
- **Least privilege for contributors.** Edit on the item means they can `rayfin up`.
- Compliance accountability for whatever the app stores. An app over a governed semantic
  model that persists extracts into its own SQL database has created a second copy of that
  data — say so, and check it against `powerbi-data-governance-traceability`.

## Not a fit

Say so early rather than fighting the platform:

- Complex multi-step transactions or stored procedures.
- Custom auth providers beyond Fabric SSO (and email/password locally).
- Anything needed in a region where Fabric Apps is not yet available.
- A report. If the deliverable is a report, build a report — `powerbi-create-pbi-report`.
  Fabric Apps is for interactions a report cannot express.

## Related skills

| Need | Skill |
|---|---|
| Template gallery, choosing and authoring templates | `powerbi-fabric-app-templates` |
| CU cost of running the app on a capacity | `powerbi-fabric-capacity` |
| Workspace / item plumbing around the app | `powerbi-fabric-cli` |
| DAX the app will execute | `powerbi-dax-mastery`, `powerbi-dax-performance` |
| Chart choice and formatting in the frontend | `powerbi-report-design` |
| Governance of a second copy of governed data | `powerbi-data-governance-traceability` |
