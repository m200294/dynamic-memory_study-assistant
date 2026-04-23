"""
Schema validation for the study knowledge base.

Canonical session and concept files are strict. Inbox files are intentionally
more forgiving because they are the boundary for external tools and notes.

Usage:
    uv run python scripts/validate.py --all
    uv run python scripts/validate.py sessions/week-01/example.md
    uv run python scripts/validate.py --kind inbox inbox/example.md
    uv run python scripts/validate.py --write-schemas
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from config import CONCEPTS_DIR, SESSIONS_DIR, TOTAL_WEEKS  # noqa: E402
from utils import parse_frontmatter  # noqa: E402


BLOOM_LEVELS = ("remember", "understand", "apply", "analyze", "evaluate")
VALID_RATINGS = ("weak", "mid", "good", "solid", "untested")
VALID_SESSION_TYPES = ("learn", "revise", "other")
VALID_SOURCES = ("claude", "codex", "chatgpt", "voice-note", "other")

BloomLevel = Literal["remember", "understand", "apply", "analyze", "evaluate"]
Rating = Literal["weak", "mid", "good", "solid", "untested"]
SessionType = Literal["learn", "revise", "other"]
CanonicalSource = Literal["claude", "codex", "chatgpt", "voice-note", "other"]
InboxSource = Literal["codex", "chatgpt", "voice-note", "other"]

BLOOM_ALIASES = {
    "remembering": "remember",
    "recall": "remember",
    "understanding": "understand",
    "comprehend": "understand",
    "comprehension": "understand",
    "application": "apply",
    "applying": "apply",
    "analysis": "analyze",
    "analysing": "analyze",
    "analyzing": "analyze",
    "evaluation": "evaluate",
    "evaluating": "evaluate",
}
RATING_ALIASES = {
    "poor": "weak",
    "low": "weak",
    "medium": "mid",
    "partial": "mid",
    "ok": "good",
    "okay": "good",
    "strong": "solid",
}
SOURCE_ALIASES = {
    "claude-code": "claude",
    "anthropic": "claude",
    "openai": "chatgpt",
    "gpt": "chatgpt",
    "chat-gpt": "chatgpt",
    "voice_note": "voice-note",
    "voice note": "voice-note",
}
SESSION_TYPE_ALIASES = {
    "learning": "learn",
    "study": "learn",
    "review": "revise",
    "revision": "revise",
    "meta": "other",
    "planning": "other",
}

SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
SLUG_RE = re.compile(SLUG_PATTERN)

# Probe-history defaults. See docs/codex-compile.md for the operational flow.
PROBE_HISTORY_LIMIT = 5
# `with_prompting: true` can support mid, but cannot alone justify good/solid.
PROMOTED_OUTCOMES_REQUIRE_UNPROMPTED = {"good", "solid"}


def normalize_question(question: str) -> str:
    """Stable normalization for probe_id derivation."""
    text = question.strip().lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def make_probe_id(
    session_id: str,
    concept_slug: str,
    bloom_level: str,
    question: str,
) -> str:
    """Deterministic probe_id: sha256 of (session_id, concept, bloom, normalized_question)."""
    payload = "|".join([
        session_id.strip(),
        concept_slug.strip().lower(),
        bloom_level.strip().lower(),
        normalize_question(question),
    ])
    return "p-" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


class ValidationFailure(Exception):
    """Raised when a markdown file does not match the expected frontmatter schema."""

    def __init__(self, path: Path, kind: str, message: str):
        self.path = path
        self.kind = kind
        self.message = message
        super().__init__(f"{path}: invalid {kind}: {message}")


def _clean_str(value: Any) -> str:
    if not isinstance(value, str):
        raise TypeError("expected a string")
    return value.strip()


def _clean_literal(value: Any) -> str:
    return _clean_str(value).lower().replace("_", "-")


def _normalize_literal(value: Any, aliases: dict[str, str]) -> Any:
    if not isinstance(value, str):
        return value
    cleaned = _clean_literal(value)
    return aliases.get(cleaned, cleaned)


def _normalize_bloom_key(key: Any) -> Any:
    if not isinstance(key, str):
        return key
    cleaned = _clean_literal(key)
    return BLOOM_ALIASES.get(cleaned, cleaned)


def _normalize_rating(value: Any) -> Any:
    return _normalize_literal(value, RATING_ALIASES)


def _normalize_source(value: Any) -> Any:
    return _normalize_literal(value, SOURCE_ALIASES)


def _normalize_session_type(value: Any) -> Any:
    return _normalize_literal(value, SESSION_TYPE_ALIASES)


def _format_errors(exc: ValidationError) -> str:
    parts: list[str] = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"])
        parts.append(f"{loc}: {err['msg']}" if loc else err["msg"])
    return "; ".join(parts)


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InboxHeader(StrictBaseModel):
    source: InboxSource
    session_type: SessionType
    week: int = Field(ge=1, le=TOTAL_WEEKS)
    date: date
    model: str | None = None

    @field_validator("source", mode="before")
    @classmethod
    def normalize_source(cls, value: Any) -> Any:
        normalized = _normalize_source(value)
        return "chatgpt" if normalized == "openai" else normalized

    @field_validator("session_type", mode="before")
    @classmethod
    def normalize_session_type(cls, value: Any) -> Any:
        return _normalize_session_type(value)

    @field_validator("model", mode="before")
    @classmethod
    def clean_model(cls, value: Any) -> Any:
        if value is None:
            return None
        cleaned = _clean_str(value)
        return cleaned or None


ProbeOutcome = Literal["weak", "mid", "good", "solid"]


class ProbeObserved(StrictBaseModel):
    """One Q&A pair from a revise session. Nested under SessionConcept."""
    probe_id: str = Field(min_length=1)
    bloom_level: BloomLevel
    question: str = Field(min_length=1)
    answer_summary: str = Field(default="")
    outcome: ProbeOutcome
    with_prompting: bool = False
    probe_context: str | None = None

    @field_validator("bloom_level", mode="before")
    @classmethod
    def _normalize_bloom(cls, value: Any) -> Any:
        return _normalize_bloom_key(value)

    @field_validator("outcome", mode="before")
    @classmethod
    def _normalize_outcome(cls, value: Any) -> Any:
        normalized = _normalize_rating(value)
        if normalized == "untested":
            raise ValueError("probe outcome cannot be 'untested'")
        return normalized

    @field_validator("question", "answer_summary")
    @classmethod
    def _clean_text(cls, value: str) -> str:
        return _clean_str(value)

    @field_validator("probe_context")
    @classmethod
    def _clean_context(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = _clean_str(value)
        return cleaned or None


class ProbeHistoryEntry(StrictBaseModel):
    """Derived cache entry in a concept file. Built by compile.py, not LLM."""
    probe_id: str = Field(min_length=1)
    date: date
    bloom_level: BloomLevel
    question: str = Field(min_length=1)
    outcome: ProbeOutcome
    with_prompting: bool = False
    session_file: str = Field(min_length=1)

    @field_validator("bloom_level", mode="before")
    @classmethod
    def _normalize_bloom(cls, value: Any) -> Any:
        return _normalize_bloom_key(value)

    @field_validator("outcome", mode="before")
    @classmethod
    def _normalize_outcome(cls, value: Any) -> Any:
        normalized = _normalize_rating(value)
        if normalized == "untested":
            raise ValueError("probe outcome cannot be 'untested'")
        return normalized


class SessionConcept(StrictBaseModel):
    slug: str = Field(pattern=SLUG_PATTERN)
    title: str | None = None
    ratings_observed: dict[BloomLevel, Rating] = Field(default_factory=dict)
    layer_reached: int = Field(ge=1, le=4)
    bloom_levels_probed: list[BloomLevel] = Field(default_factory=list)
    weak_spots: list[str] = Field(default_factory=list)
    solid_connections: list[str] = Field(default_factory=list)
    sources_consulted: list[str] = Field(default_factory=list)
    probes: list[ProbeObserved] = Field(default_factory=list)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        value = _clean_str(value)
        if not SLUG_RE.match(value):
            raise ValueError("must be kebab-case")
        return value

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = _clean_str(value)
        return cleaned or None

    @field_validator("weak_spots", "solid_connections", "sources_consulted")
    @classmethod
    def clean_string_list(cls, values: list[str]) -> list[str]:
        return [_clean_str(v) for v in values if _clean_str(v)]

    @model_validator(mode="after")
    def probed_levels_have_observations(self) -> "SessionConcept":
        missing = [
            level for level in self.bloom_levels_probed
            if level not in self.ratings_observed
        ]
        if missing:
            raise ValueError(f"bloom_levels_probed missing ratings_observed entries: {missing}")
        return self

    @model_validator(mode="after")
    def prompted_probes_cannot_alone_justify_promotion(self) -> "SessionConcept":
        """`with_prompting: true` can support mid, but cannot alone justify good/solid.
        If ratings_observed[level] is good/solid and ALL probes at that level were
        prompted, the rating is not supported by the probe evidence."""
        if not self.probes:
            return self
        by_level: dict[str, list[ProbeObserved]] = {}
        for probe in self.probes:
            by_level.setdefault(probe.bloom_level, []).append(probe)
        for level, rating in self.ratings_observed.items():
            if rating not in PROMOTED_OUTCOMES_REQUIRE_UNPROMPTED:
                continue
            level_probes = by_level.get(level, [])
            if not level_probes:
                continue  # non-probe evidence path; cannot enforce
            if all(p.with_prompting for p in level_probes):
                raise ValueError(
                    f"ratings_observed[{level}]={rating!r} cannot be justified by "
                    "prompted-only probes; needs an unprompted probe at this level"
                )
        return self


class SessionLogFrontmatter(StrictBaseModel):
    session_type: SessionType
    source: CanonicalSource
    session_id: str = Field(min_length=1)
    model: str | None = None
    week: int = Field(ge=1, le=TOTAL_WEEKS)
    date: date
    primary_concept: str = Field(pattern=SLUG_PATTERN)
    concepts: list[SessionConcept] = Field(default_factory=list)

    @field_validator("session_id")
    @classmethod
    def clean_session_id(cls, value: str) -> str:
        value = _clean_str(value)
        if not value:
            raise ValueError("must not be empty")
        return value

    @field_validator("primary_concept")
    @classmethod
    def validate_primary_concept(cls, value: str) -> str:
        value = _clean_str(value)
        if not SLUG_RE.match(value):
            raise ValueError("must be kebab-case")
        return value

    @field_validator("model")
    @classmethod
    def clean_model(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = _clean_str(value)
        return cleaned or None

    @model_validator(mode="after")
    def study_sessions_have_concepts(self) -> "SessionLogFrontmatter":
        if self.session_type in {"learn", "revise"} and not self.concepts:
            raise ValueError("learn/revise sessions must include at least one concept")
        return self


class ConceptFrontmatter(StrictBaseModel):
    title: str = Field(min_length=1)
    slug: str = Field(pattern=SLUG_PATTERN)
    week: int = Field(ge=1, le=TOTAL_WEEKS)
    also_in_weeks: list[int] = Field(default_factory=list)
    mastery: dict[BloomLevel, Rating]
    layer_reached: int = Field(ge=1, le=4)
    last_studied: date
    last_revised: date
    sources: list[str] = Field(default_factory=list)
    weak_spots: list[str] = Field(default_factory=list)
    solid_connections: list[str] = Field(default_factory=list)
    probe_history: list[ProbeHistoryEntry] = Field(default_factory=list)

    @field_validator("title", "slug")
    @classmethod
    def clean_required_string(cls, value: str) -> str:
        return _clean_str(value)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        if not SLUG_RE.match(value):
            raise ValueError("must be kebab-case")
        return value

    @field_validator("also_in_weeks")
    @classmethod
    def validate_also_weeks(cls, values: list[int]) -> list[int]:
        invalid = [v for v in values if v < 1 or v > TOTAL_WEEKS]
        if invalid:
            raise ValueError(f"week values out of range: {invalid}")
        return sorted(set(values))

    @field_validator("sources", "weak_spots", "solid_connections")
    @classmethod
    def clean_string_list(cls, values: list[str]) -> list[str]:
        return [_clean_str(v) for v in values if _clean_str(v)]

    @model_validator(mode="after")
    def mastery_has_exact_levels(self) -> "ConceptFrontmatter":
        keys = set(self.mastery)
        expected = set(BLOOM_LEVELS)
        if keys != expected:
            missing = sorted(expected - keys)
            extra = sorted(keys - expected)
            raise ValueError(
                f"mastery must have exact Bloom levels; missing={missing}, extra={extra}"
            )
        if self.last_revised < self.last_studied:
            raise ValueError("last_revised cannot be earlier than last_studied")
        return self


def normalize_session_frontmatter(
    data: dict[str, Any],
    *,
    source: str | None = None,
    session_id: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Normalize forgiving LLM output into canonical session frontmatter."""
    normalized = dict(data)
    if "session_type" in normalized:
        normalized["session_type"] = _normalize_session_type(normalized["session_type"])
    if source is not None:
        normalized["source"] = _normalize_source(source)
    elif "source" in normalized:
        normalized["source"] = _normalize_source(normalized["source"])
    if session_id is not None:
        normalized["session_id"] = session_id
    if model is not None:
        normalized["model"] = model

    effective_session_id = session_id or normalized.get("session_id") or ""

    top_level_probes = normalized.pop("probes", []) or []
    probes_by_concept: dict[str, list[dict[str, Any]]] = {}
    for raw_probe in top_level_probes:
        probe = dict(raw_probe)
        concept_slug = (
            probe.pop("concept", None)
            or probe.pop("slug", None)
            or normalized.get("primary_concept", "")
        )
        if concept_slug:
            probes_by_concept.setdefault(str(concept_slug), []).append(probe)

    concepts = []
    for raw_concept in normalized.get("concepts") or []:
        concept = dict(raw_concept)
        concept_slug = str(concept.get("slug", ""))
        ratings = concept.get("ratings_observed") or {}
        concept["ratings_observed"] = {
            _normalize_bloom_key(k): _normalize_rating(v)
            for k, v in ratings.items()
        }
        concept["bloom_levels_probed"] = [
            _normalize_bloom_key(level)
            for level in (concept.get("bloom_levels_probed") or [])
        ]

        raw_probes = list(concept.get("probes") or [])
        raw_probes.extend(probes_by_concept.pop(concept_slug, []))

        probes = []
        for raw_probe in raw_probes:
            probe = dict(raw_probe)
            if "bloom_level" in probe:
                probe["bloom_level"] = _normalize_bloom_key(probe["bloom_level"])
            if "outcome" in probe:
                probe["outcome"] = _normalize_rating(probe["outcome"])
            if not probe.get("probe_id"):
                probe["probe_id"] = make_probe_id(
                    effective_session_id,
                    concept_slug,
                    str(probe.get("bloom_level", "")),
                    str(probe.get("question", "")),
                )
            probes.append(probe)
        concept["probes"] = probes

        concepts.append(concept)

    if probes_by_concept and concepts:
        primary_slug = str(normalized.get("primary_concept", ""))
        fallback = next((c for c in concepts if c.get("slug") == primary_slug), concepts[0])
        for concept_slug, raw_probes in probes_by_concept.items():
            fallback_probes = list(fallback.get("probes") or [])
            for raw_probe in raw_probes:
                probe = dict(raw_probe)
                if "bloom_level" in probe:
                    probe["bloom_level"] = _normalize_bloom_key(probe["bloom_level"])
                if "outcome" in probe:
                    probe["outcome"] = _normalize_rating(probe["outcome"])
                if not probe.get("probe_id"):
                    probe["probe_id"] = make_probe_id(
                        effective_session_id,
                        concept_slug,
                        str(probe.get("bloom_level", "")),
                        str(probe.get("question", "")),
                    )
                fallback_probes.append(probe)
            fallback["probes"] = fallback_probes
    normalized["concepts"] = concepts
    return normalized


def split_markdown_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    content = path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)
    if not frontmatter:
        raise ValidationFailure(path, "frontmatter", "missing or invalid YAML frontmatter")
    return frontmatter, body


def validate_inbox_frontmatter(data: dict[str, Any], path: Path | None = None) -> InboxHeader:
    try:
        return InboxHeader.model_validate(data)
    except ValidationError as exc:
        raise ValidationFailure(path or Path("<memory>"), "inbox", _format_errors(exc)) from exc


def validate_session_frontmatter(
    data: dict[str, Any],
    path: Path | None = None,
) -> SessionLogFrontmatter:
    try:
        return SessionLogFrontmatter.model_validate(normalize_session_frontmatter(data))
    except ValidationError as exc:
        raise ValidationFailure(path or Path("<memory>"), "session", _format_errors(exc)) from exc


def validate_concept_frontmatter(
    data: dict[str, Any],
    path: Path | None = None,
) -> ConceptFrontmatter:
    try:
        return ConceptFrontmatter.model_validate(data)
    except ValidationError as exc:
        raise ValidationFailure(path or Path("<memory>"), "concept", _format_errors(exc)) from exc


def validate_inbox_file(path: Path) -> InboxHeader:
    frontmatter, _ = split_markdown_frontmatter(path)
    return validate_inbox_frontmatter(frontmatter, path)


def validate_session_file(path: Path) -> SessionLogFrontmatter:
    frontmatter, _ = split_markdown_frontmatter(path)
    return validate_session_frontmatter(frontmatter, path)


def session_warnings(session: SessionLogFrontmatter) -> list[str]:
    """Non-fatal schema-quality warnings."""
    warnings: list[str] = []
    if session.session_type == "revise":
        probe_count = sum(len(concept.probes) for concept in session.concepts)
        if probe_count == 0:
            warnings.append("revise session has no structured probes")
    return warnings


def validate_concept_file(path: Path) -> ConceptFrontmatter:
    frontmatter, _ = split_markdown_frontmatter(path)
    return validate_concept_frontmatter(frontmatter, path)


def write_json_schemas() -> None:
    schemas_dir = ROOT_DIR / "docs" / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    schemas = {
        "inbox-header.schema.json": InboxHeader.model_json_schema(),
        "session-log.schema.json": SessionLogFrontmatter.model_json_schema(),
        "concept-frontmatter.schema.json": ConceptFrontmatter.model_json_schema(),
    }
    for filename, schema in schemas.items():
        path = schemas_dir / filename
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def infer_kind(path: Path) -> str:
    try:
        rel = path.resolve().relative_to(ROOT_DIR)
    except ValueError:
        rel = path
    parts = rel.parts
    if parts and parts[0] == "sessions":
        return "session"
    if len(parts) >= 2 and parts[0] == "knowledge" and parts[1] == "concepts":
        return "concept"
    if parts and parts[0] == "inbox":
        return "inbox"
    raise ValidationFailure(path, "path", "could not infer kind; pass --kind")


def validate_path(path: Path, kind: str) -> list[str]:
    if kind == "auto":
        kind = infer_kind(path)
    if kind == "inbox":
        validate_inbox_file(path)
        return []
    elif kind == "session":
        return session_warnings(validate_session_file(path))
    elif kind == "concept":
        validate_concept_file(path)
        return []
    else:
        raise ValueError(f"unknown validation kind: {kind}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate study-pipeline markdown frontmatter")
    parser.add_argument("paths", nargs="*", type=Path, help="Markdown files to validate")
    parser.add_argument("--kind", choices=["auto", "inbox", "session", "concept"], default="auto")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all sessions and concept files",
    )
    parser.add_argument(
        "--write-schemas",
        action="store_true",
        help="Write JSON Schema docs to docs/schemas/",
    )
    args = parser.parse_args()

    if args.write_schemas or args.all or not args.paths:
        write_json_schemas()

    paths = list(args.paths)
    if args.all:
        paths.extend(sorted(SESSIONS_DIR.rglob("*.md")) if SESSIONS_DIR.exists() else [])
        paths.extend(sorted(CONCEPTS_DIR.glob("*.md")) if CONCEPTS_DIR.exists() else [])

    if not paths:
        print("Wrote JSON schemas to docs/schemas/. No files requested for validation.")
        return

    failures: list[ValidationFailure] = []
    for path in paths:
        try:
            warnings = validate_path(path, args.kind)
            print(f"ok: {path.relative_to(ROOT_DIR) if path.is_relative_to(ROOT_DIR) else path}")
            for warning in warnings:
                print(f"warning: {path}: {warning}", file=sys.stderr)
        except ValidationFailure as exc:
            failures.append(exc)
            print(f"error: {exc}", file=sys.stderr)

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
