"""Source connector CRUD routes."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from powerbi_agent.web import storage
from powerbi_agent.web.models.config import (
    APISourceConfig,
    AuthType,
    CSVSourceConfig,
    DatabaseDialect,
    DatabaseSourceConfig,
    DataSource,
    LoadStrategy,
    SourceType,
    WebscrapeSourceConfig,
)

router    = APIRouter()
templates: Jinja2Templates = None  # injected by app.py


@router.get("/", response_class=HTMLResponse)
async def list_sources(request: Request, project: str = "default"):
    cfg = storage.load_project(project)
    return templates.TemplateResponse("sources.html", {
        "request": request, "cfg": cfg, "project": project, "page": "sources",
        "source_types": list(SourceType), "dialects": list(DatabaseDialect),
        "auth_types": list(AuthType), "load_strategies": list(LoadStrategy),
    })


@router.post("/add", response_class=HTMLResponse)
async def add_source(
    request: Request,
    project:     str = Form("default"),
    name:        str = Form(...),
    description: str = Form(""),
    source_type: str = Form(...),
    target_table: str = Form(""),
    # DB fields
    dialect:           str = Form("sqlserver"),
    host:              str = Form(""),
    port:              int = Form(1433),
    database:          str = Form(""),
    db_username:       str = Form(""),
    db_password:       str = Form(""),
    schema_name:       str = Form("dbo"),
    tables:            str = Form(""),
    load_strategy:     str = Form("incremental"),
    watermark_column:  str = Form(""),
    # API fields
    base_url:          str = Form(""),
    auth_type:         str = Form("bearer"),
    auth_value:        str = Form(""),
    watermark_field:   str = Form("updatedAt"),
    # CSV fields
    delimiter:         str = Form(","),
    has_header:        bool = Form(True),
    # Scrape fields
    scrape_url:        str = Form(""),
    css_selector:      str = Form(""),
    max_pages:         int = Form(10),
):
    stype = SourceType(source_type)
    source = DataSource(
        id=str(uuid.uuid4())[:8],
        name=name,
        description=description,
        source_type=stype,
        target_table=target_table or name.lower().replace(" ", "_"),
    )

    if stype == SourceType.database:
        source.database_config = DatabaseSourceConfig(
            dialect=DatabaseDialect(dialect),
            host=host, port=port, database=database,
            username=db_username, password=db_password,
            schema_name=schema_name,
            tables=[t.strip() for t in tables.split(",") if t.strip()],
            load_strategy=LoadStrategy(load_strategy),
            watermark_column=watermark_column,
        )
    elif stype == SourceType.api:
        source.api_config = APISourceConfig(
            base_url=base_url,
            auth_type=AuthType(auth_type),
            auth_value=auth_value,
            load_strategy=LoadStrategy(load_strategy),
            watermark_field=watermark_field,
        )
    elif stype == SourceType.csv:
        source.csv_config = CSVSourceConfig(delimiter=delimiter, has_header=has_header)
    elif stype == SourceType.webscrape:
        source.webscrape_config = WebscrapeSourceConfig(
            url=scrape_url, css_selector=css_selector, max_pages=max_pages,
        )

    storage.add_source(source, project)
    return RedirectResponse(url=f"/sources/?project={project}", status_code=303)


@router.post("/delete/{source_id}")
async def delete_source(source_id: str, project: str = "default"):
    storage.delete_source(source_id, project)
    return RedirectResponse(url=f"/sources/?project={project}", status_code=303)


@router.post("/toggle/{source_id}")
async def toggle_source(source_id: str, project: str = "default"):
    cfg = storage.load_project(project)
    for s in cfg.sources:
        if s.id == source_id:
            s.enabled = not s.enabled
    storage.save_project(cfg, project)
    return RedirectResponse(url=f"/sources/?project={project}", status_code=303)
