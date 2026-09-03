---
description: "Turn the session's uncommitted work into ordered git add commands and commit messages"
agent: "agent"
---
Review the **entire current conversation** and produce a logically ordered set of copy-pasteable blocks — each
staging (`git add`/`git rm`/`git mv`) and committing (`git commit`) one logical change — covering the work done
this session that is **not yet committed**.

You generate commands for **the user** to run — `git add`, `git rm`, `git mv`, and `git commit` are all fine to
*emit* for them. Per repo policy, you yourself use **read-only** git only (`git status`, `git log`, `git diff`,
`git show`) — never stage, remove, move, commit, or otherwise modify repository state yourself.

## Steps

1. **Inventory the session's work.** Scan the whole conversation for every file created, edited, renamed, or
   deleted, and note the purpose of each so related changes can be grouped.
2. **Reconcile against git — don't trust the conversation alone.** Some changes may already be committed, and the
   working tree may have moved since. Run:

   - `git --no-pager status` to see what is actually uncommitted right now.
   - `git --no-pager log --oneline -20` to see what already landed (a change discussed earlier may be in already).
   - `git --no-pager diff <path>` to confirm a file's current working-tree contents when in doubt.

   Include only files that are genuinely still uncommitted (modified, untracked, or deleted); drop anything
   already committed or reverted. In `status`, a deletion shows as `D`/"deleted", and a not-yet-staged rename
   shows up as the old path deleted plus the new path untracked — pair those two back into a single rename.
3. **Exclude non-check-in artifacts.** Skip scratch/generated files (ad-hoc logs, one-off outputs, throwaway
   scripts) and anything the user said earlier not to commit. If a file's intent is ambiguous, flag it rather
   than silently including or excluding it.
4. **Group into coherent, dependency-ordered commits.** One logical change per commit — keep a shared/library
   fix separate from the tests that consume it, and an unrelated refactor separate from a bug fix. Order the
   groups so prerequisite changes (shared code) come before their consumers.
5. **Match the repo's commit-message style.** Inspect recent `git --no-pager log` and mirror the prevailing
   convention (prefix/scope, tense, casing). Keep the subject near 50 characters; wrap body lines at 120.

## Output

For each commit, in dependency order, emit:

- A one-line rationale for why those files belong together.
- **One** fenced `sh` block the user can paste as-is that performs **both** the staging and the commit:
  - Stage every path in the group explicitly with the command that matches how each file changed, then chain
    the commit after with `&&` so it only runs once staging succeeds. Never use `git add .` or `git add -A`.
    - **Created or modified** files → `git add <path>`.
    - **Deleted** files → `git rm <path>` (works even though the session already removed it from the working
      tree). This is also how you stage the *old* side of a rename.
    - **Renamed/moved** files → the session already moved the file on disk, so stage the removal of the old
      path and the addition of the new one: `git rm <oldpath> && git add <newpath>`. Git records the pair as a
      rename at commit time when the contents match. Emit `git mv <oldpath> <newpath>` only when the file has
      not actually been moved yet.
  - Put the subject in a single `-m "..."`; for a body, add a blank line inside the same quotes, then the
    wrapped body. Keep the subject near 50 characters and wrap body lines at 120.
  - Use double quotes and keep the message plain ASCII; escape any `"`, `` ` ``, `$`, or `\` it must contain.

Shapes (illustrative — adapt, don't emit verbatim). A plain add-and-commit:

```sh
git add path/to/a.py path/to/b.py \
  && git commit -m "Scope: imperative subject near 50 chars

Body explaining what changed and why, wrapped at 120 columns. Add more lines as needed, each under the limit."
```

A commit that renames a file (old path removed, new path added) alongside an edit:

```sh
git rm path/to/old_name.py \
  && git add path/to/new_name.py path/to/edited.py \
  && git commit -m "Scope: imperative subject near 50 chars

Body explaining what moved, what was deleted, and why, wrapped at 120 columns."
```

Do **not** run these commands yourself — output them for the user. If nothing session-related remains
uncommitted, say so in one line rather than inventing commits.
