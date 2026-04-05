"""
FastAPI web application — powerbi-agent Configuration Tool.
Launch with: pbi-agent ui
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from powerbi_agent.web.routes import api, model_designer, pipeline, rules, sources

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR    = Path(__file__).parent / "static"

app = FastAPI(title="powerbi-agent", docs_url=None, redoc_url=None)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Inject templates into routers that need them
sources.templates        = templates
rules.templates          = templates
model_designer.templates = templates
pipeline.templates       = templates

app.include_router(sources.router,        prefix="/sources")
app.include_router(rules.router,          prefix="/rules")
app.include_router(model_designer.router, prefix="/model")
app.include_router(pipeline.router,       prefix="/pipeline")
app.include_router(api.router,            prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    from powerbi_agent.web.storage import list_projects, load_project
    projects = list_projects()
    cfg = load_project("default")
    return templates.TemplateResponse("index.html", {
        "request":  request,
        "cfg":      cfg,
        "projects": projects,
        "page":     "dashboard",
    })


@app.get("/health")
async def health():
    return {"status": "ok", "app": "powerbi-agent"}
