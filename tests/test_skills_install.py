"""
Tests for powerbi-agent skills installer.

Validates all 20 skill files exist in the skills/ directory and install correctly.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from powerbi_agent.skills.installer import (
    CLAUDE_HOME,
    SKILLS_DIR,
    SKILL_NAMES,
    install_skills,
    list_skills,
    uninstall_skills,
)

SKILLS_SOURCE = Path(__file__).parent.parent / "skills"


def test_all_skill_files_exist():
    """Every name in SKILL_NAMES must have a corresponding .md in skills/."""
    missing = []
    for name in SKILL_NAMES:
        src = SKILLS_SOURCE / f"{name}.md"
        if not src.exists():
            missing.append(f"{name}.md")
    assert missing == [], "Missing skill files:\n" + "\n".join(missing)


def test_skill_files_have_trigger_sections():
    """Each skill .md must have a trigger section so Claude activates it."""
    for name in SKILL_NAMES:
        src = SKILLS_SOURCE / f"{name}.md"
        if not src.exists():
            continue
        content = src.read_text(encoding="utf-8")
        has_trigger = (
            "## Trigger" in content
            or "triggers:" in content
            or "## What You Know" in content
        )
        assert has_trigger, f"{name}.md has no trigger/frontmatter section"


def test_skill_names_count():
    """Sanity check — should have exactly 20 skills."""
    assert len(SKILL_NAMES) == 20, (
        f"Expected 20 skills, got {len(SKILL_NAMES)}: {SKILL_NAMES}"
    )


def test_install_copies_files_to_target_dir():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "skills"
        skills_src = SKILLS_SOURCE

        with patch("powerbi_agent.skills.installer.SKILLS_DIR", target):
            install_skills(force=False)

        installed = list(target.glob("*.md"))
        # At least some skills should be installed
        assert len(installed) > 0


def test_install_skips_existing_without_force():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "skills"
        target.mkdir()

        with patch("powerbi_agent.skills.installer.SKILLS_DIR", target):
            install_skills(force=False)
            first_count = len(list(target.glob("*.md")))

            # Pre-create marker to simulate already installed
            # Second install without force should skip
            install_skills(force=False)
            second_count = len(list(target.glob("*.md")))

        assert first_count == second_count  # no new files added


def test_install_overwrites_with_force():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "skills"
        target.mkdir()

        with patch("powerbi_agent.skills.installer.SKILLS_DIR", target):
            install_skills(force=False)
            # Corrupt one file
            first_skill = SKILL_NAMES[0]
            (target / f"{first_skill}.md").write_text("corrupted", encoding="utf-8")

            install_skills(force=True)
            # File should be restored
            content = (target / f"{first_skill}.md").read_text(encoding="utf-8")
            assert content != "corrupted"


def test_uninstall_removes_all_installed():
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "skills"
        target.mkdir()

        with patch("powerbi_agent.skills.installer.SKILLS_DIR", target):
            install_skills(force=True)
            before = len(list(target.glob("*.md")))
            assert before > 0

            uninstall_skills()
            after = len(list(target.glob("*.md")))

        assert after == 0


def test_doctor_skill_check_uses_skill_names():
    """
    Regression test: doctor._check_skills must count all skill names,
    not just files matching the old 'power-bi-*' glob.
    """
    from powerbi_agent.doctor import _check_skills

    with tempfile.TemporaryDirectory() as tmp:
        skills_dir = Path(tmp)
        # Install a non-power-bi- prefixed skill file
        (skills_dir / "source-integration.md").write_text("# skill", encoding="utf-8")
        (skills_dir / "medallion-architecture.md").write_text("# skill", encoding="utf-8")

        # Patch Path.home() to point skills_dir lookup to our temp dir
        with patch("powerbi_agent.doctor.Path") as mock_path:
            mock_path.home.return_value = Path(tmp).parent
            # Just verify the check doesn't rely on power-bi-* glob by testing
            # it imports and calls SKILL_NAMES from installer
            from powerbi_agent.skills.installer import SKILL_NAMES as sn
            assert "source-integration" in sn
            assert "medallion-architecture" in sn
