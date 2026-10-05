---
name: powerbi-pbi-cli
description: The pbi CLI (pbi-cli) for driving Power BI Desktop and PBIR reports from the terminal — visual bind with Column vs Measure resolution from the semantic model, implicit aggregation wrappers, --kind and --aggregation overrides, batching with --no-sync, and what pbi report reload actually does (closes and reopens Desktop, not a keyboard shortcut). Use when the user mentions: pbi CLI, pbi-cli, pbi visual bind, pbi visual bulk-bind, pbi report reload, pbi measure create, pbi connect, sync_desktop, --no-sync, broken slicer after bind, measure reference will not resolve, pbi-cli skills install, import-custom pbiviz.
license: MIT
---

# The `pbi` CLI

`pbi-cli` (Mina Saad, MIT) drives Power BI Desktop and PBIR report folders from the terminal:
semantic model edits over the local Analysis Services instance, and report-layer edits written
straight into PBIR JSON. It overlaps `pbi-agent` deliberately — use whichever is installed, and
know the differences below, because the failure modes are not the same.

**Target version: ≥ 3.12.0.** Earlier versions wrap every bound field as a `Measure`, which
silently produces broken slicers and tables. Check with `pbi --version` — and note that
`--version` itself only became trustworthy in 3.12.0, where it reads from package metadata
instead of a hardcoded constant that had drifted.

## Two entry points, and it matters

| Entry point | Owns |
|---|---|
| `pbi` | all model and report work — `connect`, `model`, `measure`, `report`, `visual`, `filters`, `bookmarks`, `format`, `database` |
| `pbi-cli` | **only** skill management: `pbi-cli skills install` / `list` / `uninstall` |

`pbi skills install` does not exist. Claude Code integration is opt-in by design: `pbi connect`
does not write to `~/.claude/`.

```bash
pipx install pbi-cli
pbi-cli skills install        # opt in to the skill pack
pbi connect                   # attach to the open Desktop instance
```

## `pbi visual bind` — the part that costs people a day

Binding a field writes a field reference into `visual.json`. Whether it is written as a
`Column` or a `Measure`, and whether it is wrapped in an aggregation, decides whether the
visual renders at all.

### How the kind is resolved (3.12.0+)

In order:

1. The TMDL or `model.bim` that the report's `definition.pbir` points at — on disk, no
   connection needed.
2. The live model via `pbi connect`, opened only for fields missing on disk.
3. A per-visual role default; **slicers default to `Column`**.

Names are canonicalised to the model's casing, and a measure referenced under the wrong table
is rewritten against its home table. A field found in neither place produces a `warnings`
entry rather than a silent guess — **read the warnings**. A warning here means the visual will
render empty, and reading it now is cheaper than opening Desktop to find out.

`bind` output carries `kind` and `resolved_by` per field. Check them. `resolved_by` telling
you a field came from a role default when you expected the model usually means the
`definition.pbir` path is wrong.

### Implicit aggregation

A column bound to a *value* role — chart Y, matrix values, card, table — must be wrapped in
the aggregation Desktop would apply, not written as a bare `Column`. 3.12.0 does this:

- The function comes from the column's `summarizeBy` in the model, falling back to `Sum` for
  numeric columns.
- On charts and matrices, a non-summarizable column (text, or `summarizeBy: none`) is wrapped
  as a **count**, matching Desktop.
- Tables and cards keep it as a plain column.
- Category, row, legend and slicer fields are **never** aggregated.

Overrides, when the model's `summarizeBy` is not what this visual needs:

```bash
pbi visual bind … --kind auto|column|measure
pbi visual bind … --aggregation sum|average|count|distinct-count|min|max|median|stdev|variance|none
```

Function codes follow Microsoft's PBIR semanticQuery schema. Reach for `--kind` only when
resolution is demonstrably wrong — forcing it is how the pre-3.12 breakage happened in the
first place.

Role flags on `bind`, matching `bulk-bind`: `--column`, `--line`, `--x`, `--y`. `--column`
binds table columns and matrix column groups.

### Preconditions

**A measure must exist in the TMDL before you bind it.** `visual bind` writes a reference; it
does not create the measure. Create it first:

```bash
pbi measure create "Total Revenue" -e "SUM(Sales[Amount])" -t Sales
```

Name positional, `-e/--expression`, `-t/--table`. The three-positional form
(`pbi measure create Sales "Total Revenue" "SUM(...)"`) is rejected by Click — it appears in
older skill docs and is wrong.

### Symptom table

| Symptom | Cause |
|---|---|
| Slicer renders broken or empty | field written as `Measure` — pre-3.12 bind, or a forced `--kind measure` |
| Column in a table shows one aggregated row | aggregation applied where a plain column was wanted — `--aggregation none` or `--kind column` |
| Chart Y axis blank | bare `Column` where Desktop expects an aggregate — let 3.12 resolve it, don't force `column` |
| Field silently absent | a `warnings` entry you did not read; the field is not in the model |
| `.pbip` will not open in Desktop | schema violation, not a bind problem — see below |

## `pbi report reload` is not a keyboard shortcut

It calls `sync_desktop()`: **saves and closes the open `.pbip`, re-applies the PBIR edits that
Desktop's save would have overwritten, then reopens the file.** It does not send
`Ctrl+Shift+F5`. Older skill text claimed it did, and people went looking in Microsoft's
shortcut docs for a key that was never pressed.

The consequence is bigger than the naming: **every write command auto-syncs by default**, so
`pbi visual update` closes and reopens Desktop. In a multi-step build that means one
close/reopen cycle per command.

```bash
# Batch: suppress per-command sync, then sync once at the end
pbi report   … --no-sync
pbi visual   … --no-sync
pbi filters  … --no-sync
pbi bookmarks … --no-sync
pbi report reload
```

`--no-sync` exists on the `report`, `visual`, `filters` and `bookmarks` groups. Use it for
anything beyond a single edit.

Desktop discovery notes that matter when reload appears to do nothing:

- Process discovery uses PowerShell `Get-CimInstance Win32_Process`, not `wmic` — `wmic` was
  removed from Windows 11 24H2 and later, where older versions reported "Power BI Desktop is
  not running" while it plainly was. If you see that message on current Windows, check the
  version before anything else.
- Discovery matches the project name exactly, not a substring of ancestor directory names.
  The loose match in earlier versions could force-close, save and reopen **a different
  person's session**. Do not downgrade past this.
- The save prompt after close is polled, not checked once, and the deadline accommodates a
  large model write. A reload that looks hung on a big model is probably saving.

## PBIP schema rules — the "won't open in Desktop" set

Desktop refuses a project on schema violations, usually with an unhelpful message:

- `definition.pbir` must point at a real model path, and the `.pbip` artifact entry must match.
- Theme JSON carries properties that crash Desktop on open; validate a theme before shipping it
  (`powerbi-modifying-theme-json`).
- Measures referenced by a visual must exist in the TMDL.
- PBIR 2.7.0 sets `additionalProperties: false` on the query object: the legacy `Commands`
  block (`SemanticQueryDataShapeCommand`) is a hard schema violation. Only `queryState`
  projections are valid. 3.10.6+ no longer writes it; a hand-edited or migrated
  `visual.json` still might.
- A missing `layoutOptimization` is **not** an error — the real Microsoft schema does not
  require it. Validators that flag it are checking a stale schema.
- `report set-background` must write `transparency` alongside the colour. Desktop defaults a
  missing `transparency` to 100 — fully invisible — so the colour silently does not render.

## Other commands worth knowing

```bash
pbi visual import-custom dist/my.pbiviz [--replace]   # embed a built .pbiviz; --replace by GUID
pbi visual list-custom                                # embedded vs public, with a kind column
pbi visual remove-custom <guid-or-name>               # deregister and delete
pbi database diff-tmdl <folderA> <folderB>            # offline TMDL diff; lineageTag-only noise stripped
pbi report validate                                   # PBIR validation
```

`pbi-agent` has equivalents for the custom-visual trio (`pbi-agent visual import-custom`,
`list-custom`, `remove-custom`) — the PBIR embedding logic there was ported from pbi-cli under
MIT and is credited in `ATTRIBUTIONS.md`. Use one tool per report; mixing them mid-build makes
a failure hard to attribute.

## Guardrails

- **Check `pbi --version` ≥ 3.12.0 before any `bind` work.** The pre-3.12 bind failure is
  silent at write time and only visible when a human opens the report.
- **Read the `warnings` array.** Every time.
- Close/reopen of Desktop touches the user's open session and unsaved state. Say what you are
  about to sync before the first write of a session.
- Use `--no-sync` for multi-step builds, then one explicit `pbi report reload`.
- Model edits over a live Desktop connection are not transactional. For anything structural,
  work in TMDL under source control (`powerbi-tmdl`) and deploy, rather than mutating a live
  model.

## Related skills

| Need | Skill |
|---|---|
| PBIR JSON structure | `powerbi-pbir-format-enhanced`, `powerbi-pbip-format` |
| pbir.tools instead of `pbi` | `powerbi-report-structure`, `powerbi-pbir-cli` |
| Authoring a custom visual to import | `powerbi-custom-visuals` |
| Theme JSON that opens in Desktop | `powerbi-modifying-theme-json` |
| TMDL the binds resolve against | `powerbi-tmdl`, `powerbi-model` |
| Measures to bind | `powerbi-dax-mastery` |
