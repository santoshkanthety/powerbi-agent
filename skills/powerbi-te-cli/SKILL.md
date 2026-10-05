---
name: powerbi-te-cli
description: The cross-platform Tabular Editor CLI (`te`) — a single self-contained binary for Windows, macOS and Linux that inspects, edits, validates, deploys, refreshes and tests Power BI and Analysis Services semantic models, with structured JSON/CSV/TMDL output and safe-by-default preview diffs. Distinct from Tabular Editor 2's TabularEditor.exe. Use when the user mentions: te CLI, Tabular Editor CLI, te auth login, te bpa run, te deploy, te refresh, te test run, te vertipaq, te diff, te script, cross-platform Tabular Editor, Tabular Editor on Mac or Linux, model CI on Linux, headless semantic model edit.
license: MIT
---

# Tabular Editor CLI (`te`)

`te` is a single self-contained binary that runs on Windows, macOS and Linux, built on the
same engine as Tabular Editor 3. It is the first way to do real semantic-model work — BPA,
deploy, refresh, VertiPaq analysis, assertion tests — from a Linux CI runner without a
Windows agent and without .NET Framework.

**Three different products, do not confuse them:**

| Tool | Executable | Platform | This skill |
|---|---|---|---|
| Tabular Editor 2 | `TabularEditor.exe` | Windows only, free | no — `powerbi-te2-cli` |
| Tabular Editor 3 | `TabularEditor3.exe` | Windows GUI, licensed | no — see `powerbi-te-docs` |
| **Tabular Editor CLI** | `te` | Windows / macOS / Linux | **yes** |

Flags and scripts are not portable between them. A TE2 invocation (`-A`, `-D`, `-S`, `-B`)
will not work here; `te` uses verb-based subcommands.

## Status — check this first

`te` is in **Limited Public Preview**. During the preview no licence is required, only a
Tabular Editor account — but **the preview build stops working after 2026-10-31**, and
licensing will be required at general availability.

Consequences to state before anyone builds on it:

- A pipeline that depends on `te` will break at the preview cutoff unless the binary is
  refreshed. Do not put it on the critical path of a release train without a fallback.
- The fallback is `powerbi-te2-cli` (free, Windows, stable) or an XMLA/TOM path via
  `pbi-agent model`.
- Pin the downloaded version and record it, so a CI failure is diagnosable as a version
  change rather than a model change.

## Setup

1. Register or sign in at [tabulareditor.com](https://tabulareditor.com), then download the
   binary for the platform.
2. `te auth login` — interactive device-code sign-in to Power BI / Fabric.
3. `te --help` and `te <command> --help` — **do this before first use of any command.**

The surface is moving during preview. Read the installed binary's help rather than trusting
any written reference, including this one. Where help and this file disagree, help wins.

```bash
te --version                 # record this in the pipeline log
te auth login
te --help
```

Connection state: `te profile` manages named connection profiles, `te session` manages
session state, `te config` sets CLI defaults. Set a profile once per environment rather than
repeating connection strings — and keep profile secrets out of the repo.

## Command families

Verified family names and representative commands; confirm exact arguments with `--help`.

| Family | Commands | Use for |
|---|---|---|
| Init / save | `te init`, `te save-as` | create, convert between `.bim` / TMDL / PBIP |
| Edit | `te set`, `te add`, `te remove`, `te move` | property and object changes without a GUI |
| Inspect | `te list`, `te find`, `te diff`, `te deps` | enumerate objects, locate usage, compare, trace dependencies |
| Analysis & quality | `te validate`, `te bpa run`, `te util`, `te vertipaq` | validation, Best Practice Analyzer, VertiPaq analysis |
| Execution | `te query`, `te script`, `te macro` | DAX queries, C# scripts, saved macros |
| Deploy & refresh | `te deploy`, `te refresh` | push a model, trigger a refresh |
| Testing | `te test run` | assertion tests against a model |
| Shell | `te interactive`, `te completion` | REPL, shell completions |

## Design properties that matter in practice

- **Structured output** — JSON, CSV and TMDL. Parse JSON; never scrape the human-readable
  table. Pass the output format flag explicitly in scripts rather than relying on a default.
- **Non-interactive mode** — a global flag suppresses prompts. Set it in every CI invocation.
  A command that blocks on a prompt in a pipeline hangs until the job times out.
- **Safe by default** — edits preview a diff before applying. In CI you will be disabling
  that confirmation; that makes reviewing the diff locally first a requirement, not a nicety.
- **Clear errors and exit codes** — errors go to stderr with predictable exit codes. Check the
  exit code. Do not infer success from empty stderr or from the absence of the word "error".

## Workflows

### BPA in CI, on Linux

```bash
te auth login                              # or a profile with CI credentials
te bpa run <model-or-connection> --help    # confirm flags for this build
# then: run BPA, emit JSON, fail the job on any error-severity finding
```

Rules for the gate: fail only on the severities the team agreed to fail on, emit the full
finding list as a build artifact, and keep the rule file in the repo under version control so
a new finding is traceable to a rule change. Rule authoring lives in `powerbi-bpa-rules`.

### Review a change before it reaches the model

```bash
te diff <source> <target>     # what this deploy would actually change
te deps <object>              # what breaks if this object changes
te validate <model>
```

`te diff` before `te deploy` is the habit to build. It converts "deploy and hope" into a
reviewable change set, and it catches the two failures that hurt most: an unintended
property reset, and a rename that orphans a report visual.

### Deploy

```bash
te diff <src> <target>        # 1. always
te deploy <src> <target> --help
```

Before deploying to a shared or production model:

- Show the user the diff summary — objects added, removed, changed — and get an explicit yes.
- **Never deploy over a model whose diff includes removals you cannot explain.** A removal in
  a deploy diff is usually a stale source, not an intended deletion.
- Deploy to a dev workspace first where one exists. Partial deployment options (what gets
  overwritten vs preserved: roles, partitions, data sources) differ by command — read `--help`
  and state which you are using.

### Refresh and test

```bash
te refresh <model> --help     # confirm scope: full, table, partition
te test run <suite>
```

A refresh draws capacity. On a shared or production capacity, state the expected CU cost
first — `powerbi-fabric-capacity`. Refresh strategy itself (incremental, partitions, policy)
is `powerbi-refresh-semantic-model`.

### VertiPaq analysis

```bash
te vertipaq <model> --help
```

This is the measurement that makes `powerbi-performance-scale` and `powerbi-dax-performance`
actionable: column cardinality, dictionary and hierarchy sizes, compression, and which
columns are actually costing memory. Capture it before and after an optimisation and report
both numbers.

## Guardrails

- **Discovery before invocation.** `te <command> --help` on first use in a session. The
  preview surface changes between builds.
- **Never run an edit, deploy or refresh against a production model without naming the model
  and the change and getting a yes.** `te` is headless; there is no GUI prompt to catch a
  mistake.
- **No credentials on the command line.** Use `te auth login` or a profile; command-line
  arguments are visible to other processes on the host.
- **Record the binary version** in any pipeline that uses it, given the preview cutoff.
- If a command fails on permissions, report the missing right. Do not retry through a
  different tool to get around it.

## Related skills

| Need | Skill |
|---|---|
| Windows-only, free, stable CLI | `powerbi-te2-cli` |
| Tabular Editor documentation lookup, scripting cookbook | `powerbi-te-docs` |
| C# scripts the CLI executes | `powerbi-c-sharp-scripting` |
| BPA rule authoring | `powerbi-bpa-rules` |
| What to do with VertiPaq findings | `powerbi-performance-scale`, `powerbi-dax-performance` |
| Refresh design | `powerbi-refresh-semantic-model` |
| CU cost of a refresh or deploy | `powerbi-fabric-capacity` |
| TMDL the CLI reads and writes | `powerbi-tmdl` |
