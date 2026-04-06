"""
Environment diagnostics — help users fix common setup issues.
"""

from __future__ import annotations

import platform
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()

CHECKS = []


def check(label: str):
    def decorator(fn):
        CHECKS.append((label, fn))
        return fn
    return decorator


@check("Python version (>=3.10)")
def _check_python():
    v = sys.version_info
    ok = v >= (3, 10)
    return ok, f"Python {v.major}.{v.minor}.{v.micro}"


@check("Operating System (Windows)")
def _check_os():
    ok = platform.system() == "Windows"
    return ok, platform.platform()


@check("Power BI Desktop installed")
def _check_pbi_desktop():
    pbi_paths = [
        Path(r"C:\Program Files\Microsoft Power BI Desktop\bin\PBIDesktop.exe"),
        Path(r"C:\Program Files (x86)\Microsoft Power BI Desktop\bin\PBIDesktop.exe"),
    ]
    local = Path.home() / "AppData" / "Local" / "Microsoft" / "WindowsApps" / "PBIDesktop.exe"
    pbi_paths.append(local)

    for p in pbi_paths:
        if p.exists():
            return True, str(p)
    return False, "Not found in standard locations"


@check("pythonnet (for Desktop integration)")
def _check_pythonnet():
    try:
        import clr  # noqa
        import pythonnet
        return True, f"pythonnet {pythonnet.__version__}"
    except ImportError:
        return False, "Not installed — run: pip install powerbi-agent[desktop]"


@check("azure-identity (for Fabric integration)")
def _check_azure():
    try:
        import azure.identity
        return True, f"azure-identity {azure.identity.__version__}"
    except ImportError:
        return None, "Not installed — run: pip install powerbi-agent[fabric]"


@check("Connection config")
def _check_connection():
    config_path = Path.home() / ".powerbi-agent" / "connection.json"
    if config_path.exists():
        import json
        cfg = json.loads(config_path.read_text())
        return True, f"Port {cfg.get('port')} — {cfg.get('name', 'unknown')}"
    return None, "Not connected — run: pbi-agent connect"


@check("Claude Code skills installed")
def _check_skills():
    from powerbi_agent.skills.installer import SKILL_NAMES
    skills_dir = Path.home() / ".claude" / "skills"
    if not skills_dir.exists():
        return None, "Not installed — run: pbi-agent skills install"
    installed = [s for s in SKILL_NAMES if (skills_dir / f"{s}.md").exists()]
    if installed:
        return True, f"{len(installed)}/{len(SKILL_NAMES)} skill(s) installed"
    return None, "Not installed — run: pbi-agent skills install"


def run_checks() -> None:
    tbl = Table(show_header=True, header_style="bold cyan", box=None)
    tbl.add_column("Check")
    tbl.add_column("Status", justify="center")
    tbl.add_column("Detail", style="dim")

    failed = 0
    for label, fn in CHECKS:
        try:
            result, detail = fn()
        except Exception as exc:
            result, detail = False, str(exc)

        if result is True:
            status = "[green]✓[/green]"
        elif result is None:
            status = "[yellow]⚠[/yellow]"
        else:
            status = "[red]✗[/red]"
            failed += 1

        tbl.add_row(label, status, detail)

    console.print(tbl)

    if failed:
        console.print(f"\n[red]{failed} check(s) failed.[/red] Fix issues above, then re-run [bold]pbi-agent doctor[/bold].")
    else:
        console.print("\n[green]All checks passed![/green] You're good to go.")
