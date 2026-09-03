---
applyTo: "**/*.py"
description: "Python coding standards: ruff, flake8, mypy, typing, docstrings, testing."
---

# Python Coding Standards

**When generating or modifying Python code**, follow these standards. New code must pass the quality
gate (`make lint` and `make test`) with zero warnings or errors.

---

## Lint & Type Checking

The enforced tools are **ruff** (lint + import sort), **flake8**, and **mypy**, all pinned to a
120-character line width.

```bash
make lint    # ruff check . + flake8 src/bear_tools + mypy src/bear_tools
make test    # pytest
```

- Run linters as **separate** commands; don't chain them in a way that hides a failure.
- Auto-fix with `poetry run ruff check <path> --fix`.
- **New code:** zero warnings/errors. **Existing issues:** don't fix unrelated ones unless asked.
- Ruff's active rule families are `E, F, I, T` (with `T201` allowed); flake8 config lives in `.flake8`.
  `pylint` is configured in `pyproject.toml` for local use but is not part of `make lint`.

---

## Code Style

### Type hints

- **Required on public functions, methods, and attributes.**
- Prefer modern built-in generics (`list[str]`, `dict[str, int]`, `X | None`) over `typing.List` etc.
- `from __future__ import annotations` is used across the package — keep new modules consistent.

### Line length

- **120 characters maximum** (see `general.instructions.md` for whitespace/EOF rules).

### Docstrings

- **reST / Sphinx-style** (`:param:` / `:return:`) — match the existing modules, not Google or NumPy.

  ```python
  def find_ip_addresses(regex: str) -> list[str]:
      """
      Short one-line summary.

      :param regex: What this parameter is for
      :return: What the function returns
      """
  ```

### Avoid magic values

- Don't hardcode bare numbers/strings for identifiers, opcodes, or status codes — use enums or named
  constants (see `enhanced_enum` / `enhanced_int_enum`) so intent is greppable and type-checked.

### Keep modules generic

- Utilities should be self-contained and dependency-light. Put a new helper in the module that owns its
  domain (or a new top-level module) rather than folding it into an unrelated one.

---

## Testing

- **pytest** (+ `pytest-mock`, `pytest-cov`). Tests live in `tests/bear_tools/`, mirroring the
  `src/bear_tools/` layout, named `test_<module>.py`.
- Write focused tests for new behavior; mock external calls (subprocess, network, filesystem) rather
  than depending on host state.
- Run the suite with `make test`; check coverage with `make coverage`.

---

## Quick Checklist

Before submitting Python code:

- [ ] `make lint` (ruff + flake8 + mypy) passes with no errors
- [ ] All public functions/methods/attributes have type hints
- [ ] reST-style docstrings (`:param:` / `:return:`) on public API
- [ ] No magic numbers/values (use enums/constants)
- [ ] `make test` passes; tests added/updated for behavior changes
