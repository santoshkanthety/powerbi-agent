"""
Tests for powerbi-agent skills installer.

Validates skills follow the shared schema (see SKILL_SCHEMA.md) and install into
the canonical ~/.claude/skills/<skill-name>/SKILL.md layout that Claude Code
actually discovers.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from powerbi_agent.skills.installer import (
    SKILL_NAMES,
    install_skills,
    list_skills,
    read_skill_description,
    uninstall_skills,
)

REPO_ROOT = Path(__file__).parent.parent
SKILLS_SOURCE = REPO_ROOT / "skills"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from validate_skills import validate  # noqa: E402


def test_all_skills_exist():
    """Every name in SKILL_NAMES must have a corresponding skills/<name>/SKILL.md."""
    missing = [n for n in SKILL_NAMES if not (SKILLS_SOURCE / n / "SKILL.md").exists()]
    assert missing == [], "Missing skills:\n" + "\n".join(missing)


def test_skill_names_match_disk():
    """SKILL_NAMES and the skills/ directory must not drift apart."""
    on_disk = {p.name for p in SKILLS_SOURCE.iterdir() if (p / "SKILL.md").exists()}
    assert set(SKILL_NAMES) == on_disk, (
        f"SKILL_NAMES has {len(SKILL_NAMES)} entries, skills/ has {len(on_disk)}. "
        f"Only in SKILL_NAMES: {sorted(set(SKILL_NAMES) - on_disk)}. "
        f"Only on disk: {sorted(on_disk - set(SKILL_NAMES))}."
    )


def test_skills_pass_shared_schema_validator():
    """The same validator runs in databricks-agent — the two packs share one schema."""
    errors = validate(SKILLS_SOURCE)
    assert errors == [], "Schema violations:\n" + "\n".join(errors)


def test_every_skill_is_platform_prefixed():
    """Prefixes prevent collisions with databricks-agent's identically named skills."""
    unprefixed = [n for n in SKILL_NAMES if not n.startswith("powerbi-")]
    assert unprefixed == [], f"Skills missing the powerbi- prefix: {unprefixed}"


def test_every_skill_has_trigger_text_in_description():
    """Claude routes on description, so trigger phrases must be folded into it."""
    thin = []
    for name in SKILL_NAMES:
        desc = read_skill_description(SKILLS_SOURCE / name / "SKILL.md")
        if len(desc) < 40:
            thin.append(f"{name}: {desc!r}")
    assert thin == [], "Descriptions too thin to route on:\n" + "\n".join(thin)


def test_no_flat_skill_files_remain():
    """Flat skills/<name>.md files are never discovered by Claude Code."""
    stray = sorted(p.name for p in SKILLS_SOURCE.glob("*.md"))
    assert stray == [], f"Flat skill files must be converted to <name>/SKILL.md: {stray}"


def test_install_creates_canonical_layout():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "skills"

        with patch("powerbi_agent.skills.installer.SKILLS_DIR", target):
            install_skills(force=False)

        installed = [d for d in target.iterdir() if (d / "SKILL.md").exists()]
        assert len(installed) == len(SKILL_NAMES)
        assert list(target.glob("*.md")) == [], "installer must not write flat .md files"


def test_install_skips_existing_without_force():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "skills"
        target.mkdir()

        with patch("powerbi_agent.skills.installer.SKILLS_DIR", target):
            install_skills(force=False)
            first = len(list(target.iterdir()))
            install_skills(force=False)
            second = len(list(target.iterdir()))

        assert first == second


def test_install_overwrites_with_force():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "skills"
        target.mkdir()

        with patch("powerbi_agent.skills.installer.SKILLS_DIR", target):
            install_skills(force=False)
            corrupted = target / SKILL_NAMES[0] / "SKILL.md"
            corrupted.write_text("corrupted", encoding="utf-8")

            install_skills(force=True)
            assert corrupted.read_text(encoding="utf-8") != "corrupted"


def test_install_cleans_up_legacy_flat_files():
    """Upgrading from <=0.5 must remove the dead flat files it left behind."""
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "skills"
        target.mkdir()
        (target / "dax-mastery.md").write_text("legacy", encoding="utf-8")
        (target / "medallion-architecture.md").write_text("legacy", encoding="utf-8")
        (target / "unrelated-other-tool.md").write_text("keep me", encoding="utf-8")

        with patch("powerbi_agent.skills.installer.SKILLS_DIR", target):
            install_skills(force=True)

        assert not (target / "dax-mastery.md").exists()
        assert not (target / "medallion-architecture.md").exists()
        assert (target / "unrelated-other-tool.md").exists(), "must not touch other tools' files"


def test_uninstall_removes_all_installed():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "skills"
        target.mkdir()

        with patch("powerbi_agent.skills.installer.SKILLS_DIR", target):
            install_skills(force=True)
            assert len(list(target.iterdir())) > 0
            uninstall_skills()
            assert list(target.iterdir()) == []


def test_list_skills_runs():
    with tempfile.TemporaryDirectory() as tmp:
        with patch("powerbi_agent.skills.installer.SKILLS_DIR", Path(tmp)):
            list_skills()


def test_doctor_counts_directory_layout():
    """Regression: doctor must look for <name>/SKILL.md, not <name>.md."""
    from powerbi_agent.doctor import _check_skills

    assert _check_skills is not None
    src = (REPO_ROOT / "src/powerbi_agent/doctor.py").read_text(encoding="utf-8")
    assert 'skills_dir / s / "SKILL.md"' in src
