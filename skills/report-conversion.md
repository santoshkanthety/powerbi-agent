---
name: powerbi-report-conversion
description: Power BI report format conversion, merging, splitting, and semantic model rebinding via pbir.tools - PBIR/PBIP/PBIX conversion, multi-report merging, page splitting, thick/thin PBIP operations, and model rebind
triggers:
  - convert report
  - PBIR
  - PBIP
  - PBIX
  - format conversion
  - merge reports
  - split pages
  - split report
  - rebind dataset
  - rebind semantic model
  - thick PBIP
  - thin report
  - report merge
  - report split
  - combine reports
  - swap dataset
  - change semantic model
  - report publish
  - download report
  - report deployment
  - CI/CD report
---

# Report Format Conversion & Structural Operations with pbir.tools

`pbir.tools` enables bidirectional format conversion between Power BI formats, structural report transformations (merge, split), and semantic model rebinding — all essential for CI/CD pipelines, modular report development, and dataset migrations.

## Format Overview

| Format | Description | Best Used For |
|--------|-------------|--------------|
| **PBIR** | Folder-based report (text files) | Version control, agent automation, diff-friendly |
| **PBIP** | Power BI Project (folder + model) | Full project with embedded semantic model |
| **PBIX** | Binary desktop file | Sharing, legacy publishing, final delivery |

**Rule of thumb**: Work in PBIR for development, convert to PBIX or publish PBIP for deployment.

## Format Conversion

```bash
# PBIX → PBIR (extract from binary — for source control)
pbir report convert revenue.pbix --to pbir --output reports/

# PBIR → PBIX (package for distribution)
pbir report convert reports/revenue.Report --to pbix --output dist/

# PBIP → PBIR (decompose project)
pbir report convert revenue.pbip --to pbir --output reports/

# PBIR → PBIP (compose project)
pbir report convert reports/revenue.Report --to pbip --output dist/

# PBIX → PBIP (convert legacy desktop file to project format)
pbir report convert legacy-report.pbix --to pbip --output projects/
```

```bash
# Always validate after conversion
pbir validate reports/revenue.Report --qa
```

## Semantic Model Rebinding

Swap a report's connected semantic model while preserving all visual design, filters, bookmarks, and layout. Critical for promoting reports across environments (dev → staging → prod) or migrating to a new dataset.

```bash
# Rebind to a different semantic model in the same workspace
pbir report rebind reports/revenue.Report \
  --workspace "Production" \
  --dataset "Revenue Model Prod"

# Rebind to a semantic model in a different workspace
pbir report rebind reports/revenue.Report \
  --workspace-id "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  --dataset-id "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy"

# Rebind using connection string (for XMLA endpoint)
pbir report rebind reports/revenue.Report \
  --connection "powerbi://api.powerbi.com/v1.0/myorg/Production" \
  --dataset "Revenue Model"

# Verify rebind result
pbir get reports/revenue.Report "datasetReference"
pbir validate reports/revenue.Report --qa  # ensure fields still resolve
```

**When to rebind:**
- Promoting reports from dev dataset → prod dataset
- Renaming a semantic model
- Merging two datasets into one
- Migrating from DirectQuery to Import mode model

## Report Merging (Combine Multiple Reports)

Combine pages from multiple reports into a single deliverable — essential for executive packs or consolidated dashboards:

```bash
# Merge pages from multiple source reports into one
pbir report merge \
  --sources reports/revenue.Report,reports/customers.Report,reports/ops.Report \
  --output dist/executive-pack.Report

# Merge with page prefix to avoid name collisions
pbir report merge \
  --sources reports/revenue.Report,reports/customers.Report \
  --prefix-by-source \
  --output dist/combined.Report

# Merge specific pages only
pbir report merge \
  --sources reports/revenue.Report \
  --pages "Revenue Overview,YTD Summary" \
  --output dist/quarterly-pack.Report
```

## Report Splitting (Decompose Reports)

Split a multi-page report into individual single-page reports — useful for per-team or per-region distribution:

```bash
# Split each page into a separate report
pbir report split-pages reports/master-report.Report \
  --output dist/pages/

# Result:
#   dist/pages/Revenue-Overview.Report
#   dist/pages/Customer-360.Report
#   dist/pages/Operations.Report

# Split specific pages only
pbir report split-pages reports/master-report.Report \
  --pages "Revenue Overview,YTD Summary" \
  --output dist/finance-reports/
```

## Thick ↔ Thin PBIP Operations

**Thick PBIP** = report + embedded semantic model in one `.pbip` folder
**Thin PBIP** = report-only `.Report` connected to a published dataset

```bash
# Convert thin report + published dataset → thick PBIP (offline development)
pbir report merge-to-thick \
  --report reports/revenue.Report \
  --dataset "Revenue Model" \
  --workspace "Production" \
  --output dev/revenue-thick.pbip

# Split thick PBIP → thin report + publish model separately (Fabric-first workflow)
pbir report split-from-thick dev/revenue-thick.pbip \
  --report-output reports/
  --model-output models/

# Clear semantic model diagram layout (before publishing for clean view)
pbir report clear-diagram dev/revenue-thick.pbip
```

## Download and Publish (Fabric Integration)

```bash
# Download a report from Fabric workspace (as PBIR for version control)
pbir download \
  --workspace "Production" \
  --report "Revenue Dashboard" \
  --format pbir \
  --output reports/

# Download as PBIX (for backup or distribution)
pbir download \
  --workspace "Production" \
  --report "Revenue Dashboard" \
  --format pbix \
  --output backups/

# Publish to Fabric workspace (overwrite existing)
pbir publish reports/revenue.Report \
  --workspace "Production" \
  --overwrite

# Publish with new name
pbir publish reports/revenue.Report \
  --workspace "Staging" \
  --name "Revenue Dashboard [STAGING]"
```

## CI/CD Pipeline Patterns

### Dev → Staging → Prod Promotion

```bash
# Step 1: In CI — download from dev workspace
pbir download --workspace "Development" --report "Revenue Dashboard" --format pbir --output reports/

# Step 2: Rebind to staging dataset
pbir report rebind reports/Revenue-Dashboard.Report \
  --workspace "Staging" --dataset "Revenue Model [Staging]"

# Step 3: Validate
pbir validate reports/Revenue-Dashboard.Report --qa --strict
if [ $? -ne 0 ]; then echo "❌ Validation failed"; exit 1; fi

# Step 4: Publish to staging
pbir publish reports/Revenue-Dashboard.Report \
  --workspace "Staging" --overwrite

# Step 5: Rebind to prod dataset and publish
pbir report rebind reports/Revenue-Dashboard.Report \
  --workspace "Production" --dataset "Revenue Model"
pbir publish reports/Revenue-Dashboard.Report \
  --workspace "Production" --overwrite

echo "✅ Report promoted to Production"
```

### Bulk Report Migration (New Dataset)

```bash
# Migrate all reports in a workspace to a new semantic model
for report in reports/*.Report; do
  pbir backup "$report"
  pbir report rebind "$report" \
    --workspace "Production" \
    --dataset "New Revenue Model"
  pbir validate "$report" --qa || { echo "Validation failed: $report"; continue; }
  pbir publish "$report" --workspace "Production" --overwrite
  echo "✅ Migrated: $report"
done
```

## Validation Before Any Structural Change

Always validate before and after structural operations:

```bash
# Quick structure check
pbir validate report.Report

# Full QA (field connectivity, broken references, filter validation)
pbir validate report.Report --qa

# Strict mode (fail on warnings too)
pbir validate report.Report --qa --strict

# Output as JSON (for CI parsing)
pbir validate report.Report --qa --json

# Verify field still resolves after rebind
pbir fields find report.Report --verify
```

## Opening Reports

```bash
# Open report in Power BI Desktop (for visual review)
pbir open reports/revenue.Report

# Open to a specific page
pbir open reports/revenue.Report --page "Revenue Overview"
```

## CLI Reference

```bash
pbir report convert report.pbix --to pbir --output reports/    # Convert format
pbir report rebind report.Report --workspace Prod --dataset DS  # Rebind dataset
pbir report merge --sources r1.Report,r2.Report --output out.Report
pbir report split-pages report.Report --output dist/pages/
pbir report merge-to-thick --report r.Report --dataset DS --workspace W
pbir report split-from-thick thick.pbip --report-output reports/
pbir download --workspace Prod --report "Revenue" --format pbir
pbir publish report.Report --workspace Prod --overwrite
pbir validate report.Report --qa --strict
pbir backup report.Report && pbir restore report.Report --latest
```
