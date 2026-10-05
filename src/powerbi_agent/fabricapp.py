"""
Microsoft Fabric Apps (Rayfin SDK) integration.

Thin, explicit wrapper over the Rayfin CLI (`@microsoft/rayfin-cli`) — the CLI that
scaffolds, runs and deploys Fabric Apps. We deliberately do NOT reimplement any part
of Rayfin: the SDK surface is version-locked per project and moves fast in preview, so
every operation shells out to the installed CLI and the output is passed through.

What this module adds over calling `npx rayfin` by hand:

  * environment verification (Node, npx, project detection) with actionable messages
  * project state read from rayfin/rayfin.yml and rayfin/.deployments.json, so Claude
    and the user can see where an app is deployed without hunting for GUIDs
  * non-interactive-safe invocation, because an agent's stdin is not a TTY
  * a confirmation gate on destructive deploys (`rayfin up --force`)

See the `powerbi-fabric-apps` and `powerbi-fabric-app-templates` skills for the
workflow, and Microsoft's CLI reference for the authoritative command surface:
https://learn.microsoft.com/fabric/apps/cli-reference
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from powerbi_agent.errors import PowerBIAgentError

console = Console()

# Pinned package specs. npx resolves these on demand; pinning the package (not the
# version) keeps us on the current preview while still being explicit about what runs.
RAYFIN_CLI_PKG = "@microsoft/rayfin-cli@latest"
CREATE_RAYFIN_PKG = "@microsoft/create-rayfin@latest"

MIN_NODE_MAJOR = 20

# Relative to the project root.
RAYFIN_CONFIG = Path("rayfin") / "rayfin.yml"
RAYFIN_DEPLOYMENTS = Path("rayfin") / ".deployments.json"
RAYFIN_SKILL = Path(".agents") / "skills" / "rayfin" / "SKILL.md"


class FabricAppError(PowerBIAgentError):
    """Raised when a Fabric App / Rayfin operation cannot proceed."""


# ── environment ───────────────────────────────────────────────────────────────


def _which(name: str) -> str | None:
    return shutil.which(name)


def _node_version() -> tuple[int, str] | None:
    """Return (major, raw) for the installed Node, or None if Node is absent."""
    node = _which("node")
    if not node:
        return None
    try:
        raw = subprocess.run(
            [node, "--version"], capture_output=True, text=True, timeout=30, check=True
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return None
    major = raw.lstrip("v").split(".")[0]
    return (int(major) if major.isdigit() else 0, raw)


def require_node() -> None:
    """Fail with an actionable message unless Node >= MIN_NODE_MAJOR and npx are present."""
    ver = _node_version()
    if ver is None:
        raise FabricAppError(
            "Node.js is required for Fabric Apps (the Rayfin CLI is a Node package).\n"
            f"Install Node.js {MIN_NODE_MAJOR} or later: https://nodejs.org/\n"
            "  winget install OpenJS.NodeJS.LTS   (Windows)\n"
            "  brew install node                  (macOS)"
        )
    major, raw = ver
    if major < MIN_NODE_MAJOR:
        raise FabricAppError(
            f"Node.js {raw} is too old for Fabric Apps — {MIN_NODE_MAJOR} or later is required.\n"
            "Upgrade Node.js: https://nodejs.org/"
        )
    if not _which("npx"):
        raise FabricAppError(
            "npx was not found even though Node.js is installed. "
            "Reinstall Node.js so npm/npx land on PATH."
        )


# ── project detection ─────────────────────────────────────────────────────────


def _depends_on_rayfin(root: Path) -> bool:
    pkg = root / "package.json"
    if not pkg.is_file():
        return False
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    for key in ("dependencies", "devDependencies"):
        for name in (data.get(key) or {}):
            if name.startswith("@microsoft/rayfin"):
                return True
    return False


def find_project(start: Path | None = None) -> Path | None:
    """Walk up from `start` to the filesystem root looking for a Rayfin project.

    A directory is a Rayfin project when it holds rayfin/rayfin.yml, or a package.json
    depending on any @microsoft/rayfin-* package. Returns the project root, or None.
    """
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / RAYFIN_CONFIG).is_file() or _depends_on_rayfin(candidate):
            return candidate
    return None


def require_project(start: Path | None = None) -> Path:
    root = find_project(start)
    if root is None:
        raise FabricAppError(
            "Not inside a Fabric App (Rayfin) project — no rayfin/rayfin.yml and no "
            "@microsoft/rayfin-* dependency found in this directory or any parent.\n"
            "Create one:   pbi-agent fabric-app new <app-name>\n"
            "Or add Rayfin here:   pbi-agent fabric-app init"
        )
    return root


def _read_deployments(root: Path) -> list[dict]:
    """Parse rayfin/.deployments.json into a list of deployment dicts, newest first."""
    path = root / RAYFIN_DEPLOYMENTS
    if not path.is_file():
        return []
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        console.print(f"[yellow]![/yellow] {RAYFIN_DEPLOYMENTS} is not valid JSON: {exc}")
        return []
    raw = parsed.get("deployments") if isinstance(parsed, dict) else None
    if not isinstance(raw, dict):
        return []
    out = []
    for key, value in raw.items():
        if isinstance(value, dict):
            out.append({"key": key, **{k: v for k, v in value.items() if isinstance(v, str)}})
    out.sort(key=lambda d: d.get("deployedAt", ""), reverse=True)
    return out


def _project_name(root: Path) -> str:
    """The app name from rayfin.yml's top-level `name:`, falling back to the dir name."""
    path = root / RAYFIN_CONFIG
    if path.is_file():
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("name:"):
                    value = line.split(":", 1)[1].strip()
                    # Strip a trailing comment, then surrounding quotes.
                    if not value.startswith(("'", '"')):
                        value = value.split("#", 1)[0].strip()
                    return value.strip("'\"") or root.name
        except OSError:
            pass
    return root.name


# ── invocation ────────────────────────────────────────────────────────────────


def _run(args: list[str], cwd: Path | None = None) -> int:
    """Run a command, streaming its output through. Returns the exit code.

    Output is NOT captured: the Rayfin CLI's own progress and error text is the most
    useful thing on screen, and re-rendering it would only lose detail.
    """
    console.print(f"[dim]$ {' '.join(args)}[/dim]")
    env = dict(os.environ)
    # An agent's stdin is not a TTY; make sure the CLI and npm know not to prompt.
    env.setdefault("CI", "1")
    try:
        return subprocess.run(args, cwd=str(cwd) if cwd else None, env=env, check=False).returncode
    except FileNotFoundError as exc:
        raise FabricAppError(f"Could not execute {args[0]!r}: {exc}") from exc
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted.[/yellow]")
        return 130


def rayfin(args: list[str], cwd: Path | None = None) -> int:
    """Invoke the Rayfin CLI via npx with the package pinned explicitly."""
    require_node()
    return _run(["npx", "-y", "-p", RAYFIN_CLI_PKG, "rayfin", *args], cwd=cwd)


def _fail_on(code: int, what: str) -> None:
    if code != 0:
        raise FabricAppError(f"{what} failed (exit code {code}). See the output above.")


# ── commands ──────────────────────────────────────────────────────────────────


def new_app(name: str, template: str, workspace: str | None, directory: str | None) -> None:
    """Scaffold a new Fabric App from a Rayfin template.

    `create-rayfin` creates a child directory named from a slugified project name, so
    the caller ends up with <cwd>/<slug>/ and must cd into it.
    """
    require_node()
    target = Path(directory).resolve() if directory else Path.cwd()
    if not target.is_dir():
        raise FabricAppError(f"Directory does not exist: {target}")

    existing = find_project(target)
    if existing is not None:
        raise FabricAppError(
            f"{target} is already inside a Rayfin project ({existing}).\n"
            "Never nest one Fabric App inside another. Work in place, or pick another directory."
        )

    args = ["npx", "-y", CREATE_RAYFIN_PKG, "--project-name", name, "--template", template]
    if workspace:
        args += ["--workspace", workspace]

    code = _run(args, cwd=target)
    _fail_on(code, "Scaffolding the Fabric App")

    console.print(
        Panel(
            f"Scaffolded with the [bold]{template}[/bold] template.\n\n"
            "[bold]Next:[/bold]\n"
            "  1. cd into the new project directory\n"
            "  2. Read AGENTS.md, then .agents/skills/rayfin/SKILL.md — that in-project\n"
            "     skill is version-locked and authoritative for every Rayfin API\n"
            "  3. pbi-agent fabric-app status\n"
            "  4. pbi-agent fabric-app dev",
            title=f"Fabric App · {name}",
            border_style="green",
        )
    )


def init_app(name: str | None, directory: str | None, list_templates: bool) -> None:
    """Add Rayfin to the current (or given) directory, or list available templates."""
    if list_templates:
        _fail_on(rayfin(["init", "--list-templates"]), "Listing templates")
        return

    target = Path(directory).resolve() if directory else Path.cwd()
    existing = find_project(target)
    if existing is not None:
        raise FabricAppError(
            f"{existing} is already a Rayfin project.\n"
            "Nothing to initialise — read .agents/skills/rayfin/SKILL.md and continue in place."
        )

    args = ["init", str(target)]
    if name:
        args += ["--project-name", name]
    else:
        raise FabricAppError(
            "--project-name is required: rayfin init cannot prompt for it in a "
            "non-interactive session.\n"
            "Run: pbi-agent fabric-app init --name <app-name>"
        )
    _fail_on(rayfin(args), "Initialising Rayfin in this directory")


def templates() -> None:
    """List the templates the installed Rayfin CLI can scaffold from."""
    _fail_on(rayfin(["init", "--list-templates"]), "Listing templates")
    console.print(
        "\n[dim]Community gallery (not Microsoft-supported — review before building on one):\n"
        "  https://github.com/microsoft/awesome-rayfin\n"
        "For a Power BI semantic model app, use the [/dim][bold]dataapp[/bold][dim] template.[/dim]"
    )


def dev(extra: tuple[str, ...]) -> None:
    """Run the app locally."""
    root = require_project()
    _fail_on(rayfin(["dev", *extra], cwd=root), "rayfin dev")


def deploy(workspace_id: str | None, dry_run: bool, force: bool, yes: bool,
           extra: tuple[str, ...]) -> None:
    """Deploy the app to Fabric with `rayfin up`.

    --force allows destructive data-schema changes, so it is gated behind an explicit
    confirmation unless --yes is also passed.
    """
    root = require_project()
    name = _project_name(root)

    if force and not yes:
        raise FabricAppError(
            f"--force allows DESTRUCTIVE data-schema changes to '{name}' — tables or "
            "columns can be dropped and their data lost.\n"
            "Re-run with --yes only after confirming with the user which entities change, "
            "and never to clear an error you have not diagnosed."
        )

    args = ["up"]
    if workspace_id:
        args += ["--workspace-id", workspace_id]
    if dry_run:
        args += ["--dry-run", "--verbose"]
    if force:
        args.append("--force")
    if yes:
        args.append("--yes")
    args += list(extra)

    code = rayfin(args, cwd=root)
    _fail_on(code, "rayfin up")

    if not dry_run:
        console.print()
        status(json_out=False)


def status(json_out: bool) -> None:
    """Show local project state plus the remote deployment status."""
    root = require_project()
    name = _project_name(root)
    deployments = _read_deployments(root)

    if json_out:
        console.print_json(
            data={
                "project": name,
                "root": str(root),
                "config": (root / RAYFIN_CONFIG).is_file(),
                "inProjectSkill": (root / RAYFIN_SKILL).is_file(),
                "deployments": deployments,
            }
        )
    else:
        table = Table(title=f"Fabric App · {name}", border_style="blue")
        table.add_column("Property", style="cyan")
        table.add_column("Value")
        table.add_row("Project root", str(root))
        table.add_row("rayfin.yml", "✓" if (root / RAYFIN_CONFIG).is_file() else "—")
        table.add_row(
            "In-project skill",
            "✓ .agents/skills/rayfin/SKILL.md" if (root / RAYFIN_SKILL).is_file()
            else "— run: pbi-agent fabric-app ai-files",
        )
        if deployments:
            latest = deployments[0]
            table.add_row("Workspace ID", latest.get("fabricWorkspaceId", "—"))
            table.add_row("Item ID", latest.get("fabricItemId", "—"))
            table.add_row("Hosting URL", latest.get("hostingUrl", "—"))
            table.add_row("Portal", latest.get("fabricDeepLink", "—"))
            table.add_row("Deployed at", latest.get("deployedAt", "—"))
            table.add_row("Recorded deployments", str(len(deployments)))
        else:
            table.add_row("Deployments", "— none recorded (not yet deployed)")
        console.print(table)

    # The remote view. A failure here is informational, not fatal: the local state above
    # is still useful when the user is offline or not signed in.
    code = rayfin(["up", "status", *(["--json"] if json_out else [])], cwd=root)
    if code != 0:
        console.print(
            "[yellow]![/yellow] Could not read the remote deployment status. "
            "Check sign-in with: pbi-agent fabric-app login"
        )


def connectors(action: str, extra: tuple[str, ...]) -> None:
    """Pass through to `rayfin connector <action>` inside the project."""
    root = require_project()
    _fail_on(rayfin(["connector", action, *extra], cwd=root), f"rayfin connector {action}")


def ai_files(check: bool, force: bool) -> None:
    """Install, refresh or check the Rayfin agent context files.

    These are AGENTS.md, .mcp.json and .agents/skills/rayfin/SKILL.md — the last being
    the version-locked skill that is authoritative over any Rayfin guidance we ship.
    """
    root = require_project()
    if check:
        _fail_on(rayfin(["init", "ai-files", "status"], cwd=root), "rayfin init ai-files status")
        return
    args = ["init", "ai-files", "install", "--yes"]
    if force:
        args += ["--force"]
    _fail_on(rayfin(args, cwd=root), "rayfin init ai-files install")


def login(status_only: bool, tenant: str | None) -> None:
    """Sign in to the Rayfin platform, or report the current sign-in state."""
    if status_only:
        _fail_on(rayfin(["login", "status"]), "rayfin login status")
        return
    args = ["login"]
    if tenant:
        args += ["--tenant", tenant]
    _fail_on(rayfin(args), "rayfin login")


def doctor() -> None:
    """Check everything needed to build and deploy a Fabric App."""
    rows: list[tuple[str, str, str]] = []

    ver = _node_version()
    if ver is None:
        rows.append(("Node.js", "FAIL", f"Not found — install Node.js {MIN_NODE_MAJOR}+"))
    elif ver[0] < MIN_NODE_MAJOR:
        rows.append(("Node.js", "FAIL", f"{ver[1]} — need {MIN_NODE_MAJOR}+"))
    else:
        rows.append(("Node.js", "OK", ver[1]))

    rows.append(("npx", "OK", _which("npx") or "") if _which("npx")
                else ("npx", "FAIL", "Not on PATH — reinstall Node.js"))

    root = find_project()
    if root is None:
        rows.append(("Rayfin project", "--", "Not in one — pbi-agent fabric-app new <name>"))
    else:
        rows.append(("Rayfin project", "OK", str(root)))
        rows.append(
            ("In-project skill", "OK", str(RAYFIN_SKILL)) if (root / RAYFIN_SKILL).is_file()
            else ("In-project skill", "WARN", "Missing — pbi-agent fabric-app ai-files")
        )
        deployments = _read_deployments(root)
        rows.append(
            ("Deployment", "OK", f"{len(deployments)} recorded, latest "
             f"{deployments[0].get('deployedAt', '?')}") if deployments
            else ("Deployment", "--", "None recorded")
        )

    table = Table(title="Fabric App environment", border_style="blue")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Detail", style="dim")
    styles = {"OK": "[green]OK[/green]", "FAIL": "[red]FAIL[/red]", "WARN": "[yellow]WARN[/yellow]"}
    for check, state, detail in rows:
        table.add_row(check, styles.get(state, f"[dim]{state}[/dim]"), detail)
    console.print(table)

    if any(state == "FAIL" for _, state, _ in rows):
        console.print(
            "\n[yellow]Fabric Apps also needs, and this cannot be checked locally:[/yellow]\n"
            "  • the [bold]Fabric Apps (preview)[/bold] tenant setting enabled\n"
            "  • a workspace on Fabric capacity, in a supported region\n"
            "  • Contributor / Member / Admin on that workspace"
        )
