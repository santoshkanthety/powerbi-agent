"""
powerbi-agent — AI-powered Power BI automation for Claude Code.

Give Claude Code enterprise-grade Power BI superpowers.
Community-driven, open-source, Python-first.
"""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__ = _pkg_version("powerbi-agent")
except PackageNotFoundError:
    __version__ = "0.0.0+dev"

__author__ = "Santosh Kanthety"
__license__ = "MIT"
