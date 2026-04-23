"""
Compile session logs into per-concept mastery files + per-week aggregates
+ progress dashboard.

Reads `sessions/week-NN/*.md` (written by flush.py), updates
`knowledge/concepts/*.md`, `knowledge/weeks/week-NN.md`, `knowledge/index.md`,
`knowledge/progress.md`, and appends to `knowledge/log.md`.

Usage:
    uv run python scripts/compile.py                 # incremental (new/changed only)
    uv run python scripts/compile.py --all           # recompile everything
    uv run python scripts/compile.py --dry-run       # list what would compile
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from config import (  # noqa: E402
    CLAUDE_MD,
    CONCEPTS_DIR,
    INDEX_FILE,
    KNOWLEDGE_DIR,
    LLM_MODEL,
    LOG_FILE,
    PROGRESS_FILE,
    SESSIONS_DIR,
    SUBJECT_NAME,
    SYLLABUS_FILE,
    TOTAL_WEEKS,
    WEEKS_DIR,
    WEEK_TITLES,
    now_iso,
    today_iso,
)
from utils import (  # noqa: E402
    dump_frontmatter,
    file_hash,
    list_concepts,
    list_sessions,
    load_state,
    parse_frontmatter,
    read_wiki_index,
    save_state,
)
from validate import (  # noqa: E402
    PROBE_HISTORY_LIMIT,
    ValidationFailure,
    session_warnings,
    validate_session_file,
)


async def compile_session(session_path: Path, state: dict) -> float:
    """Compile one session log. Updates concept + week files. Returns API cost."""
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    session_content = session_path.read_text(encoding="utf-8")

    # Bundle current knowledge state for the LLM.
    existing_concepts_block = ""
    if CONCEPTS_DIR.exists():
        parts = []
        for p in sorted(CONCEPTS_DIR.glob("*.md")):
            rel = p.relative_to(KNOWLEDGE_DIR)
            parts.append(f"### {rel}\n```markdown\n{p.read_text(encoding='utf-8')}\n```")
        if parts:
            existing_concepts_block = "\n\n".join(parts)

    index_block = read_wiki_index()
    timestamp = now_iso()

    prompt = f"""You are the knowledge compiler for the {SUBJECT_NAME} study pipeline. Read one session log and update the
per-concept mastery files accordingly, following the rules below exactly.

## Session log to compile

**File:** {session_path.relative_to(ROOT_DIR)}

```markdown
{session_content}
```

## Current index

{index_block}

## Existing concept files

{existing_concepts_block if existing_concepts_block else "(no concept files yet)"}

## Rules

### 1. For every concept in the session log's frontmatter `concepts:` list

Compute the update for `knowledge/concepts/<slug>.md`:

- **If the concept file does not exist:** create it. Starting state = session's
  `ratings_observed` (untested levels stay untested). Set `last_studied` and
  `last_revised` to the session `date`. Populate `weak_spots`, `solid_connections`,
  and `sources` from the session.

- **If the concept file exists:** apply the **evidence rule**. For each Bloom
  level, change the rating only if there is evidence in the session:
    * Session rated it `weak` or `mid` when it was previously `good` or `solid`
      → rating drops (evidence: user stumbled).
    * Session rated it `good` or `solid` when it was previously `mid` or `weak`
      → rating rises (evidence: user demonstrated new depth).
    * Session rated it `untested` → rating stays (level wasn't probed).
    * Session rating == existing rating → stays.
  Always bump `last_revised` to the session date. `last_studied` never changes
  after the first encounter.
  Merge new `weak_spots` into the existing list (deduplicate). Same for
  `solid_connections`. Add the session file path to `sources` if missing.

### 2. YAML frontmatter — exact shape

```yaml
---
title: <Human-readable title>
slug: <slug>
week: <primary week the concept first appeared in>
also_in_weeks: [<other weeks where it recurred>]
mastery:
  remember:   good
  understand: good
  apply:      mid
  analyze:    mid
  evaluate:   weak
layer_reached: 2
last_studied: 2026-04-22
last_revised: 2026-04-23
sources:
  - source-material/week-02/lecture-notes.md
  - sessions/week-02/2026-04-22-learn-core-concept.md
weak_spots:
  - "can't classify real-code examples"
solid_connections:
  - "connected the concept to a related idea from another week"
---
```

### 3. Body — short encyclopedia-style explanation

Below the frontmatter, write 2–6 concise paragraphs covering the Layers of
Learning: logic (big picture), concepts, important details. Link related
concepts with `[[concepts/<slug>]]`. On update, ADD to the body if the session
contributed new nuance — do not rewrite from scratch. Preserve prior content.

### 4. Update `knowledge/index.md`

A single table with the header:

```
| Concept | Week(s) | Mastery (R/U/A/A/E) | Layer | Last revised | Sources |
|---------|---------|---------------------|-------|--------------|---------|
| [[concepts/core-concept]] | 2 | good/good/mid/mid/weak | 2 | 2026-04-23 | 2 sessions |
```

Use the compact glyph form `good/good/mid/mid/weak` in R/U/A/A/E order (remember,
understand, apply, analyze, evaluate).

### 5. Update `knowledge/weeks/week-NN.md` for each week touched

```markdown
---
week: 2
title: Core concept
topic: Foundation
updated: 2026-04-23
---

# Week 2 - Core concept

## Concepts studied

- [[concepts/core-concept]] - mastery: good/good/mid/mid/weak (2 sessions)
- ...

## Sessions

- [[sessions/week-02/2026-04-22-learn-core-concept]] - learn
- ...

## Aggregate weak spots
- ...
```

### 6. Append to `knowledge/log.md`

```
## [{timestamp}] compile | sessions/week-NN/<session>.md
- Source: {session_path.name}
- Concepts created: [[concepts/x]]
- Concepts updated: [[concepts/y]]
- Week files updated: [[weeks/week-NN]]
```

### 7. DO NOT touch `knowledge/progress.md` here — that's regenerated separately.

### 8. File paths

- Concepts: `{CONCEPTS_DIR}`
- Weeks:    `{WEEKS_DIR}`
- Index:    `{INDEX_FILE}`
- Log:      `{LOG_FILE}`

If existing concept frontmatter contains `probe_history`, preserve it if
convenient, but do not manually curate it. `probe_history` is a deterministic
cache rebuilt locally after the LLM compile step from `sessions/**` probes.

Use Read/Write/Edit tools. Be precise with YAML. Never write invalid YAML.
"""

    cost = 0.0
    try:
        async for message in query(
            prompt=prompt,
            options=ClaudeAgentOptions(
                model=LLM_MODEL,
                cwd=str(ROOT_DIR),
                system_prompt={"type": "preset", "preset": "claude_code"},
                allowed_tools=["Read", "Write", "Edit", "Glob", "Grep"],
                permission_mode="acceptEdits",
                max_turns=30,
            ),
        ):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        pass
            elif isinstance(message, ResultMessage):
                cost = message.total_cost_usd or 0.0
                print(f"  Cost: ${cost:.4f}")
    except Exception as e:
        print(f"  Error: {e}")
        return 0.0

    state.setdefault("ingested", {})[str(session_path.relative_to(ROOT_DIR))] = {
        "hash": file_hash(session_path),
        "compiled_at": now_iso(),
        "cost_usd": cost,
    }
    state["total_cost"] = state.get("total_cost", 0.0) + cost
    save_state(state)
    return cost


# ── Probe-history cache rebuild (local, no LLM needed) ─────────────────

def _probe_sort_key(entry: dict) -> tuple[str, str, str]:
    return (
        str(entry.get("date", "")),
        str(entry.get("session_file", "")),
        str(entry.get("probe_id", "")),
    )


def _select_probe_history(entries: list[dict], limit: int = PROBE_HISTORY_LIMIT) -> list[dict]:
    """
    Keep recent probes, while preserving unresolved weak/mid probes until a
    later unprompted good/solid probe at the same Bloom level supersedes them.
    """
    deduped: dict[str, dict] = {}
    for entry in sorted(entries, key=_probe_sort_key):
        deduped[str(entry["probe_id"])] = entry

    ordered = sorted(deduped.values(), key=_probe_sort_key)
    unresolved: list[dict] = []
    for i, entry in enumerate(ordered):
        if entry.get("outcome") not in {"weak", "mid"}:
            continue
        level = entry.get("bloom_level")
        later_strong = any(
            later.get("bloom_level") == level
            and later.get("outcome") in {"good", "solid"}
            and not later.get("with_prompting", False)
            for later in ordered[i + 1:]
        )
        if not later_strong:
            unresolved.append(entry)

    selected: dict[str, dict] = {}
    for entry in sorted(unresolved, key=_probe_sort_key, reverse=True):
        selected[str(entry["probe_id"])] = entry
        if len(selected) >= limit:
            break

    for entry in sorted(ordered, key=_probe_sort_key, reverse=True):
        if len(selected) >= limit:
            break
        selected.setdefault(str(entry["probe_id"]), entry)

    return sorted(selected.values(), key=_probe_sort_key, reverse=True)


def rebuild_probe_history() -> None:
    """Rebuild concept-file probe_history from canonical session logs."""
    probes_by_concept: dict[str, list[dict]] = {}

    for session_path in list_sessions():
        session = validate_session_file(session_path)
        rel_session = str(session_path.relative_to(ROOT_DIR))
        for concept in session.concepts:
            for probe in concept.probes:
                probes_by_concept.setdefault(concept.slug, []).append({
                    "probe_id": probe.probe_id,
                    "date": session.date.isoformat(),
                    "bloom_level": probe.bloom_level,
                    "question": probe.question,
                    "outcome": probe.outcome,
                    "with_prompting": probe.with_prompting,
                    "session_file": rel_session,
                })

    changed = 0
    for concept_path in list_concepts():
        content = concept_path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(content)
        if not frontmatter:
            continue
        slug = str(frontmatter.get("slug") or concept_path.stem)
        selected = _select_probe_history(probes_by_concept.get(slug, []))
        if selected:
            if frontmatter.get("probe_history") == selected:
                continue
            frontmatter["probe_history"] = selected
        elif "probe_history" in frontmatter:
            frontmatter.pop("probe_history", None)
        else:
            continue
        concept_path.write_text(dump_frontmatter(frontmatter, body), encoding="utf-8")
        changed += 1

    if changed:
        print(f"  Probe history rebuilt for {changed} concept file(s).")


# ── Progress regeneration (local, no LLM needed) ──────────────────────

def regenerate_progress() -> None:
    """Rebuild knowledge/progress.md from concept frontmatter. Deterministic."""
    from utils import BLOOM_LEVELS, empty_mastery, is_covered, mastery_summary
    from validate import validate_concept_file

    by_week: dict[int, list[dict]] = {}

    for path in list_concepts():
        concept = validate_concept_file(path)
        fm = concept.model_dump(mode="json")
        week = fm.get("week")
        also = fm.get("also_in_weeks") or []
        weeks = set([week] + list(also))
        for w in weeks:
            if not isinstance(w, int):
                continue
            by_week.setdefault(w, []).append({
                "title":   fm.get("title", path.stem),
                "slug":    fm.get("slug", path.stem),
                "mastery": fm.get("mastery") or empty_mastery(),
                "weak_spots": fm.get("weak_spots") or [],
                "last_revised": fm.get("last_revised", "—"),
            })

    lines: list[str] = [f"# {SUBJECT_NAME} - Progress Dashboard", ""]
    lines.append(f"_Generated {now_iso()}_")
    lines.append("")
    lines.append("## Tiered coverage by week")
    lines.append("")
    lines.append("Understanding coverage = concepts at `understand: good` or better.  ")
    lines.append("Evaluation coverage = concepts at `evaluate: good` or better.")
    lines.append("")
    lines.append("| Week | Title | Concepts | Understanding | Evaluation |")
    lines.append("|------|-------|----------|---------------|------------|")

    total_concepts = 0
    total_understood = 0
    total_evaluated = 0

    for w in range(1, TOTAL_WEEKS + 1):
        title = WEEK_TITLES.get(w, "—")
        concepts = by_week.get(w, [])
        n = len(concepts)
        total_concepts += n
        understood = sum(1 for c in concepts if is_covered(c["mastery"], "understand", "good"))
        evaluated  = sum(1 for c in concepts if is_covered(c["mastery"], "evaluate",   "good"))
        total_understood += understood
        total_evaluated += evaluated

        if n == 0:
            u_bar = e_bar = "`..........`"
            u_cell = e_cell = "0/0"
        else:
            u_cell = f"{understood}/{n}"
            e_cell = f"{evaluated}/{n}"
            u_bar = "`" + ("#" * understood) + ("." * (n - understood)) + "`"
            e_bar = "`" + ("#" * evaluated) + ("." * (n - evaluated)) + "`"

        lines.append(f"| {w:>2} | {title} | {n} | {u_bar} {u_cell} | {e_bar} {e_cell} |")

    lines.append("")
    lines.append(f"**Totals:** {total_concepts} concepts · understanding {total_understood}/{total_concepts} · evaluation {total_evaluated}/{total_concepts}")
    lines.append("")

    # Weak spots roll-up
    lines.append("## Weak spots across all weeks")
    lines.append("")
    any_weak = False
    for w in range(1, TOTAL_WEEKS + 1):
        concepts = by_week.get(w, [])
        for c in concepts:
            if c["weak_spots"]:
                any_weak = True
                lines.append(f"- **Week {w} · {c['title']}** (last revised {c['last_revised']})")
                for ws in c["weak_spots"]:
                    lines.append(f"  - {ws}")
    if not any_weak:
        lines.append("_(none recorded yet)_")

    PROGRESS_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  Progress dashboard regenerated: {PROGRESS_FILE.relative_to(ROOT_DIR)}")


# ── CLI ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Compile study session logs into knowledge base")
    parser.add_argument("--all", action="store_true", help="Recompile every session log")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be compiled")
    parser.add_argument("--progress-only", action="store_true", help="Only regenerate progress.md")
    args = parser.parse_args()

    if os.environ.get("STUDY_PIPELINE_CODEX_FALLBACK") and not args.progress_only and not args.dry_run:
        print(
            "Refusing semantic compile in STUDY_PIPELINE_CODEX_FALLBACK mode; "
            "use ./codex_compile so Codex performs the evidence-rule edits directly.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)
    WEEKS_DIR.mkdir(parents=True, exist_ok=True)

    if args.progress_only:
        rebuild_probe_history()
        regenerate_progress()
        return

    state = load_state()
    all_sessions = list_sessions()

    try:
        for session in all_sessions:
            validated = validate_session_file(session)
            for warning in session_warnings(validated):
                print(f"Validation warning before compile: {session}: {warning}", file=sys.stderr)
    except ValidationFailure as exc:
        print(f"Validation failed before compile: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    if args.all:
        to_compile = all_sessions
    else:
        to_compile = []
        for s in all_sessions:
            rel = str(s.relative_to(ROOT_DIR))
            prev = state.get("ingested", {}).get(rel, {})
            if not prev or prev.get("hash") != file_hash(s):
                to_compile.append(s)

    if not to_compile:
        print("Nothing to compile - all session logs are up to date.")
        if args.dry_run:
            return
        rebuild_probe_history()
        regenerate_progress()
        return

    print(f"{'[DRY RUN] ' if args.dry_run else ''}Session logs to compile ({len(to_compile)}):")
    for s in to_compile:
        print(f"  - {s.relative_to(ROOT_DIR)}")

    if args.dry_run:
        return

    total_cost = 0.0
    for i, sp in enumerate(to_compile, 1):
        print(f"\n[{i}/{len(to_compile)}] Compiling {sp.relative_to(ROOT_DIR)}...")
        cost = asyncio.run(compile_session(sp, state))
        total_cost += cost

    rebuild_probe_history()
    regenerate_progress()
    print(f"\nCompilation complete. Total cost this run: ${total_cost:.4f}")
    print(f"Concepts: {len(list_concepts())}")


if __name__ == "__main__":
    main()
