"""Rule engine CRUD routes."""
from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from powerbi_agent.web import storage
from powerbi_agent.web.models.config import Rule, RuleAction, RuleType

router    = APIRouter()
templates: Jinja2Templates = None


@router.get("/", response_class=HTMLResponse)
async def list_rules(request: Request, project: str = "default"):
    cfg = storage.load_project(project)
    return templates.TemplateResponse("rules.html", {
        "request": request, "cfg": cfg, "project": project, "page": "rules",
        "rule_types": list(RuleType), "rule_actions": list(RuleAction),
        "sources": cfg.sources,
    })


@router.post("/add")
async def add_rule(
    request: Request,
    project:        str = Form("default"),
    name:           str = Form(...),
    description:    str = Form(""),
    rule_type:      str = Form(...),
    applies_to:     str = Form("all"),
    column:         str = Form(""),
    action_on_fail: str = Form("flag_and_pass"),
    order:          int = Form(0),
    # Flexible parameters encoded as JSON string from frontend
    params_json:    str = Form("{}"),
):
    try:
        params = json.loads(params_json) if params_json else {}
    except Exception:
        params = {}

    rule = Rule(
        id=str(uuid.uuid4())[:8],
        name=name,
        description=description,
        rule_type=RuleType(rule_type),
        applies_to=applies_to,
        column=column,
        parameters=params,
        action_on_fail=RuleAction(action_on_fail),
        order=order,
    )
    storage.add_rule(rule, project)
    return RedirectResponse(url=f"/rules/?project={project}", status_code=303)


@router.post("/delete/{rule_id}")
async def delete_rule(rule_id: str, project: str = "default"):
    storage.delete_rule(rule_id, project)
    return RedirectResponse(url=f"/rules/?project={project}", status_code=303)


@router.post("/toggle/{rule_id}")
async def toggle_rule(rule_id: str, project: str = "default"):
    cfg = storage.load_project(project)
    for r in cfg.rules:
        if r.id == rule_id:
            r.enabled = not r.enabled
    storage.save_project(cfg, project)
    return RedirectResponse(url=f"/rules/?project={project}", status_code=303)
