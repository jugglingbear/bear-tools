---
applyTo: "**"
description: "Repository-wide whitespace, EOF, and general file hygiene rules."
---

# General File Standards

These standards apply to **all file types** (Python, Markdown, YAML, TOML, JSON, Makefiles, etc.) in
this repository.

---

## Whitespace & Line Endings

- **No trailing whitespace** on any line in any file type.
- **Blank lines must contain no spaces or tabs.**
- **Every file must end with exactly one newline.**

---

## Line Length

- **120 characters maximum** for Python and Markdown. Reflow long prose to stay within the limit.
- Other formats: follow the language/format convention (Makefiles use tabs for recipes; YAML/TOML as
  the format dictates).

---

## When to Apply These Standards

- **New files:** must comply with all standards from creation.
- **Modified files:** only the modified sections need to comply — do not reformat unrelated regions
  unless explicitly requested.
