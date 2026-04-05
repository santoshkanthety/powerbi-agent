"""JSON API routes for dynamic UI interactions."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from powerbi_agent.web import storage

router = APIRouter()


@router.get("/config/{project}")
async def get_config(project: str = "default"):
    cfg = storage.load_project(project)
    return JSONResponse(cfg.model_dump())


@router.get("/projects")
async def get_projects():
    return {"projects": storage.list_projects()}


@router.get("/stats/{project}")
async def get_stats(project: str = "default"):
    cfg = storage.load_project(project)
    return {
        "sources": len(cfg.sources),
        "sources_enabled": sum(1 for s in cfg.sources if s.enabled),
        "rules": len(cfg.rules),
        "rules_enabled": sum(1 for r in cfg.rules if r.enabled),
        "tables": len(cfg.tables),
        "bronze_tables": sum(1 for t in cfg.tables if t.layer == "bronze"),
        "silver_tables": sum(1 for t in cfg.tables if t.layer == "silver"),
        "gold_tables":   sum(1 for t in cfg.tables if t.layer == "gold"),
    }
