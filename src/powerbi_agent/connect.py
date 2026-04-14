"""
Power BI Desktop connection via Analysis Services (SSAS) TCP port.

Power BI Desktop hosts a local Analysis Services instance on a dynamic port.
We detect it by scanning running processes for msmdsrv.exe and reading
the port from the workspace folder or by scanning TCP sockets.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from rich.console import Console

console = Console()

# Config file stores the last used connection
_CONFIG_PATH = Path.home() / ".powerbi-agent" / "connection.json"

# Glob pattern for individual workspace subdirectories.
# The container dir is "AnalysisServicesWorkspace" (no suffix); each running
# instance creates "AnalysisServicesWorkspace_<guid>".
WORKSPACE_GLOB = "AnalysisServicesWorkspace_*/"


def detect_instances() -> list[dict]:
    """
    Return a list of open Power BI Desktop instances with their SSAS ports.

    Each entry: {"port": int, "name": str, "pid": int, "workspace": str}
    """
    instances = []

    try:
        # Strategy 1: Walk PBI Desktop workspace folders to find msmdsrv.port.txt
        local_app_data = Path(os.environ.get("LOCALAPPDATA", ""))
        pbi_root = local_app_data / "Microsoft" / "Power BI Desktop"

        # Bug fix: The container directory is named "AnalysisServicesWorkspace"
        # (no suffix), while individual workspaces are named
        # "AnalysisServicesWorkspace_<guid>".  The old glob
        # "AnalysisServicesWorkspace*/" matched the container itself,
        # causing detection to always fail.  Use "_*" to match only the
        # per-instance workspace sub-directories.
        for workspace_dir in pbi_root.glob(WORKSPACE_GLOB):
            port_file = workspace_dir / "Data" / "msmdsrv.port.txt"
            if port_file.exists():
                # Bug fix: Power BI Desktop writes this file in UTF-16 LE.
                # Reading as UTF-8 leaves embedded NUL bytes that make
                # int() crash.  Decode as utf-16-le and strip NULs/BOM.
                raw = port_file.read_bytes()
                text = raw.decode("utf-16-le").strip().replace("\ufeff", "")
                port = int(text)
                name = _get_pbix_name_for_workspace(workspace_dir)
                instances.append({
                    "port": port,
                    "name": name or workspace_dir.name,
                    "workspace": str(workspace_dir),
                })

    except Exception as exc:
        console.print(f"[dim]Instance detection warning: {exc}[/dim]")

    return instances


def _get_pbix_name_for_workspace(workspace_dir: Path) -> str | None:
    """Try to read the model name from the workspace metadata."""
    try:
        model_schema = workspace_dir / "Data" / "Model" / "model.tmdl"
        if model_schema.exists():
            for line in model_schema.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("model "):
                    return line.strip().split(" ", 1)[1].strip()
    except Exception:
        pass
    return None


def connect_to_instance(instance: dict) -> None:
    """
    Persist connection details so subsequent commands use this instance.
    """
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CONFIG_PATH.write_text(json.dumps(instance, indent=2), encoding="utf-8")


def get_connection() -> dict:
    """
    Load the saved connection, or raise a helpful error.
    """
    if not _CONFIG_PATH.exists():
        raise RuntimeError(
            "Not connected to any Power BI Desktop instance.\n"
            "Run: pbi-agent connect"
        )
    return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))


def get_connection_string(port: int | None = None) -> str:
    """Return an OLEDB/ADOMD connection string for the local SSAS instance."""
    if port is None:
        conn = get_connection()
        port = conn["port"]
    return f"Data Source=localhost:{port};"
