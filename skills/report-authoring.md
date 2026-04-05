# Skill: Power BI Report Authoring

## Trigger
Activate when the user mentions: report, page, visual, chart, bar chart, line chart, matrix, table, slicer, filter, bookmark, tooltip, drill-through, navigation, layout, canvas, report design, visual formatting, conditional formatting, KPI, card, decomposition tree

## What You Know

You are a report design expert who has built hundreds of Power BI reports for C-suite executives, operations teams, and analysts. You know the difference between a report users love and one they abandon after day 2.

## Report Design Principles (The Foundation)

### 1. Define the audience before touching Power BI
```
Executive:    3–5 KPIs, trend, one insight per page, mobile-ready
Operational:  Tables with filters, drilldown, export capability
Analytical:   Self-service filters, custom visuals, decomposition trees
```

### 2. The F-Pattern and Z-Pattern layouts
- Eye tracks top-left → right → down → left
- Place most important KPIs top-left
- Navigation always top or left panel
- Filters and slicers: right panel or top bar (consistent)

### 3. Page Structure Template
```
┌─────────────────────────────────────────────────────┐
│ LOGO    │  Report Title               │  Date Range  │
│─────────────────────────────────────────────────────│
│ KPI 1   │  KPI 2   │  KPI 3   │  KPI 4   │  KPI 5  │
│─────────────────────────────────────────────────────│
│                                      │              │
│   Primary Chart (60% width)          │  Slicers     │
│                                      │  - Region    │
│                                      │  - Product   │
│──────────────────────────────────────│  - Customer  │
│  Secondary Chart   │ Supporting Info │              │
└─────────────────────────────────────────────────────┘
```

## Visual Selection Guide

| Data Story | Best Visual |
|---|---|
| Part of whole (< 5 categories) | Donut or Pie |
| Part of whole (5+ categories) | Stacked Bar |
| Trend over time | Line Chart |
| Comparison across categories | Bar/Column Chart |
| Correlation between two metrics | Scatter Plot |
| Hierarchy + proportion | Treemap |
| Geographic data | Map / Filled Map |
| Detailed data with interactions | Matrix |
| Single metric vs target | KPI Card / Gauge |
| Decomposing a metric | Decomposition Tree |
| Anomaly detection | Anomaly Detection (line chart) |
| Key influencers | Key Influencers Visual |

## Formatting Standards

### Colours
- Max 4–5 colours in a report
- One accent colour for highlights
- Use grey for context/comparison (prior period, budget)
- Semantic colours: red = bad, green = good, amber = warning (unless colour-blind mode needed)
- Never use red/green together without a pattern alternative

### Typography
- Report title: 18–22pt, bold
- Section headers: 14–16pt, bold
- KPI values: 24–32pt, bold
- Labels: 10–12pt, regular
- Consistent font family throughout (Segoe UI or DM Sans)

### Cards & KPIs
```
┌──────────────────┐
│  Total Sales     │  ← Label (small, grey)
│  $4.2M           │  ← Value (large, bold)
│  ▲ 12% vs LY    │  ← Trend indicator (colour-coded)
└──────────────────┘
```

## Advanced Techniques

### Bookmarks for Navigation
```
Use bookmarks for:
- Toggle between chart types (user preference)
- Show/hide filter panels
- "Reset filters" button
- Storytelling slides
Never use: More than 20 bookmarks (maintenance nightmare)
```

### Drillthrough Pages
```
Setup: Right-click drill context → specific product, customer, region
Keep: Drillthrough pages as hidden pages
Add: Back button on every drillthrough page
```

### Conditional Formatting
```dax
-- Colour scale based on performance vs target
Color Rule:
  If [Achievement %] < 0.8  → Red (#D32F2F)
  If [Achievement %] < 1.0  → Amber (#F57C00)
  Else                       → Green (#388E3C)
```

### Tooltips
- Report page tooltips: rich context on hover (mini-report)
- Always include: current period value, prior period, % change
- Max tooltip page size: 320×240px

## CLI Commands
```bash
# List report pages
pbi-agent report pages myreport.pbix

# Add a new report page
pbi-agent report add-page "Executive Summary" myreport.pbix

# Show visual types used across all pages
pbi-agent report visuals myreport.pbix

# Validate report against design standards
pbi-agent report validate --check design-standards myreport.pbix
```

## Report Quality Checklist
```
☐ Title matches workspace/app name
☐ Date of last refresh visible on every page
☐ All slicers synced across relevant pages
☐ Mobile layout configured for KPI pages
☐ Alt text on all visuals (accessibility)
☐ No cross-filter conflicts between visuals
☐ Drillthrough pages have Back buttons
☐ Tested on 1920x1080, 1366x768, and mobile
☐ No more than 15 visuals per page
☐ Export to PDF tested for critical reports
```
