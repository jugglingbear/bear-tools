# Bear Tools — Copilot Instructions

> **Read [`AGENTS.md`](../AGENTS.md) first.** It is the agent-agnostic source of truth for this
> repository's structure, tech stack, conventions, and quality gate. This file only notes how
> VS Code / Copilot picks up customizations.

## Customization file layout

| Form | Location | Loaded |
|------|----------|--------|
| Agent-agnostic instructions | `AGENTS.md` (repo root) | Always |
| Copilot-specific notes | `.github/copilot-instructions.md` (this file) | Always |
| File-scoped instructions | `.github/instructions/*.instructions.md` | Auto-attached via `applyTo` glob |
| Reusable prompts | `.github/prompts/*.prompt.md` | On demand (invoke by name) |

The file-scoped instructions auto-attach by glob:

- `general.instructions.md` (`**`) — whitespace, EOF, line length.
- `python.instructions.md` (`**/*.py`) — ruff, flake8, mypy, typing, docstrings, testing.
- `markdown.instructions.md` (`**/*.md`) — MkDocs (Material) Markdown formatting.
- `makefile.instructions.md` (`**/Makefile,**/*.mk`) — self-documenting help, colors, standard targets.

## Before generating code

- Match the existing stack: **Poetry** package, **ruff + flake8 + mypy**, **pytest**, **MkDocs
  (Material)** docs. Python 3.10+, fully type-hinted, reST-style docstrings, 120-char lines.
- Run `make lint` and `make test` before considering a change complete.
- Keep utilities **generic and self-contained**; import submodules directly rather than assuming a
  re-export. See `AGENTS.md` for the full conventions.
