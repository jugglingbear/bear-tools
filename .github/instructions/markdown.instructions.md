---
applyTo: "**/*.md"
description: "Markdown formatting rules for the MkDocs (Material) docs site."
---

# Markdown Standards

Documentation is authored in **Markdown** and built with **MkDocs** (Material theme). Keep Markdown
clean and consistently formatted.

---

## Line Length

- **120 characters maximum** (see `general.instructions.md` for whitespace/EOF rules).
- Reflow long lines at logical points (after sentences, before lists).

---

## Formatting Rules

### Headings

- **Surround headings with blank lines** (blank line before and after).

### Lists

- **Surround lists with blank lines** (blank line before the first item and after the last).

### Consecutive bold / key-value lines

- **Separate them with blank lines** if each should render on its own line. Adjacent lines with only a
  single newline merge into one paragraph — the most common rendering bug.

  ```markdown
  <!-- Correct: each renders on its own line -->
  **Transport:** serial

  **Encoding:** length-prefixed frame

  <!-- Incorrect: both merge into one paragraph -->
  **Transport:** serial
  **Encoding:** length-prefixed frame
  ```

### URLs

- **Use `[text](url)` link syntax**, not bare URLs.

### Code blocks

- Surround fenced code blocks with blank lines; always specify a language for syntax highlighting.

---

## MkDocs Material Notes

- **Admonitions** use `!!! note` / `!!! warning` blocks (the `admonition` + `pymdownx.details`
  extensions are enabled). Prefer plain Markdown; reach for admonitions when they add clarity.
- **Tabbed content** uses `pymdownx.tabbed`; **collapsible** blocks use `pymdownx.details`.
- **Mermaid diagrams** render via `pymdownx.superfences` — use a fenced ` ```mermaid ` block. Mermaid
  label lines may exceed 120 characters; that is acceptable inside the fence.
- Build and preview locally with `make docs-dev` (serves at http://localhost:8000).

---

## Quick Checklist

Before submitting Markdown:

- [ ] Lines ≤ 120 characters
- [ ] Headings surrounded by blank lines
- [ ] Lists surrounded by blank lines
- [ ] Fenced code blocks surrounded by blank lines, with a language tag
- [ ] URLs use `[text](url)` syntax
- [ ] `make docs-dev` renders the page correctly
