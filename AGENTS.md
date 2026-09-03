# Bear Tools — Agent Instructions

This file is the **agent-agnostic** source of truth for AI coding assistants working in this
repository (Copilot, Claude Code, Cursor, Aider, Codex, Continue, etc.). Tool-specific extensions
live alongside it:

- `.github/copilot-instructions.md` — GitHub Copilot / VS Code extensions
- `.github/instructions/*.instructions.md` — File-type-scoped rules auto-attached by `applyTo` glob

---

## Repository Overview

**Bear Tools** (`bear_tools`) is a collection of QA/Automation-related Python utilities, published to
PyPI as `bear-tools`. It is a single importable library — consumers install it (`pip install bear-tools`)
and import submodules directly (e.g. `from bear_tools.network_utils import find_ip_addresses`).

### Layout

| Path | Purpose |
|------|---------|
| `src/bear_tools/` | The library (`src`-layout). Standalone utility modules plus subpackages. Ships `py.typed`. |
| `src/bear_tools/*.py` | Utility modules (e.g. `network_utils`, `os_utils`, `string_utils`, `security_utils`, `usb_utils`). |
| `src/bear_tools/<subpkg>/` | Cohesive subpackages: `cereal`, `fsm`, `lumberjack`, `publisher`. |
| `tests/bear_tools/` | Pytest suite mirroring the `src/bear_tools/` layout (`test_<module>.py`). |
| `docs/` | MkDocs (Material) documentation sources. |
| `samples/` | Runnable example scripts that exercise the library. |

Utilities are **generic and self-contained** — each module owns one area (networking, macOS helpers,
strings, YAML, threading, time, spreadsheets, …) and avoids hard dependencies on the others.

---

## Tech Stack

- **Python** 3.10+ (`from __future__ import annotations` is used throughout), packaged with **Poetry**.
- **Lint:** `ruff` (lint + import sort) and `flake8`, both pinned to a 120-character line width. `mypy`
  for type checking. (`pylint` is configured in `pyproject.toml` for local use but is not part of
  `make lint`.)
- **Tests:** `pytest` (+ `pytest-cov`, `pytest-mock`, `pytest-watch`).
- **Docs:** **MkDocs** with the **Material** theme (`mkdocs.yml`).

---

## Core Conventions

- **Type hints everywhere.** Public functions/methods are fully annotated; prefer modern built-in
  generics (`list[str]`, `dict[str, int]`, `X | None`).
- **reST / Sphinx-style docstrings** (`:param:` / `:return:`) — match the existing modules, not Google
  or NumPy style.
- **120-character** line width everywhere (enforced by ruff and flake8).
- **Submodule imports.** Consumers import submodules directly; not every module is re-exported from
  `bear_tools/__init__.py`. Only add a module to `__init__.py`'s import list + `__all__` when a
  first-class re-export is intended.
- **Keep modules generic and dependency-light.** A new helper belongs in the module that owns its
  domain (or a new top-level module) rather than being folded into an unrelated one.
- **Avoid magic values.** Use enums or named constants (see `enhanced_enum` / `enhanced_int_enum`) so
  intent is greppable and type-checked.
- **File hygiene:** no trailing whitespace; every file ends with exactly one newline.

---

## Quality Gate

Run before considering work done:

```bash
make lint    # ruff + flake8 + mypy
make test    # pytest
```

- **New code must pass `make lint` and `make test` with zero warnings/errors.**
- Don't fix unrelated pre-existing issues unless asked.
- Add or update tests in `tests/bear_tools/` for any behavior change.

---

## Scratch / Temporary Files

Keep throwaway scripts, scratch output, and intermediate artifacts out of tracked directories — never
leave them in `src/`, `tests/`, or `docs/`, and don't commit them. Never write scratch to `/tmp/`; use a
local, git-ignored scratch location instead.

---

## Quick Reference

| Task | Command |
|------|---------|
| Lint (ruff + flake8 + mypy) | `make lint` |
| Run tests | `make test` |
| Test coverage report | `make coverage` |
| Build + serve docs locally | `make docs-dev` |
| Remove build/test artifacts | `make clean` |
| Build + publish to PyPI | `make publish` |

Type `make help` for the full, always-current list.
