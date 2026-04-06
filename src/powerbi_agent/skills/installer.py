"""
Install / uninstall powerbi-agent skills into Claude Code.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()

CLAUDE_HOME = Path.home() / ".claude"
SKILLS_DIR = CLAUDE_HOME / "skills"
CLAUDE_MD = CLAUDE_HOME / "CLAUDE.md"

SKILL_NAMES = [
    "power-bi-connect",
    "data-catalog-lineage",
    "data-transformation",
    "dax-mastery",
    "fabric-pipelines",
    "measure-glossary",
    "medallion-architecture",
    "performance-scale",
    "project-management",
    "report-authoring",
    "security-rls",
    "source-integration",
    "star-schema-modeling",
    "testing-validation",
    "time-series-data",
    "data-governance-traceability",
    "cyber-security",
]

CLAUDE_MD_BLOCK = """
<!-- powerbi-agent:start -->
## powerbi-agent Skills

You have access to the following Power BI skills. Trigger them based on context:

- **power-bi-connect**: Use when the user wants to connect to Power BI Desktop
- **power-bi-dax**: Use when the user wants to run, validate, or explain DAX
- **power-bi-model**: Use when the user wants to inspect or modify the data model
- **power-bi-report**: Use when the user wants to work with report pages or visuals
- **power-bi-fabric**: Use when the user mentions Fabric, Power BI Service, workspace, or refresh
- **power-bi-doctor**: Use when the user reports connection problems or setup issues

Always prefer pbi-agent CLI commands over explaining how to do things manually.
<!-- powerbi-agent:end -->
"""


def install_skills(force: bool = False) -> None:
    """Copy skill files to ~/.claude/skills/ and update CLAUDE.md."""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    skill_files_dir = Path(__file__).parent.parent.parent.parent / "skills"

    installed = 0
    skipped = 0

    for skill_name in SKILL_NAMES:
        src = skill_files_dir / f"{skill_name}.md"
        dst = SKILLS_DIR / f"{skill_name}.md"

        if not src.exists():
            console.print(f"[yellow]⚠[/yellow] Skill file not found: {src.name}")
            continue

        if dst.exists() and not force:
            console.print(f"[dim]  {skill_name}: already installed (use --force to overwrite)[/dim]")
            skipped += 1
            continue

        shutil.copy2(src, dst)
        console.print(f"[green]✓[/green]  {skill_name}: installed")
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
            console.print(f"[red]✗[/red]  {skill_name}: removed")
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
        "power-bi-connect": "Connect to Power BI Desktop instances",
        "power-bi-dax": "Run and validate DAX queries",
        "power-bi-model": "Inspect and modify semantic model",
        "power-bi-report": "Work with report pages and visuals",
        "power-bi-fabric": "Power BI Service / Fabric operations",
        "power-bi-doctor": "Diagnose environment issues",
    }

    for skill_name in SKILL_NAMES:
        installed = (SKILLS_DIR / f"{skill_name}.md").exists()
        tbl.add_row(
            skill_name,
            "[green]✓ installed[/green]" if installed else "[dim]not installed[/dim]",
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
        console.print("[green]✓[/green]  CLAUDE.md updated")


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
    console.print("[green]✓[/green]  CLAUDE.md cleaned up")
