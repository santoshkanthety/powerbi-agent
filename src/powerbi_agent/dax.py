"""
DAX query execution and validation.

Uses pythonnet + Microsoft.AnalysisServices.AdomdClient to run DAX
directly against the local Power BI Desktop SSAS instance.
"""

from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from powerbi_agent.errors import DaxQueryError, DotNetNotFoundError

console = Console()


def _get_adomd():
    """Import AdomdClient via pythonnet with assembly resolver."""
    from powerbi_agent._asm import ensure_assemblies
    ensure_assemblies()
    try:
        import clr  # pythonnet
        clr.AddReference("Microsoft.AnalysisServices.AdomdClient")
        from Microsoft.AnalysisServices.AdomdClient import (  # noqa: F401
            AdomdCommand,
            AdomdConnection,
        )
        return AdomdConnection, AdomdCommand
    except Exception as exc:
        raise DotNetNotFoundError(
            f"Failed to load ADOMD client: {exc}\n"
            "Install Power BI Report Builder, or set the "
            "PBI_REPORT_BUILDER environment variable to its install directory."
        ) from exc


def run_query(
    expression: str,
    table: str | None = None,
    fmt: str = "table",
    port: int | None = None,
) -> None:
    """Execute a DAX query and display results."""
    from powerbi_agent._asm import disposable
    from powerbi_agent.connect import get_connection_string

    conn_str = get_connection_string(port)
    AdomdConnection, AdomdCommand = _get_adomd()

    # Wrap in EVALUATE if needed.
    # If the expression looks like a table expression (contains VALUES, FILTER, ALL, SUMMARIZE,
    # SELECTCOLUMNS, ADDCOLUMNS, TOPN, or is already a table constructor {…}) use it directly.
    # Otherwise treat as a scalar and wrap with ROW() so DAX engine accepts it.
    dax = expression.strip()
    if not dax.upper().startswith("EVALUATE"):
        _TABLE_FUNCS = ("VALUES(", "FILTER(", "ALL(", "SUMMARIZE(", "SELECTCOLUMNS(",
                        "ADDCOLUMNS(", "TOPN(", "CALCULATETABLE(", "UNION(", "EXCEPT(",
                        "INTERSECT(", "CROSSJOIN(", "NATURALLEFTOUTERJOIN(", "ALLEXCEPT(")
        _is_table = (
            dax.startswith("{")
            or any(dax.upper().startswith(fn) for fn in _TABLE_FUNCS)
        )
        if table:
            # Always a table expression scoped to the given table
            dax = f"EVALUATE CALCULATETABLE({dax}, '{table}')"
        elif _is_table:
            dax = f"EVALUATE {dax}"
        else:
            # Scalar expression — wrap in ROW() to produce a single-row table
            dax = f"EVALUATE ROW(\"Value\", {dax})"

    # Bug fix: pythonnet 3.x removed automatic IDisposable → context manager
    # mapping. Use disposable() wrapper instead of bare `with AdomdConnection(...)`.
    with disposable(AdomdConnection(conn_str)) as conn:
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
    from powerbi_agent._asm import disposable
    from powerbi_agent.connect import get_connection_string

    conn_str = get_connection_string(port)
    AdomdConnection, AdomdCommand = _get_adomd()

    # Use DEFINE to parse without full execution
    test_dax = f"DEFINE MEASURE __test__ = {expression}\nEVALUATE ROW(\"x\", [__test__])"

    try:
        # Bug fix: use disposable() wrapper for pythonnet 3.x compatibility
        with disposable(AdomdConnection(conn_str)) as conn:
            conn.Open()
            cmd = AdomdCommand(test_dax, conn)
            cmd.ExecuteNonQuery()
        console.print("[green]✓[/green] DAX expression is valid.")
    except Exception as exc:
        raise DaxQueryError(str(exc)) from exc
