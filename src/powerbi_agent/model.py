"""
Semantic model inspection and modification via TOM (Tabular Object Model).

Uses pythonnet + Microsoft.AnalysisServices to read and write model metadata
directly against the Power BI Desktop local SSAS instance.
"""

from __future__ import annotations

import sys
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def _get_tom():
    """Load TOM assembly via pythonnet."""
    try:
        import clr
        clr.AddReference("Microsoft.AnalysisServices.Tabular")
        from Microsoft.AnalysisServices.Tabular import Server, Database, Measure  # noqa
        return Server, Database, Measure
    except ImportError:
        console.print(
            "[red]pythonnet not installed.[/red]\n"
            "Install: [bold]pip install powerbi-agent[desktop][/bold]"
        )
        sys.exit(1)


def _open_server(port: Optional[int] = None):
    """Return an open TOM Server connected to the local SSAS instance."""
    from powerbi_agent.connect import get_connection_string
    Server, _, _ = _get_tom()
    conn_str = get_connection_string(port)
    server = Server()
    server.Connect(conn_str)
    return server


def show_info(port: Optional[int] = None) -> None:
    """Display a summary of the connected model."""
    server = _open_server(port)
    try:
        db = server.Databases[0]
        model = db.Model
        table_count = model.Tables.Count
        measure_count = sum(t.Measures.Count for t in model.Tables)
        rel_count = model.Relationships.Count

        console.print(Panel(
            f"[bold]Model:[/bold] {model.Name}\n"
            f"[bold]Tables:[/bold] {table_count}\n"
            f"[bold]Measures:[/bold] {measure_count}\n"
            f"[bold]Relationships:[/bold] {rel_count}\n"
            f"[bold]Compatibility Level:[/bold] {db.CompatibilityLevel}",
            title="Semantic Model Info",
            border_style="cyan",
        ))
    finally:
        server.Disconnect()


def list_tables(port: Optional[int] = None) -> None:
    """List all tables with column and measure counts."""
    server = _open_server(port)
    try:
        tbl = Table(show_header=True, header_style="bold cyan")
        tbl.add_column("Table", style="bold")
        tbl.add_column("Columns", justify="right")
        tbl.add_column("Measures", justify="right")
        tbl.add_column("Rows (est.)", justify="right")
        tbl.add_column("Hidden", justify="center")

        for t in server.Databases[0].Model.Tables:
            tbl.add_row(
                t.Name,
                str(t.Columns.Count),
                str(t.Measures.Count),
                "—",
                "✓" if t.IsHidden else "",
            )
        console.print(tbl)
    finally:
        server.Disconnect()


def list_measures(table: Optional[str] = None, port: Optional[int] = None) -> None:
    """List measures across all tables, or a specific table."""
    server = _open_server(port)
    try:
        tbl = Table(show_header=True, header_style="bold cyan")
        tbl.add_column("Table", style="dim")
        tbl.add_column("Measure", style="bold")
        tbl.add_column("Expression")
        tbl.add_column("Format")
        tbl.add_column("Hidden", justify="center")

        for t in server.Databases[0].Model.Tables:
            if table and t.Name.lower() != table.lower():
                continue
            for m in t.Measures:
                tbl.add_row(
                    t.Name,
                    m.Name,
                    m.Expression[:80] + ("…" if len(m.Expression) > 80 else ""),
                    m.FormatString or "",
                    "✓" if m.IsHidden else "",
                )
        console.print(tbl)
    finally:
        server.Disconnect()


def add_measure(
    name: str,
    expression: str,
    table: str,
    format_string: Optional[str] = None,
    port: Optional[int] = None,
) -> None:
    """Add or replace a measure in the model."""
    Server, _, Measure = _get_tom()
    server = _open_server(port)

    try:
        model = server.Databases[0].Model
        target_table = next((t for t in model.Tables if t.Name == table), None)

        if target_table is None:
            console.print(f"[red]Table '{table}' not found.[/red]")
            console.print("Available tables: " + ", ".join(t.Name for t in model.Tables))
            sys.exit(1)

        # Check if measure already exists → update
        existing = next((m for m in target_table.Measures if m.Name == name), None)
        if existing:
            existing.Expression = expression
            if format_string:
                existing.FormatString = format_string
            console.print(f"[yellow]⟳[/yellow] Updated measure [bold]{name}[/bold]")
        else:
            m = Measure()
            m.Name = name
            m.Expression = expression
            if format_string:
                m.FormatString = format_string
            target_table.Measures.Add(m)
            console.print(f"[green]✓[/green] Added measure [bold]{name}[/bold] to table [cyan]{table}[/cyan]")

        model.SaveChanges()
    finally:
        server.Disconnect()


def list_relationships(port: Optional[int] = None) -> None:
    """List all relationships in the model."""
    server = _open_server(port)
    try:
        tbl = Table(show_header=True, header_style="bold cyan")
        tbl.add_column("From Table")
        tbl.add_column("From Column")
        tbl.add_column("→", justify="center")
        tbl.add_column("To Table")
        tbl.add_column("To Column")
        tbl.add_column("Cardinality")
        tbl.add_column("Active", justify="center")

        for r in server.Databases[0].Model.Relationships:
            tbl.add_row(
                r.FromTable.Name,
                r.FromColumn.Name,
                "→",
                r.ToTable.Name,
                r.ToColumn.Name,
                str(r.FromCardinality).replace("RelationshipEndCardinality.", ""),
                "✓" if r.IsActive else "",
            )
        console.print(tbl)
    finally:
        server.Disconnect()
