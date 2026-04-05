"""Data model designer routes."""
from __future__ import annotations

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from powerbi_agent.web import storage
from powerbi_agent.web.models.config import ColumnDefinition, TableDefinition

router    = APIRouter()
templates: Jinja2Templates = None

DATA_TYPES = [
    "VARCHAR", "NVARCHAR", "INT", "BIGINT", "SMALLINT", "TINYINT",
    "DECIMAL", "FLOAT", "BIT", "DATE", "DATETIME", "TIMESTAMP",
    "BOOLEAN", "GUID", "BINARY",
]

LAYERS = ["bronze", "silver", "gold"]


@router.get("/", response_class=HTMLResponse)
async def model_overview(request: Request, project: str = "default"):
    cfg = storage.load_project(project)
    return templates.TemplateResponse("model_designer.html", {
        "request": request, "cfg": cfg, "project": project,
        "page": "model", "data_types": DATA_TYPES, "layers": LAYERS,
        "sources": cfg.sources,
    })


@router.post("/add-table")
async def add_table(
    project:          str = Form("default"),
    name:             str = Form(...),
    description:      str = Form(""),
    source_id:        str = Form(""),
    layer:            str = Form("bronze"),
    partition_column: str = Form(""),
    scd_type:         int = Form(0),
):
    cfg = storage.load_project(project)
    table = TableDefinition(
        name=name, description=description, source_id=source_id,
        layer=layer, partition_column=partition_column, scd_type=scd_type,
    )
    cfg.tables.append(table)
    storage.save_project(cfg, project)
    return RedirectResponse(url=f"/model/?project={project}", status_code=303)


@router.post("/add-column/{table_name}")
async def add_column(
    table_name:        str,
    project:           str = Form("default"),
    col_name:          str = Form(...),
    source_column:     str = Form(""),
    data_type:         str = Form("VARCHAR"),
    nullable:          bool = Form(True),
    is_primary_key:    bool = Form(False),
    is_foreign_key:    bool = Form(False),
    references_table:  str = Form(""),
    references_column: str = Form(""),
    description:       str = Form(""),
    pii:               bool = Form(False),
):
    cfg = storage.load_project(project)
    for table in cfg.tables:
        if table.name == table_name:
            col = ColumnDefinition(
                name=col_name,
                source_column=source_column or col_name,
                data_type=data_type,
                nullable=nullable,
                is_primary_key=is_primary_key,
                is_foreign_key=is_foreign_key,
                references_table=references_table,
                references_column=references_column,
                description=description,
                pii=pii,
            )
            table.columns.append(col)
            break
    storage.save_project(cfg, project)
    return RedirectResponse(url=f"/model/?project={project}", status_code=303)


@router.post("/delete-table/{table_name}")
async def delete_table(table_name: str, project: str = "default"):
    cfg = storage.load_project(project)
    cfg.tables = [t for t in cfg.tables if t.name != table_name]
    storage.save_project(cfg, project)
    return RedirectResponse(url=f"/model/?project={project}", status_code=303)
