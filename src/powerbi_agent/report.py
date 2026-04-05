"""
Report layout inspection and modification.

Works with the PBIR (Enhanced Report Format) JSON files —
no live Power BI Desktop connection required.

PBIR format: extract a .pbix with 7-zip to get the Report/Layout JSON,
or use Power BI Desktop's "Save as enhanced report format" option.
"""

from __future__ import annotations

import json
import sys
import uuid
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.tree import Tree

console = Console()


def _find_pbix(pbix_path: str | None = None) -> Path:
    """Resolve the .pbix or PBIR report directory to work with."""
    if pbix_path:
        p = Path(pbix_path)
        if not p.exists():
            console.print(f"[red]File not found:[/red] {pbix_path}")
            sys.exit(1)
        return p

    # Auto-detect: look for a single .pbix in cwd
    pbix_files = list(Path(".").glob("*.pbix")) + list(Path(".").glob("*.pbir"))
    if len(pbix_files) == 1:
        return pbix_files[0]
    if len(pbix_files) > 1:
        console.print("[yellow]Multiple report files found. Specify one:[/yellow]")
        for f in pbix_files:
            console.print(f"  {f}")
        sys.exit(1)

    console.print(
        "[red]No .pbix or .pbir file found in current directory.[/red]\n"
        "Specify the path: [bold]pbi-agent report info path/to/file.pbix[/bold]"
    )
    sys.exit(1)


def _load_layout(report_path: Path) -> tuple[dict, Path]:
    """
    Load the Layout JSON from a PBIX (requires extraction) or PBIR directory.
    Returns (layout_dict, layout_path).
    """
    if report_path.is_dir():
        # PBIR format
        layout_file = report_path / "definition" / "report.json"
        if not layout_file.exists():
            layout_file = report_path / "Layout"
    else:
        # .pbix — needs extraction; guide user
        console.print(
            "[yellow]Note:[/yellow] .pbix files are binary archives.\n"
            "For full report editing, save your report in [bold]Enhanced Format (.pbir)[/bold]:\n"
            "  File → Save as → Power BI enhanced report format\n\n"
            "For read-only inspection, we'll attempt to extract the layout…"
        )
        layout_file = _extract_layout_from_pbix(report_path)

    if not layout_file or not layout_file.exists():
        console.print("[red]Could not load report layout.[/red]")
        sys.exit(1)

    layout = json.loads(layout_file.read_bytes().decode("utf-16-le", errors="replace"))
    return layout, layout_file


def _extract_layout_from_pbix(pbix_path: Path) -> Path | None:
    """Extract Layout file from a .pbix using Python's zipfile module."""
    import tempfile
    import zipfile

    try:
        out_dir = Path(tempfile.mkdtemp())
        with zipfile.ZipFile(pbix_path, "r") as zf:
            if "Report/Layout" in zf.namelist():
                zf.extract("Report/Layout", out_dir)
                return out_dir / "Report" / "Layout"
    except Exception as exc:
        console.print(f"[red]Extraction failed:[/red] {exc}")
    return None


def show_info(pbix_path: str | None = None) -> None:
    """Display a tree overview of the report structure."""
    report_path = _find_pbix(pbix_path)
    layout, _ = _load_layout(report_path)

    pages = layout.get("sections", [])
    tree = Tree(f"[bold]{report_path.name}[/bold]")

    for page in pages:
        page_name = page.get("displayName", page.get("name", "Untitled"))
        visuals = page.get("visualContainers", [])
        branch = tree.add(f"[cyan]{page_name}[/cyan] ({len(visuals)} visual(s))")
        for v in visuals[:5]:
            config = json.loads(v.get("config", "{}"))
            vtype = config.get("singleVisual", {}).get("visualType", "unknown")
            branch.add(f"[dim]{vtype}[/dim]")
        if len(visuals) > 5:
            branch.add(f"[dim]… and {len(visuals) - 5} more[/dim]")

    console.print(tree)


def list_pages(pbix_path: str | None = None) -> None:
    """List all report pages."""
    report_path = _find_pbix(pbix_path)
    layout, _ = _load_layout(report_path)

    tbl = Table(show_header=True, header_style="bold cyan")
    tbl.add_column("#", justify="right", style="dim")
    tbl.add_column("Page Name", style="bold")
    tbl.add_column("Visuals", justify="right")
    tbl.add_column("Hidden", justify="center")

    for i, page in enumerate(layout.get("sections", []), 1):
        tbl.add_row(
            str(i),
            page.get("displayName", page.get("name", "")),
            str(len(page.get("visualContainers", []))),
            "✓" if page.get("visibility", 0) == 1 else "",
        )
    console.print(tbl)


def add_page(name: str, pbix_path: str | None = None) -> None:
    """Add a new blank page to the report."""
    report_path = _find_pbix(pbix_path)
    layout, layout_file = _load_layout(report_path)

    new_page = {
        "name": str(uuid.uuid4()).replace("-", "")[:20],
        "displayName": name,
        "visualContainers": [],
        "filters": "[]",
        "ordinal": len(layout.get("sections", [])),
    }
    layout.setdefault("sections", []).append(new_page)

    layout_file.write_bytes(json.dumps(layout, ensure_ascii=False).encode("utf-16-le"))
    console.print(f"[green]✓[/green] Added page [bold]{name}[/bold]")
