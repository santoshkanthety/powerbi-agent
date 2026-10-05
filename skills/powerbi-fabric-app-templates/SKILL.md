---
name: powerbi-fabric-app-templates
description: Choose, scaffold and author Rayfin templates for Microsoft Fabric Apps — the bundled dataapp and blankapp templates, the awesome-rayfin community gallery, and how to publish a reusable template with rayfin-template.yml so a delivery team scaffolds a governed starting point instead of a blank page. Use when the user mentions: rayfin template, Fabric app template, awesome-rayfin, dataapp template, blankapp, --list-templates, app starter, app scaffold, reusable Fabric app, template gallery, publish a template, rayfin-template.yml.
license: MIT
---

# Rayfin templates for Fabric Apps

A Rayfin template is a repo (or a path in one) carrying `rayfin-template.yml` at its root,
which `rayfin init` and `create-rayfin` can scaffold from. Templates are where a delivery
team's conventions live: the auth flow, the data-access layer, the chart primitives, the
theme, the validation harness. Getting the template right once is worth more than reviewing
twenty hand-rolled apps.

Read `powerbi-fabric-apps` first for the CLI, the SDK and rule zero (never write Rayfin API
code from memory). This skill covers only template selection and authoring.

## Always list before choosing

The bundled template set moves with the CLI version. Enumerate it rather than trusting any
list — including this one:

```bash
npx rayfin init --list-templates
```

## Which template

| Situation | Template | Why |
|---|---|---|
| Analytical app over a Power BI semantic model | `dataapp` | Ships DAX-generation guidance, chart primitives with cross-highlighting, a formatted data grid, centralised theming, format-string reuse and a Playwright validation workflow. Currently the CLI is the only supported way to use it. |
| Anything else, or a build you want to own end to end | `blankapp` | Auth and nothing else. No framework opinions to unpick. |
| A team standard exists | your own template | See *Authoring* below. |
| User explicitly asks for a gallery app | an `awesome-rayfin` entry | Read it before scaffolding; see the caveat below. |

For a Power BI–adjacent app, default to `dataapp`:

```bash
npm create @microsoft/rayfin@latest -- "<app-name>" --template dataapp --workspace "<workspace-name>"
```

Everything the `dataapp` template provides is work an agent would otherwise redo — badly —
in every session: authentication, DAX quality, and visual coherence. Without it the usual
failures are broken or empty visuals, inconsistent chart behaviour, and far more model
queries than the app needs.

### What `dataapp` gives you

- **Visuals**: bar (vertical, horizontal, grouped, stacked), line with optional markers,
  area, scatter, pie and donut, heatmap, bubble, waterfall, KPI cards, and layered
  composites such as bars with data labels or dual-axis lines — with cross-highlighting.
- **Data grid**: headers from semantic model metadata, per-column number and date formatting
  from format strings, sorting, overflow handling, light/dark themes, and cell renderers for
  data bars, boolean indicators, clickable URLs, image cells with a lightbox, and multi-field
  cells.
- **Theming**: shared styles in one place, so a palette or font change flows to cards,
  buttons, charts, grids and tooltips instead of drifting per component.
- **Format strings**: define once per result column; reused across axes, tooltips, labels,
  cards and grid cells.
- **Browser validation**: a Playwright workflow that opens the real app and checks rendering,
  clipping, readability, grid overflow, loading/empty/error states, cross-highlighting and
  the console — at desktop and mobile widths.

Use the template's primitives. A visual with no primitive is possible but costs iterations
and validation, so say that out loud before promising it.

## The community gallery

[`microsoft/awesome-rayfin`](https://github.com/microsoft/awesome-rayfin) is a
community-curated gallery. Scaffold from it by URL:

```bash
npm create @microsoft/rayfin -- --template https://github.com/microsoft/awesome-rayfin
```

Entries most relevant to a Power BI / Fabric practice:

| Template | What it is |
|---|---|
| **Power BI Fixer** | Workspace that inspects, documents and fixes Power BI semantic models and reports |
| **Semantic Directory** | Searchable directory of Power BI / Fabric semantic models with lineage and relationship tracing |
| **Fabric Atlas** | Workspace catalog, lineage, governance and access review for Fabric |
| **Finance Analytics** | Config-driven FP&A app — variance, trend and aging tables with native Excel copy |
| **Helsinki Public Transport** | Live transit visualisation on Fabric Real-Time Intelligence with DirectQuery |
| **Universal App** | Lean React + Vite starter with capability routing, meant to grow |
| **Angular Blank / Angular Dashboard** | Fabric-authenticated Angular + Material starters |

Caveat, and state it to the user: gallery templates are community contributions, not
Microsoft-supported product surface. Before building on one, check what it actually does
with your data — connectors declared in `rayfin.yml`, entities under `rayfin/data/`, and
anything it persists. A domain template that copies a governed semantic model's output into
its own SQL database has created a second copy of that data; that is a governance decision,
not an implementation detail.

Gallery templates are also where to look for a *pattern* even when you scaffold `dataapp` —
reading how Semantic Directory traces lineage is cheaper than inventing it.

## Authoring a template

Make a template when the same decisions keep getting re-made: tenant-specific auth wiring,
a house theme, a standard connector set, an approved chart vocabulary, a validation gate.

Requirements:

1. **`rayfin-template.yml` at the repo root.** This is what makes the repo scaffoldable.
2. **A working Rayfin project.** The template is a project; if `npx rayfin dev` and
   `npx rayfin up --dry-run` don't pass in it, they won't pass for anyone scaffolding it.
3. **No tenant-specific identifiers committed.** Workspace IDs, item IDs, app URLs and
   publishable keys belong in `rayfin/.env` or `rayfin.yml` values the scaffolding step
   fills in — never hardcoded in source.
4. **No secrets.** Including in frontend assets, regardless of `assetAccess`.
5. **Agent context files.** Ship `AGENTS.md` and let
   `npx rayfin init ai-files install` manage `.agents/skills/rayfin/SKILL.md` so whoever
   scaffolds it gets the version-locked skill, not your snapshot of it.

A house template worth maintaining usually carries:

```
rayfin-template.yml          # required at root
AGENTS.md                    # capability router: what exists, what to read first
rayfin/
  rayfin.yml                 # services + auth + static hosting defaults
  data/                      # shared entities (audit columns, user profile, …)
  connectors/                # connector shape, no tenant IDs
src/
  lib/client.ts              # one data-access path
  theme/                     # the house palette, tokens, type scale
  components/charts/         # the approved chart vocabulary
tests/                       # the validation gate the team agreed on
```

Verify the scaffold from a clean directory before publishing — `--list-templates` then
scaffold, install, `rayfin dev`, `rayfin up --dry-run`. A template that only works in the
directory it was authored in is the most common defect.

To contribute to the gallery, follow `CONTRIBUTING.md` in `microsoft/awesome-rayfin`.

## Template hygiene after scaffolding

The scaffold is a starting point, not a verdict:

- Read `AGENTS.md` and `.agents/skills/rayfin/SKILL.md` before editing anything.
- Run `npx rayfin init ai-files status` — a `user-modified` or stale in-project skill is the
  usual cause of code written against the wrong Rayfin version.
- Delete the template's demo entities and sample data you are not using. Shipped sample
  entities become real tables in a real SQL database on `rayfin up`.
- If the scaffold includes its own semantic model client *and* you added a
  `fabric-semanticmodel` connector, replace the scaffold's calls rather than maintaining two
  data-access paths.

## Related skills

| Need | Skill |
|---|---|
| CLI, SDK, connectors, deployment, security | `powerbi-fabric-apps` |
| CU cost of what the template stands up | `powerbi-fabric-capacity` |
| Chart choice and layout in the frontend | `powerbi-report-design` |
| DAX the template's queries will run | `powerbi-dax-mastery`, `powerbi-dax-performance` |
| Theme tokens shared with reports on the same model | `powerbi-modifying-theme-json` |
