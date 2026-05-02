"""Tests for the typed error hierarchy in powerbi_agent.errors."""

from __future__ import annotations

import click
import pytest

from powerbi_agent.errors import (
    ConnectionRequiredError,
    DaxQueryError,
    DotNetNotFoundError,
    InstanceNotFoundError,
    PowerBIAgentError,
    ReportNotFoundError,
    TomError,
)


def test_base_inherits_click_exception():
    err = PowerBIAgentError("boom")
    assert isinstance(err, click.ClickException)
    assert err.message == "boom"


@pytest.mark.parametrize("cls", [
    DotNetNotFoundError,
    ConnectionRequiredError,
    InstanceNotFoundError,
    ReportNotFoundError,
])
def test_default_messages_nonempty(cls):
    err = cls()
    assert isinstance(err, PowerBIAgentError)
    assert err.message
    assert isinstance(err.message, str)


def test_connection_required_default_mentions_connect_command():
    err = ConnectionRequiredError()
    assert "pbi-agent connect" in err.message


def test_dotnet_default_mentions_install_path():
    err = DotNetNotFoundError()
    assert "powerbi-agent[desktop]" in err.message


def test_tom_error_carries_operation_and_detail():
    err = TomError("add_measure", "duplicate name")
    assert err.operation == "add_measure"
    assert err.detail == "duplicate name"
    assert err.message == "add_measure: duplicate name"


def test_dax_query_error_prefix():
    err = DaxQueryError("syntax error near EVALUATE")
    assert err.detail == "syntax error near EVALUATE"
    assert err.message.startswith("DAX error:")


def test_errors_format_via_click(capsys):
    """ClickException.show() writes to stderr without raising."""
    PowerBIAgentError("a clean message").show()
    captured = capsys.readouterr()
    assert "a clean message" in captured.err
