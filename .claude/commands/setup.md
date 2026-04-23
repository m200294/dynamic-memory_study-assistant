---
description: Configure this study pipeline for a new subject.
---

Read `SETUP_AGENT.md` in full, then configure the repo for the student's
subject.

Follow that setup workflow exactly:

1. Inspect existing files, especially `subject.yml`, `syllabus.md`, and
   `source-material/`.
2. Ask only for missing course details that cannot be inferred.
3. Update `subject.yml`.
4. Create needed `source-material/week-NN/` folders.
5. Ensure runtime folders exist.
6. Run validation/setup checks:

```bash
uv sync
uv run python scripts/validate.py --write-schemas
uv run python scripts/compile.py --progress-only
```

If dependency installation is blocked, explain the exact blocker and still
finish the file setup.

Do not edit `scripts/`, `hooks/`, `.claude/settings.json`, `sessions/`, or
`knowledge/` unless a validation failure proves a repair is required.
