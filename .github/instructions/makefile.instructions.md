---
applyTo: "**/Makefile,**/*.mk"
description: "Makefile conventions: self-documenting help system, standard targets, ANSI colors."
---

# Makefile Standards

**When creating or modifying Makefiles**, follow these conventions for a consistent, user-friendly
experience. This repository's root `Makefile` is the reference implementation.

---

## Self-Documenting Help System

Every Makefile **must** include a `help` target that prints colorized usage. Typing `make` or
`make help` should show a scannable list of available targets.

### How it works

1. Each user-facing target's help text is an **inline `## Description`** comment on the target line.
2. The `help` target runs a `grep` + `awk` pass over `$(MAKEFILE_LIST)` and prints the targets.
3. `help` is the **first target**, so it is the default goal when `make` is run with no arguments.

### Template

```makefile
.PHONY: help
help:  ## Show this help message
	@echo "\n\033[1mAvailable targets:\033[0m"
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: lint
lint:  ## Run the linters
	poetry run ruff check .

.PHONY: test
test:  ## Run the test suite
	poetry run pytest -v tests
```

### Rules

- **Every `.PHONY` target users should invoke** gets a `## Description` comment.
- **Internal/helper targets** get **no** `##` comment — that keeps them out of the help listing.
- Target names use **lowercase kebab-case**: `docs-dev`, `coverage`.
- Bump the `%-20s` column width if target names grow longer.

---

## Recipe Conventions

- **Tabs, not spaces**, for recipe indentation — Makefiles require it.
- Declare non-file targets `.PHONY`.
- Prefix commands with `@` when you want their output but not the command line itself echoed.
- Use emoji markers in `@echo` output to make progress scannable (see below).

---

## Emoji Conventions

Use emoji as visual markers in `@echo` output to make progress scannable:

| Emoji | Meaning |
|-------|---------|
| 🎯 | Analyzing / measuring (e.g. coverage) |
| 🧪 | Running tests |
| 🫣 | Running ruff |
| 🧹 | Linting (flake8) |
| 🔍 | Type-checking (mypy) |
| 🧼 | Cleaning artifacts |
| 📦 | Building / packaging / publishing |
| 👷🏻 | Building docs |
| 🌐 | Serving docs / networking |

---

## ANSI Color Reference

| Code | Color | Usage |
|------|-------|-------|
| `\033[1m` | Bold | Help banner |
| `\033[0m` | Reset | End of styled text |
| `\033[36m` | Cyan | Target names in help |

---

## Anti-Patterns

- **No `##` comment on a user-facing target** — it won't appear in `make help`.
- **Spaces for recipe indentation** — Makefiles **require tabs**.
- **Hardcoding tool paths** you might want to override — prefer a variable (e.g. `POETRY ?= poetry`).
