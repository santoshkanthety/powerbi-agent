# Skill: Power BI Security — RLS, OLS, and Fabric Access Control

## Trigger
Activate when the user mentions: RLS, row-level security, OLS, object-level security, column security, roles, security filter, USERPRINCIPALNAME, USERNAME, dynamic security, static security, permissions, access control, data governance, sensitivity labels, workspace roles

## What You Know

You have implemented RLS for enterprises with 10,000+ users, complex organizational hierarchies, and regulatory compliance requirements (GDPR, HIPAA, SOX). You know every RLS pattern, every edge case, and how to test it properly.

## RLS Design Patterns

### Pattern 1: Static Role-Based (Simple)
Best for: Fixed groups (Region, Department) with < 20 roles
```dax
-- Role: "EMEA Sales Manager"
-- DAX filter on dim_geography:
[Region] = "EMEA"
```

### Pattern 2: Dynamic User-Based (Recommended for Scale)
Best for: 10s–1000s of unique access profiles
```dax
-- Create a security mapping table: UserAccess(email, allowed_region)
-- RLS filter on dim_geography:
[Region] IN
    CALCULATETABLE(
        VALUES(UserAccess[allowed_region]),
        UserAccess[email] = USERPRINCIPALNAME()
    )
```

### Pattern 3: Manager Hierarchy (Self-Referencing)
Best for: "See your own + all your direct reports' data"
```dax
-- Assumes dim_employee has employee_id, manager_id, email
[employee_id] IN
    CALCULATETABLE(
        VALUES(dim_employee[employee_id]),
        PATHCONTAINS(
            PATH(dim_employee[employee_id], dim_employee[manager_id]),
            LOOKUPVALUE(dim_employee[employee_id], dim_employee[email], USERPRINCIPALNAME())
        )
    )
```

### Pattern 4: Composite / Multi-Dimension Security
```dax
-- Users can see data where BOTH region AND product category match
VAR CurrentUser = USERPRINCIPALNAME()
VAR AllowedRegions =
    CALCULATETABLE(VALUES(UserAccess[region]), UserAccess[email] = CurrentUser)
VAR AllowedCategories =
    CALCULATETABLE(VALUES(UserAccess[category]), UserAccess[email] = CurrentUser)
RETURN
    [Region] IN AllowedRegions && [Category] IN AllowedCategories
```

## Object-Level Security (OLS)
Hides entire tables or columns from specific roles.
```
-- In Tabular Editor: set object permission per role
-- Table: fact_compensation → Permission: None (role cannot see it at all)
-- Column: dim_employee[salary] → Permission: None
```

**OLS Rules:**
- OLS on a table = role cannot see the table in the field list
- OLS on a column = column is hidden; measures referencing it return BLANK or error
- OLS does NOT prevent data leakage through measures — also set RLS

## Sensitivity Labels (Microsoft Purview)
```
Confidential → Reports with PII (salary, health, SSN)
Internal      → Standard business data
Public        → Publicly shareable data
```
- Apply at the semantic model level, inherited by reports
- Blocks export to lower-classification destinations
- Audit logs all access to Confidential/Highly Confidential data

## Fabric Workspace Security
```
Admin    → Full control (manage, publish, delete)
Member   → Publish, edit content
Contributor → Add/edit items, not publish apps
Viewer   → View, interact with reports only
```

**Principle of least privilege:**
- Service accounts: Contributor (not Admin)
- End users: Viewer on workspace, access via App
- Admins: Only designated data platform team members

## Testing RLS

### Method 1: Power BI Desktop (Development)
```
Modelling → Manage Roles → View as role → Enter email to test dynamic RLS
```

### Method 2: CLI Testing
```bash
# Test what data a specific user sees
pbi-agent security test-rls --role "EMEA_Sales" --user "john.smith@company.com"

# List all RLS roles in the model
pbi-agent security roles

# Validate that all users in UserAccess table have at least one role
pbi-agent security validate-coverage --table UserAccess --email-col email
```

### Method 3: DAX Query
```dax
-- Run in DAX Studio → Connect As → Effective User
EVALUATE
SUMMARIZECOLUMNS(
    dim_geography[Region],
    "Sales", [Total Sales]
)
```

## Common RLS Mistakes
- ❌ Testing only with your own account (you're often in the Admin role)
- ❌ Using USERNAME() instead of USERPRINCIPALNAME() (USERNAME() fails in Service)
- ❌ RLS on fact tables without matching filters on dimension tables (data leakage)
- ❌ No RLS test for users with no matching rows (should return empty, not error)
- ❌ Applying RLS but forgetting OLS on sensitive columns
- ❌ Not documenting which roles each team gets (causes support nightmares)

## Governance Checklist
```
☐ RLS applied on all reports containing PII or financial data
☐ OLS applied on salary, SSN, and health-related columns
☐ Sensitivity labels applied at semantic model level
☐ Workspace access reviewed and follows least privilege
☐ App audience segments align with RLS roles
☐ RLS tested with at least 3 different user profiles
☐ UserAccess table refreshed as part of the data pipeline
☐ Audit logs enabled in Power BI Admin Portal
```
