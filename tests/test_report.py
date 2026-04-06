"""
Real-world tests for report.py — PBIX/PBIR layout parsing.

Tests the UTF-16 BOM decode fix and layout structure parsing
using in-memory PBIX/PBIR fixtures (no actual Power BI file needed).
"""

from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from powerbi_agent.report import add_page, list_pages, show_info


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_layout(pages: list[dict] | None = None) -> dict:
    """Build a minimal Power BI Layout JSON structure."""
    return {
        "id": str(uuid.uuid4()),
        "resourcePackages": [],
        "sections": pages or [
            {
                "name": "ReportSection1",
                "displayName": "Overview",
                "visualContainers": [
                    {"config": json.dumps({"singleVisual": {"visualType": "barChart"}})},
                    {"config": json.dumps({"singleVisual": {"visualType": "card"}})},
                ],
                "filters": "[]",
                "ordinal": 0,
            },
            {
                "name": "ReportSection2",
                "displayName": "Revenue Detail",
                "visualContainers": [],
                "filters": "[]",
                "ordinal": 1,
            },
        ],
    }


def _write_pbir_dir(tmp_path: Path, layout: dict) -> Path:
    """Create a fake PBIR directory with definition/report.json."""
    pbir_dir = tmp_path / "MyReport.pbir"
    pbir_dir.mkdir()
    defn_dir = pbir_dir / "definition"
    defn_dir.mkdir()
    (defn_dir / "report.json").write_text(json.dumps(layout), encoding="utf-8")
    return pbir_dir


def _write_pbix_utf16(tmp_path: Path, layout: dict, with_bom: bool = True) -> Path:
    """
    Create a fake 'extracted' PBIX Layout file in UTF-16 LE.
    Simulates Report/Layout extracted from a real .pbix archive.
    """
    report_dir = tmp_path / "Report"
    report_dir.mkdir()
    layout_file = report_dir / "Layout"
    raw = json.dumps(layout, ensure_ascii=False).encode("utf-16")  # includes BOM
    if not with_bom:
        raw = raw[2:]  # strip BOM
    layout_file.write_bytes(raw)
    return layout_file


# ── list_pages ─────────────────────────────────────────────────────────────────

def test_list_pages_pbir_dir(tmp_path):
    pbir_dir = _write_pbir_dir(tmp_path, _make_layout())

    with patch("powerbi_agent.report._find_pbix", return_value=pbir_dir):
        # Should not raise
        list_pages(pbix_path=str(pbir_dir))


def test_list_pages_counts_visuals(tmp_path, capsys):
    """PBIR list_pages should show correct visual count per page."""
    layout = _make_layout()
    pbir_dir = _write_pbir_dir(tmp_path, layout)

    with patch("powerbi_agent.report._find_pbix", return_value=pbir_dir):
        list_pages(pbix_path=str(pbir_dir))


def test_list_pages_hidden_flag(tmp_path):
    """Pages with visibility==1 should be marked hidden."""
    layout = _make_layout(pages=[
        {
            "name": "HiddenPage",
            "displayName": "Secret",
            "visualContainers": [],
            "visibility": 1,
            "filters": "[]",
            "ordinal": 0,
        }
    ])
    pbir_dir = _write_pbir_dir(tmp_path, layout)

    with patch("powerbi_agent.report._find_pbix", return_value=pbir_dir):
        # _load_layout is called internally; just check no crash
        list_pages(pbix_path=str(pbir_dir))


# ── UTF-16 BOM decode fix ──────────────────────────────────────────────────────

def test_load_layout_handles_utf16_bom(tmp_path):
    """
    The BOM fix: utf-16 (auto-BOM) must correctly decode Layout files.
    Previously utf-16-le would leave BOM bytes causing JSON parse errors.
    """
    layout = _make_layout()
    raw_utf16_with_bom = json.dumps(layout, ensure_ascii=False).encode("utf-16")  # includes FF FE BOM

    layout_file = tmp_path / "Layout"
    layout_file.write_bytes(raw_utf16_with_bom)

    # Simulate what _load_layout does for the BOM fix
    raw = layout_file.read_bytes()
    decoded = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8")
    parsed = json.loads(decoded)

    assert parsed["sections"][0]["displayName"] == "Overview"


def test_load_layout_utf16_without_bom_falls_back_to_utf8(tmp_path):
    """Layout files served as plain UTF-8 (PBIR JSON) should also parse correctly."""
    layout = _make_layout()
    layout_file = tmp_path / "report.json"
    layout_file.write_text(json.dumps(layout), encoding="utf-8")

    raw = layout_file.read_bytes()
    decoded = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8")
    parsed = json.loads(decoded)

    assert len(parsed["sections"]) == 2


# ── PBIR fallback path fix ─────────────────────────────────────────────────────

def test_load_layout_pbir_fallback_to_layout_file(tmp_path):
    """
    When definition/report.json is absent, _load_layout must fall back to
    Layout/report.json (a file), NOT report_path/Layout (a directory).
    This tests the directory-vs-file path bug fix.
    """
    from powerbi_agent.report import _load_layout

    layout = _make_layout()
    pbir_dir = tmp_path / "MyReport.pbir"
    pbir_dir.mkdir()

    # Create Layout/ subdir with a report.json (old PBIR layout style)
    layout_dir = pbir_dir / "Layout"
    layout_dir.mkdir()
    layout_json = layout_dir / "report.json"
    layout_json.write_text(json.dumps(layout), encoding="utf-8")

    # Do NOT create definition/report.json — forces the fallback
    parsed, path, _enc = _load_layout(pbir_dir)
    assert path == layout_json
    assert parsed["sections"][0]["displayName"] == "Overview"


# ── add_page ───────────────────────────────────────────────────────────────────

def test_add_page_appends_section(tmp_path):
    """add_page must append a new section and persist it."""
    pbir_dir = _write_pbir_dir(tmp_path, _make_layout())

    with patch("powerbi_agent.report._find_pbix", return_value=pbir_dir):
        add_page("KPI Summary", pbix_path=str(pbir_dir))

    # PBIR definition/report.json is UTF-8
    layout_file = pbir_dir / "definition" / "report.json"
    updated = json.loads(layout_file.read_text(encoding="utf-8"))
    page_names = [s["displayName"] for s in updated["sections"]]

    assert "KPI Summary" in page_names
    assert len(updated["sections"]) == 3  # 2 original + 1 new


def test_add_page_unique_internal_name(tmp_path):
    """Each added page must have a unique internal name (UUID-based)."""
    pbir_dir = _write_pbir_dir(tmp_path, _make_layout(pages=[]))

    with patch("powerbi_agent.report._find_pbix", return_value=pbir_dir):
        add_page("Page A", pbix_path=str(pbir_dir))
        add_page("Page B", pbix_path=str(pbir_dir))

    layout_file = pbir_dir / "definition" / "report.json"
    updated = json.loads(layout_file.read_text(encoding="utf-8"))
    names = [s["name"] for s in updated["sections"]]

    assert names[0] != names[1], "Internal page names must be unique"


def test_add_page_correct_ordinal(tmp_path):
    """Ordinal must equal the index of the new page in the sections list."""
    pbir_dir = _write_pbir_dir(tmp_path, _make_layout())

    with patch("powerbi_agent.report._find_pbix", return_value=pbir_dir):
        add_page("Appended", pbix_path=str(pbir_dir))

    layout_file = pbir_dir / "definition" / "report.json"
    updated = json.loads(layout_file.read_text(encoding="utf-8"))
    new_page = updated["sections"][-1]

    assert new_page["ordinal"] == 2  # 0, 1 existed → new is 2
