"""Path constants and editable subject configuration for the study pipeline."""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# -- Paths -----------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent

SUBJECT_FILE = ROOT_DIR / "subject.yml"
SYLLABUS_FILE = ROOT_DIR / "syllabus.md"
WEEKS_LESSONS_DIR = ROOT_DIR / "source-material"
EXTRA_RESOURCES_DIR = ROOT_DIR / "extra-resources"
SESSIONS_DIR = ROOT_DIR / "sessions"
INBOX_DIR = ROOT_DIR / "inbox"
KNOWLEDGE_DIR = ROOT_DIR / "knowledge"
CONCEPTS_DIR = KNOWLEDGE_DIR / "concepts"
CONNECTIONS_DIR = KNOWLEDGE_DIR / "connections"
WEEKS_DIR = KNOWLEDGE_DIR / "weeks"

INDEX_FILE = KNOWLEDGE_DIR / "index.md"
PROGRESS_FILE = KNOWLEDGE_DIR / "progress.md"
LOG_FILE = KNOWLEDGE_DIR / "log.md"

SCRIPTS_DIR = ROOT_DIR / "scripts"
HOOKS_DIR = ROOT_DIR / "hooks"
STATE_FILE = SCRIPTS_DIR / "state.json"
CLAUDE_MD = ROOT_DIR / "CLAUDE.md"


DEFAULT_CONFIG: dict[str, Any] = {
    "student_name": "the student",
    "subject_name": "Your subject",
    "subject_code": "",
    "semester_start": None,
    "midterm_date": None,
    "final_date": None,
    "total_weeks": 12,
    "compile_after_hour": 18,
    "llm_model": "claude-sonnet-4-6",
    "weeks": {},
    "week_to_topic": {},
}


def _read_subject_config() -> dict[str, Any]:
    if not SUBJECT_FILE.exists():
        return dict(DEFAULT_CONFIG)
    raw = yaml.safe_load(SUBJECT_FILE.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("subject.yml must contain a YAML mapping")
    config = dict(DEFAULT_CONFIG)
    config.update(raw)
    return config


def _parse_optional_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


SUBJECT_CONFIG = _read_subject_config()

STUDENT_NAME = str(SUBJECT_CONFIG.get("student_name") or "the student")
SUBJECT_NAME = str(SUBJECT_CONFIG.get("subject_name") or "Your subject")
SUBJECT_CODE = str(SUBJECT_CONFIG.get("subject_code") or "")
TOTAL_WEEKS = int(SUBJECT_CONFIG.get("total_weeks") or 12)
SEMESTER_START = _parse_optional_date(SUBJECT_CONFIG.get("semester_start"))
MIDTERM_DATE = _parse_optional_date(SUBJECT_CONFIG.get("midterm_date"))
FINAL_DATE = _parse_optional_date(SUBJECT_CONFIG.get("final_date"))
COMPILE_AFTER_HOUR = int(SUBJECT_CONFIG.get("compile_after_hour") or 18)
LLM_MODEL = str(SUBJECT_CONFIG.get("llm_model") or "claude-sonnet-4-6")

WEEK_TITLES: dict[int, str] = {
    int(k): str(v) for k, v in (SUBJECT_CONFIG.get("weeks") or {}).items()
}
for week in range(1, TOTAL_WEEKS + 1):
    WEEK_TITLES.setdefault(week, f"Week {week}")

WEEK_TO_TOPIC: dict[int, str] = {
    int(k): str(v) for k, v in (SUBJECT_CONFIG.get("week_to_topic") or {}).items()
}


def now_iso() -> str:
    """Current time in ISO 8601 format."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def today_iso() -> str:
    """Current date in ISO 8601 format."""
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")


def today_date() -> date:
    """Current date as a date object in the local timezone."""
    return datetime.now(timezone.utc).astimezone().date()


def current_week(today: date | None = None) -> int:
    """
    Compute the current study week.

    If `semester_start` is unset in subject.yml, week 1 is used by default.
    """
    if today is None:
        today = today_date()
    if SEMESTER_START is None:
        return 1
    if today < SEMESTER_START:
        return 0
    delta_days = (today - SEMESTER_START).days
    week = (delta_days // 7) + 1
    return min(week, TOTAL_WEEKS)


def days_until(target: date | None, today: date | None = None) -> int | None:
    """Days from today to target, or None when the target is not configured."""
    if target is None:
        return None
    if today is None:
        today = today_date()
    return (target - today).days
