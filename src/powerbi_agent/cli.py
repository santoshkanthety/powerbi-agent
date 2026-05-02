"""Main CLI entry point for powerbi-agent."""

import io
import sys

import click
from rich.console import Console
from rich.panel import Panel

from powerbi_agent import __version__

# ── Windows Unicode fix ────────────────────────────────────────────────────────
# The default Windows console uses cp1252 which cannot encode Unicode emoji
# (e.g. ⚠, ✓, ✗). Force UTF-8 so Rich output never crashes with
# UnicodeEncodeError: 'charmap' codec can't encode character ...
if sys.platform == "win32":
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "buffer"):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

console = Console()


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-v", "--version", message="powerbi-agent %(version)s")
def main():
    """
    \b
    ██████╗ ██████╗ ██╗      █████╗  ██████╗ ███████╗███╗   ██╗████████╗
    ██╔══██╗██╔══██╗██║     ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
    ██████╔╝██████╔╝██║     ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
    ██╔═══╝ ██╔══██╗██║     ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
    ██║     ██████╔╝██║     ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
    ╚═╝     ╚═════╝ ╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝

    AI-powered Power BI automation for Claude Code.
    Give Claude the Power BI skills it needs.
    """


# ─── connect ──────────────────────────────────────────────────────────────────

@main.command()
@click.option("--port", default=None, type=int,
              help="SSAS port (auto-detected if omitted). Bypasses detection when given.")
@click.option("--list", "list_only", is_flag=True, help="List open Power BI Desktop instances")
def connect(port, list_only):
    """Connect to a running Power BI Desktop instance."""
    from powerbi_agent.connect import connect_to_instance, detect_instances

    # Rec 6: When --port is given, bypass detection and connect directly.
    if port and not list_only:
        target = {"port": port, "name": f"manual (port {port})"}
        connect_to_instance(target)
        console.print(f"[green]✓[/green] Connected to [bold]{target['name']}[/bold] on port [cyan]{port}[/cyan]")
        return

    instances = detect_instances()

    if list_only or not instances:
        if not instances:
            console.print("[yellow]No Power BI Desktop instances found.[/yellow]")
            console.print("[dim]Open Power BI Desktop with a .pbix file first.[/dim]")
            sys.exit(1)
        console.print(Panel(
            "\n".join(f"  [{i}] Port [cyan]{inst['port']}[/cyan]  —  [bold]{inst['name']}[/bold]"
                      for i, inst in enumerate(instances)),
            title="Open Power BI Instances",
            border_style="blue",
        ))
        return

    target = instances[0]
    connect_to_instance(target)
    console.print(f"[green]✓[/green] Connected to [bold]{target['name']}[/bold] on port [cyan]{target['port']}[/cyan]")


# ─── dax ──────────────────────────────────────────────────────────────────────

@main.group()
def dax():
    """Execute and validate DAX queries and expressions."""


@dax.command("query")
@click.argument("expression")
@click.option("--table", "-t", default=None, help="Table to query against")
@click.option("--format", "fmt", type=click.Choice(["table", "json", "csv"]), default="table")
@click.option("--port", default=None, type=int)
def dax_query(expression, table, fmt, port):
    """Run a DAX query against the connected model.

    \b
    Examples:
        pbi-agent dax query "EVALUATE VALUES('Product'[Category])"
        pbi-agent dax query "CALCULATE(SUM(Sales[Amount]), YEAR(Sales[Date])=2024)"
    """
    from powerbi_agent.dax import run_query
    run_query(expression, table=table, fmt=fmt, port=port)


@dax.command("validate")
@click.argument("expression")
@click.option("--port", default=None, type=int)
def dax_validate(expression, port):
    """Validate a DAX expression without executing it."""
    from powerbi_agent.dax import validate_expression
    validate_expression(expression, port=port)


# ─── model ────────────────────────────────────────────────────────────────────

@main.group()
def model():
    """Inspect and modify the semantic model (tables, measures, relationships)."""


@model.command("info")
@click.option("--port", default=None, type=int)
def model_info(port):
    """Show summary of the connected model."""
    from powerbi_agent.model import show_info
    show_info(port=port)


@model.command("tables")
@click.option("--port", default=None, type=int)
@click.option("--format", "fmt", type=click.Choice(["table", "json", "csv"]), default="table", help="Output format")
def model_tables(port, fmt):
    """List all tables in the model."""
    from powerbi_agent.model import list_tables
    list_tables(port=port, fmt=fmt)


@model.command("measures")
@click.option("--table", "-t", default=None, help="Filter by table name")
@click.option("--port", default=None, type=int)
@click.option("--format", "fmt", type=click.Choice(["table", "json", "csv"]), default="table", help="Output format")
def model_measures(table, port, fmt):
    """List all measures, optionally filtered by table."""
    from powerbi_agent.model import list_measures
    list_measures(table=table, port=port, fmt=fmt)


@model.command("add-measure")
@click.argument("name")
@click.argument("expression")
@click.option("--table", "-t", required=True, help="Target table")
@click.option("--format-string", default=None, help="DAX format string e.g. '#,0.00'")
@click.option("--port", default=None, type=int)
def model_add_measure(name, expression, table, format_string, port):
    """Add or replace a measure in the model.

    \b
    Examples:
        pbi-agent model add-measure "Total Sales" "SUM(Sales[Amount])" --table Sales
        pbi-agent model add-measure "YoY Growth" "[Total Sales] / [PY Sales] - 1" --table Sales --format-string "0.0%"
    """
    from powerbi_agent.model import add_measure
    add_measure(name=name, expression=expression, table=table,
                format_string=format_string, port=port)


@model.command("relationships")
@click.option("--port", default=None, type=int)
def model_relationships(port):
    """List all relationships in the model."""
    from powerbi_agent.model import list_relationships
    list_relationships(port=port)


# ─── report ───────────────────────────────────────────────────────────────────

@main.group()
def report():
    """Inspect and modify report layout and visuals (works on .pbir files)."""


@report.command("info")
@click.argument("pbix_path", required=False)
def report_info(pbix_path):
    """Show report structure: pages, visuals, bookmarks."""
    from powerbi_agent.report import show_info
    show_info(pbix_path=pbix_path)


@report.command("pages")
@click.argument("pbix_path", required=False)
def report_pages(pbix_path):
    """List all pages in the report."""
    from powerbi_agent.report import list_pages
    list_pages(pbix_path=pbix_path)


@report.command("add-page")
@click.argument("name")
@click.argument("pbix_path", required=False)
def report_add_page(name, pbix_path):
    """Add a new page to the report."""
    from powerbi_agent.report import add_page
    add_page(name=name, pbix_path=pbix_path)


# ─── fabric ───────────────────────────────────────────────────────────────────

@main.group()
def fabric():
    """Microsoft Fabric / Power BI Service operations (requires Azure auth)."""


@fabric.command("login")
def fabric_login():
    """Authenticate with Microsoft Fabric / Azure."""
    from powerbi_agent.fabric import login
    login()


@fabric.command("workspaces")
def fabric_workspaces():
    """List accessible Fabric workspaces."""
    from powerbi_agent.fabric import list_workspaces
    list_workspaces()


@fabric.command("datasets")
@click.option("--workspace", "-w", default=None, help="Workspace name or ID")
def fabric_datasets(workspace):
    """List semantic models (datasets) in a workspace."""
    from powerbi_agent.fabric import list_datasets
    list_datasets(workspace=workspace)


@fabric.command("refresh")
@click.argument("dataset_name")
@click.option("--workspace", "-w", default=None)
@click.option("--wait", is_flag=True, help="Wait for refresh to complete")
def fabric_refresh(dataset_name, workspace, wait):
    """Trigger a dataset refresh in Power BI Service / Fabric."""
    from powerbi_agent.fabric import trigger_refresh
    trigger_refresh(dataset_name=dataset_name, workspace=workspace, wait=wait)


# ─── skills ───────────────────────────────────────────────────────────────────

@main.group()
def skills():
    """Manage Claude Code skill integrations."""


@skills.command("install")
@click.option("--force", is_flag=True, help="Overwrite existing skills")
def skills_install(force):
    """Register powerbi-agent skills with Claude Code.

    Copies skill files into ~/.claude/skills/ and updates ~/.claude/CLAUDE.md.
    """
    from powerbi_agent.skills.installer import install_skills
    install_skills(force=force)


@skills.command("uninstall")
def skills_uninstall():
    """Remove powerbi-agent skills from Claude Code."""
    from powerbi_agent.skills.installer import uninstall_skills
    uninstall_skills()


@skills.command("list")
def skills_list():
    """List all available powerbi-agent skills."""
    from powerbi_agent.skills.installer import list_skills
    list_skills()


# ─── doctor ───────────────────────────────────────────────────────────────────

@main.command()
def doctor():
    """Check your environment and diagnose common issues."""
    from powerbi_agent.doctor import run_checks
    run_checks()


if __name__ == "__main__":
    main()
