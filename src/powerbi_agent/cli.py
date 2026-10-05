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


# ─── visual ───────────────────────────────────────────────────────────────────

@main.group()
@click.option("--path", "-p", default=None,
              help="Path to .Report folder (auto-detected from CWD if omitted).")
@click.pass_context
def visual(ctx, path):
    """Manage custom visuals (.pbiviz) in PBIR reports."""
    ctx.ensure_object(dict)
    ctx.obj["report_path"] = path


@visual.command("import-custom")
@click.argument("pbiviz_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--replace", is_flag=True, default=False,
              help="Overwrite an existing custom visual with the same GUID.")
@click.pass_context
def visual_import_custom(ctx, pbiviz_file, replace):
    """Import a locally-built .pbiviz into the report.

    \b
    Examples:
        pbi-agent visual import-custom dist/myvisual.pbiviz
        pbi-agent visual import-custom dist/myvisual.pbiviz --replace
    """
    from powerbi_agent.visual import cli_import_custom
    cli_import_custom(ctx.obj.get("report_path"), pbiviz_file, replace)


@visual.command("list-custom")
@click.pass_context
def visual_list_custom(ctx):
    """List embedded and public custom visuals registered in the report."""
    from powerbi_agent.visual import cli_list_custom
    cli_list_custom(ctx.obj.get("report_path"))


@visual.command("remove-custom")
@click.argument("identifier")
@click.pass_context
def visual_remove_custom(ctx, identifier):
    """Remove an embedded custom visual by GUID or friendly name."""
    from powerbi_agent.visual import cli_remove_custom
    cli_remove_custom(ctx.obj.get("report_path"), identifier)


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


# ─── fabric-app ───────────────────────────────────────────────────────────────

@main.group("fabric-app")
def fabric_app():
    """Fabric Apps via the Rayfin SDK — scaffold, run, deploy, connect to a model.

    \b
    Wraps the Rayfin CLI (@microsoft/rayfin-cli); requires Node.js 20+.
    Rayfin's own API surface is version-locked per project: after scaffolding,
    read .agents/skills/rayfin/SKILL.md before writing app code.
    """


@fabric_app.command("new")
@click.argument("name")
@click.option("--template", default="dataapp", show_default=True,
              help="Rayfin template. 'dataapp' for an app over a Power BI semantic model; "
                   "'blankapp' for auth and nothing else.")
@click.option("--workspace", "-w", default=None, help="Target Fabric workspace name")
@click.option("--directory", "-C", default=None, help="Parent directory (default: cwd)")
def fabric_app_new(name, template, workspace, directory):
    """Scaffold a new Fabric App from a Rayfin template.

    \b
    Examples:
        pbi-agent fabric-app new sales-explorer -w "Analytics"
        pbi-agent fabric-app new scratch-app --template blankapp
    """
    from powerbi_agent.fabricapp import new_app
    new_app(name=name, template=template, workspace=workspace, directory=directory)


@fabric_app.command("init")
@click.option("--name", default=None, help="Project name (required to initialise)")
@click.option("--directory", "-C", default=None, help="Directory to initialise (default: cwd)")
@click.option("--list-templates", is_flag=True, help="List available templates and exit")
def fabric_app_init(name, directory, list_templates):
    """Add Rayfin to a directory that already has source code."""
    from powerbi_agent.fabricapp import init_app
    init_app(name=name, directory=directory, list_templates=list_templates)


@fabric_app.command("templates")
def fabric_app_templates():
    """List the templates the installed Rayfin CLI can scaffold from."""
    from powerbi_agent.fabricapp import templates
    templates()


@fabric_app.command("dev", context_settings={"ignore_unknown_options": True})
@click.argument("extra", nargs=-1, type=click.UNPROCESSED)
def fabric_app_dev(extra):
    """Run the app and its Functions locally. Extra args pass through to `rayfin dev`."""
    from powerbi_agent.fabricapp import dev
    dev(extra=extra)


@fabric_app.command("deploy", context_settings={"ignore_unknown_options": True})
@click.option("--workspace-id", default=None, help="Target Fabric workspace ID")
@click.option("--dry-run", is_flag=True, help="Validate and resolve the workspace; deploy nothing")
@click.option("--force", is_flag=True,
              help="Allow DESTRUCTIVE data-schema changes. Requires --yes.")
@click.option("--yes", is_flag=True, help="Accept confirmations non-interactively")
@click.argument("extra", nargs=-1, type=click.UNPROCESSED)
def fabric_app_deploy(workspace_id, dry_run, force, yes, extra):
    """Deploy the app to Fabric (`rayfin up`).

    \b
    Examples:
        pbi-agent fabric-app deploy --dry-run
        pbi-agent fabric-app deploy --workspace-id <guid> --yes
        pbi-agent fabric-app deploy -- --exclude-services functions
    """
    from powerbi_agent.fabricapp import deploy
    deploy(workspace_id=workspace_id, dry_run=dry_run, force=force, yes=yes, extra=extra)


@fabric_app.command("status")
@click.option("--json", "json_out", is_flag=True, help="Emit JSON")
def fabric_app_status(json_out):
    """Show local project state and the recorded Fabric deployment."""
    from powerbi_agent.fabricapp import status
    status(json_out=json_out)


@fabric_app.command("connector", context_settings={"ignore_unknown_options": True})
@click.argument("action", type=click.Choice(
    ["types", "search", "add", "list", "inspect", "invoke", "remove"]))
@click.argument("extra", nargs=-1, type=click.UNPROCESSED)
def fabric_app_connector(action, extra):
    """Manage Fabric data connectors, including fabric-semanticmodel.

    \b
    Examples:
        pbi-agent fabric-app connector types -- -v
        pbi-agent fabric-app connector search -- --type fabric-semanticmodel --json
        pbi-agent fabric-app connector add -- --type fabric-semanticmodel \\
            --workspace-id <ws> --item-id <model> --name salesModel --operations executeQuery
        pbi-agent fabric-app connector inspect -- --name salesModel --entity Sales
    """
    from powerbi_agent.fabricapp import connectors
    connectors(action=action, extra=extra)


@fabric_app.command("ai-files")
@click.option("--check", is_flag=True, help="Report file state instead of installing")
@click.option("--force", is_flag=True, help="Overwrite modified managed items (never AGENTS.md)")
def fabric_app_ai_files(check, force):
    """Install or check the Rayfin agent context files (incl. the version-locked skill)."""
    from powerbi_agent.fabricapp import ai_files
    ai_files(check=check, force=force)


@fabric_app.command("login")
@click.option("--status", "status_only", is_flag=True, help="Report sign-in state only")
@click.option("--tenant", default=None, help="Microsoft Entra tenant ID")
def fabric_app_login(status_only, tenant):
    """Sign in to the Rayfin platform."""
    from powerbi_agent.fabricapp import login
    login(status_only=status_only, tenant=tenant)


@fabric_app.command("doctor")
def fabric_app_doctor():
    """Check Node, the Rayfin CLI, and the current project's deployment state."""
    from powerbi_agent.fabricapp import doctor
    doctor()


# ─── skills ───────────────────────────────────────────────────────────────────

@main.group()
def skills():
    """Manage Claude Code skill integrations."""


@skills.command("install")
@click.option("--force", is_flag=True, help="Overwrite existing skills")
def skills_install(force):
    """Register powerbi-agent skills with Claude Code.

    Copies each skill into ~/.claude/skills/<skill-name>/SKILL.md.
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
