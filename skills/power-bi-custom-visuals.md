---
name: power-bi-custom-visuals
version: 0.2.0
description: Build, package, and embed Power BI custom visuals (.pbiviz) into PBIR reports via the powerbi-visuals SDK. Automatically invoke when the user asks to "create a custom visual", "vibe-code a visual", "build a pbiviz", "scaffold a custom visual project", "import a custom visual into the report", "iterate on visual.ts", or mentions powerbi-visuals-tools, pbiviz, capabilities.json, IVisual, or D3-based custom Power BI visuals.
---

# Authoring Power BI custom visuals end-to-end

Author a TypeScript Power BI custom visual, package it as `.pbiviz`, and embed it in a PBIR report so Power BI Desktop loads it on open. Three CLI commands plus the `powerbi-visuals-tools` SDK do the work; this skill drives Claude through the iteration loop.

## Toolchain

| Tool | Role |
|---|---|
| `pbiviz` (`powerbi-visuals-tools`) | Scaffolds, type-checks, packages |
| `pbi-agent visual import-custom` | Copies `.pbiviz` into `RegisteredResources/`, registers in `report.json` |
| `pbi-agent visual list-custom` | Shows what's currently registered (embedded + public) |
| `pbi-agent visual remove-custom` | Removes registration + on-disk `.pbiviz` |

## First-run setup (with user consent)

Confirm the user is on a machine that can run Node before installing anything.

```bash
node --version          # need 18+ ; if missing, ask before installing
npm --version
npm install -g powerbi-visuals-tools
pbiviz --version
```

Pin SDK packages to known-good versions inside the visual project:

- `powerbi-visuals-tools` matching the global pbiviz
- `powerbi-visuals-api` matching the `apiVersion` in `pbiviz.json`

## Scaffold

Always create the visual project as a **sibling of the `.pbip`**, never inside the `.Report` or `.SemanticModel` folders — Power BI Desktop will reject contaminated PBIR folders.

```text
MyProject.pbip
MyProject.Report/
MyProject.SemanticModel/
mygaugevisual/         ← scaffolded here
```

```bash
pbiviz new mygaugevisual
cd mygaugevisual
npm install
```

**Naming constraint:** `pbiviz new` rejects names with anything other than letters and digits. Strip hyphens and underscores from any user-provided name before running it (`my-gauge-v1` → `mygaugev1`).

## Fill required pbiviz.json metadata

`pbiviz package` strict-validates `author.name`, `author.email`, `visual.description`, and `visual.supportUrl`. The fresh scaffold leaves them blank, so the first package call will fail on metadata before any code runs. Populate them up-front:

- `author.name` / `author.email` — derive from `git config user.name` / `user.email` (no extra prompt to the user)
- `visual.description` — derived from the spec from the plan-then-code step
- `visual.supportUrl` — placeholder URL is fine; real value required only at AppSource publish

## Plan-then-code (fresh scaffold only)

Before editing `src/visual.ts`, lock in two things:

1. **Data roles + capabilities** — what fields does the user drop into the visual? Edit `capabilities.json`.
2. **Render approach** — D3, Canvas, plain DOM, or SVG? Pick one and don't switch mid-iteration.

Skip the planning step on subsequent edits — go straight to the inner loop.

## Inner loop (iterate)

Every change cycle:

```bash
npx tsc --noEmit                # fast type check; fix errors before packaging
pbiviz package                  # produces dist/<name>.pbiviz
pbi-agent visual import-custom dist/<name>.pbiviz --replace
```

Then reload the `.pbip` in Power BI Desktop to see the result.

**Caps:** if 5 turns pass with no progress on `tsc --noEmit` errors, stop and ask the user. Detect oscillation (same error reappearing after a "fix") and break out.

**Cache invalidation:** Power BI Desktop caches custom visuals by GUID + version. The `--replace` flag rewrites the registration, but Desktop sometimes still serves the cached bundle. Bump the patch version in `pbiviz.json` between iterations to force a reload — `pbiviz_bump_patch()` in `powerbi_agent.visual` does this if you need to script it. Skip the bump if the user has set a non-semver version (treat as user-managed).

## npm allowlist

Only install packages from this short list without explicit user approval:

- `d3`, `d3-*` (visualization primitives)
- `lodash` (utility)
- `date-fns` (date formatting)
- `powerbi-visuals-utils-*` (official Microsoft visual utilities)

For anything else: surface **package name + version + reason + bundle-size estimate** and wait for explicit approval. Custom visuals ship every dependency to the browser; bundle bloat is a real cost.

## Embedding into the report

```bash
pbi-agent visual import-custom dist/mygaugevisual.pbiviz
pbi-agent visual list-custom
```

Embedded entries land in:

- `<.Report>/StaticResources/RegisteredResources/<name>.<guid>.pbiviz`
- `<.Report>/definition/report.json` → `customVisuals` + `resourcePackages`

To swap an iteration in place, pass `--replace`. To uninstall, `pbi-agent visual remove-custom <guid-or-name>`.

## Publishing to AppSource

Out of scope for this skill. The `pbiviz package` output is what you submit to the AppSource publish flow, but the registration step lives outside this CLI.

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `tsc --noEmit` clean but `pbiviz package` fails | metadata missing in `pbiviz.json` (see above) |
| Visual loads but renders nothing | check the browser console in Desktop's report view; usually a `capabilities.json` data-role mismatch |
| Visual won't update after re-import | Desktop cache — bump patch version, close + reopen `.pbip` |
| `import-custom` errors `not a valid zip archive` | `pbiviz package` step didn't succeed; rebuild |
| `import-custom` errors `already registered` | pass `--replace`, or `remove-custom` first |
