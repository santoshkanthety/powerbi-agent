"""Tests for Power BI Desktop instance detection.

Covers the upstream-aligned hardening: Microsoft Store install path,
UTF-16 / UTF-8 port file fallback, and most-recent-instance ordering.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest

from powerbi_agent import connect


def _write_workspace(
    root: Path,
    instance_id: str,
    port: int,
    *,
    encoding: str = "utf-16-le",
    bom: bool = False,
    model_name: str | None = None,
    mtime: float | None = None,
) -> Path:
    """Create a fake AnalysisServicesWorkspace_<id>/Data layout."""
    workspace = root / f"AnalysisServicesWorkspace_{instance_id}"
    data = workspace / "Data"
    data.mkdir(parents=True, exist_ok=True)

    payload = str(port)
    if bom:
        payload = "\ufeff" + payload
    data_bytes = payload.encode(encoding)
    port_file = data / "msmdsrv.port.txt"
    port_file.write_bytes(data_bytes)

    if model_name is not None:
        model_dir = data / "Model"
        model_dir.mkdir(parents=True, exist_ok=True)
        (model_dir / "model.tmdl").write_text(
            f"model {model_name}\n",
            encoding="utf-8",
        )

    if mtime is not None:
        os.utime(port_file, (mtime, mtime))

    return workspace


@pytest.fixture
def isolated_pbi_paths(tmp_path, monkeypatch):
    """Redirect both MSI (LOCALAPPDATA) and Microsoft Store roots to tmp_path."""
    msi_root = tmp_path / "msi" / "Microsoft" / "Power BI Desktop"
    store_root = tmp_path / "store_home" / "Microsoft" / "Power BI Desktop Store App"
    msi_root.mkdir(parents=True)
    store_root.mkdir(parents=True)

    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "msi"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "store_home")

    return msi_root, store_root


def test_detects_msi_install(isolated_pbi_paths):
    msi_root, _ = isolated_pbi_paths
    _write_workspace(msi_root, "abc", 51111, model_name="SalesModel")

    instances = connect.detect_instances()
    assert len(instances) == 1
    assert instances[0]["port"] == 51111
    assert instances[0]["name"] == "SalesModel"


def test_detects_microsoft_store_install(isolated_pbi_paths):
    _, store_root = isolated_pbi_paths
    _write_workspace(store_root, "store-1", 52222)

    instances = connect.detect_instances()
    assert len(instances) == 1
    assert instances[0]["port"] == 52222


def test_detects_both_installs_simultaneously(isolated_pbi_paths):
    msi_root, store_root = isolated_pbi_paths
    _write_workspace(msi_root, "msi-1", 50001)
    _write_workspace(store_root, "store-1", 50002)

    ports = sorted(i["port"] for i in connect.detect_instances())
    assert ports == [50001, 50002]


def test_utf16_le_with_bom_decoded(isolated_pbi_paths):
    msi_root, _ = isolated_pbi_paths
    _write_workspace(msi_root, "x", 55001, encoding="utf-16-le", bom=True)
    instances = connect.detect_instances()
    assert instances[0]["port"] == 55001


def test_utf8_fallback_decoded(isolated_pbi_paths):
    """Older PBI builds emitted UTF-8 — the reader must fall back."""
    msi_root, _ = isolated_pbi_paths
    _write_workspace(msi_root, "u8", 55002, encoding="utf-8")
    instances = connect.detect_instances()
    assert instances[0]["port"] == 55002


def test_most_recent_instance_listed_first(isolated_pbi_paths):
    msi_root, _ = isolated_pbi_paths
    base = time.time()
    _write_workspace(msi_root, "old", 50100, mtime=base - 600)
    _write_workspace(msi_root, "new", 50200, mtime=base)

    instances = connect.detect_instances()
    assert [i["port"] for i in instances] == [50200, 50100]


def test_unreadable_port_file_skipped(isolated_pbi_paths):
    msi_root, _ = isolated_pbi_paths
    workspace = msi_root / "AnalysisServicesWorkspace_bad"
    (workspace / "Data").mkdir(parents=True)
    (workspace / "Data" / "msmdsrv.port.txt").write_bytes(b"\xff\xfe\x00not-a-number")

    _write_workspace(msi_root, "good", 50300)
    instances = connect.detect_instances()
    assert [i["port"] for i in instances] == [50300]


def test_no_workspaces_returns_empty(isolated_pbi_paths):
    assert connect.detect_instances() == []


def test_get_connection_raises_typed_error(monkeypatch, tmp_path):
    monkeypatch.setattr(connect, "_CONFIG_PATH", tmp_path / "missing.json")
    from powerbi_agent.errors import ConnectionRequiredError

    with pytest.raises(ConnectionRequiredError):
        connect.get_connection()
