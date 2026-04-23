---
description: Show the study progress dashboard - tiered coverage per week + weak spots across all concepts.
---

Regenerate the progress dashboard from current concept state, then show it to the user.

Do the following, in order:

1. Run `uv run python scripts/compile.py --progress-only` to regenerate `knowledge/progress.md` from the current concept files. This is a deterministic local computation - no LLM call, no cost.

2. Read `knowledge/progress.md` and present it to the user exactly as written. Do not summarize or paraphrase — show the full tiered progress bar.

3. After the dashboard, add a short honest assessment (2–4 sentences). Cover:
   - Which week is most behind.
   - Which concept has the oldest `last_revised` date (read from `knowledge/index.md`).
   - Whether the user is on track given any configured assessment dates from the SessionStart status header.
   - One concrete next action - either a revise session for a specific stale concept or a learn session for an untouched week.

No motivation, no cheerleading. If the data is thin (few concepts), say so plainly: "Not enough sessions logged yet to draw conclusions."
