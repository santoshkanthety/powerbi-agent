"""Pipeline & Fabric workflow configuration routes."""
from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from powerbi_agent.web import storage
from powerbi_agent.web.models.config import FabricConfig

router    = APIRouter()
templates: Jinja2Templates = None


@router.get("/", response_class=HTMLResponse)
async def pipeline_page(request: Request, project: str = "default"):
    cfg = storage.load_project(project)
    return templates.TemplateResponse("pipeline.html", {
        "request": request, "cfg": cfg, "project": project, "page": "pipeline",
    })


@router.post("/save-fabric")
async def save_fabric(
    project:                  str  = Form("default"),
    workspace_name:           str  = Form(""),
    lakehouse_name:           str  = Form(""),
    semantic_model_name:      str  = Form(""),
    enable_directlake:        bool = Form(True),
    refresh_schedule:         str  = Form("0 6 * * *"),
    enable_incremental_refresh: bool = Form(True),
    rolling_window_years:     int  = Form(3),
    incremental_days:         int  = Form(7),
):
    fabric = FabricConfig(
        workspace_name=workspace_name,
        lakehouse_name=lakehouse_name,
        semantic_model_name=semantic_model_name,
        enable_directlake=enable_directlake,
        refresh_schedule=refresh_schedule,
        enable_incremental_refresh=enable_incremental_refresh,
        rolling_window_years=rolling_window_years,
        incremental_days=incremental_days,
    )
    storage.update_fabric_config(fabric, project)
    return RedirectResponse(url=f"/pipeline/?project={project}&saved=1", status_code=303)
