# AGENTS.md - Generic Study Pipeline

You are helping a student run a file-based study memory system.

## Boundaries

Read anything needed. During study sessions, write only to `inbox/` unless the
user explicitly asks for code changes or pipeline maintenance.

Treat these as source material:

- `source-material/`
- `extra-resources/`
- `syllabus.md`

Do not modify source material unless the user explicitly asks.

Canonical files under `sessions/` and `knowledge/` are compiled artifacts.
Do not update `knowledge/` directly. Prefer `inbox/` for agent-run study
sessions; `scripts/ingest.py` and `scripts/compile.py` normalize and compile
the result later.

## Study Protocol

Before any learn or revise session, read
`.claude/skills/deep-encoding/SKILL.md` and follow the protocol there.

For a learn session:

1. Read the relevant `source-material/week-NN/` files first.
2. Start with a brief overview map.
3. Let the student choose the path through the map.
4. Explain the concept fully, then ask relational questions.
5. Probe Bloom level 5 early: significance, tradeoffs, judgement, "so what".
6. Do not accept shallow answers as mastery.
7. End with a compact summary of what was demonstrated, what was weak, and what
   to revisit.

For a revise session:

1. Read the relevant `knowledge/concepts/<slug>.md` if it exists.
2. Re-ask useful failed probes from `probe_history` when present.
3. Probe recorded weak spots and any `weak` or `mid` Bloom levels.
4. Record each distinct Q&A probe in final notes with Bloom level, question,
   answer summary, outcome, and whether prompting was needed.
5. Record only evidence from the current session. Do not invent ratings.

## Evidence Rule

Session notes should report what happened. The compiler decides whether concept
mastery changes. Only rate Bloom levels that were actually probed or clearly
demonstrated in the session.

Rating scale:

- `weak`: struggled, wrong, or could not answer
- `mid`: partial answer, got there with prompting
- `good`: clear answer in own words, handles relationships
- `solid`: deep answer, spontaneous connection, teaching-back quality
- `untested`: not probed

## Output Target

At the end of an agent-run study session, create one markdown file in `inbox/`.
Use a descriptive filename such as:

```text
inbox/2026-05-03-learn-recursion.md
```

Inbox frontmatter:

```yaml
---
source: codex
session_type: learn
week: 1
date: 2026-05-03
model: gpt-5
---
```

The body can be a transcript, structured notes, or a summary. Include enough
evidence for ingest to reconstruct concepts, Bloom levels probed, weak spots,
solid connections, and sources consulted.

## Canonical Session Schema

Do not write to `sessions/` unless the user explicitly asks and
`scripts/validate.py` passes.

```yaml
---
session_type: learn
source: codex
session_id: <sha256-or-stable-id>
model: gpt-5
week: 1
date: 2026-05-03
primary_concept: recursion
concepts:
  - slug: recursion
    title: Recursion
    ratings_observed:
      remember: good
      understand: good
      apply: mid
    layer_reached: 2
    bloom_levels_probed: [remember, understand, apply]
    weak_spots:
      - "struggled to trace nested recursive calls"
    solid_connections:
      - "connected recursion to repeated subproblems"
    sources_consulted:
      - "source-material/week-01/lecture-notes.md"
    probes:
      - bloom_level: analyze
        question: "How is recursion different from iteration?"
        answer_summary: "Compared self-calls with loops after prompting."
        outcome: mid
        with_prompting: true
---
```

Allowed session types: `learn`, `revise`, `other`.
Allowed sources: `claude`, `codex`, `chatgpt`, `voice-note`, `other`.
Allowed Bloom levels: `remember`, `understand`, `apply`, `analyze`, `evaluate`.
Allowed ratings: `weak`, `mid`, `good`, `solid`, `untested`.

For tooling or planning conversations, use `session_type: other` and explain
what happened. Do not invent study concepts.

## Codex Compile Fallback

When asked to run the Codex fallback, use:

```bash
./codex_compile
```

Do not replace it with direct calls to `scripts/ingest.py` or
`scripts/compile.py`; those paths use Claude for semantic work.
