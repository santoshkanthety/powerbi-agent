"""
Power BI Desktop connection via Analysis Services (SSAS) TCP port.

Power BI Desktop hosts a local Analysis Services instance on a dynamic port.
Detect it by walking the per-instance workspace folders and reading
``msmdsrv.port.txt``.  Both the MSI installer and the Microsoft Store
build are supported.

Detection hardening (Microsoft Store path, UTF-16 / UTF-8 fallback,
most-recent-instance ordering) is patterned after pbi-cli
(https://github.com/MinaSaad1/pbi-cli, MIT) — independently written here.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from rich.console import Console

from powerbi_agent.errors import ConnectionRequiredError

console = Console()

# Config file stores the last used connection
_CONFIG_PATH = Path.home() / ".powerbi-agent" / "connection.json"

# Glob pattern for individual workspace subdirectories.
# The container dir is "AnalysisServicesWorkspace" (no suffix); each running
# instance creates "AnalysisServicesWorkspace_<guid>".
WORKSPACE_GLOB = "AnalysisServicesWorkspace_*/"


def _workspace_roots() -> list[Path]:
    """Return candidate roots that contain per-instance workspace folders.

    Power BI Desktop (MSI):
      %LOCALAPPDATA%/Microsoft/Power BI Desktop/

    Power BI Desktop (Microsoft Store):
      %USERPROFILE%/Microsoft/Power BI Desktop Store App/
    """
    roots: list[Path] = []

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        roots.append(Path(local_app_data) / "Microsoft" / "Power BI Desktop")

    roots.append(Path.home() / "Microsoft" / "Power BI Desktop Store App")

    return roots


def _read_port_file(port_file: Path) -> int | None:
    """Read a Power BI ``msmdsrv.port.txt`` value.

    Power BI writes UTF-16 LE (sometimes with BOM); older builds emitted
    UTF-8.  Try the common encoding first and fall back gracefully.
    """
    try:
        raw = port_file.read_bytes()
    except OSError:
        return None

    for decode in (
        lambda b: b.decode("utf-16-le").strip().replace("\ufeff", "").strip("\x00"),
        lambda b: b.decode("utf-8").strip().replace("\ufeff", "").strip("\x00"),
    ):
        try:
            text = decode(raw).strip()
            if text:
                return int(text)
        except (UnicodeDecodeError, ValueError):
            continue
    return None


def detect_instances() -> list[dict]:
    """
    Return a list of open Power BI Desktop instances with their SSAS ports.

    Each entry: {"port": int, "name": str, "workspace": str}.  Sorted by
    workspace mtime descending so the most recently opened report is first.
    """
    instances: list[dict] = []

    try:
        candidates: list[tuple[float, Path, Path]] = []
        for root in _workspace_roots():
            if not root.exists():
                continue
            for workspace_dir in root.glob(WORKSPACE_GLOB):
                port_file = workspace_dir / "Data" / "msmdsrv.port.txt"
                if not port_file.exists():
                    continue
                try:
                    mtime = port_file.stat().st_mtime
                except OSError:
                    mtime = 0.0
                candidates.append((mtime, workspace_dir, port_file))

        candidates.sort(key=lambda t: t[0], reverse=True)

        for _mtime, workspace_dir, port_file in candidates:
            port = _read_port_file(port_file)
            if port is None:
                continue
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
        raise ConnectionRequiredError()
    return json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))


def get_connection_string(port: int | None = None) -> str:
    """Return an OLEDB/ADOMD connection string for the local SSAS instance."""
    if port is None:
        conn = get_connection()
        port = conn["port"]
    return f"Data Source=localhost:{port};"
