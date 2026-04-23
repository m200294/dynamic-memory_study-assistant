"""
Memory flush — extract a structured session log from a conversation transcript.

Spawned in the background by session-end.py or pre-compact.py. Reads a
pre-extracted markdown context file, uses the Claude Agent SDK (with Read/Write
tool access) to produce a session log under `sessions/week-NN/`, then
optionally spawns compile.py if it's past the compile hour.

Usage:
    uv run python scripts/flush.py <context_file.md> <session_id>
"""

from __future__ import annotations

# Recursion guard: set BEFORE any import that might spawn Claude.
import os
os.environ["CLAUDE_INVOKED_BY"] = "memory_flush"

import asyncio
import json
import logging
import subprocess as _sp
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from config import (  # noqa: E402
    CLAUDE_MD,
    CONCEPTS_DIR,
    COMPILE_AFTER_HOUR,
    LLM_MODEL,
    SCRIPTS_DIR,
    SESSIONS_DIR,
    STUDENT_NAME,
    SUBJECT_NAME,
    SYLLABUS_FILE,
    WEEK_TITLES,
    current_week,
    today_date,
    today_iso,
)

LAST_FLUSH_FILE = SCRIPTS_DIR / "last-flush.json"
FLUSH_LOG = SCRIPTS_DIR / "flush.log"

logging.basicConfig(
    filename=str(FLUSH_LOG),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [flush] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


# ── Dedup state ────────────────────────────────────────────────────────

def load_dedup() -> dict:
    if LAST_FLUSH_FILE.exists():
        try:
            return json.loads(LAST_FLUSH_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def save_dedup(state: dict) -> None:
    LAST_FLUSH_FILE.write_text(json.dumps(state), encoding="utf-8")


# ── Agent call ─────────────────────────────────────────────────────────

def build_prompt(context: str, week: int, today: str, session_id: str) -> str:
    existing_slugs: list[str] = []
    if CONCEPTS_DIR.exists():
        existing_slugs = sorted(p.stem for p in CONCEPTS_DIR.glob("*.md"))

    slugs_block = (
        "\n".join(f"- {s}" for s in existing_slugs)
        if existing_slugs else "(none yet — this will be the first concept file)"
    )

    week_title = WEEK_TITLES.get(week, "(between weeks)")
    session_dir = SESSIONS_DIR / f"week-{week:02d}"

    return f"""You are the session-flush agent for the {SUBJECT_NAME} study knowledge base.

Your one job: read the conversation transcript below and write a single session
log file to `{session_dir}/`. That file must follow the study session format
exactly: YAML frontmatter with structured mastery data plus a short markdown body.

## Context

- Today's date: **{today}**
- Current course week: **{week}** — *{week_title}*
- Target session file directory: `{session_dir}/`
- Filename format: `YYYY-MM-DD-<type>-<slug>.md`
  where `<type>` is `learn` or `revise`, and `<slug>` is the primary concept.

## Existing concept slugs (reuse if the same concept is discussed)

{slugs_block}

## Output format — write EXACTLY this structure

```markdown
---
session_type: learn        # learn | revise | other
source: claude
session_id: claude-{session_id}
model: {LLM_MODEL}
week: {week}
date: {today}
primary_concept: <slug>    # main topic, kebab-case
concepts:
  - slug: <slug>
    title: <Human-readable title>
    ratings_observed:
      remember:   good      # weak | mid | good | solid | untested
      understand: good
      apply:      mid
      analyze:    untested
      evaluate:   untested
    layer_reached: 2        # Layers-of-Learning depth 1-4
    bloom_levels_probed: [remember, understand, apply]
    weak_spots:
      - "specific thing the user struggled with"
    solid_connections:
      - "X ↔ Y (why)"
    sources_consulted:
      - "source-material/week-{week:02d}/<file>"
    probes:                 # revise sessions only; [] or omit for learn/other
      - bloom_level: analyze
        question: "near-verbatim question Claude asked"
        answer_summary: "one-sentence summary of the student's answer"
        outcome: mid        # weak | mid | good | solid
        with_prompting: true
        probe_context: "optional note if this probe spanned multiple turns"
---

# Session: {today} — <type> — <primary-concept-title>

## Overview
One to three sentences on what happened this session.

## Concepts covered

### <Concept 1>
- What Claude explained
- What the user demonstrated understanding of
- Where the user stumbled or made a connection

## Weak spots
- Specific things to revisit

## Next steps
- One to three suggestions for the next revise session
```

## Rules

1. **Only rate a Bloom level if it was actually probed this session.** If the user was never asked an Evaluate-level question, leave `evaluate: untested`. Do not fake completeness.

2. **Rating scale:**
   - `weak`   — struggled, couldn't answer, or answered wrong
   - `mid`    — partial understanding, got there with prompting
   - `good`   — answered clearly in own words, handled a relational question
   - `solid`  — demonstrated depth, spontaneous connection, teaching-back quality
   - `untested` — level was not probed

3. **Session type:**
   - `learn` if this was a first-encounter encoding session (deep-encoding protocol)
   - `revise` if the user referenced prior knowledge or asked to review
   - `other` for planning/meta sessions (design conversations, tooling discussions, etc.)

4. **Slug hygiene:** If the concept matches an existing slug, reuse it. Otherwise coin a new kebab-case slug (short, memorable, no week number).

5. **Multiple concepts:** one entry per concept under `concepts:`. The most central one also goes in `primary_concept` and drives the filename.

6. **Be honest and specific.** "The student could define the concept but struggled to apply it to a concrete example" beats "the student has gaps." Claude's assessment is the evidence that compile.py will later turn into concept-file updates.

7. **If the session was not a study session** (e.g. purely tooling/setup/chat), write the file anyway with `session_type: other`, `concepts: []`, and a short note in the body explaining what happened. Do not invent concepts.

8. **Revise-session probes:** If `session_type: revise`, extract every distinct
   probe Q&A pair you can identify. Put probes under the matching concept entry.
   Use the question verbatim or near-verbatim. For multi-turn probes, summarize
   the final tested question and use `probe_context` for the turn shape. Set
   `with_prompting: true` if {STUDENT_NAME} needed a hint to reach the answer. A prompted
   answer can support `mid`, but do not set a concept's `ratings_observed` to
   `good` or `solid` for a Bloom level when all probes at that level needed
   prompting.

9. **Use the Write tool to create the file.** Do not output the file contents inline in the response. The file path must be `{session_dir}/{today}-<type>-<slug>.md`. Create the directory if it doesn't exist (use mkdir -p via a shell — actually no, just use Write, which creates parent dirs).

## Conversation transcript

{context}
"""


async def run_flush(prompt: str) -> str:
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    response = ""
    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                model=LLM_MODEL,
                cwd=str(ROOT),
                system_prompt={"type": "preset", "preset": "claude_code"},
                allowed_tools=["Read", "Write", "Glob"],
                permission_mode="acceptEdits",
                max_turns=8,
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response += block.text
            elif isinstance(message, ResultMessage):
                pass
    except Exception as e:
        import traceback
        logging.error("Agent SDK error: %s\n%s", e, traceback.format_exc())
        response = f"FLUSH_ERROR: {type(e).__name__}: {e}"
    return response


# ── End-of-day auto-compile ────────────────────────────────────────────

def maybe_trigger_compile() -> None:
    now = datetime.now(timezone.utc).astimezone()
    if now.hour < COMPILE_AFTER_HOUR:
        return
    compile_script = SCRIPTS_DIR / "compile.py"
    if not compile_script.exists():
        return

    logging.info("End-of-day compile triggered (after %d:00 local)", COMPILE_AFTER_HOUR)
    cmd = ["uv", "run", "--directory", str(ROOT), "python", str(compile_script)]
    kwargs: dict = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = _sp.CREATE_NEW_PROCESS_GROUP | _sp.DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True
    try:
        log_handle = open(str(SCRIPTS_DIR / "compile.log"), "a")
        _sp.Popen(cmd, stdout=log_handle, stderr=_sp.STDOUT, cwd=str(ROOT), **kwargs)
    except Exception as e:
        logging.error("Failed to spawn compile.py: %s", e)


# ── Main ───────────────────────────────────────────────────────────────

def main() -> None:
    if len(sys.argv) < 3:
        logging.error("Usage: flush.py <context_file.md> <session_id>")
        sys.exit(1)

    context_file = Path(sys.argv[1])
    session_id = sys.argv[2]
    logging.info("flush started: session=%s ctx=%s", session_id, context_file)

    if not context_file.exists():
        logging.error("Context file not found: %s", context_file)
        return

    # 60s dedup
    dedup = load_dedup()
    if (dedup.get("session_id") == session_id
            and time.time() - dedup.get("timestamp", 0) < 60):
        logging.info("Skipping duplicate flush for session %s", session_id)
        context_file.unlink(missing_ok=True)
        return

    context = context_file.read_text(encoding="utf-8").strip()
    if not context:
        logging.info("Context is empty, skipping")
        context_file.unlink(missing_ok=True)
        return

    today = today_date()
    week = current_week(today)
    if week < 1:
        week = 1  # pre-semester sessions land in week-01 by convention
    week_dir = SESSIONS_DIR / f"week-{week:02d}"
    week_dir.mkdir(parents=True, exist_ok=True)

    logging.info("Flushing session %s (%d chars) for week %d", session_id, len(context), week)

    prompt = build_prompt(context, week, today.isoformat(), session_id)
    response = asyncio.run(run_flush(prompt))
    logging.info("Flush agent response (%d chars): %s",
                 len(response), response[:400].replace("\n", " "))

    save_dedup({"session_id": session_id, "timestamp": time.time()})
    context_file.unlink(missing_ok=True)

    maybe_trigger_compile()
    logging.info("Flush complete for session %s", session_id)


if __name__ == "__main__":
    main()
