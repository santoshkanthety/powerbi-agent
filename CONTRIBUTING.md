# Contributing to powerbi-agent

Thank you for helping make Power BI automation better for everyone.

## Ways to Contribute

**No Python required:**
- Improve a skill file in `skills/` (just Markdown)
- Add a real-world DAX example to `dax-mastery.md`
- Report a bug with reproduction steps
- Add a missing CLI command to the docs

**With Python:**
- Add a new CLI command
- Improve error messages
- Write tests for existing commands
- Add Fabric API coverage

## Getting Started

```bash
git clone https://github.com/santoshkanthety/powerbi-agent
cd powerbi-agent
pip install -e ".[dev]"
pre-commit install
pytest
```

## Submitting a PR

1. Fork the repo
2. Create a branch: `git checkout -b feat/my-improvement`
3. Make your change
4. Add a test if you changed Python code
5. Run `pytest` and `ruff check src/`
6. Open a PR — describe what you changed and why

## Skill Files

Each file in `skills/` is a Markdown document that teaches Claude a domain.
Format:

```markdown
# Skill: [Name]

## Trigger
Keywords that activate this skill.

## What You Know
Domain expertise — patterns, anti-patterns, examples, CLI commands.
```

## Code Style

- `ruff` for linting: `ruff check src/`
- Type hints on public functions
- Docstrings on public modules and classes
- Tests in `tests/` using pytest

## Questions?

Open a [Discussion](https://github.com/santoshkanthety/powerbi-agent/discussions) — no question is too small.
