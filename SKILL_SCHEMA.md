# Shared skill schema

`powerbi-agent` and `databricks-agent` are two adapters over one delivery
doctrine. They therefore share one skill schema, one validator
(`scripts/validate_skills.py`, byte-identical in both repos) and one install
layout. This file is the contract — change it in both repos on the same day.

## Layout

```
skills/
└── <skill-name>/
    └── SKILL.md          # required entrypoint
```

Installed to `~/.claude/skills/<skill-name>/SKILL.md`.

This is the only layout Claude Code discovers. Flat `skills/<name>.md` files are
**not** loaded — they were the layout both packs shipped before this schema
landed, which meant the skills were never active.

## Frontmatter

```yaml
---
name: <skill-name>            # required; must equal the directory name
description: <what it does>. Use when the user mentions: <trigger phrases>.
license: MIT
---
```

Only [Agent Skills spec](https://agentskills.io) fields are permitted:
`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`.

Claude Code accepts many more fields (`when_to_use`, `argument-hint`, `model`,
`allowed-tools`, …), but claude.ai uploads and the Skills API hard-error on any
key outside the spec:

```
Unexpected key(s) in SKILL.md frontmatter: triggers. Allowed properties are:
allowed-tools, compatibility, description, license, metadata, name
```

Restricting to the six spec fields means one skill file works in Claude Code, in
claude.ai, and through the API without a per-target build step. That portability
is the point — it is the same argument as the doctrine itself.

### Why triggers live in `description`

Claude Code offers a `when_to_use` field, but it is a Claude Code extension and
not in the spec. Trigger phrases are therefore folded into `description` as a
trailing `Use when the user mentions: …` clause. Claude reads `description` to
decide when to auto-load a skill, so this loses nothing and stays portable.

Keep `description` under 1024 characters. Claude Code truncates the combined
description text at 1,536 characters in the skill listing, and every skill's
description is loaded into context on every session — the budget is shared.

## Naming

Skill directories are platform-prefixed: `powerbi-<concern>` and
`databricks-<concern>`.

The prefix is not decoration. Ten concerns exist in both packs under the same
name — `medallion-architecture`, `data-catalog-lineage`,
`data-governance-traceability`, `data-transformation`, `source-integration`,
`performance-scale`, `testing-validation`, `time-series-data`, `cyber-security`,
`project-management`. Without the prefix, installing both packs means one
silently overwrites the other in `~/.claude/skills/`.

Prefixing also makes the paired-dialect structure visible in the `/` menu:

| Doctrine layer | Power BI | Databricks |
|---|---|---|
| Metric semantics | `powerbi-measure-glossary` | `databricks-metric-glossary` |
| Access control | `powerbi-security-rls` | `databricks-security-governance` |
| Query language | `powerbi-dax-mastery` | `databricks-spark-sql-mastery` |
| Physical modeling | `powerbi-model` | `databricks-delta-modeling` |
| Orchestration | `powerbi-fabric-pipelines` | `databricks-dlt-pipelines` |
| Presentation | `powerbi-report-design` | `databricks-dashboard-authoring` |

## Body

Anything after the frontmatter is the skill's instructions. Keep `SKILL.md`
under 500 lines; move long reference material into sibling files in the skill
directory and point at them from `SKILL.md`.

## Validation

```bash
python scripts/validate_skills.py
```

Runs in CI in both repos. Checks layout, required keys, spec-only keys,
name/directory agreement, kebab-case names, and description length.
