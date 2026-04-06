---
name: powerbi-report-theming
description: Power BI report theming via pbir.tools - color palettes, typography, text classes, theme templates, visual formatting, icons, background images, and conditional formatting rules
triggers:
  - theme
  - theming
  - color palette
  - brand colors
  - fonts
  - typography
  - text class
  - formatting
  - conditional formatting
  - theme template
  - theme apply
  - icon
  - background image
  - visual style
  - report style
  - color swap
  - push visual
---

# Report Theming with pbir.tools

Power BI themes control colors, fonts, and default visual formatting. `pbir.tools` exposes full programmatic control over all theme elements — enabling brand consistency across reports, bulk style application, and reusable theme templates — without opening Power BI Desktop.

## Installation

```bash
uv tool install pbir-cli
```

## Exploring the Current Theme

```bash
# Display current color palette
pbir theme colors report.Report

# List all text class configurations (title, label, callout, etc.)
pbir theme text-classes report.Report

# List available fonts
pbir theme fonts report.Report

# List available built-in theme templates
pbir theme list-templates

# Show full theme JSON
pbir cat report.Report/definition/report/theme
```

## Color Management

```bash
# Assign brand colors to palette positions
pbir theme set-colors report.Report \
  --primary "#1a3a8f" \
  --secondary "#e8612c" \
  --background "#f5f7fa" \
  --foreground "#1c1c1c"

# Replace a specific color across all visuals
pbir theme colors report.Report \
  --replace "#FF0000" \
  --with "#CC3333"

# Normalize all hex colors to lowercase (consistency)
pbir theme colors report.Report --normalize

# Apply Tron Ares color palette
pbir theme set-colors report.Report \
  --primary "#00f0ff" \
  --secondary "#ff4e00" \
  --background "#04060f" \
  --foreground "#c8e8f0" \
  --accent1 "#007a88" \
  --accent2 "#7a2500"
```

## Typography Configuration

```bash
# Set default font family for the entire report
pbir theme set-text-classes report.Report \
  --font "Segoe UI" \
  --fallback "sans-serif"

# Configure individual text classes
pbir theme set-text-classes report.Report \
  --class "title" \
  --font "Segoe UI Semibold" \
  --size 16 \
  --color "#1c1c1c" \
  --bold true

pbir theme set-text-classes report.Report \
  --class "calloutValue" \
  --font "Segoe UI Light" \
  --size 28 \
  --color "#1a3a8f"

pbir theme set-text-classes report.Report \
  --class "label" \
  --font "Segoe UI" \
  --size 10 \
  --color "#666666"

# Available text classes:
# title, subTitle, label, calloutValue, header, smallLabel, semiboldLabel
```

## Default Visual Formatting

```bash
# Apply default styling rules to all visuals
pbir theme set-formatting report.Report \
  --visual-background "#ffffff" \
  --visual-border false \
  --visual-shadow false \
  --visual-padding 10

# Apply to a specific visual type only
pbir theme set-formatting report.Report \
  --visual-type lineChart \
  --line-width 2 \
  --marker false \
  --legend true \
  --legend-position bottom

pbir theme set-formatting report.Report \
  --visual-type card \
  --border false \
  --padding 12 \
  --alignment center

# Push theme defaults to an individual visual (override with theme values)
pbir theme push-visual report.Report/definition/pages/Overview/visuals/RevenueCard

# Push to all visuals of a type
pbir theme push-visual report.Report --type card --all
```

## Conditional Formatting Rules

```bash
# List existing conditional formatting rules on a visual
pbir visuals report.Report/definition/pages/Overview/visuals/RevenueTable \
  conditional-formatting list

# Apply a color scale rule
pbir visuals report.Report/definition/pages/Overview/visuals/RevenueTable \
  conditional-formatting apply \
  --field "Orders[Revenue]" \
  --type color-scale \
  --min-color "#e8f5e9" \
  --mid-color "#66bb6a" \
  --max-color "#1b5e20"

# Apply a rules-based icon set
pbir visuals report.Report/definition/pages/Overview/visuals/StatusTable \
  conditional-formatting apply \
  --field "KPIs[Status]" \
  --type icon-set \
  --rules ">=1:green-circle,=0:yellow-circle,<0:red-circle"

# Copy rules from one visual to another
pbir visuals .../RevenueTable conditional-formatting copy \
  --to .../OrderTable \
  --field "Orders[Revenue]"

# Remove a conditional formatting rule
pbir visuals .../RevenueTable conditional-formatting remove \
  --field "Orders[Revenue]"
```

## Theme Templates

```bash
# Save current theme as a reusable template
pbir theme create-template report.Report \
  --name "AcmeCorp-Brand-2025" \
  --description "Official Acme Corporation brand theme"

# List saved templates
pbir theme list-templates

# Apply a saved template to another report
pbir theme apply-template target-report.Report \
  --name "AcmeCorp-Brand-2025"

# Apply a built-in template
pbir theme apply-template report.Report --name "Executive"
pbir theme apply-template report.Report --name "Accessible"

# Export theme to JSON file (for sharing or version control)
pbir theme serialize report.Report --output themes/acme-brand.json

# Build a theme from JSON
pbir theme build themes/acme-brand.json --output report.Report

# Validate theme JSON
pbir theme validate themes/acme-brand.json
```

## Icons and Image Assets

```bash
# List all icons in the theme
pbir theme icons report.Report

# Add a custom icon to the theme
pbir theme icons report.Report --add icons/arrow-up.svg --name "trend-up"
pbir theme icons report.Report --add icons/arrow-down.svg --name "trend-down"

# Add background image to a page
pbir theme background report.Report \
  --page "Executive Summary" \
  --image assets/dashboard-bg.png \
  --transparency 90

# Add background image to the full report via theme
pbir theme background report.Report \
  --report-level \
  --image assets/watermark.png \
  --fit contain
```

## Brand Consistency Workflow

Apply consistent branding across a fleet of reports:

```bash
# Step 1: Audit current colors across all reports
for report in reports/*.Report; do
  echo "=== $report ==="
  pbir theme colors "$report"
done

# Step 2: Create the brand template from master report
pbir theme create-template reports/master.Report --name "Brand-2025"

# Step 3: Apply to all other reports
for report in reports/*.Report; do
  pbir backup "$report"
  pbir theme apply-template "$report" --name "Brand-2025"
  pbir validate "$report"
done
```

## CLI Reference

```bash
pbir theme colors report.Report                           # View color palette
pbir theme set-colors report.Report --primary "#1a3a8f"  # Set brand colors
pbir theme text-classes report.Report                     # View typography
pbir theme set-text-classes report.Report --class title   # Set text class
pbir theme set-formatting report.Report                   # Default visual styles
pbir theme push-visual .../visual                         # Apply theme to visual
pbir theme create-template report.Report --name "T1"      # Save theme template
pbir theme apply-template report.Report --name "T1"       # Apply template
pbir theme serialize report.Report --output theme.json    # Export theme
pbir theme icons report.Report --add icon.svg             # Add custom icon
```
