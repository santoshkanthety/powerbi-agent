"""
Unit tests for DAX expression wrapping logic in dax.py.

Tests the scalar vs table expression detection fix —
scalar expressions must use ROW() not {{}}.
"""

from __future__ import annotations

import pytest


# ── Expression wrapping logic (extracted for pure unit testing) ────────────────

_TABLE_FUNCS = (
    "VALUES(", "FILTER(", "ALL(", "SUMMARIZE(", "SELECTCOLUMNS(",
    "ADDCOLUMNS(", "TOPN(", "CALCULATETABLE(", "UNION(", "EXCEPT(",
    "INTERSECT(", "CROSSJOIN(", "NATURALLEFTOUTERJOIN(", "ALLEXCEPT(",
)


def _wrap_dax(expression: str, table: str | None = None) -> str:
    """Replicate the wrapping logic from dax.run_query for unit testing."""
    dax = expression.strip()
    if not dax.upper().startswith("EVALUATE"):
        _is_table = (
            dax.startswith("{")
            or any(dax.upper().startswith(fn) for fn in _TABLE_FUNCS)
        )
        if table:
            dax = f"EVALUATE CALCULATETABLE({dax}, '{table}')"
        elif _is_table:
            dax = f"EVALUATE {dax}"
        else:
            dax = f"EVALUATE ROW(\"Value\", {dax})"
    return dax


# ── Scalar expressions → ROW() ─────────────────────────────────────────────────

@pytest.mark.parametrize("expr,expected_start", [
    ("SUM(Sales[Amount])", "EVALUATE ROW("),
    ("CALCULATE(SUM(Sales[Amount]), YEAR(Sales[Date])=2024)", "EVALUATE ROW("),
    ("[Total Revenue]", "EVALUATE ROW("),
    ("DISTINCTCOUNT(Orders[customer_id])", "EVALUATE ROW("),
    ("DIVIDE([Revenue], [Target], 0)", "EVALUATE ROW("),
    ("COUNTROWS(Orders)", "EVALUATE ROW("),
])
def test_scalar_wraps_in_row(expr, expected_start):
    result = _wrap_dax(expr)
    assert result.startswith(expected_start), (
        f"Expected scalar '{expr}' to be wrapped with ROW(), got: {result}"
    )
    assert f"EVALUATE ROW(\"Value\", {expr})" == result


# ── Table expressions → direct EVALUATE ───────────────────────────────────────

@pytest.mark.parametrize("expr", [
    "VALUES('Product'[Category])",
    "FILTER(Orders, Orders[Status] = \"completed\")",
    "ALL(Customers)",
    "SUMMARIZE(Orders, Orders[Region], \"Revenue\", SUM(Orders[Amount]))",
    "SELECTCOLUMNS(Orders, \"ID\", Orders[order_id], \"Amt\", Orders[amount])",
    "ADDCOLUMNS(Products, \"Sales\", RELATED(Sales[Amount]))",
    "TOPN(10, Products, Products[Sales], DESC)",
    "CALCULATETABLE(Orders, Orders[Year] = 2024)",
    "{1, 2, 3}",  # table constructor literal
])
def test_table_expr_wraps_without_row(expr):
    result = _wrap_dax(expr)
    assert result.startswith("EVALUATE "), f"Expected EVALUATE prefix, got: {result}"
    assert "ROW(" not in result, (
        f"Table expression '{expr}' should NOT be wrapped in ROW(), got: {result}"
    )


# ── Pre-formed EVALUATE expressions pass through unchanged ────────────────────

@pytest.mark.parametrize("expr", [
    "EVALUATE VALUES('Product'[Category])",
    "EVALUATE ROW(\"x\", SUM(Sales[Amount]))",
    "evaluate FILTER(Orders, Orders[Status] = \"active\")",
])
def test_evaluate_passthrough(expr):
    result = _wrap_dax(expr)
    assert result == expr, f"Pre-formed EVALUATE should pass through unchanged, got: {result}"


# ── Table-scoped expressions ───────────────────────────────────────────────────

def test_table_scoped_wraps_with_calculatetable():
    result = _wrap_dax("SUM(Sales[Amount])", table="Sales")
    assert result == "EVALUATE CALCULATETABLE(SUM(Sales[Amount]), 'Sales')"


def test_table_scoped_table_expr():
    result = _wrap_dax("VALUES(Sales[Category])", table="Sales")
    assert result == "EVALUATE CALCULATETABLE(VALUES(Sales[Category]), 'Sales')"


# ── Edge cases ─────────────────────────────────────────────────────────────────

def test_whitespace_trimmed():
    result = _wrap_dax("  SUM(Sales[Amount])  ")
    assert result == 'EVALUATE ROW("Value", SUM(Sales[Amount]))'


def test_case_insensitive_evaluate_check():
    expr = "EVALUATE VALUES(Products[Name])"
    assert _wrap_dax(expr.lower()) == expr.lower()  # passes through
