---
description: "Generate a git commit message for staged changes"
agent: "agent"
---
Always re-run `git diff --cached` (and `git diff --cached --stat`) fresh every time this prompt is invoked — the
staged contents may have changed since any previous invocation in this conversation. Do NOT reuse cached diff
output from earlier turns.

Then generate a concise, well-formatted commit message for the currently staged changes, and emit it as a single
copy-pasteable block that both stages and commits.

## Output

Emit **one** fenced `sh` block the user can paste as-is:

- Start with an explicit `git add <paths>` listing every path reported by `git diff --cached --stat` — one path
  per file, never `git add .` or `git add -A`. (This re-stages exactly the current staged set so the block is
  self-contained; if you staged partial hunks, drop the `git add` line and keep only the commit.)
- Chain the commit after the add with `&&` so it only runs if staging succeeds.
- Put the subject in a single `-m "..."`; for a body, add a blank line inside the same quotes, then the wrapped
  body. Keep the subject near 50 characters and wrap body lines at 120.
- Use double quotes and keep the message plain ASCII; escape any `"`, `` ` ``, `$`, or `\` it must contain.
- Match the repo's commit-message style — inspect recent `git --no-pager log` and mirror the prevailing
  convention (prefix/scope, tense, casing).

Shape (illustrative — adapt, don't emit verbatim):

```sh
git add path/to/a.py path/to/b.py \
  && git commit -m "Scope: imperative subject near 50 chars

Body explaining what changed and why, wrapped at 120 columns. Add more lines as needed, each under the limit."
```

Do **not** run these commands yourself — output them for the user. If nothing is staged, say so in one line
rather than inventing a commit.
