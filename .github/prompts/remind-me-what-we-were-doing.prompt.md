---
description: "Briefly re-orient the user on the current session: what's done, what remains, and any open decisions"
agent: "agent"
---
Review the **entire current conversation** and give the user a fast re-orientation of what we've been working
on. This is a memory jog, not a report — optimize for signal and brevity.

Output rules:

- Lead with a single one-line summary of the overall goal/through-line (skip if there isn't a clear one).
- Use short, high-signal bullets and/or one compact table. No prose paragraphs, no preamble, no restating
  this request, no closing pleasantries.
- Keep the whole thing well under a screen. Collapse minor/mechanical steps; report outcomes, not play-by-play.
- Link files/tickets only when it aids orientation. Don't pad.

Sections — include a section **only if it has content**. Never emit an empty section or a "none"/"nothing to
report" placeholder for a section:

1. **Done** — what's completed, as brief bullets.
2. **Remaining** — what's left or in progress.
3. **Decisions needed** — open questions or forks awaiting the user's input. If there are none, **omit this
   section entirely** — do not write "no decisions needed" or anything similar (that just wastes the reader's
   time).

If the conversation spans multiple unrelated threads, focus on the most recent/active one and fold the rest
into a single trailing line. If there's genuinely nothing substantive yet, say so in one line.
