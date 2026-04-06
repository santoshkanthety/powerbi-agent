"""
Environment diagnostics — help users fix common setup issues.
"""

from __future__ import annotations

import platform
import shutil
import sysconfig
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
    detail = f"Python {v.major}.{v.minor}.{v.micro}"
    if v >= (3, 14):
        detail += " — Desktop integration requires Python <=3.13 (pythonnet limitation)"
    return ok, detail


@check("Operating System (Windows)")
def _check_os():
    ok = platform.system() == "Windows"
    return ok, platform.platform()


@check("Scripts directory on PATH")
def _check_path():
    """Detect the common Windows pitfall where pip installs scripts to a dir not on PATH."""
    scripts_dir = sysconfig.get_path("scripts")
    if not scripts_dir:
        return None, "Could not determine scripts directory"

    pbi_agent_bin = shutil.which("pbi-agent")
    if pbi_agent_bin:
        return True, f"pbi-agent found at {pbi_agent_bin}"

    # pbi-agent not found on PATH — give the exact fix
    if sys.platform == "win32":
        fix = (
            f"Scripts dir not on PATH: {scripts_dir}\n"
            "  Fix (PowerShell, run once):\n"
            f'  [Environment]::SetEnvironmentVariable("PATH", $env:PATH + ";{scripts_dir}", "User")\n'
            "  Then restart your terminal."
        )
    else:
        fix = f"Scripts dir not on PATH: {scripts_dir} — add it to your shell profile."
    return False, fix


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
    return None, "Not found in standard locations (required only for Desktop/DAX commands)"


@check("pythonnet (for Desktop integration)")
def _check_pythonnet():
    try:
        import clr  # noqa: F401
        # Use importlib.metadata — pythonnet pre-releases lack __version__
        from importlib.metadata import version as pkg_version, PackageNotFoundError
        try:
            ver = pkg_version("pythonnet")
        except PackageNotFoundError:
            ver = "unknown"
        return True, f"pythonnet {ver}"
    except ImportError:
        if sys.version_info >= (3, 14):
            return None, (
                "Not installed — pythonnet has no stable release for Python 3.14 yet. "
                "Use Python 3.13 for Desktop features, or install pre-release: "
                "pip install --pre pythonnet"
            )
        return None, "Not installed (optional) — run: pip install powerbi-agent[desktop]"


@check("azure-identity (for Fabric integration)")
def _check_azure():
    try:
        from importlib.metadata import version as pkg_version
        ver = pkg_version("azure-identity")
        return True, f"azure-identity {ver}"
    except Exception:
        return None, "Not installed (optional) — run: pip install powerbi-agent[fabric]"


@check("Connection config")
def _check_connection():
    config_path = Path.home() / ".powerbi-agent" / "connection.json"
    if config_path.exists():
        import json
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
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
            status = "[green]OK[/green]"
        elif result is None:
            status = "[yellow]--[/yellow]"
        else:
            status = "[red]FAIL[/red]"
            failed += 1

        tbl.add_row(label, status, detail)

    console.print(tbl)

    if failed:
        console.print(
            f"\n[red]{failed} check(s) failed.[/red] "
            "Fix issues above, then re-run [bold]pbi-agent doctor[/bold]."
        )
    else:
        console.print("\n[green]All checks passed![/green] You're good to go.")
