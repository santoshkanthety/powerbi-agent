"""Basic CLI tests — no Power BI Desktop required."""

from click.testing import CliRunner
from powerbi_agent.cli import main


def test_version():
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


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
    assert "power-bi-connect" in result.output
