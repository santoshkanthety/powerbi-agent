"""
Install / uninstall powerbi-agent skills into Claude Code.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console
from rich.table import Table

# force_terminal=False + legacy_windows=False avoids the cp1252 crash when Rich
# tries to render Unicode glyphs (e.g. U+26A0) to a Windows console that is
# configured with a non-UTF-8 code page. Rich's default Windows renderer
# attempts direct console writes that bypass PYTHONIOENCODING and fall back
# to the active code page — which on Windows 10/11 is still cp1252 by default.
console = Console(legacy_windows=False, safe_box=True)

CLAUDE_HOME = Path.home() / ".claude"
SKILLS_DIR = CLAUDE_HOME / "skills"
CLAUDE_MD = CLAUDE_HOME / "CLAUDE.md"

# Skills source resolution — works for both `pip install` and `git clone` dev setups:
#   Installed (pip):  skills live at powerbi_agent/skills/data/  (bundled via force-include)
#   Development:      skills live at project_root/skills/  (4 levels above this file)
_PKG_DATA_DIR = Path(__file__).parent / "data"
_REPO_SKILLS_DIR = Path(__file__).parent.parent.parent.parent / "skills"

SKILL_NAMES = [
    # pbi-agent CLI skills (thin wrappers around this package's commands)
    "power-bi-connect",
    "power-bi-dax",
    "power-bi-model",
    "power-bi-report",
    "power-bi-fabric",
    "power-bi-doctor",
    # Core connectivity
    "connect-pbid",
    "fabric-cli",
    # Semantic model authoring
    "dax-mastery",
    "dax-performance",
    "tmdl",
    "power-query",
    "review-semantic-model",
    "standardize-naming-conventions",
    "refresh-semantic-model",
    "lineage-analysis",
    "bpa-rules",
    "c-sharp-scripting",
    "te2-cli",
    "audit-tenant-settings",
    # Report authoring
    "report-authoring",
    "pbi-report-design",
    "create-pbi-report",
    "review-report",
    "report-structure",
    "report-theming",
    "report-conversion",
    "modifying-theme-json",
    # Visuals
    "deneb-visuals",
    "python-visuals",
    "r-visuals",
    "svg-visuals",
    # PBIP / PBIR format
    "pbip-format",
    "pbir-format-enhanced",
    "pbir-cli",
    # Fabric / data platform
    "fabric-pipelines",
    "medallion-architecture",
    "data-transformation",
    "data-catalog-lineage",
    "source-integration",
    # Modeling & design
    "star-schema-modeling",
    "measure-glossary",
    "performance-scale",
    "security-rls",
    "time-series-data",
    # Governance & process
    "data-governance-traceability",
    "testing-validation",
    "project-management",
    "cyber-security",
]

CLAUDE_MD_BLOCK = """
<!-- powerbi-agent:start -->
## powerbi-agent Skills

You have access to the following Power BI / Fabric skills. Load and apply them automatically based on context:

### pbi-agent CLI
- **power-bi-connect**: Connect to a running Power BI Desktop instance via pbi-agent
- **power-bi-dax**: Run and validate DAX queries against the connected model
- **power-bi-model**: Inspect and modify tables, measures, relationships via pbi-agent
- **power-bi-report**: Inspect PBIR report structure; list pages; scaffold new pages
- **power-bi-fabric**: Fabric / Power BI Service auth, workspaces, datasets, refresh
- **power-bi-doctor**: Diagnose pbi-agent environment, connection, and auth issues

### Connectivity
- **connect-pbid**: Connect via TOM/ADOMD.NET in PowerShell; query and modify live models
- **fabric-cli**: fab CLI, nb CLI, DuckDB — workspace navigation, notebook management, deployment, refresh, APIs

### Semantic Model Authoring
- **dax-mastery**: DAX measures, calculated columns, time intelligence, evaluation context
- **dax-performance**: DAX optimization, query plans, server timings, anti-patterns
- **tmdl**: TMDL file authoring for PBIP projects; measures, columns, roles, relationships
- **power-query**: Power Query M expressions, query folding, partitions
- **review-semantic-model**: Audit and validate semantic models against best practices
- **standardize-naming-conventions**: Interactive naming convention standardization
- **refresh-semantic-model**: Trigger, monitor, and validate semantic model refreshes
- **audit-tenant-settings**: Audit Fabric/Power BI tenant settings for governance
- **lineage-analysis**: Trace model-to-report lineage across Fabric workspaces
- **bpa-rules**: Tabular Editor Best Practice Analyzer rules — authoring and execution
- **c-sharp-scripting**: C# scripting in Tabular Editor for bulk model operations
- **te2-cli**: Tabular Editor 2 CLI for TMDL deployment, BPA, scripting

### Report Authoring
- **report-authoring**: General Power BI report authoring patterns
- **pbi-report-design**: Report design principles, UX, accessibility, layout best practices
- **create-pbi-report**: Step-by-step new report creation workflow
- **review-report**: Audit reports against design and best practice standards
- **report-structure**: PBIR report structure, pages, visuals
- **report-theming**: Power BI theme JSON authoring
- **report-conversion**: PBIX → PBIR / PBIP conversion
- **modifying-theme-json**: Edit and extend theme JSON for custom branding

### Custom Visuals
- **deneb-visuals**: Deneb / Vega / Vega-Lite custom visuals in Power BI
- **python-visuals**: Python visuals (matplotlib, seaborn, plotly)
- **r-visuals**: R visuals (ggplot2, plotly)
- **svg-visuals**: SVG-based custom visuals

### PBIP / PBIR Format
- **pbip-format**: PBIP project structure, file types, connection, Git workflows
- **pbir-format-enhanced**: PBIR JSON schemas, visual.json, report.json editing
- **pbir-cli**: PBIR CLI operations and scripting

### Fabric / Data Platform
- **fabric-pipelines**: Fabric Data Factory pipelines, orchestration
- **medallion-architecture**: Bronze/Silver/Gold lakehouse design
- **data-transformation**: ETL/ELT transformation patterns
- **data-catalog-lineage**: Data catalog and lineage management
- **source-integration**: Source system integration patterns

### Modeling & Design
- **star-schema-modeling**: Star schema design, dimensions, facts
- **measure-glossary**: Standard measure naming and documentation
- **performance-scale**: Performance optimization and scaling
- **security-rls**: Row-level security design and implementation
- **time-series-data**: Time series analysis patterns

### Governance & Process
- **data-governance-traceability**: Data governance and traceability
- **testing-validation**: Testing and validation frameworks
- **project-management**: Project management for BI projects
- **cyber-security**: Security considerations for Power BI

Always prefer pbi-agent CLI commands over explaining how to do things manually.
<!-- powerbi-agent:end -->
"""


def _get_skills_source_dir() -> Path:
    """Return the directory containing skill .md files.

    Prefers the bundled package-data path (works after ``pip install``).
    Falls back to the source-repo layout (works in ``git clone`` / editable installs).
    """
    if _PKG_DATA_DIR.exists():
        return _PKG_DATA_DIR
    if _REPO_SKILLS_DIR.exists():
        return _REPO_SKILLS_DIR
    raise FileNotFoundError(
        "Skills source directory not found.\n"
        "If you installed via pip, the package may be missing bundled data — "
        "try reinstalling: pip install --force-reinstall powerbi-agent\n"
        "If running from source, make sure the top-level skills/ directory exists."
    )


def install_skills(force: bool = False) -> None:
    """Copy skill files to ~/.claude/skills/ and update CLAUDE.md."""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    skill_files_dir = _get_skills_source_dir()

    installed = 0
    skipped = 0

    for skill_name in SKILL_NAMES:
        src = skill_files_dir / f"{skill_name}.md"
        dst = SKILLS_DIR / f"{skill_name}.md"

        if not src.exists():
            console.print(f"[yellow][!][/yellow] Skill file not found: {src.name}")
            continue

        if dst.exists() and not force:
            console.print(f"[dim]  {skill_name}: already installed (use --force to overwrite)[/dim]")
            skipped += 1
            continue

        shutil.copy2(src, dst)
        console.print(f"[green][+][/green]  {skill_name}: installed")
        installed += 1

    _update_claude_md()
    console.print(
        f"\n[bold]{installed}[/bold] skill(s) installed, {skipped} skipped.\n"
        "Claude Code will now use your Power BI skills automatically."
    )


def uninstall_skills() -> None:
    """Remove powerbi-agent skills from Claude Code."""
    removed = 0
    for skill_name in SKILL_NAMES:
        dst = SKILLS_DIR / f"{skill_name}.md"
        if dst.exists():
            dst.unlink()
            console.print(f"[red][-][/red]  {skill_name}: removed")
            removed += 1

    _remove_claude_md_block()
    console.print(f"\n{removed} skill(s) removed.")


def list_skills() -> None:
    """Show all available skills and their installation status."""
    tbl = Table(show_header=True, header_style="bold cyan")
    tbl.add_column("Skill")
    tbl.add_column("Status", justify="center")
    tbl.add_column("Description")

    descriptions = {
        "power-bi-connect": "Connect to Power BI Desktop via pbi-agent CLI",
        "power-bi-dax": "Run and validate DAX via pbi-agent",
        "power-bi-model": "Inspect/modify tables, measures, relationships via pbi-agent",
        "power-bi-report": "Inspect PBIR structure; list/add pages via pbi-agent",
        "power-bi-fabric": "Fabric/Service auth, workspaces, datasets, refresh via pbi-agent",
        "power-bi-doctor": "Diagnose pbi-agent environment, connection, and auth issues",
        "connect-pbid": "Connect via TOM/ADOMD.NET PowerShell; query/modify live models",
        "fabric-cli": "fab CLI, DuckDB — workspace, notebook, deployment, refresh",
        "dax-mastery": "DAX measures, time intelligence, evaluation context",
        "dax-performance": "DAX optimization, query plans, server timings",
        "tmdl": "TMDL file authoring for PBIP projects",
        "power-query": "Power Query M expressions and query folding",
        "review-semantic-model": "Audit semantic models against best practices",
        "standardize-naming-conventions": "Interactive naming convention standardization",
        "refresh-semantic-model": "Trigger, monitor, and validate model refreshes",
        "audit-tenant-settings": "Audit Fabric/Power BI tenant settings for governance",
        "lineage-analysis": "Trace model-to-report lineage across workspaces",
        "bpa-rules": "Tabular Editor Best Practice Analyzer rules",
        "c-sharp-scripting": "C# scripting in Tabular Editor for bulk operations",
        "te2-cli": "Tabular Editor 2 CLI for deployment and scripting",
        "report-authoring": "General report authoring patterns",
        "pbi-report-design": "Report design, UX, accessibility, layout",
        "create-pbi-report": "Step-by-step new report creation workflow",
        "review-report": "Audit reports against design best practices",
        "report-structure": "PBIR report structure, pages, visuals",
        "report-theming": "Power BI theme JSON authoring",
        "report-conversion": "PBIX → PBIR/PBIP conversion",
        "modifying-theme-json": "Edit and extend theme JSON for custom branding",
        "deneb-visuals": "Deneb/Vega/Vega-Lite custom visuals",
        "python-visuals": "Python visuals (matplotlib, seaborn, plotly)",
        "r-visuals": "R visuals (ggplot2, plotly)",
        "svg-visuals": "SVG-based custom visuals",
        "pbip-format": "PBIP project structure and Git workflows",
        "pbir-format-enhanced": "PBIR JSON schemas, visual.json, report.json",
        "pbir-cli": "PBIR CLI operations and scripting",
        "fabric-pipelines": "Fabric Data Factory pipelines and orchestration",
        "medallion-architecture": "Bronze/Silver/Gold lakehouse design",
        "data-transformation": "ETL/ELT transformation patterns",
        "data-catalog-lineage": "Data catalog and lineage management",
        "source-integration": "Source system integration patterns",
        "star-schema-modeling": "Star schema design, dimensions, facts",
        "measure-glossary": "Standard measure naming and documentation",
        "performance-scale": "Performance optimization and scaling",
        "security-rls": "Row-level security design and implementation",
        "time-series-data": "Time series analysis patterns",
        "data-governance-traceability": "Data governance and traceability",
        "testing-validation": "Testing and validation frameworks",
        "project-management": "Project management for BI projects",
        "cyber-security": "Security considerations for Power BI",
    }

    for skill_name in SKILL_NAMES:
        installed = (SKILLS_DIR / f"{skill_name}.md").exists()
        tbl.add_row(
            skill_name,
            "[green][+] installed[/green]" if installed else "[dim]not installed[/dim]",
            descriptions.get(skill_name, ""),
        )
    console.print(tbl)


def _update_claude_md() -> None:
    """Append powerbi-agent block to CLAUDE.md if not present."""
    CLAUDE_HOME.mkdir(parents=True, exist_ok=True)
    existing = CLAUDE_MD.read_text(encoding="utf-8") if CLAUDE_MD.exists() else ""
    if "<!-- powerbi-agent:start -->" not in existing:
        with CLAUDE_MD.open("a", encoding="utf-8") as f:
            f.write(CLAUDE_MD_BLOCK)
        console.print("[green][+][/green]  CLAUDE.md updated")


def _remove_claude_md_block() -> None:
    """Remove the powerbi-agent block from CLAUDE.md."""
    if not CLAUDE_MD.exists():
        return
    text = CLAUDE_MD.read_text(encoding="utf-8")
    import re
    cleaned = re.sub(
        r"<!-- powerbi-agent:start -->.*?<!-- powerbi-agent:end -->",
        "",
        text,
        flags=re.DOTALL,
    )
    CLAUDE_MD.write_text(cleaned.strip() + "\n", encoding="utf-8")
    console.print("[green][+][/green]  CLAUDE.md cleaned up")
