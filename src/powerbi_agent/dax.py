"""
DAX query execution and validation.

Uses pythonnet + Microsoft.AnalysisServices.AdomdClient to run DAX
directly against the local Power BI Desktop SSAS instance.
"""

from __future__ import annotations

import json
import sys

from rich.console import Console
from rich.table import Table

console = Console()


def _get_adomd():
    """Import AdomdClient via pythonnet. Raises ImportError with guidance if unavailable."""
    try:
        import clr  # pythonnet
        clr.AddReference("Microsoft.AnalysisServices.AdomdClient")
        from Microsoft.AnalysisServices.AdomdClient import (  # noqa: F401
            AdomdCommand,
            AdomdConnection,
        )
        return AdomdConnection, AdomdCommand
    except ImportError:
        console.print(
            "[red]pythonnet not installed.[/red] Install the desktop extra:\n"
            "  [bold]pip install powerbi-agent[desktop][/bold]"
        )
        sys.exit(1)
    except Exception as exc:
        console.print(f"[red]Failed to load ADOMD client:[/red] {exc}")
        console.print("[dim]Make sure Power BI Desktop is installed on this machine.[/dim]")
        sys.exit(1)


def run_query(
    expression: str,
    table: str | None = None,
    fmt: str = "table",
    port: int | None = None,
) -> None:
    """Execute a DAX query and display results."""
    from powerbi_agent.connect import get_connection_string

    conn_str = get_connection_string(port)
    AdomdConnection, AdomdCommand = _get_adomd()

    # Wrap in EVALUATE if needed
    dax = expression.strip()
    if not dax.upper().startswith("EVALUATE"):
        if table:
            dax = f"EVALUATE CALCULATETABLE({{{dax}}}, '{table}')"
        else:
            dax = f"EVALUATE {{{dax}}}"

    with AdomdConnection(conn_str) as conn:
        conn.Open()
        cmd = AdomdCommand(dax, conn)
        reader = cmd.ExecuteReader()

        columns = [reader.GetName(i) for i in range(reader.FieldCount)]
        rows = []
        while reader.Read():
            rows.append([str(reader[i]) for i in range(reader.FieldCount)])
        reader.Close()

    if fmt == "json":
        print(json.dumps([dict(zip(columns, r)) for r in rows], indent=2, ensure_ascii=False))
    elif fmt == "csv":
        print(",".join(columns))
        for row in rows:
            print(",".join(row))
    else:
        tbl = Table(show_header=True, header_style="bold cyan")
        for col in columns:
            tbl.add_column(col)
        for row in rows:
            tbl.add_row(*row)
        console.print(tbl)
        console.print(f"[dim]{len(rows)} row(s)[/dim]")


def validate_expression(expression: str, port: int | None = None) -> None:
    """Validate a DAX expression by running an empty EVALUATE."""
    from powerbi_agent.connect import get_connection_string

    conn_str = get_connection_string(port)
    AdomdConnection, AdomdCommand = _get_adomd()

    # Use DEFINE to parse without full execution
    test_dax = f"DEFINE MEASURE __test__ = {expression}\nEVALUATE ROW(\"x\", [__test__])"

    try:
        with AdomdConnection(conn_str) as conn:
            conn.Open()
            cmd = AdomdCommand(test_dax, conn)
            cmd.ExecuteNonQuery()
        console.print("[green]✓[/green] DAX expression is valid.")
    except Exception as exc:
        # Parse the SSAS error for a friendly message
        msg = str(exc)
        console.print(f"[red]✗ DAX error:[/red] {msg}")
        sys.exit(1)
