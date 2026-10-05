"""Tests for the Fabric Apps (Rayfin) integration.

These cover the parts powerbi-agent owns — project detection, deployment-file
parsing, name resolution, and the guard rails on destructive deploys. The Rayfin
CLI itself is never invoked: it is version-locked and remote, so every test that
would shell out patches the runner instead.
"""

from __future__ import annotations

import json

import pytest
from click.testing import CliRunner

from powerbi_agent import fabricapp
from powerbi_agent.cli import main

# ── project detection ─────────────────────────────────────────────────────────


def test_find_project_detects_rayfin_yml(tmp_path):
    (tmp_path / "rayfin").mkdir()
    (tmp_path / "rayfin" / "rayfin.yml").write_text("name: demo\n")
    assert fabricapp.find_project(tmp_path) == tmp_path.resolve()


def test_find_project_detects_package_dependency(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps({"dependencies": {"@microsoft/rayfin-client": "^1.0.0"}})
    )
    assert fabricapp.find_project(tmp_path) == tmp_path.resolve()


def test_find_project_detects_dev_dependency(tmp_path):
    (tmp_path / "package.json").write_text(
        json.dumps({"devDependencies": {"@microsoft/rayfin-cli": "latest"}})
    )
    assert fabricapp.find_project(tmp_path) == tmp_path.resolve()


def test_find_project_walks_up_from_subdirectory(tmp_path):
    (tmp_path / "rayfin").mkdir()
    (tmp_path / "rayfin" / "rayfin.yml").write_text("name: demo\n")
    nested = tmp_path / "src" / "components"
    nested.mkdir(parents=True)
    assert fabricapp.find_project(nested) == tmp_path.resolve()


def test_find_project_returns_none_for_unrelated_directory(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({"dependencies": {"react": "^18"}}))
    assert fabricapp.find_project(tmp_path) is None


def test_find_project_tolerates_malformed_package_json(tmp_path):
    (tmp_path / "package.json").write_text("{ not json")
    assert fabricapp.find_project(tmp_path) is None


def test_require_project_raises_with_actionable_message(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(fabricapp.FabricAppError) as exc:
        fabricapp.require_project()
    assert "fabric-app new" in str(exc.value)


# ── .deployments.json ─────────────────────────────────────────────────────────


def _write_deployments(root, payload):
    (root / "rayfin").mkdir(exist_ok=True)
    (root / "rayfin" / ".deployments.json").write_text(json.dumps(payload))


def test_read_deployments_sorts_newest_first(tmp_path):
    _write_deployments(tmp_path, {
        "deployments": {
            "old": {"fabricItemId": "a", "deployedAt": "2026-01-01T00:00:00Z"},
            "new": {"fabricItemId": "b", "deployedAt": "2026-09-01T00:00:00Z"},
        }
    })
    got = fabricapp._read_deployments(tmp_path)
    assert [d["fabricItemId"] for d in got] == ["b", "a"]


def test_read_deployments_missing_file_is_empty(tmp_path):
    assert fabricapp._read_deployments(tmp_path) == []


def test_read_deployments_invalid_json_is_empty_not_fatal(tmp_path):
    (tmp_path / "rayfin").mkdir()
    (tmp_path / "rayfin" / ".deployments.json").write_text("{{{")
    assert fabricapp._read_deployments(tmp_path) == []


def test_read_deployments_ignores_non_string_fields(tmp_path):
    _write_deployments(tmp_path, {
        "deployments": {"a": {"fabricItemId": "x", "hostingUrl": 42, "deployedAt": "2026-01-01"}}
    })
    entry = fabricapp._read_deployments(tmp_path)[0]
    assert entry["fabricItemId"] == "x"
    assert "hostingUrl" not in entry


def test_read_deployments_ignores_non_object_entries(tmp_path):
    _write_deployments(tmp_path, {"deployments": {"a": "not-an-object"}})
    assert fabricapp._read_deployments(tmp_path) == []


# ── project name ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "line,expected",
    [
        ("name: sales-explorer\n", "sales-explorer"),
        ('name: "Sales Explorer"\n', "Sales Explorer"),
        ("name: 'quoted'\n", "quoted"),
        ("name: demo  # trailing comment\n", "demo"),
    ],
)
def test_project_name_from_rayfin_yml(tmp_path, line, expected):
    (tmp_path / "rayfin").mkdir()
    (tmp_path / "rayfin" / "rayfin.yml").write_text(line)
    assert fabricapp._project_name(tmp_path) == expected


def test_project_name_falls_back_to_directory(tmp_path):
    (tmp_path / "rayfin").mkdir()
    (tmp_path / "rayfin" / "rayfin.yml").write_text("services: []\n")
    assert fabricapp._project_name(tmp_path) == tmp_path.name


# ── guard rails ───────────────────────────────────────────────────────────────


def test_deploy_force_without_yes_is_refused(tmp_path, monkeypatch):
    (tmp_path / "rayfin").mkdir()
    (tmp_path / "rayfin" / "rayfin.yml").write_text("name: demo\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(fabricapp, "rayfin", lambda *a, **k: pytest.fail("must not deploy"))

    with pytest.raises(fabricapp.FabricAppError) as exc:
        fabricapp.deploy(workspace_id=None, dry_run=False, force=True, yes=False, extra=())
    assert "DESTRUCTIVE" in str(exc.value)


def test_new_app_refuses_to_nest_inside_existing_project(tmp_path, monkeypatch):
    (tmp_path / "rayfin").mkdir()
    (tmp_path / "rayfin" / "rayfin.yml").write_text("name: outer\n")
    monkeypatch.setattr(fabricapp, "require_node", lambda: None)
    monkeypatch.setattr(fabricapp, "_run", lambda *a, **k: pytest.fail("must not scaffold"))

    with pytest.raises(fabricapp.FabricAppError) as exc:
        fabricapp.new_app(name="inner", template="dataapp", workspace=None,
                          directory=str(tmp_path))
    assert "nest" in str(exc.value).lower()


def test_init_requires_project_name(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(fabricapp, "rayfin", lambda *a, **k: pytest.fail("must not run"))
    with pytest.raises(fabricapp.FabricAppError) as exc:
        fabricapp.init_app(name=None, directory=None, list_templates=False)
    assert "--project-name" in str(exc.value)


def test_deploy_dry_run_passes_verbose(tmp_path, monkeypatch):
    (tmp_path / "rayfin").mkdir()
    (tmp_path / "rayfin" / "rayfin.yml").write_text("name: demo\n")
    monkeypatch.chdir(tmp_path)
    seen: list[list[str]] = []
    monkeypatch.setattr(fabricapp, "rayfin", lambda args, cwd=None: seen.append(args) or 0)

    fabricapp.deploy(workspace_id="ws-1", dry_run=True, force=False, yes=False, extra=())
    assert seen == [["up", "--workspace-id", "ws-1", "--dry-run", "--verbose"]]


def test_require_node_rejects_old_major(monkeypatch):
    monkeypatch.setattr(fabricapp, "_node_version", lambda: (18, "v18.20.0"))
    with pytest.raises(fabricapp.FabricAppError) as exc:
        fabricapp.require_node()
    assert "too old" in str(exc.value)


def test_require_node_reports_missing_node(monkeypatch):
    monkeypatch.setattr(fabricapp, "_node_version", lambda: None)
    with pytest.raises(fabricapp.FabricAppError) as exc:
        fabricapp.require_node()
    assert "Node.js is required" in str(exc.value)


# ── CLI wiring ────────────────────────────────────────────────────────────────


def test_cli_exposes_fabric_app_group():
    result = CliRunner().invoke(main, ["fabric-app", "--help"])
    assert result.exit_code == 0
    for cmd in ("new", "init", "templates", "dev", "deploy", "status",
                "connector", "ai-files", "login", "doctor"):
        assert cmd in result.output


def test_cli_fabric_app_deploy_help_documents_force_gate():
    result = CliRunner().invoke(main, ["fabric-app", "deploy", "--help"])
    assert result.exit_code == 0
    assert "DESTRUCTIVE" in result.output
    assert "--yes" in result.output


def test_cli_fabric_app_new_defaults_to_dataapp_template():
    result = CliRunner().invoke(main, ["fabric-app", "new", "--help"])
    assert result.exit_code == 0
    assert "dataapp" in result.output
