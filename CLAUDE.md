# CLAUDE.md - Generic Study Pipeline

You are running inside a portable study workspace. This is not tied to one
subject. Your job is to help the student encode, revise, and track mastery of
whatever course material they place in this repo.

Read this file at the start of every session. If Claude Code hooks are enabled,
`SessionStart` injects a compact status header with current week, pending inbox
files, stale concepts, and current source material.

For first-run setup, read `SETUP_AGENT.md` or run `/setup`.

## Project Layout

```text
subject.yml                   - student-editable subject settings
syllabus.md                   - optional course map
source-material/week-NN/      - read-only class material for week NN
extra-resources/              - optional read-only depth material
inbox/                        - external Codex/ChatGPT/voice-note sessions
sessions/week-NN/             - canonical session logs
knowledge/concepts/<slug>.md  - per-concept mastery files
knowledge/weeks/week-NN.md    - per-week aggregates
knowledge/index.md            - master concept table
knowledge/progress.md         - progress dashboard
knowledge/log.md              - build log
hooks/                        - Claude Code lifecycle hooks
scripts/                      - validation, flush, ingest, compile scripts
.claude/skills/               - project-local study skills
SETUP_AGENT.md                - first-run setup workflow for Claude Code
```

Read anything needed. Treat `source-material/`, `extra-resources/`, and
`syllabus.md` as source material. Do not modify them unless the user explicitly
asks.

Do not edit `knowledge/` directly during normal study. It is compiled from
session evidence by:

```bash
uv run python scripts/compile.py
```

## Session Types

Every session is one of:

- `learn`: first serious encounter with a concept. Use the `deep-encoding`
  skill. Read relevant `source-material/week-NN/` files first.
- `revise`: return visit to a concept. Read `knowledge/concepts/<slug>.md`
  first, including weak spots and `probe_history`.
- `other`: planning, setup, tooling, or non-study conversations.

If intent is unclear, ask whether this is learn or revise.

## Mastery Tracking

Concepts are tracked by slug. Reuse an existing slug if the same idea appears
again in another week.

Allowed Bloom levels:

- `remember`
- `understand`
- `apply`
- `analyze`
- `evaluate`

Allowed ratings:

- `weak`: struggled, wrong, or could not answer
- `mid`: partial answer or needed prompting
- `good`: clear answer in own words
- `solid`: deep answer, connections, or teaching-back quality
- `untested`: not probed

Only rate a level when there is evidence from the current session. If a level
was not probed, leave it untested in the session log. The compiler preserves
the previous concept rating when there is no new evidence.

## Learn Sessions

Use `.claude/skills/deep-encoding/SKILL.md`.

Required shape:

1. Read relevant source material.
2. Start with an overview map.
3. Let the student choose where to begin.
4. Explain the chosen concept fully.
5. Ask relational and evaluative questions.
6. Probe shallow answers.
7. End with an evidence summary.

## Revise Sessions

Before a revise session:

1. Read the concept file in `knowledge/concepts/`.
2. Revisit weak spots and unresolved weak/mid probes.
3. Ask concrete Q&A probes.
4. Track whether prompting was needed.
5. Do not count prompted-only answers as `good` or `solid`.

## Automation

If hooks are installed, session logs are written automatically by:

- `hooks/session-end.py`
- `hooks/pre-compact.py`
- `scripts/flush.py`

External notes can be placed in `inbox/` and processed with:

```bash
uv run python scripts/ingest.py --compile
```

If Claude usage is unavailable and Codex is installed, the fallback is:

```bash
./codex_compile
```

The fallback asks Codex to do the semantic ingest/compile work, then runs local
validation and deterministic progress regeneration.
