"""Persist project config as JSON in the user's home directory."""
from __future__ import annotations

import uuid
from pathlib import Path

from powerbi_agent.web.models.config import DataSource, ProjectConfig, Rule

CONFIG_DIR = Path.home() / ".powerbi-agent" / "projects"


def _config_path(project: str) -> Path:
    return CONFIG_DIR / f"{project}.json"


def list_projects() -> list[str]:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return [p.stem for p in CONFIG_DIR.glob("*.json")]


def load_project(name: str = "default") -> ProjectConfig:
    path = _config_path(name)
    if not path.exists():
        cfg = ProjectConfig(project_name=name)
        save_project(cfg, name)
        return cfg
    return ProjectConfig.model_validate_json(path.read_text(encoding="utf-8"))


def save_project(config: ProjectConfig, name: str = "default") -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _config_path(name).write_text(
        config.model_dump_json(indent=2), encoding="utf-8"
    )


def add_source(source: DataSource, project: str = "default") -> DataSource:
    cfg = load_project(project)
    source.id = source.id or str(uuid.uuid4())[:8]
    cfg.sources = [s for s in cfg.sources if s.id != source.id]
    cfg.sources.append(source)
    save_project(cfg, project)
    return source


def delete_source(source_id: str, project: str = "default") -> None:
    cfg = load_project(project)
    cfg.sources = [s for s in cfg.sources if s.id != source_id]
    save_project(cfg, project)


def add_rule(rule: Rule, project: str = "default") -> Rule:
    cfg = load_project(project)
    rule.id = rule.id or str(uuid.uuid4())[:8]
    cfg.rules = [r for r in cfg.rules if r.id != rule.id]
    cfg.rules.append(rule)
    save_project(cfg, project)
    return rule


def delete_rule(rule_id: str, project: str = "default") -> None:
    cfg = load_project(project)
    cfg.rules = [r for r in cfg.rules if r.id != rule_id]
    save_project(cfg, project)


def update_fabric_config(fabric_cfg, project: str = "default") -> None:
    cfg = load_project(project)
    cfg.fabric = fabric_cfg
    save_project(cfg, project)
