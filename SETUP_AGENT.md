# SETUP_AGENT.md - First-Run Setup Instructions

Use this file when a new student opens this repo in Claude Code and says
something like:

> Set this study system up for my subject.

Your job is to configure the pipeline for their course without requiring them
to understand the internals first.

## Setup Goals

By the end, the repo should have:

- A completed `subject.yml`.
- Week folders under `source-material/week-NN/`.
- A useful `syllabus.md` placeholder or converted course map.
- Empty runtime folders ready for sessions and knowledge output.
- Dependencies installed or clear instructions if installation is blocked.
- Validation passing.
- A short explanation of how the student should use the system tomorrow.

## First Questions

Ask only for information you cannot infer from files already present.

Start with these:

1. What subject or course is this for?
2. How many teaching weeks or topic blocks are there?
3. What is the first week start date, if they know it?
4. Are there exam or assessment dates to track?
5. Do they already have lecture notes, PDFs, slides, transcripts, or a syllabus
   to place in `source-material/`?

If the student gives a syllabus file, read it and infer week titles, assessment
dates, and topic groups. Confirm assumptions before writing `subject.yml`.

## Files To Edit

You may edit:

- `subject.yml`
- `syllabus.md`
- `source-material/**`
- `README.md` only if the student wants repo-specific wording

You normally should not edit:

- `scripts/**`
- `hooks/**`
- `.claude/settings.json`
- `.claude/skills/**`
- `knowledge/**`
- `sessions/**`

`knowledge/` and `sessions/` are generated after study sessions.

## Subject Configuration

Update `subject.yml` with:

```yaml
student_name: "the student"     # or the student's preferred name
subject_name: "Course name"
subject_code: "Optional code"
semester_start: 2026-05-04      # blank if unknown
midterm_date:                   # blank if none or unknown
final_date:                     # blank if none or unknown
total_weeks: 12
compile_after_hour: 18
llm_model: "claude-sonnet-4-6"

weeks:
  1: "Week title"
  2: "Week title"

week_to_topic:
  1: "Topic block"
  2: "Topic block"
```

Keep dates as `YYYY-MM-DD` or blank.

## Source Material Setup

Create folders:

```text
source-material/week-01/
source-material/week-02/
...
```

If files are already present, organize them by teaching week. Do not delete
originals unless the student explicitly asks.

If only a syllabus exists, put it in `syllabus.md` and leave week folders empty
but ready.

## Runtime Folders

Ensure these exist:

```text
inbox/
inbox/processed/
inbox/failed/
sessions/
knowledge/
knowledge/concepts/
knowledge/weeks/
extra-resources/
```

Use `.gitkeep` files for empty folders if needed.

## Install And Validate

Preferred setup:

```bash
uv sync
uv run python scripts/validate.py --write-schemas
uv run python scripts/compile.py --progress-only
```

If `uv sync` fails because `uv` is missing, tell the student to install it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If dependency installation is blocked by network or permissions, explain the
blocker and continue with file configuration.

## Claude Code Hooks

The repo already includes `.claude/settings.json` with:

- `SessionStart` -> `hooks/session-start.py`
- `PreCompact` -> `hooks/pre-compact.py`
- `SessionEnd` -> `hooks/session-end.py`

Do not rewrite hook registration unless the student has a custom Claude Code
setup.

## Final User Handoff

End setup with:

1. What subject was configured.
2. Where to put source files.
3. The exact command that passed or failed.
4. How to start the first learn session.
5. How to ingest external notes.

Example:

```text
Your course is configured in subject.yml.
Put lecture files in source-material/week-01/, source-material/week-02/, etc.
To start, open Claude Code here and say: "Let's learn week 1."
For external notes, place a markdown file in inbox/ and run /ingest.
```

## Safety

Do not add private IDs, API keys, email addresses, or personal data to committed
files. If the student wants their own name in `subject.yml`, that is fine, but
avoid hard-coding it elsewhere.
