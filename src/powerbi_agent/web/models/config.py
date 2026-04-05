"""Pydantic models for the configuration tool."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# ── Source Types ──────────────────────────────────────────────────────────────

class SourceType(str, Enum):
    database   = "database"
    api        = "api"
    csv        = "csv"
    webscrape  = "webscrape"


class DatabaseDialect(str, Enum):
    sqlserver  = "sqlserver"
    postgresql = "postgresql"
    mysql      = "mysql"
    oracle     = "oracle"
    snowflake  = "snowflake"
    sqlite     = "sqlite"


class AuthType(str, Enum):
    basic        = "basic"
    bearer       = "bearer"
    oauth2       = "oauth2"
    api_key      = "api_key"
    none         = "none"


class LoadStrategy(str, Enum):
    full_load    = "full_load"
    incremental  = "incremental"
    cdc          = "cdc"


class DatabaseSourceConfig(BaseModel):
    dialect: DatabaseDialect = DatabaseDialect.sqlserver
    host: str = ""
    port: int = 1433
    database: str = ""
    username: str = ""
    password: str = ""          # stored encrypted in prod
    schema_name: str = "dbo"
    tables: list[str] = Field(default_factory=list)
    load_strategy: LoadStrategy = LoadStrategy.incremental
    watermark_column: str = ""
    use_key_vault: bool = False
    key_vault_url: str = ""


class APISourceConfig(BaseModel):
    base_url: str = ""
    auth_type: AuthType = AuthType.bearer
    auth_value: str = ""         # token / key
    headers: dict[str, str] = Field(default_factory=dict)
    pagination_type: str = "offset"    # offset | cursor | link_header
    page_size: int = 100
    endpoints: list[dict[str, str]] = Field(default_factory=list)
    load_strategy: LoadStrategy = LoadStrategy.incremental
    watermark_field: str = "updatedAt"


class CSVSourceConfig(BaseModel):
    upload_path: str = ""
    delimiter: str = ","
    encoding: str = "utf-8"
    has_header: bool = True
    date_format: str = "%Y-%m-%d"
    null_values: list[str] = Field(default_factory=lambda: ["", "NULL", "null", "N/A", "na"])
    skip_rows: int = 0


class WebscrapeSourceConfig(BaseModel):
    url: str = ""
    css_selector: str = ""
    xpath: str = ""
    pagination_selector: str = ""
    max_pages: int = 10
    rate_limit_seconds: float = 1.0
    headers: dict[str, str] = Field(default_factory=lambda: {
        "User-Agent": "Mozilla/5.0 (compatible; powerbi-agent/1.0)"
    })


class DataSource(BaseModel):
    id: str = ""
    name: str = ""
    description: str = ""
    source_type: SourceType = SourceType.database
    enabled: bool = True
    target_table: str = ""       # bronze layer target
    database_config: DatabaseSourceConfig | None = None
    api_config: APISourceConfig | None = None
    csv_config: CSVSourceConfig | None = None
    webscrape_config: WebscrapeSourceConfig | None = None
    tags: list[str] = Field(default_factory=list)


# ── Rule Engine ───────────────────────────────────────────────────────────────

class RuleType(str, Enum):
    not_null        = "not_null"
    unique          = "unique"
    regex           = "regex"
    range_check     = "range_check"
    allowed_values  = "allowed_values"
    type_cast       = "type_cast"
    rename          = "rename"
    derive          = "derive"
    drop_column     = "drop_column"
    trim_whitespace = "trim_whitespace"
    fill_null       = "fill_null"
    custom_sql      = "custom_sql"


class RuleAction(str, Enum):
    fail_pipeline   = "fail_pipeline"
    flag_and_pass   = "flag_and_pass"
    quarantine      = "quarantine"
    drop_row        = "drop_row"
    replace_value   = "replace_value"


class Rule(BaseModel):
    id: str = ""
    name: str = ""
    description: str = ""
    rule_type: RuleType = RuleType.not_null
    applies_to: str = ""          # table or "all"
    column: str = ""
    parameters: dict[str, Any] = Field(default_factory=dict)
    action_on_fail: RuleAction = RuleAction.flag_and_pass
    enabled: bool = True
    order: int = 0


# ── Raw Data Model ─────────────────────────────────────────────────────────────

class ColumnDefinition(BaseModel):
    name: str = ""
    source_column: str = ""
    data_type: str = "VARCHAR"
    nullable: bool = True
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references_table: str = ""
    references_column: str = ""
    description: str = ""
    pii: bool = False
    default_value: str = ""


class TableDefinition(BaseModel):
    name: str = ""
    description: str = ""
    source_id: str = ""
    layer: str = "bronze"          # bronze | silver | gold
    columns: list[ColumnDefinition] = Field(default_factory=list)
    partition_column: str = ""
    cluster_columns: list[str] = Field(default_factory=list)
    scd_type: int = 0              # 0 = not SCD, 1, 2, or 6


# ── Pipeline Workflow ─────────────────────────────────────────────────────────

class FabricConfig(BaseModel):
    workspace_name: str = ""
    lakehouse_name: str = ""
    semantic_model_name: str = ""
    enable_directlake: bool = True
    refresh_schedule: str = "0 6 * * *"   # cron
    enable_incremental_refresh: bool = True
    rolling_window_years: int = 3
    incremental_days: int = 7


# ── Root Config ───────────────────────────────────────────────────────────────

class ProjectConfig(BaseModel):
    project_name: str = "My Data Platform"
    description: str = ""
    version: str = "0.1.0"
    sources: list[DataSource] = Field(default_factory=list)
    rules: list[Rule] = Field(default_factory=list)
    tables: list[TableDefinition] = Field(default_factory=list)
    fabric: FabricConfig = Field(default_factory=FabricConfig)
