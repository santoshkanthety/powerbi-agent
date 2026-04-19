---
name: Power BI Report
description: Inspect and modify Power BI report structure (PBIR / .pbir) using powerbi-agent — show report info, list pages, add pages. Invoke when the user asks about report pages, visuals, bookmarks, or wants to scaffold new report content.
tools: powerbi-agent CLI (pbi-agent)
---

# Skill: Inspect and Modify Report Layout

## Trigger
Activate when the user asks about report pages, report structure, visuals, bookmarks, or wants to add a new page. Works against unpacked PBIR folders (`.Report/`) — does not require a Power BI Desktop connection.

## Commands

```bash
# Show the full report structure: pages, visuals, bookmarks
pbi-agent report info

# Explicitly point at a .pbip / .Report path (auto-detected from CWD if omitted)
pbi-agent report info path/to/MyReport.Report

# List pages only
pbi-agent report pages

# Add a new page
pbi-agent report add-page "Executive Summary"
pbi-agent report add-page "Regional Deep Dive" path/to/MyReport.Report
```

## Guidance
- The `PBIX_PATH` argument is optional. When omitted, powerbi-agent searches the current working directory for a `.Report` folder.
- Page names become folder names on disk — avoid special characters (slashes, colons) that would break filesystem paths.
- After adding a page, reload it in Power BI Desktop via pbi-cli's `pbi report reload` (if available) or reopen the project.

## Common Failures
- **"No .Report folder found"** → pass the path explicitly, or `cd` into the folder containing the PBIR project
- **Permission errors writing to the folder** → close Power BI Desktop first; it holds a lock on some files
