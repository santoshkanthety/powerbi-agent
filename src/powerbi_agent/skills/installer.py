"""
Install / uninstall powerbi-agent skills into Claude Code.

Skills ship in the canonical Agent Skills layout — one directory per skill with
``SKILL.md`` as the entrypoint — and are installed to
``~/.claude/skills/<skill-name>/SKILL.md``, which is the only layout Claude Code
discovers. Skill metadata (name, description) is read from each ``SKILL.md``
frontmatter, so the files themselves are the single source of truth.
"""

from __future__ import annotations

import re
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
    "powerbi-connect",
    "powerbi-dax",
    "powerbi-model",
    "powerbi-report",
    "powerbi-fabric",
    "powerbi-doctor",
    # Core connectivity
    "powerbi-connect-pbid",
    "powerbi-fabric-cli",
    # Semantic model authoring
    "powerbi-dax-mastery",
    "powerbi-dax-performance",
    "powerbi-tmdl",
    "powerbi-power-query",
    "powerbi-review-semantic-model",
    "powerbi-standardize-naming-conventions",
    "powerbi-refresh-semantic-model",
    "powerbi-lineage-analysis",
    "powerbi-bpa-rules",
    "powerbi-c-sharp-scripting",
    "powerbi-te2-cli",
    "powerbi-te-docs",
    "powerbi-audit-tenant-settings",
    # Report authoring
    "powerbi-report-authoring",
    "powerbi-report-design",
    "powerbi-create-pbi-report",
    "powerbi-review-report",
    "powerbi-report-structure",
    "powerbi-report-theming",
    "powerbi-report-conversion",
    "powerbi-modifying-theme-json",
    # Visuals
    "powerbi-deneb-visuals",
    "powerbi-python-visuals",
    "powerbi-r-visuals",
    "powerbi-svg-visuals",
    "powerbi-custom-visuals",
    # PBIP / PBIR format
    "powerbi-pbip-format",
    "powerbi-pbir-format-enhanced",
    "powerbi-pbir-cli",
    # Fabric / data platform
    "powerbi-fabric-pipelines",
    "powerbi-medallion-architecture",
    "powerbi-data-transformation",
    "powerbi-data-catalog-lineage",
    "powerbi-source-integration",
    # Modeling & design
    "powerbi-star-schema-modeling",
    "powerbi-measure-glossary",
    "powerbi-performance-scale",
    "powerbi-security-rls",
    "powerbi-time-series-data",
    # Governance & process
    "powerbi-data-governance-traceability",
    "powerbi-testing-validation",
    "powerbi-project-management",
    "powerbi-cyber-security",
]

# Legacy flat-file names installed by powerbi-agent <= 0.5. Claude Code never
# discovered these (it requires <skill-name>/SKILL.md), so they are dead files
# in ~/.claude/skills/ and are cleaned up on install and uninstall.
_LEGACY_FLAT_NAMES = [
    "power-bi-connect", "power-bi-dax", "power-bi-model", "power-bi-report",
    "power-bi-fabric", "power-bi-doctor", "connect-pbid", "fabric-cli",
    "dax-mastery", "dax-performance", "tmdl", "power-query",
    "review-semantic-model", "standardize-naming-conventions",
    "refresh-semantic-model", "lineage-analysis", "bpa-rules",
    "c-sharp-scripting", "te2-cli", "te-docs", "audit-tenant-settings",
    "report-authoring", "pbi-report-design", "create-pbi-report",
    "review-report", "report-structure", "report-theming", "report-conversion",
    "modifying-theme-json", "deneb-visuals", "python-visuals", "r-visuals",
    "svg-visuals", "power-bi-custom-visuals", "pbip-format",
    "pbir-format-enhanced", "pbir-cli", "fabric-pipelines",
    "medallion-architecture", "data-transformation", "data-catalog-lineage",
    "source-integration", "star-schema-modeling", "measure-glossary",
    "performance-scale", "security-rls", "time-series-data",
    "data-governance-traceability", "testing-validation", "project-management",
    "cyber-security",
]


def _get_skills_source_dir() -> Path:
    """Return the directory containing skill directories.

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


def read_skill_description(skill_md: Path) -> str:
    """Read the ``description`` field from a SKILL.md frontmatter block."""
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return ""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    m = re.search(r"^description:\s*(.+)$", text[3:end], re.M)
    return m.group(1).strip() if m else ""


def _clean_legacy_flat_files() -> int:
    """Remove pre-0.6 flat ``<name>.md`` skill files that Claude Code never loaded."""
    removed = 0
    for legacy in _LEGACY_FLAT_NAMES:
        stale = SKILLS_DIR / f"{legacy}.md"
        if stale.is_file():
            stale.unlink()
            removed += 1
    return removed


def install_skills(force: bool = False) -> None:
    """Copy skill directories to ~/.claude/skills/<name>/SKILL.md."""
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)

    skill_files_dir = _get_skills_source_dir()

    installed = 0
    skipped = 0

    for skill_name in SKILL_NAMES:
        src = skill_files_dir / skill_name
        dst = SKILLS_DIR / skill_name

        if not (src / "SKILL.md").exists():
            console.print(f"[yellow][!][/yellow] Skill not found: {skill_name}")
            continue

        if dst.exists() and not force:
            console.print(f"[dim]  {skill_name}: already installed (use --force to overwrite)[/dim]")
            skipped += 1
            continue

        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        console.print(f"[green][+][/green]  {skill_name}: installed")
        installed += 1

    legacy = _clean_legacy_flat_files()
    if legacy:
        console.print(f"[dim]  cleaned up {legacy} legacy flat skill file(s) from a previous version[/dim]")

    _remove_claude_md_block()
    console.print(
        f"\n[bold]{installed}[/bold] skill(s) installed, {skipped} skipped.\n"
        "Claude Code will now use your Power BI skills automatically."
    )


def uninstall_skills() -> None:
    """Remove powerbi-agent skills from Claude Code."""
    removed = 0
    for skill_name in SKILL_NAMES:
        dst = SKILLS_DIR / skill_name
        if dst.is_dir():
            shutil.rmtree(dst)
            console.print(f"[red][-][/red]  {skill_name}: removed")
            removed += 1

    removed += _clean_legacy_flat_files()
    _remove_claude_md_block()
    console.print(f"\n{removed} skill(s) removed.")


def list_skills() -> None:
    """Show all available skills and their installation status."""
    tbl = Table(show_header=True, header_style="bold cyan")
    tbl.add_column("Skill")
    tbl.add_column("Status", justify="center")
    tbl.add_column("Description")

    try:
        source = _get_skills_source_dir()
    except FileNotFoundError:
        source = None

    for skill_name in SKILL_NAMES:
        installed = (SKILLS_DIR / skill_name / "SKILL.md").exists()
        desc = read_skill_description(source / skill_name / "SKILL.md") if source else ""
        # The description doubles as trigger text, so trim it for the table.
        short = desc.split(". Use when", 1)[0]
        tbl.add_row(
            skill_name,
            "[green][+] installed[/green]" if installed else "[dim]not installed[/dim]",
            short,
        )
    console.print(tbl)


def _remove_claude_md_block() -> None:
    """Remove the legacy powerbi-agent block from CLAUDE.md.

    Versions <= 0.5 injected a skill index into the user's global CLAUDE.md to
    work around skills not being discoverable in the flat layout. With the
    canonical ``<skill-name>/SKILL.md`` layout Claude Code loads descriptions
    directly, so the block is redundant context and is removed on install.
    """
    if not CLAUDE_MD.exists():
        return
    text = CLAUDE_MD.read_text(encoding="utf-8")
    if "<!-- powerbi-agent:start -->" not in text:
        return
    cleaned = re.sub(
        r"<!-- powerbi-agent:start -->.*?<!-- powerbi-agent:end -->",
        "",
        text,
        flags=re.DOTALL,
    )
    CLAUDE_MD.write_text(cleaned.strip() + "\n", encoding="utf-8")
    console.print("[green][+][/green]  CLAUDE.md cleaned up (skill index is no longer needed)")
