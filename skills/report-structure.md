---
name: powerbi-report-structure
description: Programmatic Power BI report structure automation via pbir.tools - add/delete/reorder pages, create/position/bind visuals, manage filters, bookmarks, and visual field bindings without opening Power BI Desktop
triggers:
  - add page
  - add visual
  - add filter
  - add bookmark
  - delete page
  - delete visual
  - remove visual
  - reorder pages
  - hide page
  - bind field
  - field binding
  - visual field
  - filter pane
  - lock filter
  - hide filter
  - bookmark
  - align visuals
  - z-order
  - report automation
  - PBIR
  - pbir.tools
---

# Report Structure Automation with pbir.tools

`pbir.tools` enables complete programmatic control over Power BI report structure — pages, visuals, filters, and bookmarks — without opening Power BI Desktop GUI. It works on PBIR format (folder-based reports).

## Installation

```bash
# Install pbir.tools
uv tool install pbir-cli

# Or via npm
npm install -g pbir-tools

# Install agent skills (registers with Claude Code automatically)
pbir setup
```

## Exploring Report Structure

```bash
# Tree view of entire report
pbir tree report.Report

# List all pages with visual counts
pbir ls report.Report --pages

# List visuals on a specific page
pbir ls report.Report/definition/pages/RevenueOverview --visuals --verbose

# Find visuals using a specific field
pbir find report.Report --field "Orders[Revenue]"

# Output raw JSON for any element
pbir cat report.Report/definition/pages/RevenueOverview

# Get a specific property using dot notation
pbir get report.Report "pages.RevenueOverview.displayName"
```

## Page Management

```bash
# Add a new page
pbir add page report.Report "Executive Summary"

# Rename a page
pbir pages rename report.Report "RevenueOverview" "Revenue Overview"

# Set page size (preset dimensions)
pbir pages resize report.Report "Executive Summary" --type "16:9"
pbir pages resize report.Report "Mobile View" --type "mobile"

# Reorder pages (move to index)
pbir pages reorder report.Report "Executive Summary" --index 0

# Hide/show a page (tooltip pages, drillthrough)
pbir pages hide report.Report "Drillthrough - Customer"
pbir pages unhide report.Report "Drillthrough - Customer"

# Set active page (default landing page)
pbir pages set-active report.Report "Executive Summary"

# Add background color or wallpaper
pbir pages background report.Report "Executive Summary" --color "#1a1a2e"

# Delete a page (requires --force)
pbir rm report.Report/definition/pages/OldPage --force
```

## Visual Management

```bash
# Add a card visual
pbir add visual report.Report/definition/pages/Overview card \
  --title "Total Revenue" \
  --x 20 --y 20 --width 240 --height 120

# Add a line chart
pbir add visual report.Report/definition/pages/Overview lineChart \
  --title "Revenue Trend" \
  --x 280 --y 20 --width 600 --height 300

# Add a table
pbir add visual report.Report/definition/pages/Overview tableEx \
  --title "Order Details" \
  --x 20 --y 160 --width 840 --height 400

# Position and resize an existing visual
pbir visuals report.Report/definition/pages/Overview/visuals/Card001 \
  position --x 40 --y 40

pbir visuals report.Report/definition/pages/Overview/visuals/Card001 \
  resize --width 300 --height 150

# Align multiple visuals
pbir visuals report.Report/definition/pages/Overview align --top \
  --visuals Card001,Card002,Card003

# Z-order (bring forward / send back)
pbir visuals report.Report/definition/pages/Overview/visuals/ChartBg \
  z-order send-to-back

# Hide/show visual
pbir visuals report.Report/definition/pages/Overview/visuals/Watermark hide

# Delete a visual (requires --force)
pbir rm report.Report/definition/pages/Overview/visuals/OldChart --force
```

## Field Binding (Data Connections)

```bash
# Bind a field to a visual role
pbir visuals report.Report/definition/pages/Overview/visuals/RevenueCard \
  fields add "Orders[Revenue]" --role "Values"

pbir visuals report.Report/definition/pages/TrendChart/visuals/LineChart \
  fields add "Calendar[Date]" --role "Axis"

pbir visuals report.Report/definition/pages/TrendChart/visuals/LineChart \
  fields add "Orders[Revenue]" --role "Values"

# List all fields bound to a visual
pbir visuals report.Report/definition/pages/Overview/visuals/RevenueCard \
  fields list

# Replace a field across all visuals (rename/model change)
pbir fields replace report.Report \
  --from "OldTable[OldColumn]" \
  --to "NewTable[NewColumn]"

# Find all visuals using a specific field
pbir fields find report.Report --field "Customers[Email]"

# Remove all field bindings from a visual
pbir visuals report.Report/definition/pages/Overview/visuals/OldCard \
  fields clear
```

## Filter Management

```bash
# List all report-level filters
pbir filters list report.Report

# List page-level filters
pbir filters list report.Report/definition/pages/Overview

# Add a filter to a page
pbir add filter report.Report/definition/pages/Overview "Calendar[Year]"

# Lock a filter (prevent users changing it)
pbir filters lock report.Report "Calendar[Year]"

# Hide a filter from the filter pane
pbir filters hide report.Report "Internal[DebugFlag]"

# Collapse the filter pane by default
pbir filters pane-collapse report.Report

# Clear filter values (reset to "All")
pbir filters clear report.Report/definition/pages/Overview "Calendar[Year]"

# Rename a filter display name
pbir filters rename report.Report "Calendar[FiscalYear]" "Fiscal Year"
```

## Bookmark Automation

```bash
# List all bookmarks
pbir bookmarks list report.Report

# Add a bookmark capturing current state
pbir add bookmark report.Report "YTD View" \
  --page "Revenue Overview" \
  --capture-filters \
  --capture-visuals

# Configure what a bookmark captures
pbir bookmarks report.Report "YTD View" \
  current-page true \
  visuals "RevenueCard,TrendLine"

# Rename a bookmark
pbir bookmarks rename report.Report "YTD View" "Year-to-Date Overview"
```

## Validation and Safety

```bash
# Validate report structure before publishing
pbir validate report.Report

# Full QA check (field connectivity, broken references, etc.)
pbir validate report.Report --qa --strict

# Create backup before making changes
pbir backup report.Report --description "Before field replacement"

# List backups
pbir backup list report.Report

# Restore if something goes wrong
pbir restore report.Report --latest
```

## Batch Automation

Automate bulk operations via spec files — ideal for CI/CD:

```yaml
# batch-spec.yaml
operations:
  - type: add_visual
    page: "Executive Summary"
    visual_type: card
    title: "Total Revenue"
    field: "Orders[Revenue]"
    position: {x: 20, y: 20, width: 240, height: 120}

  - type: add_filter
    page: "Executive Summary"
    field: "Calendar[Year]"
    locked: true

  - type: set_active_page
    page: "Executive Summary"
```

```bash
# Preview batch plan
pbir batch batch-spec.yaml --plan

# Execute batch operations
pbir batch batch-spec.yaml --run
```

## CLI Reference

```bash
pbir tree report.Report                              # View full report structure
pbir ls report.Report --pages                        # List pages
pbir add page report.Report "New Page"               # Add page
pbir add visual report.Report/pages/P1 card          # Add visual
pbir visuals .../V1 fields add "T[Col]" --role Values # Bind field
pbir filters lock report.Report "T[Col]"             # Lock filter
pbir bookmarks list report.Report                    # List bookmarks
pbir validate report.Report --qa                     # Validate
pbir backup report.Report                            # Backup before changes
pbir restore report.Report --latest                  # Restore backup
```
