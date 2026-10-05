"""Basic CLI tests — no Power BI Desktop required."""

from click.testing import CliRunner

from powerbi_agent.cli import main


def test_version():
    from powerbi_agent import __version__
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output
    assert __version__ != "0.0.0+dev", "version must resolve from package metadata"


def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "connect" in result.output
    assert "dax" in result.output
    assert "model" in result.output
    assert "fabric" in result.output
    assert "skills" in result.output
    assert "doctor" in result.output


def test_dax_help():
    runner = CliRunner()
    result = runner.invoke(main, ["dax", "--help"])
    assert result.exit_code == 0
    assert "query" in result.output
    assert "validate" in result.output


def test_model_help():
    runner = CliRunner()
    result = runner.invoke(main, ["model", "--help"])
    assert result.exit_code == 0


def test_skills_list():
    runner = CliRunner()
    result = runner.invoke(main, ["skills", "list"])
    assert result.exit_code == 0
    assert "powerbi-connect" in result.output


def test_import_does_not_rebind_stdio():
    """Importing the CLI must not replace sys.stdout/sys.stderr.

    The Windows UTF-8 fix used to rebind both to a fresh TextIOWrapper around
    .buffer. The discarded wrapper closes that buffer when garbage-collected, and
    under pytest the buffer is the capture tmpfile — so every Windows test job died
    during collection with "ValueError: I/O operation on closed file" and ran zero
    tests. The fix reconfigures the existing streams in place; this guards it.
    """
    import sys

    before_out, before_err = sys.stdout, sys.stderr

    import importlib

    import powerbi_agent.cli

    importlib.reload(powerbi_agent.cli)

    assert sys.stdout is before_out, "cli import replaced sys.stdout"
    assert sys.stderr is before_err, "cli import replaced sys.stderr"
