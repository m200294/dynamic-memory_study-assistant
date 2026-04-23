"""
SessionStart hook - injects a compact study-status header into every session.

Content injected:
  - Today's date, current study week, week title
  - Days remaining until configured assessments, if any
  - Compact progress line (concepts at >= understand:good)
  - Up to 5 stale concepts (last_revised > 14 days ago)
  - Up to 5 paused concepts from the most recent session
  - Current week's source-material file listing
  - Pointer to CLAUDE.md for full instructions

Pure local I/O. No API calls. Runs <1s.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

# Allow importing scripts/config + utils
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from config import (  # noqa: E402
    CLAUDE_MD,
    CONCEPTS_DIR,
    FINAL_DATE,
    INBOX_DIR,
    MIDTERM_DATE,
    PROGRESS_FILE,
    SESSIONS_DIR,
    SUBJECT_NAME,
    TOTAL_WEEKS,
    WEEKS_LESSONS_DIR,
    WEEK_TITLES,
    current_week,
    days_until,
    today_date,
)
from utils import (  # noqa: E402
    BLOOM_LEVELS,
    empty_mastery,
    is_covered,
    list_concepts,
    parse_frontmatter,
)

MAX_CONTEXT_CHARS = 10_000
STALE_DAYS = 14
MAX_STALE = 5
MAX_PAUSED = 5


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    try:
        return datetime.strptime(str(s)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _gather_concept_stats() -> tuple[int, int, list[tuple[str, int]]]:
    """
    Returns (total_concepts, covered_at_understand_good, stale_list).
    stale_list items: (concept_title, days_since_last_revised) sorted most-stale first.
    """
    today = today_date()
    total = 0
    covered = 0
    stale: list[tuple[str, int]] = []

    for path in list_concepts():
        content = path.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(content)
        if not fm:
            continue
        total += 1
        mastery = fm.get("mastery") or empty_mastery()
        if is_covered(mastery, level="understand", min_rating="good"):
            covered += 1
        last_revised = _parse_date(fm.get("last_revised"))
        if last_revised:
            days = (today - last_revised).days
            if days >= STALE_DAYS:
                title = fm.get("title", path.stem)
                stale.append((title, days))

    stale.sort(key=lambda x: -x[1])
    return total, covered, stale[:MAX_STALE]


def _recent_paused_from_last_session() -> list[str]:
    """
    Find the most recent session log and extract '🔄 paused' entries from its
    tracker block, if present. Best-effort — returns empty list if none found.
    """
    if not SESSIONS_DIR.exists():
        return []
    all_sessions = sorted(SESSIONS_DIR.rglob("*.md"))
    if not all_sessions:
        return []

    latest = all_sessions[-1]
    content = latest.read_text(encoding="utf-8")

    paused: list[str] = []
    in_paused = False
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(("paused", "🔄 paused", "🔄 incomplete")):
            in_paused = True
            continue
        if in_paused:
            if stripped.startswith("-"):
                paused.append(stripped.lstrip("- ").strip())
                if len(paused) >= MAX_PAUSED:
                    break
            elif stripped == "" or stripped.startswith("#") or stripped.lower().startswith(("complete", "not started", "✅", "📍")):
                if paused:
                    break

    return paused


def _current_week_materials(week: int) -> list[str]:
    """List filenames in source-material/week-NN/ for the current week."""
    if week < 1 or week > TOTAL_WEEKS:
        return []
    wdir = WEEKS_LESSONS_DIR / f"week-{week:02d}"
    if not wdir.exists():
        return []
    return sorted(p.name for p in wdir.iterdir() if p.is_file() and not p.name.startswith("."))


def _inbox_count() -> int:
    """Count unprocessed external sessions waiting in inbox/."""
    if not INBOX_DIR.exists():
        return 0
    return sum(1 for p in INBOX_DIR.glob("*.md") if p.is_file())


def build_context() -> str:
    today = today_date()
    week = current_week(today)
    week_title = WEEK_TITLES.get(week, "(between weeks)")
    days_to_mid = days_until(MIDTERM_DATE, today)
    days_to_final = days_until(FINAL_DATE, today)

    total, covered, stale = _gather_concept_stats()
    paused = _recent_paused_from_last_session()
    materials = _current_week_materials(week)
    inbox_count = _inbox_count()

    parts: list[str] = []

    parts.append(
        f"## {SUBJECT_NAME} Study Session - Status Header\n"
        f"- Today: **{today.strftime('%A, %Y-%m-%d')}**\n"
        f"- Study week: **{week} / {TOTAL_WEEKS}** - *{week_title}*"
    )
    if MIDTERM_DATE:
        parts[-1] += f"\n- Midterm: {MIDTERM_DATE.isoformat()} ({days_to_mid} days)"
    if FINAL_DATE:
        parts[-1] += f"\n- Final: {FINAL_DATE.isoformat()} ({days_to_final} days)"

    if total == 0:
        progress_line = "Concepts encoded: 0 — knowledge base is empty. Next learn session will seed it."
    else:
        progress_line = f"Concepts at ≥ understand:good: **{covered} / {total}**"
    if inbox_count:
        plural = "session" if inbox_count == 1 else "sessions"
        progress_line += f"\nExternal inbox: **{inbox_count}** {plural} waiting to ingest."
    parts.append(f"## Progress\n{progress_line}")

    if stale:
        stale_lines = "\n".join(f"- {title} — {days}d since last revise" for title, days in stale)
        parts.append(f"## Stale concepts (>{STALE_DAYS}d)\n{stale_lines}")

    if paused:
        paused_lines = "\n".join(f"- {p}" for p in paused)
        parts.append(f"## Paused from last session\n{paused_lines}")

    if materials:
        mat_lines = "\n".join(f"- source-material/week-{week:02d}/{m}" for m in materials)
        parts.append(f"## This week's must-read material (week {week})\n{mat_lines}")
    elif 1 <= week <= TOTAL_WEEKS:
        parts.append(f"## This week's material\n(no files in source-material/week-{week:02d}/ yet)")

    parts.append(
        "## Instructions\n"
        "Full study-mode instructions live in `CLAUDE.md`. Use the `deep-encoding` skill "
        "for learn sessions. For a full progress dashboard run `/progress`. "
        "Do not modify `source-material/`, `extra-resources/`, or `syllabus.md`."
    )

    context = "\n\n---\n\n".join(parts)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n\n...(truncated)"
    return context


def main() -> None:
    context = build_context()
    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
