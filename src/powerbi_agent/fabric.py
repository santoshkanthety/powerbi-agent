"""
Microsoft Fabric / Power BI Service integration.

Uses the Power BI REST API with Azure identity (azure-identity).
Install the fabric extra: pip install powerbi-agent[fabric]
"""

from __future__ import annotations

import json
import sys
import time
from typing import Optional

import httpx
from rich.console import Console
from rich.table import Table

console = Console()

_PBI_BASE = "https://api.powerbi.com/v1.0/myorg"
_TOKEN_CACHE = None


def _get_token() -> str:
    """Get a Bearer token via Azure identity (DeviceCode / browser flow)."""
    global _TOKEN_CACHE
    if _TOKEN_CACHE:
        return _TOKEN_CACHE

    try:
        from azure.identity import InteractiveBrowserCredential, TokenCachePersistenceOptions
        cred = InteractiveBrowserCredential(
            cache_persistence_options=TokenCachePersistenceOptions()
        )
        token = cred.get_token("https://analysis.windows.net/powerbi/api/.default")
        _TOKEN_CACHE = token.token
        return _TOKEN_CACHE
    except ImportError:
        console.print(
            "[red]azure-identity not installed.[/red]\n"
            "Install: [bold]pip install powerbi-agent[fabric][/bold]"
        )
        sys.exit(1)


def _headers() -> dict:
    return {"Authorization": f"Bearer {_get_token()}", "Content-Type": "application/json"}


def login() -> None:
    """Interactively authenticate with Azure / Microsoft Fabric."""
    token = _get_token()
    if token:
        console.print("[green]✓[/green] Authenticated with Microsoft Fabric.")


def list_workspaces() -> None:
    """List accessible Power BI workspaces."""
    resp = httpx.get(f"{_PBI_BASE}/groups", headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json().get("value", [])

    tbl = Table(show_header=True, header_style="bold cyan")
    tbl.add_column("Name", style="bold")
    tbl.add_column("ID", style="dim")
    tbl.add_column("Type")
    tbl.add_column("State")

    for ws in data:
        tbl.add_row(
            ws.get("name", ""),
            ws.get("id", ""),
            ws.get("type", ""),
            ws.get("state", ""),
        )
    console.print(tbl)
    console.print(f"[dim]{len(data)} workspace(s)[/dim]")


def list_datasets(workspace: Optional[str] = None) -> None:
    """List semantic models in a workspace."""
    url = (
        f"{_PBI_BASE}/groups/{_resolve_workspace_id(workspace)}/datasets"
        if workspace
        else f"{_PBI_BASE}/datasets"
    )
    resp = httpx.get(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    data = resp.json().get("value", [])

    tbl = Table(show_header=True, header_style="bold cyan")
    tbl.add_column("Name", style="bold")
    tbl.add_column("ID", style="dim")
    tbl.add_column("Configured By")
    tbl.add_column("Created")

    for ds in data:
        tbl.add_row(
            ds.get("name", ""),
            ds.get("id", ""),
            ds.get("configuredBy", ""),
            ds.get("createdDate", "")[:10] if ds.get("createdDate") else "",
        )
    console.print(tbl)


def trigger_refresh(
    dataset_name: str,
    workspace: Optional[str] = None,
    wait: bool = False,
) -> None:
    """Trigger a dataset refresh and optionally wait for completion."""
    ws_id = _resolve_workspace_id(workspace) if workspace else None
    ds_id = _resolve_dataset_id(dataset_name, ws_id)

    url = (
        f"{_PBI_BASE}/groups/{ws_id}/datasets/{ds_id}/refreshes"
        if ws_id
        else f"{_PBI_BASE}/datasets/{ds_id}/refreshes"
    )
    resp = httpx.post(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    console.print(f"[green]✓[/green] Refresh triggered for [bold]{dataset_name}[/bold]")

    if wait:
        console.print("[dim]Waiting for refresh to complete…[/dim]")
        _poll_refresh(ds_id, ws_id)


def _poll_refresh(dataset_id: str, workspace_id: Optional[str]) -> None:
    """Poll refresh status until completed or failed."""
    base = f"{_PBI_BASE}/groups/{workspace_id}" if workspace_id else _PBI_BASE
    url = f"{base}/datasets/{dataset_id}/refreshes?$top=1"

    with console.status("Refreshing…"):
        while True:
            time.sleep(10)
            resp = httpx.get(url, headers=_headers(), timeout=30)
            resp.raise_for_status()
            items = resp.json().get("value", [])
            if not items:
                continue
            status = items[0].get("status", "")
            if status == "Completed":
                console.print("[green]✓[/green] Refresh completed.")
                return
            if status == "Failed":
                error = items[0].get("serviceExceptionJson", "Unknown error")
                console.print(f"[red]✗ Refresh failed:[/red] {error}")
                sys.exit(1)


def _resolve_workspace_id(name_or_id: Optional[str]) -> Optional[str]:
    if not name_or_id:
        return None
    # If it looks like a GUID, use as-is
    if len(name_or_id) == 36 and name_or_id.count("-") == 4:
        return name_or_id
    # Otherwise resolve by name
    resp = httpx.get(f"{_PBI_BASE}/groups", headers=_headers(), timeout=30)
    resp.raise_for_status()
    for ws in resp.json().get("value", []):
        if ws["name"].lower() == name_or_id.lower():
            return ws["id"]
    console.print(f"[red]Workspace '{name_or_id}' not found.[/red]")
    sys.exit(1)


def _resolve_dataset_id(name_or_id: str, workspace_id: Optional[str]) -> str:
    if len(name_or_id) == 36 and name_or_id.count("-") == 4:
        return name_or_id
    url = (
        f"{_PBI_BASE}/groups/{workspace_id}/datasets"
        if workspace_id
        else f"{_PBI_BASE}/datasets"
    )
    resp = httpx.get(url, headers=_headers(), timeout=30)
    resp.raise_for_status()
    for ds in resp.json().get("value", []):
        if ds["name"].lower() == name_or_id.lower():
            return ds["id"]
    console.print(f"[red]Dataset '{name_or_id}' not found.[/red]")
    sys.exit(1)
