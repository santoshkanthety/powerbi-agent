#!/usr/bin/env python3
"""Validate skill files against the shared skill schema.

This script is intentionally identical in powerbi-agent and databricks-agent —
the two packs are adapters over one delivery doctrine, so they validate against
one schema. Keep the two copies in sync when either changes.

Schema (see SKILL_SCHEMA.md):

  * layout      skills/<skill-name>/SKILL.md
  * name        matches the directory name, kebab-case, platform-prefixed
  * description non-empty, single line, folds trigger phrases in, <= 1024 chars
  * license     present
  * frontmatter only Agent Skills spec fields, so the pack also survives
                claude.ai / Skills API upload, which hard-errors on extra keys

Usage:  python scripts/validate_skills.py [skills_dir]
Exit code 0 = valid, 1 = one or more violations.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# The Agent Skills spec fields accepted everywhere: Claude Code, claude.ai
# uploads, and the Skills API. Anything else fails packaging with
# "Unexpected key(s) in SKILL.md frontmatter".
ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
REQUIRED_KEYS = {"name", "description"}
MAX_DESCRIPTION = 1024
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str | None]:
    """Return (frontmatter, error). Only top-level scalar keys are read."""
    if not text.startswith("---"):
        return {}, "missing YAML frontmatter block"
    end = text.find("\n---", 3)
    if end == -1:
        return {}, "unterminated YAML frontmatter block"

    fm: dict[str, str] = {}
    for line in text[3:end].splitlines():
        if not line.strip():
            continue
        if line[:1].isspace():
            return {}, f"nested/multi-line frontmatter value not allowed: {line.strip()!r}"
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            return {}, f"unparseable frontmatter line: {line.strip()!r}"
        fm[m.group(1)] = m.group(2).strip()
    return fm, None


def validate(skills_dir: Path) -> list[str]:
    errors: list[str] = []

    stray = sorted(p.name for p in skills_dir.glob("*.md"))
    if stray:
        errors.append(
            f"flat skill files found in {skills_dir}/ — Claude Code only discovers <skill-name>/SKILL.md: {', '.join(stray)}"
        )

    dirs = sorted(p for p in skills_dir.iterdir() if p.is_dir())
    if not dirs:
        errors.append(f"no skill directories found in {skills_dir}/")

    for d in dirs:
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            errors.append(f"{d.name}/: missing SKILL.md")
            continue

        fm, err = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
        if err:
            errors.append(f"{d.name}/SKILL.md: {err}")
            continue

        missing = REQUIRED_KEYS - fm.keys()
        if missing:
            errors.append(f"{d.name}/SKILL.md: missing required key(s): {', '.join(sorted(missing))}")

        extra = fm.keys() - ALLOWED_KEYS
        if extra:
            errors.append(
                f"{d.name}/SKILL.md: non-spec frontmatter key(s) {', '.join(sorted(extra))} — "
                f"allowed: {', '.join(sorted(ALLOWED_KEYS))}"
            )

        name = fm.get("name", "")
        if name and name != d.name:
            errors.append(f"{d.name}/SKILL.md: name {name!r} does not match directory name")
        if name and not NAME_RE.match(name):
            errors.append(f"{d.name}/SKILL.md: name {name!r} is not kebab-case")

        desc = fm.get("description", "")
        if desc and len(desc) > MAX_DESCRIPTION:
            errors.append(f"{d.name}/SKILL.md: description is {len(desc)} chars (max {MAX_DESCRIPTION})")
        if "description" in fm and not desc:
            errors.append(f"{d.name}/SKILL.md: description is empty")

    return errors


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    skills_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "skills"
    if not skills_dir.is_dir():
        print(f"skills directory not found: {skills_dir}", file=sys.stderr)
        return 1

    errors = validate(skills_dir)
    if errors:
        print(f"✗ {len(errors)} schema violation(s):\n", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    count = sum(1 for p in skills_dir.iterdir() if (p / "SKILL.md").exists())
    print(f"✓ {count} skills valid against the shared schema")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
