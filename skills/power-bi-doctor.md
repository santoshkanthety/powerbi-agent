---
name: Power BI Doctor
description: Diagnose powerbi-agent environment issues — Python/pythonnet install, Power BI Desktop detection, SSAS port access, Fabric auth state. Invoke when the user reports setup issues, connection failures, import errors, or asks "why isn't this working".
tools: powerbi-agent CLI (pbi-agent)
---

# Skill: Diagnose Environment Issues

## Trigger
Activate when the user reports connection problems, setup issues, import errors (pythonnet, clr, pyadomd), "command not found", or generally asks why powerbi-agent isn't working.

## Commands

```bash
# Run the full diagnostic
pbi-agent doctor
```

## What `doctor` Checks
- Python version and interpreter path
- `pythonnet` / `clr` availability (required for Desktop connection)
- Power BI Desktop installation and process detection
- SSAS port accessibility for detected instances
- Fabric auth state (cached token presence / validity)

## Recovery Playbook by Symptom

| Symptom | Fix |
|---|---|
| `pbi-agent: command not found` | Reinstall: `pipx install powerbi-agent` or `pip install powerbi-agent` |
| `ImportError: clr` / `pythonnet` | `pip install powerbi-agent[desktop]` (installs pythonnet) |
| `No Power BI Desktop instances found` | Open Power BI Desktop with a `.pbix` file loaded, then retry |
| `Port X in use` / connection refused | Close other AS clients; use `pbi-agent connect --port <port>` to target a specific instance |
| `Not authenticated` (Fabric commands) | Run `pbi-agent fabric login` |
| `Token expired` | Re-run `pbi-agent fabric login` |

## When to Escalate
If `pbi-agent doctor` passes but commands still fail, collect:
1. Output of `pbi-agent doctor`
2. Output of `pbi-agent --version`
3. The full failing command and its error
4. OS version and Power BI Desktop version

Then file an issue at https://github.com/santoshkanthety/powerbi-agent/issues.
