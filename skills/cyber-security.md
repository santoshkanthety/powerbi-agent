---
name: powerbi-cyber-security
description: Power BI and Microsoft Fabric cybersecurity - tenant hardening, conditional access, OAuth flows, export controls, data exfiltration prevention, audit log threat detection, and compliance controls
triggers:
  - cyber security
  - cybersecurity
  - tenant hardening
  - conditional access
  - MFA
  - OAuth
  - export control
  - data exfiltration
  - threat detection
  - zero trust
  - SOC2
  - HIPAA
  - PCI-DSS
  - vulnerability
  - attack surface
  - hardening
  - incident response
  - access review
  - service principal
  - workspace security
  - embed token
  - firewall
  - IP allowlist
---

# Cybersecurity in Power BI / Microsoft Fabric

## Attack Surface Overview

| Area | Primary Risk | Control |
|------|-------------|---------|
| **Tenant** | Unauthorised workspace access | Conditional Access + MFA |
| **Embedding** | Embed token abuse | Short-lived tokens, service principal isolation |
| **Export** | Data exfiltration via report exports | Export controls, sensitivity labels |
| **Dataflows** | Credential exposure in Power Query | Key Vault integration |
| **Workspace** | Over-sharing, guest user access | Workspace roles, guest access policy |
| **APIs** | Service principal token theft | Certificate auth, secret rotation |

## Tenant Hardening (Admin Settings)

Critical Power BI admin tenant settings to lock down:

```bash
# Check tenant security posture
pbi-agent fabric admin tenant-audit --workspace "Production"
```

| Admin Setting | Recommended | Risk if Left Open |
|---|---|---|
| Allow service principals to use Power BI APIs | Specific security groups only | Unauthorised API access |
| Export data | Restricted groups | Mass data export |
| Export reports as PowerPoint | Disabled or restricted | Slides with embedded data |
| Publish to web | Disabled | Public data leak |
| Share content with external users | Disabled or restricted | Data shared outside org |
| Allow Azure Active Directory guest users to edit | Disabled | Guest elevating to editor |
| Allow DirectQuery connections to datasets | Specific groups | Live connection to source |

## Conditional Access for Power BI

Enforce MFA and device compliance before accessing Fabric / Power BI:

```
In Azure AD / Entra ID → Conditional Access:
  Target: Cloud app = "Power BI Service"
  Conditions:
    - Users: All users (exclude break-glass accounts)
    - Platforms: Any
  Controls:
    - Require MFA
    - Require compliant device (Intune)
    - Block legacy authentication
    - Session: Sign-in frequency = 8 hours
```

```bash
# Verify: check if any users accessed Power BI without MFA
pbi-agent catalog audit --workspace "Production" --check mfa-compliance
```

## OAuth and Service Principal Security

```python
# Use certificate-based auth for service principals (not client secrets)
# Client secrets can be extracted; certificates are harder to steal

from azure.identity import CertificateCredential
import httpx

# Load certificate from Azure Key Vault (never from disk in production)
credential = CertificateCredential(
    tenant_id=os.environ["AZURE_TENANT_ID"],
    client_id=os.environ["AZURE_CLIENT_ID"],
    certificate_path="/run/secrets/service-principal.pem"  # mounted secret
)
token = credential.get_token("https://analysis.windows.net/powerbi/api/.default")
```

```bash
# Audit: list all service principals with Power BI access
pbi-agent fabric admin list-service-principals

# Check for service principals with expired or near-expiry secrets
pbi-agent fabric admin audit-sp-credentials --warn-days 30
```

## Export Controls

```bash
# Restrict export to specific sensitivity-label-aware groups
pbi-agent fabric admin set-export-policy \
  --allow-groups "finance-reporting,exec-team" \
  --block-formats "csv,excel" \  # block raw data export formats
  --audit-log-level detailed
```

```python
# Monitor export events in Power BI activity log
import httpx, os

def get_export_events(days: int = 7) -> list:
    """Retrieve all export activity from Power BI audit log."""
    token = os.environ["FABRIC_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}

    export_ops = ["ExportReport", "ExportDataflow", "ExportTile", "DownloadReport"]

    events = []
    for op in export_ops:
        resp = httpx.get(
            "https://api.powerbi.com/v1.0/myorg/admin/activityevents",
            headers=headers,
            params={"activityType": op, "continuationToken": None}
        )
        events.extend(resp.json().get("activityEventEntities", []))

    return events

# Flag bulk exports (> 5 exports by same user in 1 hour)
from collections import Counter
exports = get_export_events(days=1)
user_counts = Counter(e["UserId"] for e in exports)
bulk_exporters = {uid: cnt for uid, cnt in user_counts.items() if cnt >= 5}
if bulk_exporters:
    print("⚠️  Potential bulk export activity:")
    for uid, cnt in bulk_exporters.items():
        print(f"   {uid}: {cnt} exports in last 24h")
```

## Embed Token Security

```python
import httpx, os
from datetime import datetime, timedelta

def generate_secure_embed_token(report_id: str, user_email: str) -> dict:
    """
    Generate a short-lived, user-scoped embed token.
    NEVER use master account credentials for embedding in production.
    """
    token = os.environ["FABRIC_TOKEN"]  # service principal token
    headers = {"Authorization": f"Bearer {token}"}

    # Embed token with:
    # - Short expiry (1 hour max)
    # - Scoped to a single report
    # - User identity passed for RLS enforcement
    resp = httpx.post(
        f"https://api.powerbi.com/v1.0/myorg/reports/{report_id}/GenerateToken",
        headers=headers,
        json={
            "accessLevel": "View",        # never "Edit" for end users
            "identities": [{
                "username": user_email,   # enforce RLS for this user
                "roles": ["RegionFilter"],
                "datasets": [os.environ["DATASET_ID"]]
            }],
            "lifetimeInMinutes": 60       # maximum 1 hour
        }
    )
    token_data = resp.json()
    expiry = datetime.utcnow() + timedelta(minutes=60)

    return {
        "embedToken": token_data["token"],
        "expiry": expiry.isoformat(),
        "reportId": report_id,
        "user": user_email
    }
```

**Embed token rules:**
- Always use service principal (never master user account)
- Token lifetime ≤ 60 minutes — refresh on the client
- Log every token generation event
- Never return embed tokens to unauthenticated clients
- Rotate service principal secrets/certificates every 90 days

## Threat Detection via Activity Log

```python
import httpx, os

def detect_threats(days: int = 1) -> list[dict]:
    """Scan Power BI activity log for suspicious patterns."""
    token   = os.environ["FABRIC_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = httpx.get(
        "https://api.powerbi.com/v1.0/myorg/admin/activityevents",
        headers=headers
    )
    events = resp.json().get("activityEventEntities", [])

    threats = []

    for e in events:
        # 1. Access from unusual location (if IPAddress available)
        if e.get("ClientIP") and not _is_corporate_ip(e["ClientIP"]):
            threats.append({"type": "external_ip_access", "user": e.get("UserId"), "ip": e["ClientIP"]})

        # 2. Publish to Web (public data exposure)
        if e.get("Activity") == "PublishToWebReport":
            threats.append({"type": "publish_to_web", "user": e.get("UserId"), "report": e.get("ReportName")})

        # 3. Workspace role escalation
        if e.get("Activity") == "AddGroupMembers" and e.get("ArtifactType") == "Workspace":
            threats.append({"type": "role_change", "user": e.get("UserId"), "detail": e})

        # 4. Dataset credentials updated (potential credential stuffing)
        if e.get("Activity") in ("UpdateDatasourceCredentials", "SetDatasourceCredentials"):
            threats.append({"type": "credential_update", "user": e.get("UserId"), "dataset": e.get("DatasetName")})

    return threats

def _is_corporate_ip(ip: str) -> bool:
    corporate_ranges = ["10.", "172.16.", "192.168.", "203.0.113."]
    return any(ip.startswith(r) for r in corporate_ranges)
```

## Workspace Access Review

```bash
# List all workspace members and their roles
pbi-agent fabric admin workspace-members --workspace "Production"

# Flag guest users with edit or admin access
pbi-agent fabric admin audit-guests --workspace "Production"

# Generate quarterly access review report
pbi-agent fabric admin access-review --workspace "Production" --output access_review_Q1_2025.csv
```

```python
# Detect stale access (users who haven't accessed in 90+ days)
import httpx, os
from datetime import datetime, timedelta

def find_stale_access(workspace_id: str, inactive_days: int = 90) -> list:
    token   = os.environ["FABRIC_TOKEN"]
    headers = {"Authorization": f"Bearer {token}"}

    # Get workspace members
    members_resp = httpx.get(
        f"https://api.powerbi.com/v1.0/myorg/groups/{workspace_id}/users",
        headers=headers
    )
    members = members_resp.json().get("value", [])

    # Get activity log for last 90 days
    cutoff = (datetime.utcnow() - timedelta(days=inactive_days)).isoformat()
    active_users = set()
    # (Query activity log for this workspace — omitted for brevity)

    return [m for m in members if m["emailAddress"] not in active_users]
```

## Incident Response Playbook

### Suspected Report Data Leak

```bash
# Step 1: Identify what was accessed
pbi-agent fabric admin activity --user suspect@company.com --days 7

# Step 2: Check exports
pbi-agent fabric admin activity --user suspect@company.com --filter ExportReport

# Step 3: Revoke access immediately
pbi-agent fabric admin revoke-access --user suspect@company.com --workspace "Production"

# Step 4: Rotate dataset credentials (if source credentials may be compromised)
pbi-agent fabric credentials rotate --dataset "Sales Model"

# Step 5: Review and invalidate any embed tokens issued to that user
```

## Compliance Controls Summary

| Standard | Control | Power BI Implementation |
|---|---|---|
| **SOC 2** | Access logging | Power BI activity log → Log Analytics |
| **GDPR** | Data subject rights | Sensitivity labels + erasure procedures |
| **HIPAA** | PHI access control | RLS + Confidential sensitivity label |
| **PCI-DSS** | Cardholder data isolation | Workspace separation + export block |
| **ISO 27001** | Asset classification | Purview labels on all certified datasets |

## CLI Reference

```bash
pbi-agent fabric admin tenant-audit                          # Tenant security posture
pbi-agent fabric admin list-service-principals               # SP inventory
pbi-agent fabric admin workspace-members --workspace Prod    # Access review
pbi-agent fabric admin activity --user u@corp.com --days 7  # User activity
pbi-agent fabric admin audit-guests --workspace Prod         # Guest access audit
pbi-agent catalog audit --workspace Prod --check mfa         # MFA compliance
```
