---
description: "Check if this session's work is complete and summarize what was done"
agent: "agent"
---
Review the full conversation history for this session and produce a concise status report.

Before writing the report, run `git status --short` and `git --no-pager diff --stat HEAD` fresh to see the current
working-tree and staging state. Use this to verify whether the code changes discussed in the session are actually
committed, still staged, or still unstaged. (Per repo policy you may only run read-only git commands.)

## 1. Summary of Work Done

List everything that was accomplished in this session — code changes, research, discussions, commits,
external actions (Slack messages, Jira queries, etc.). Use brief bullet points grouped by category
(e.g. Code, Documentation, Infrastructure, Analysis/Discussion). Do not re-explain things in detail;
just identify what was done.

## 2. Completion Analysis

Determine whether any of the following remain:

- **Unanswered questions** — Did the user ask something that never got a clear answer?
- **Incomplete tasks** — Was any requested work started but not finished?
- **Uncommitted changes** — Cross-reference the code changes made or discussed this session against `git status`.
  Are any of them still uncommitted (unstaged or staged-but-not-committed)? Call out specific files that are
  dirty. Note that this repo's policy forbids you from committing — so surface the state for the user to act on.
- **Pending external actions** — Are there things the user said they'd do (send a message, run a test,
  file a ticket) where the outcome hasn't been confirmed?
- **Stale todo items** — Does the sidebar todo list have items that are out of date or still marked
  in-progress/not-started despite being done?
- **Follow-up work** — Were any next steps identified that haven't been acted on yet?

## 3. Verdict

End with a single clear line:

- **Session complete** — if all work is done, no loose ends remain, and the session's changes are committed
- **Session mostly complete** — if only external/user-side actions remain (e.g. "send Slack message", or
  committing the still-dirty changes, since repo policy forbids the agent from committing)
- **Session incomplete** — if there is unfinished code, unanswered questions, or blocked tasks

If mostly complete or incomplete, list the specific remaining items.
