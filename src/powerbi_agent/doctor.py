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

# legacy_windows=False avoids Rich's Win32 console renderer, which tries to
# write box-drawing chars through APIs that hit the active code page (cp1252
# by default on Windows). safe_box further restricts to ASCII-compatible boxes.
console = Console(legacy_windows=False, safe_box=True)

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


@check("Power BI Report Builder (TOM/ADOMD DLLs)")
def _check_report_builder():
    from powerbi_agent._asm import find_report_builder_dir
    rb_dir = find_report_builder_dir()
    if rb_dir is not None:
        return True, str(rb_dir)
    return None, (
        "Not found — install Power BI Report Builder or set PBI_REPORT_BUILDER env var. "
        "Required for Desktop model/DAX commands."
    )


@check("Workspace directories")
def _check_workspaces():
    import os as _os

    from powerbi_agent.connect import WORKSPACE_GLOB

    local_app_data = Path(_os.environ.get("LOCALAPPDATA", ""))
    pbi_root = local_app_data / "Microsoft" / "Power BI Desktop"
    if not pbi_root.exists():
        return None, "Power BI Desktop AppData folder not found (expected on Windows)"
    workspaces = list(pbi_root.glob(WORKSPACE_GLOB))
    if not workspaces:
        return None, f"No active workspaces in {pbi_root}"
    return True, f"{len(workspaces)} workspace(s) in {pbi_root}"


@check("SSAS connectivity")
def _check_connectivity():
    config_path = Path.home() / ".powerbi-agent" / "connection.json"
    if not config_path.exists():
        return None, "Not connected — run: pbi-agent connect"
    import json
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    port = cfg.get("port")
    if port is None:
        return None, "Connection config missing port"
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("localhost", port))
        sock.close()
        if result == 0:
            return True, f"Port {port} is reachable"
        return False, f"Port {port} is not reachable — is Power BI Desktop running?"
    except Exception as exc:
        return None, f"Could not test port {port}: {exc}"


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
