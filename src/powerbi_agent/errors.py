"""User-facing error types for powerbi-agent.

Click-integrated exceptions so failures render cleanly through the CLI.

Patterned after pbi-cli (https://github.com/MinaSaad1/pbi-cli, MIT) —
independently written for this codebase.
"""

from __future__ import annotations

import click


class PowerBIAgentError(click.ClickException):
    """Base error for all powerbi-agent user-facing failures."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class DotNetNotFoundError(PowerBIAgentError):
    """Raised when pythonnet or the bundled .NET DLLs are missing."""

    def __init__(
        self,
        message: str = (
            "pythonnet is required for Desktop features. "
            "Install it with: pip install powerbi-agent[desktop]"
        ),
    ) -> None:
        super().__init__(message)


class ConnectionRequiredError(PowerBIAgentError):
    """Raised when a command requires an active connection but none exists."""

    def __init__(
        self,
        message: str = (
            "Not connected to any Power BI Desktop instance.\n"
            "Run: pbi-agent connect"
        ),
    ) -> None:
        super().__init__(message)


class InstanceNotFoundError(PowerBIAgentError):
    """Raised when no running Power BI Desktop instance can be detected."""

    def __init__(
        self,
        message: str = (
            "No Power BI Desktop instances found. "
            "Open a .pbix file in Power BI Desktop, then re-run."
        ),
    ) -> None:
        super().__init__(message)


class TomError(PowerBIAgentError):
    """Raised when a TOM operation fails."""

    def __init__(self, operation: str, detail: str) -> None:
        self.operation = operation
        self.detail = detail
        super().__init__(f"{operation}: {detail}")


class DaxQueryError(PowerBIAgentError):
    """Raised when a DAX query fails to parse or execute."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(f"DAX error: {detail}")


class ReportNotFoundError(PowerBIAgentError):
    """Raised when no PBIR report definition folder can be found."""

    def __init__(
        self,
        message: str = (
            "No PBIR report found. Run this command inside a .pbip project "
            "or pass --path to the .Report folder."
        ),
    ) -> None:
        super().__init__(message)


class VisualError(PowerBIAgentError):
    """Raised when a visual or custom-visual operation fails."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)
