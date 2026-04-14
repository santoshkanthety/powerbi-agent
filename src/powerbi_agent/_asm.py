"""
Shared .NET assembly resolver for Power BI Desktop / Report Builder DLLs.

pythonnet's ``clr.AddReference()`` only searches the GAC and the current
working directory by default.  The TOM (Microsoft.AnalysisServices.Tabular)
and ADOMD (Microsoft.AnalysisServices.AdomdClient) assemblies ship inside
the **Power BI Report Builder** install directory, which is *not* on the
default CLR search path.

This module:
1. Locates the Report Builder install directory.
2. Registers a CLR ``AssemblyResolve`` handler so ``clr.AddReference()``
   finds the DLLs automatically.
3. Provides a ``disposable()`` context-manager wrapper that works around
   the pythonnet 3.x removal of automatic ``IDisposable`` → context-manager
   mapping.

Call ``ensure_assemblies()`` once before using any TOM/ADOMD types.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from rich.console import Console

console = Console()

# Cached after first successful discovery
_report_builder_dir: Path | None = None
_resolver_registered: bool = False


def find_report_builder_dir() -> Path | None:
    """
    Locate the Power BI Report Builder directory that contains the
    Analysis Services DLLs (TOM + ADOMD).

    Search order:
      1. ``PBI_REPORT_BUILDER`` environment variable (explicit override).
      2. Common install paths under Program Files (x86).
    """
    global _report_builder_dir

    if _report_builder_dir is not None:
        return _report_builder_dir

    # 1. Env-var override
    env_path = os.environ.get("PBI_REPORT_BUILDER")
    if env_path:
        p = Path(env_path)
        if p.is_dir():
            _report_builder_dir = p
            return _report_builder_dir

    # 2. Well-known install locations
    candidates = [
        Path(r"C:\Program Files (x86)\Microsoft Power BI Report Builder"),
        Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"))
        / "Microsoft Power BI Report Builder",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            _report_builder_dir = candidate
            return _report_builder_dir

    return None


def _register_assembly_resolver() -> None:
    """
    Register a CLR ``AssemblyResolve`` event handler that looks for DLLs
    in the Report Builder directory.  Called once by ``ensure_assemblies()``.
    """
    global _resolver_registered
    if _resolver_registered:
        return

    rb_dir = find_report_builder_dir()
    if rb_dir is None:
        return  # nothing to register; AddReference will fail with a clear message later

    import clr  # noqa: F401 – side-effect: initialises pythonnet runtime
    import System  # type: ignore[import-untyped]

    def _resolve(sender: object, args: object) -> object | None:
        """Resolve assemblies by probing the Report Builder directory."""
        # .NET fully-qualified assembly names include version/culture info
        # after the first comma, e.g. "AssemblyName, Version=1.0, Culture=neutral, ...".
        # We only need the short name to locate the DLL file.
        name = str(args.Name).split(",")[0]  # type: ignore[union-attr]
        dll = rb_dir / f"{name}.dll"
        if dll.exists():
            return System.Reflection.Assembly.LoadFrom(str(dll))
        return None

    System.AppDomain.CurrentDomain.AssemblyResolve += _resolve  # type: ignore[operator]
    _resolver_registered = True


def ensure_assemblies() -> None:
    """
    Ensure the TOM / ADOMD assemblies are resolvable.

    * On first call: locates Report Builder, registers the assembly resolver,
      and adds the directory to ``sys.path`` so ``clr.AddReference()`` works.
    * Subsequent calls are no-ops.

    Raises ``ImportError`` with actionable guidance when pythonnet is missing.
    """
    try:
        import clr  # noqa: F401
    except ImportError:
        console.print(
            "[red]pythonnet not installed.[/red]\n"
            "Install: [bold]pip install powerbi-agent[desktop][/bold]"
        )
        sys.exit(1)

    rb_dir = find_report_builder_dir()
    if rb_dir is not None:
        rb_str = str(rb_dir)
        if rb_str not in sys.path:
            sys.path.insert(0, rb_str)

    _register_assembly_resolver()


# ── pythonnet 3.x IDisposable helper ──────────────────────────────────────────


@contextmanager
def disposable(obj: object) -> Generator:
    """
    Context-manager wrapper for .NET ``IDisposable`` objects.

    pythonnet 3.x removed the automatic ``__enter__``/``__exit__`` mapping
    that 2.x provided for ``IDisposable``.  This wrapper calls ``Dispose()``
    in the ``finally`` block so you can write::

        with disposable(AdomdConnection(conn_str)) as conn:
            conn.Open()
            ...

    If the object does not have a ``Dispose`` method the block still executes
    normally and cleanup is skipped.
    """
    try:
        yield obj
    finally:
        dispose = getattr(obj, "Dispose", None)
        if callable(dispose):
            dispose()
