<p align="center">
  <img width="1499" height="1049" alt="lookatthis" src="https://github.com/user-attachments/assets/1c183f6b-30ff-4dbe-a8f3-7bcb649597ce" />
</p>

<div style="height: 48px;"></div>

<p align="center">
  <img width="1536" height="1024" alt="LATP2" src="https://github.com/user-attachments/assets/3e598446-a143-4e80-b157-a89da44576de" />
</p>

# Progress dashboard example 
<img width="1054" height="762" alt="image" src="https://github.com/user-attachments/assets/026fb75f-ed2b-432f-b907-18ef257446fc" />

# Week log example 
<img width="946" height="924" alt="image" src="https://github.com/user-attachments/assets/2ba6b9b0-fc50-4aeb-b645-12ee025e288a" />

# Concepts log example 
<img width="933" height="855" alt="image" src="https://github.com/user-attachments/assets/a5593be5-7b62-41e7-99e3-562214968458" />




# Study Memory Pipeline

A local, file-based study system for turning conversations into tracked mastery.

This repo gives you a reusable Claude Code study workspace. Drop your course
material into `source-material/`, ask Claude to teach or revise with you, and
the system records evidence from the conversation into a structured knowledge
base.

It is built for students who want more than notes. It tracks what you actually
demonstrated: weak spots, solid connections, Bloom-level mastery, revision
probes, and progress by week.

## What It Does

- Reads course material dropped into the current week folder before study sessions.
- Guides learn/revise sessions using a custom made deep-encoding protocol skill.
- Saves session evidence when a Claude Code session ends or compacts.
- Compiles evidence into per-concept mastery files.
- Tracks weak spots and unresolved revision probes.
- Builds a progress dashboard by week and Bloom level.
- Accepts external notes from Codex, ChatGPT, voice notes, or manual summaries.
- Provides a Codex fallback when Claude usage is unavailable.

# Examples

## saved session evidence
<img width="1920" height="1078" alt="image" src="https://github.com/user-attachments/assets/08244cca-1c81-4cc8-bf40-f6c4be106793" />

## Sessoin compiler log:
<img width="1899" height="799" alt="image" src="https://github.com/user-attachments/assets/0faa63d4-5119-4205-932e-bb4aef67b43d" />



Everything is plain files. There is no database, daemon, hosted service, or
vendor lock-in.

## Quick Start With Claude Code

Clone or download this repo, open it in Claude Code, then say:

```text
Read SETUP_AGENT.md and set this system up for my subject.
```

Or run the included slash command:

```text
/setup
```

Claude will ask for your subject name, number of weeks, start date, assessment
dates, and where your lecture files or syllabus are. It should then:

1. Fill in `subject.yml`.
2. Create `source-material/week-NN/` folders.
3. Prepare `inbox/`, `sessions/`, and `knowledge/`.
4. Run validation checks.
5. Tell you how to start your first learn session.

After setup, put your files here:

```text
source-material/week-01/
source-material/week-02/
source-material/week-03/
```

Then start studying:

```text
Let's learn week 1.
```

or:

```text
Let's revise recursion.
```

## Install Requirements

This repo uses `uv` for Python dependency management.

Install `uv` if needed:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Install dependencies:

```bash
uv sync
```

Run setup checks:

```bash
uv run python scripts/validate.py --write-schemas
uv run python scripts/compile.py --progress-only
```

## How The System Works

The pipeline has four layers:

1. **Instructions**  
   `CLAUDE.md`, `AGENTS.md`, `SETUP_AGENT.md`, and the deep-encoding skill tell
   the agent how to teach, revise, and record evidence.

2. **Hooks**  
   Claude Code lifecycle hooks run automatically:
   - `hooks/session-start.py`
   - `hooks/pre-compact.py`
   - `hooks/session-end.py`

3. **Scripts**  
   Python workers do the real processing:
   - `scripts/flush.py`
   - `scripts/ingest.py`
   - `scripts/compile.py`
   - `scripts/validate.py`
   - `scripts/codex_compile.py`

4. **Data**  
   The durable state is just markdown and YAML:
   - `source-material/`
   - `inbox/`
   - `sessions/`
   - `knowledge/`

The main loop:

```text
study conversation
-> session evidence
-> canonical session log
-> concept mastery files
-> progress dashboard
```

## Key Folders

```text
subject.yml                   # your subject settings
SETUP_AGENT.md                # first-run setup workflow
CLAUDE.md                     # Claude Code study instructions
AGENTS.md                     # Codex/agent study instructions
.claude/settings.json         # hook registration
.claude/skills/deep-encoding/ # study protocol
source-material/              # your course material
extra-resources/              # optional extra reading
inbox/                        # external notes waiting to ingest
sessions/                     # canonical study evidence logs
knowledge/concepts/           # compiled concept mastery files
knowledge/progress.md         # progress dashboard
hooks/                        # Claude Code lifecycle triggers
scripts/                      # pipeline workers
```

## Evidence Rule

The system only tracks what happened in actual study sessions.

Ratings:

- `weak`: struggled, wrong, or could not answer
- `mid`: partial answer or needed prompting
- `good`: clear answer in own words
- `solid`: deep answer with connections or teaching-back quality
- `untested`: not probed

If a Bloom level was not tested, it should stay untested. The compiler preserves
previous ratings when there is no new evidence.

## Common Commands

Show progress:

```text
/progress
```

Ingest external notes from `inbox/`:

```text
/ingest
```

Manual ingest:

```bash
uv run python scripts/ingest.py --compile
```

Manual compile:

```bash
uv run python scripts/compile.py
```

Validate everything:

```bash
uv run python scripts/validate.py --all
```

Codex fallback:

```bash
./codex_compile
```

Manual flush of the latest Claude Code transcript:

```bash
./flush-now.sh
```

## External Notes

You can place notes from another tool in `inbox/`.

Minimal frontmatter:

```yaml
---
source: chatgpt
session_type: learn
week: 1
date: 2026-05-03
model: gpt-5
---
```

Then run:

```bash
uv run python scripts/ingest.py --compile
```

## Before Publishing Your Fork

This template contains no personal course data by default. If you customize it,
scan before publishing:

```bash
rg -n "your-name|your-course|private-term|api-key|token" .
```

Runtime files are ignored by `.gitignore`, including logs, temp flush files,
virtual environments, and local state.

## Status

This is a practical starter system, not a polished product. It is best used by
someone comfortable opening a repo in Claude Code and letting the setup agent
configure it for their subject.
