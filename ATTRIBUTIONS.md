# Attributions & Credits

**powerbi-agent** is an original work by **Santosh Kanthety**.

This project was inspired by the broader Power BI open-source community. We gratefully acknowledge:

---

## Inspirations

### pbi-cli — Mina Saad
- Repository: https://github.com/MinaSaad1/pbi-cli
- License: MIT (compatible with this project's MIT license)
- Inspired the direct .NET TOM/ADOMD interop pattern for connecting to Power BI Desktop's local Analysis Services instance.
- The connection architecture in `connect.py` and `dax.py` is original work, written independently using the same underlying Windows APIs.
- The following hardening behaviours were patterned after pbi-cli (no code copied; equivalent logic written from scratch). Each module carries an attribution comment in its docstring:
  - Microsoft Store install path detection in addition to MSI — `connect._workspace_roots`
  - UTF-16 LE → UTF-8 fallback when reading `msmdsrv.port.txt` — `connect._read_port_file`
  - Most-recent-instance ordering when multiple Power BI Desktop sessions are open
  - Click-integrated error hierarchy — `powerbi_agent.errors`
- The `powerbi-pbi-cli` skill documents pbi-cli's own CLI surface and the behaviours its
  maintainers established through real-world testing — `visual bind` Column-vs-Measure
  resolution from the semantic model, the implicit-aggregation wrapper derived from
  `summarizeBy`, `--kind` / `--aggregation`, the `sync_desktop` close-and-reopen semantics
  behind `report reload`, `--no-sync` batching, and the PBIR schema constraints that stop a
  `.pbip` from opening. This is documentation *of* a separate MIT tool for Claude's benefit,
  written from its public CHANGELOG, release notes and `--help` output; no pbi-cli source is
  vendored here. Credit for the underlying findings belongs to Mina Saad and the pbi-cli
  contributors (including @BMATPowerBI for the `wmic` → `Get-CimInstance` fix and @Priya-BI
  for the PBIP schema warnings).
- The PBIR custom-visual embedding logic in `powerbi_agent.visual` (resource-package layout, `customVisuals` registration, GUID-based filename pattern, patch-bump cache invalidation) was ported from pbi-cli's `core/custom_visual_backend.py` (PR #4, MIT). The CLI surface and skill content are adapted to powerbi-agent. The module docstring carries the attribution.

### power-bi-agentic-development — Kurt Buhler (data-goblin)
- Repository: https://github.com/data-goblin/power-bi-agentic-development
- License: **GPL-3.0**
- Inspired the concept of Claude Code skill files as domain-specific knowledge modules for Power BI agentic development.
- **Important:** No code, skill file content, or documentation text was copied or derived from this GPL-3.0 licensed project. All skill files in the `skills/` directory — including `te-docs.md` (added v0.2.0 after data-goblin v0.26.1 introduced a same-named skill upstream) — are original works by Santosh Kanthety, written from scratch based on independent expertise and the public Tabular Editor / Microsoft Analysis Services documentation. This project's MIT license applies only to its own original content.
- **Capability-area credit, v0.7.** The upstream v26.28 → v26.40.3 line is where several
  capability areas first appeared in an agentic Power BI toolkit: Fabric Apps on the Rayfin
  CLI (`fabric-data-app` plugin), a `databricks-cli` plugin and Databricks pane, a Fabric
  capacity skill reading Capacity Metrics, Spark/Livy execution, DuckDB over lakehouse data,
  paginated reports, the cross-platform Tabular Editor CLI, workspace task flows, and Claude
  Code pane mods (`/fabric-pane`, `/databricks-pane`, `/report-pane`, `/data-app-pane`).
  `powerbi-agent` v0.7 adds skills covering several of the same areas. **Those skills were
  written from scratch against Microsoft Learn, the Rayfin and awesome-rayfin repositories,
  the Tabular Editor documentation, and independent delivery experience — not from upstream
  skill text.** Capability overlap in a shared problem domain is not derivation; the credit
  here is for pointing at the areas first, which is worth stating plainly.
- One upstream capability was deliberately **not** reproduced: workspace task flows. The
  Fabric task-flow API is not publicly documented, and shipping a skill asserting undocumented
  endpoints would be guesswork.
- If you fork this project and wish to incorporate any content from `power-bi-agentic-development`, you must comply with its GPL-3.0 terms.

### Rayfin / Fabric Apps — Microsoft
- Repositories: https://github.com/microsoft/rayfin · https://github.com/microsoft/awesome-rayfin
- License: **MIT** (packages are published on npm under `@microsoft/rayfin-*`)
- `pbi-agent fabric-app` is a thin wrapper: every operation shells out to the installed
  Rayfin CLI (`npx -y -p @microsoft/rayfin-cli rayfin …`) or `@microsoft/create-rayfin`.
  **No part of the Rayfin SDK or CLI is reimplemented, vendored, or re-exported.** What this
  project adds is environment verification, project and deployment-state detection, a
  confirmation gate on destructive schema deploys, and the skills that teach Claude when and
  how to use the CLI.
- The `powerbi-fabric-apps` and `powerbi-fabric-app-templates` skills are original work by
  Santosh Kanthety, written from Microsoft Learn's public Fabric Apps documentation
  ([overview](https://learn.microsoft.com/fabric/apps/overview),
  [CLI reference](https://learn.microsoft.com/fabric/apps/cli-reference),
  [data app template](https://learn.microsoft.com/fabric/apps/data-apps-template)) and the
  two public repositories above.
- Both skills defer by design to the **version-locked in-project skill** Rayfin installs at
  `.agents/skills/rayfin/SKILL.md`, and to the `rayfin docs` CLI. That deference is
  deliberate: Rayfin is in preview, its API surface moves, and Microsoft's own guidance is
  that agents must not write Rayfin code from memory.
- Templates in `awesome-rayfin` are community contributions, not Microsoft-supported product
  surface. The templates skill says so, and says to review what a template does with your
  data before building on it.

### Tabular Editor — Kapacity / Daniel Otykier
- Site: https://tabulareditor.com · Docs: https://docs.tabulareditor.com
- Tabular Editor 2 is MIT-licensed; Tabular Editor 3 and the cross-platform `te` CLI are
  commercial products (the `te` CLI is in Limited Public Preview at the time of writing).
- `powerbi-te2-cli`, `powerbi-te-cli` and `powerbi-te-docs` are original skill files
  describing how to drive these tools. No Tabular Editor code or documentation text is
  vendored. The `te` CLI's preview expiry is documented in the skill because a pipeline built
  on it will stop working, and users deserve to know that before they depend on it.

---

## Key Dependencies

| Package | License | Purpose |
|---|---|---|
| [Click](https://github.com/pallets/click) | BSD-3-Clause | CLI framework |
| [Rich](https://github.com/Textualize/rich) | MIT | Terminal output formatting |
| [httpx](https://github.com/encode/httpx) | BSD-3-Clause | HTTP client for Fabric REST API |
| [Pydantic](https://github.com/pydantic/pydantic) | MIT | Data validation |
| [pythonnet](https://github.com/pythonnet/pythonnet) | MIT | .NET interop for TOM/ADOMD |
| [azure-identity](https://github.com/Azure/azure-sdk-for-python) | MIT | Azure authentication for Fabric |

---

## Microsoft Technologies

This tool automates and extends:
- **Microsoft Power BI** — https://powerbi.microsoft.com
- **Microsoft Fabric** — https://www.microsoft.com/fabric
- **Analysis Services (SSAS)** — local engine embedded in Power BI Desktop
- **Tabular Object Model (TOM)** — .NET API for semantic model management
- **ADOMD.NET** — .NET client for DAX query execution
- **Microsoft Fabric Apps / Rayfin SDK** — https://learn.microsoft.com/fabric/apps/overview
- **Fabric Capacity Metrics app** — read over XMLA by the `powerbi-fabric-capacity` skill
- **Fabric Livy API** — ephemeral Spark execution, used by `powerbi-spark-livy`
- **Power BI Report Builder / RDL** — paginated report authoring

All Microsoft product names are trademarks of Microsoft Corporation.
This project is not affiliated with, endorsed by, or sponsored by Microsoft.

---

## Community

Built with gratitude for the Power BI community, SQLBI, the Power BI Guy, Guy in a Cube, and every practitioner who has shared knowledge publicly over the years.
