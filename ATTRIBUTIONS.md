# Attributions & Credits

**powerbi-agent** is an original work by **Santosh Kanthety**.

This project was inspired by the broader Power BI open-source community. We gratefully acknowledge:

---

## Inspirations

### pbi-cli — Mina Saad
- Repository: https://github.com/MinaSaad1/pbi-cli
- License: MIT (compatible with this project's MIT license)
- Inspired the direct .NET TOM/ADOMD interop pattern for connecting to Power BI Desktop's local Analysis Services instance.
- The connection architecture in `connect.py` and `dax.py` is original work, written independently using the same underlying Windows APIs.
- The following hardening behaviours were patterned after pbi-cli (no code copied; equivalent logic written from scratch). Each module carries an attribution comment in its docstring:
  - Microsoft Store install path detection in addition to MSI — `connect._workspace_roots`
  - UTF-16 LE → UTF-8 fallback when reading `msmdsrv.port.txt` — `connect._read_port_file`
  - Most-recent-instance ordering when multiple Power BI Desktop sessions are open
  - Click-integrated error hierarchy — `powerbi_agent.errors`

### power-bi-agentic-development — Kurt Buhler (data-goblin)
- Repository: https://github.com/data-goblin/power-bi-agentic-development
- License: **GPL-3.0**
- Inspired the concept of Claude Code skill files as domain-specific knowledge modules for Power BI agentic development.
- **Important:** No code, skill file content, or documentation text was copied or derived from this GPL-3.0 licensed project. All skill files in the `skills/` directory are original works by Santosh Kanthety, written from scratch based on independent expertise and experience. This project's MIT license applies only to its own original content.
- If you fork this project and wish to incorporate any content from `power-bi-agentic-development`, you must comply with its GPL-3.0 terms.

---

## Key Dependencies

| Package | License | Purpose |
|---|---|---|
| [Click](https://github.com/pallets/click) | BSD-3-Clause | CLI framework |
| [Rich](https://github.com/Textualize/rich) | MIT | Terminal output formatting |
| [httpx](https://github.com/encode/httpx) | BSD-3-Clause | HTTP client for Fabric REST API |
| [Pydantic](https://github.com/pydantic/pydantic) | MIT | Data validation |
| [pythonnet](https://github.com/pythonnet/pythonnet) | MIT | .NET interop for TOM/ADOMD |
| [azure-identity](https://github.com/Azure/azure-sdk-for-python) | MIT | Azure authentication for Fabric |

---

## Microsoft Technologies

This tool automates and extends:
- **Microsoft Power BI** — https://powerbi.microsoft.com
- **Microsoft Fabric** — https://www.microsoft.com/fabric
- **Analysis Services (SSAS)** — local engine embedded in Power BI Desktop
- **Tabular Object Model (TOM)** — .NET API for semantic model management
- **ADOMD.NET** — .NET client for DAX query execution

All Microsoft product names are trademarks of Microsoft Corporation.
This project is not affiliated with, endorsed by, or sponsored by Microsoft.

---

## Community

Built with gratitude for the Power BI community, SQLBI, the Power BI Guy, Guy in a Cube, and every practitioner who has shared knowledge publicly over the years.
