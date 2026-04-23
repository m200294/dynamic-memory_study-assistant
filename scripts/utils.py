"""Shared utilities for the study knowledge base."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

import yaml

from config import (
    CONCEPTS_DIR,
    CONNECTIONS_DIR,
    INDEX_FILE,
    KNOWLEDGE_DIR,
    LOG_FILE,
    SESSIONS_DIR,
    STATE_FILE,
    WEEKS_DIR,
)


# ── State management ──────────────────────────────────────────────────

def load_state() -> dict:
    """Load persistent state from state.json."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"ingested": {}, "total_cost": 0.0}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


# ── File hashing ──────────────────────────────────────────────────────

def file_hash(path: Path) -> str:
    """SHA-256 hash of a file (first 16 hex chars)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


# ── Slug / naming ─────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


# ── YAML frontmatter ──────────────────────────────────────────────────

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Split a markdown file into (frontmatter_dict, body). Empty dict if missing."""
    m = FRONTMATTER_RE.match(content)
    if not m:
        return {}, content
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, m.group(2)


def dump_frontmatter(fm: dict, body: str) -> str:
    """Rebuild a markdown file with YAML frontmatter."""
    yaml_text = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
    return f"---\n{yaml_text}\n---\n{body}"


# ── Concept listing ───────────────────────────────────────────────────

def list_concepts() -> list[Path]:
    """All concept files."""
    if not CONCEPTS_DIR.exists():
        return []
    return sorted(CONCEPTS_DIR.glob("*.md"))


def list_connections() -> list[Path]:
    if not CONNECTIONS_DIR.exists():
        return []
    return sorted(CONNECTIONS_DIR.glob("*.md"))


def list_week_files() -> list[Path]:
    if not WEEKS_DIR.exists():
        return []
    return sorted(WEEKS_DIR.glob("week-*.md"))


def list_sessions(week: int | None = None) -> list[Path]:
    """All session logs, optionally filtered to a specific week."""
    if not SESSIONS_DIR.exists():
        return []
    if week is None:
        return sorted(SESSIONS_DIR.rglob("*.md"))
    week_dir = SESSIONS_DIR / f"week-{week:02d}"
    if not week_dir.exists():
        return []
    return sorted(week_dir.glob("*.md"))


# ── Wiki content helpers ──────────────────────────────────────────────

def read_wiki_index() -> str:
    if INDEX_FILE.exists():
        return INDEX_FILE.read_text(encoding="utf-8")
    return (
        "# Knowledge Base Index\n\n"
        "| Concept | Week | Mastery (R/U/A/A/E) | Last revised | Sources |\n"
        "|---------|------|---------------------|--------------|---------|\n"
    )


# ── Mastery ratings ───────────────────────────────────────────────────

VALID_RATINGS = {"weak", "mid", "good", "solid", "untested"}
BLOOM_LEVELS = ["remember", "understand", "apply", "analyze", "evaluate"]


def empty_mastery() -> dict[str, str]:
    return {level: "untested" for level in BLOOM_LEVELS}


def mastery_glyph(rating: str) -> str:
    return {
        "weak":      "w",
        "mid":       "m",
        "good":      "g",
        "solid":     "S",
        "untested":  "-",
    }.get(rating, "?")


def mastery_summary(mastery: dict[str, str]) -> str:
    """Short compact form: 'g/g/m/m/w' in R/U/A/A/E order."""
    return "/".join(mastery_glyph(mastery.get(lvl, "untested")) for lvl in BLOOM_LEVELS)


def is_covered(mastery: dict[str, str], level: str = "understand", min_rating: str = "good") -> bool:
    """Is this concept 'covered' at a given Bloom level and minimum rating?"""
    order = ["untested", "weak", "mid", "good", "solid"]
    current = mastery.get(level, "untested")
    if current not in order or min_rating not in order:
        return False
    return order.index(current) >= order.index(min_rating)


# ── Log ───────────────────────────────────────────────────────────────

def append_log(entry: str) -> None:
    """Append a block to knowledge/log.md."""
    if not LOG_FILE.exists():
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        LOG_FILE.write_text("# Build Log\n\n", encoding="utf-8")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry.rstrip() + "\n\n")


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""
