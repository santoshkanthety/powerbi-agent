"""
Semantic model inspection and modification via TOM (Tabular Object Model).

Uses pythonnet + Microsoft.AnalysisServices to read and write model metadata
directly against the Power BI Desktop local SSAS instance.
"""

from __future__ import annotations

import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def _get_tom():
    """Load TOM assembly via pythonnet with assembly resolver."""
    from powerbi_agent._asm import ensure_assemblies
    ensure_assemblies()
    try:
        import clr
        clr.AddReference("Microsoft.AnalysisServices.Tabular")
        from Microsoft.AnalysisServices.Tabular import Server, Database, Measure  # noqa
        return Server, Database, Measure
    except Exception as exc:
        console.print(f"[red]Failed to load TOM assembly:[/red] {exc}")
        console.print(
            "[dim]Make sure Power BI Report Builder is installed, or set the\n"
            "PBI_REPORT_BUILDER environment variable to its install directory.[/dim]"
        )
        sys.exit(1)


def _open_server(port: int | None = None):
    """Return an open TOM Server connected to the local SSAS instance."""
    from powerbi_agent.connect import get_connection_string
    Server, _, _ = _get_tom()
    conn_str = get_connection_string(port)
    server = Server()
    server.Connect(conn_str)
    return server


def show_info(port: int | None = None) -> None:
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


def list_tables(port: int | None = None, fmt: str = "table") -> None:
    """List all tables with column and measure counts."""
    server = _open_server(port)
    try:
        tables_data = []
        for t in server.Databases[0].Model.Tables:
            tables_data.append({
                "name": t.Name,
                "columns": t.Columns.Count,
                "measures": t.Measures.Count,
                "hidden": t.IsHidden,
            })

        if fmt == "json":
            import json as _json
            print(_json.dumps(tables_data, indent=2, ensure_ascii=False))
        elif fmt == "csv":
            print("Table,Columns,Measures,Hidden")
            for row in tables_data:
                print(f"{row['name']},{row['columns']},{row['measures']},{row['hidden']}")
        else:
            tbl = Table(show_header=True, header_style="bold cyan")
            tbl.add_column("Table", style="bold")
            tbl.add_column("Columns", justify="right")
            tbl.add_column("Measures", justify="right")
            tbl.add_column("Rows (est.)", justify="right")
            tbl.add_column("Hidden", justify="center")

            for row in tables_data:
                tbl.add_row(
                    row["name"],
                    str(row["columns"]),
                    str(row["measures"]),
                    "—",
                    "✓" if row["hidden"] else "",
                )
            console.print(tbl)
    finally:
        server.Disconnect()


def list_measures(table: str | None = None, port: int | None = None, fmt: str = "table") -> None:
    """List measures across all tables, or a specific table."""
    server = _open_server(port)
    try:
        measures_data = []
        for t in server.Databases[0].Model.Tables:
            if table and t.Name.lower() != table.lower():
                continue
            for m in t.Measures:
                measures_data.append({
                    "table": t.Name,
                    "measure": m.Name,
                    "expression": m.Expression,
                    "format": m.FormatString or "",
                    "hidden": m.IsHidden,
                })

        if fmt == "json":
            import json as _json
            print(_json.dumps(measures_data, indent=2, ensure_ascii=False))
        elif fmt == "csv":
            print("Table,Measure,Expression,Format,Hidden")
            for row in measures_data:
                # Escape all string fields for CSV (double-quote embedded quotes, wrap in quotes)
                def _csv_esc(val: str) -> str:
                    return '"' + val.replace('"', '""') + '"'

                print(f'{_csv_esc(row["table"])},{_csv_esc(row["measure"])},'
                      f'{_csv_esc(row["expression"])},{_csv_esc(row["format"])},{row["hidden"]}')
        else:
            tbl = Table(show_header=True, header_style="bold cyan")
            tbl.add_column("Table", style="dim")
            tbl.add_column("Measure", style="bold")
            tbl.add_column("Expression")
            tbl.add_column("Format")
            tbl.add_column("Hidden", justify="center")

            for row in measures_data:
                expr = row["expression"]
                tbl.add_row(
                    row["table"],
                    row["measure"],
                    expr[:80] + ("…" if len(expr) > 80 else ""),
                    row["format"],
                    "✓" if row["hidden"] else "",
                )
            console.print(tbl)
    finally:
        server.Disconnect()


def add_measure(
    name: str,
    expression: str,
    table: str,
    format_string: str | None = None,
    port: int | None = None,
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


def list_relationships(port: int | None = None) -> None:
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
