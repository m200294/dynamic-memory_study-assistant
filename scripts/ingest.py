"""
Ingest external study sessions from inbox/ into canonical sessions/.

Inbox files are freeform markdown with minimal frontmatter. This script asks the
LLM judge to normalize each file into the strict session-log schema, validates
the result, writes it under sessions/week-NN/, and moves the source file to
inbox/processed/. Failed files move to inbox/failed/ with an error note.

Usage:
    uv run python scripts/ingest.py
    uv run python scripts/ingest.py --compile
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from config import (  # noqa: E402
    INBOX_DIR,
    LLM_MODEL,
    ROOT_DIR as CONFIG_ROOT,
    SCRIPTS_DIR,
    SESSIONS_DIR,
    SUBJECT_NAME,
    WEEK_TITLES,
)
from utils import dump_frontmatter, parse_frontmatter  # noqa: E402
from validate import (  # noqa: E402
    ValidationFailure,
    normalize_session_frontmatter,
    split_markdown_frontmatter,
    validate_inbox_frontmatter,
    validate_session_frontmatter,
)

PROCESSED_DIR = INBOX_DIR / "processed"
FAILED_DIR = INBOX_DIR / "failed"

INGEST_MODEL = LLM_MODEL


def content_session_id(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def safe_destination(directory: Path, filename: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    i = 2
    while True:
        candidate = directory / f"{stem}-{i}{suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def move_to_processed(path: Path) -> Path:
    dest = safe_destination(PROCESSED_DIR, path.name)
    shutil.move(str(path), str(dest))
    return dest


def move_to_failed(path: Path, error: str) -> Path:
    dest = safe_destination(FAILED_DIR, path.name)
    shutil.move(str(path), str(dest))
    error_path = dest.with_suffix(dest.suffix + ".error.txt")
    error_path.write_text(error.strip() + "\n", encoding="utf-8")
    return dest


def existing_session_ids() -> dict[str, Path]:
    ids: dict[str, Path] = {}
    if not SESSIONS_DIR.exists():
        return ids
    for path in sorted(SESSIONS_DIR.rglob("*.md")):
        content = path.read_text(encoding="utf-8")
        frontmatter, _ = parse_frontmatter(content)
        session_id = frontmatter.get("session_id") if frontmatter else None
        if isinstance(session_id, str) and session_id:
            ids[session_id] = path
    return ids


def extract_markdown_response(response: str) -> str:
    text = response.strip()
    fenced = re.search(r"```(?:markdown|md)?\s*\n(.*?)\n```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip() + "\n"
    return text + "\n"


def build_prompt(inbox_path: Path, header: Any, body: str, session_id: str) -> str:
    week_title = WEEK_TITLES.get(header.week, "(unknown week)")
    return f"""You are the external-session ingest judge for the {SUBJECT_NAME} study pipeline.

Read the inbox entry below and return exactly one canonical session-log markdown
file. Do not write files. Do not wrap the answer in a code fence.

## Fixed metadata

- source: {header.source}
- model: {header.model or ""}
- session_id: {session_id}
- session_type: {header.session_type}
- week: {header.week} — {week_title}
- date: {header.date.isoformat()}
- input file: {inbox_path.relative_to(CONFIG_ROOT)}

## Canonical frontmatter schema

```yaml
---
session_type: learn
source: codex
session_id: <stable id>
model: <optional model name>
week: 3
date: 2026-05-03
primary_concept: <kebab-case slug>
concepts:
  - slug: <kebab-case slug>
    title: <Human-readable title>
    ratings_observed:
      remember: good
      understand: mid
    layer_reached: 2
    bloom_levels_probed: [remember, understand]
    weak_spots:
      - "specific observed struggle"
    solid_connections:
      - "specific connection demonstrated"
    sources_consulted:
      - "source-material/week-03/<file>"
    probes:
      - bloom_level: analyze
        question: "near-verbatim question asked"
        answer_summary: "one-sentence answer summary"
        outcome: mid
        with_prompting: true
        probe_context: "optional note for multi-turn probes"
---
```

Allowed `session_type`: learn, revise, other.
Allowed `source`: claude, codex, chatgpt, voice-note, other.
Allowed Bloom levels: remember, understand, apply, analyze, evaluate.
Allowed ratings: weak, mid, good, solid, untested.

If the input is a meta/tooling session rather than study content, use
`session_type: other`, `concepts: []`, and a short body explaining what happened.
For learn/revise sessions, include one concept entry per real concept discussed.
Only put Bloom levels in `ratings_observed` when the input contains evidence
that level was actually probed or demonstrated.
For revise sessions, extract every distinct probe Q&A pair into `probes:` under
the matching concept. A prompted answer can support `mid`, but do not set a
concept's `ratings_observed` to `good` or `solid` for a Bloom level when all
probes at that level needed prompting.

## Inbox body

```markdown
{body}
```
"""


async def run_ingest_agent(prompt: str) -> str:
    from claude_agent_sdk import (
        AssistantMessage,
        ClaudeAgentOptions,
        ResultMessage,
        TextBlock,
        query,
    )

    response = ""
    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            model=INGEST_MODEL,
            cwd=str(ROOT_DIR),
            system_prompt={"type": "preset", "preset": "claude_code"},
            allowed_tools=[],
            permission_mode="acceptEdits",
            max_turns=4,
        ),
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    response += block.text
        elif isinstance(message, ResultMessage):
            pass
    return response


def canonical_session_path(frontmatter: dict[str, Any]) -> Path:
    week = int(frontmatter["week"])
    date = str(frontmatter["date"])
    session_type = frontmatter["session_type"]
    slug = frontmatter["primary_concept"]
    session_dir = SESSIONS_DIR / f"week-{week:02d}"
    filename = f"{date}-{session_type}-{slug}.md"
    target = session_dir / filename
    if not target.exists():
        return target
    existing_fm, _ = parse_frontmatter(target.read_text(encoding="utf-8"))
    if existing_fm.get("session_id") == frontmatter.get("session_id"):
        return target
    short_id = str(frontmatter["session_id"])[:8]
    return session_dir / f"{date}-{session_type}-{slug}-{short_id}.md"


async def ingest_one(path: Path, known_ids: dict[str, Path]) -> tuple[str, Path | None]:
    raw = path.read_bytes()
    session_id = content_session_id(raw)

    try:
        raw_frontmatter, body = split_markdown_frontmatter(path)
        header = validate_inbox_frontmatter(raw_frontmatter, path)
    except ValidationFailure as exc:
        failed = move_to_failed(path, str(exc))
        return f"failed: {failed.relative_to(ROOT_DIR)} ({exc.message})", None

    if session_id in known_ids:
        processed = move_to_processed(path)
        existing = known_ids[session_id].relative_to(ROOT_DIR)
        return (
            f"skipped duplicate: {processed.relative_to(ROOT_DIR)} -> {existing}",
            known_ids[session_id],
        )

    prompt = build_prompt(path, header, body, session_id)
    try:
        response = await run_ingest_agent(prompt)
        markdown = extract_markdown_response(response)
        generated_frontmatter, generated_body = parse_frontmatter(markdown)
        if not generated_frontmatter:
            raise ValidationFailure(
                path,
                "session",
                "LLM response did not contain YAML frontmatter",
            )

        normalized_frontmatter = normalize_session_frontmatter(
            generated_frontmatter,
            source=header.source,
            session_id=session_id,
            model=header.model,
        )
        normalized_frontmatter["session_type"] = header.session_type
        normalized_frontmatter["week"] = header.week
        normalized_frontmatter["date"] = header.date.isoformat()

        session = validate_session_frontmatter(normalized_frontmatter, path)
        canonical_frontmatter = session.model_dump(mode="json", exclude_none=True)
        target = canonical_session_path(canonical_frontmatter)
        if target.exists():
            existing_fm, _ = parse_frontmatter(target.read_text(encoding="utf-8"))
            if existing_fm.get("session_id") == session_id:
                processed = move_to_processed(path)
                known_ids[session_id] = target
                return (
                    "skipped duplicate: "
                    f"{processed.relative_to(ROOT_DIR)} -> {target.relative_to(ROOT_DIR)}",
                    target,
                )

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            dump_frontmatter(canonical_frontmatter, generated_body.lstrip()),
            encoding="utf-8",
        )
        known_ids[session_id] = target
        processed = move_to_processed(path)
        return (
            f"ingested: {processed.relative_to(ROOT_DIR)} -> {target.relative_to(ROOT_DIR)}",
            target,
        )
    except Exception as exc:
        failed = move_to_failed(path, f"{type(exc).__name__}: {exc}")
        return f"failed: {failed.relative_to(ROOT_DIR)} ({type(exc).__name__}: {exc})", None


def inbox_files() -> list[Path]:
    if not INBOX_DIR.exists():
        return []
    return sorted(p for p in INBOX_DIR.glob("*.md") if p.is_file())


def run_compile() -> None:
    cmd = ["uv", "run", "--directory", str(ROOT_DIR), "python", str(SCRIPTS_DIR / "compile.py")]
    subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)


async def async_main(compile_after: bool) -> int:
    if os.environ.get("STUDY_PIPELINE_CODEX_FALLBACK"):
        print(
            "Refusing ingest.py in STUDY_PIPELINE_CODEX_FALLBACK mode; "
            "use ./codex_compile so Codex converts inbox files directly.",
            file=sys.stderr,
        )
        return 2

    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    FAILED_DIR.mkdir(parents=True, exist_ok=True)

    files = inbox_files()
    if not files:
        print("No inbox files to ingest.")
        return 0

    known_ids = existing_session_ids()
    written: list[Path] = []
    for path in files:
        status, target = await ingest_one(path, known_ids)
        print(status)
        if target is not None:
            written.append(target)

    if compile_after and written:
        run_compile()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest external study sessions from inbox/")
    parser.add_argument(
        "--compile",
        action="store_true",
        help="Run compile.py after successful ingest",
    )
    args = parser.parse_args()

    raise SystemExit(asyncio.run(async_main(args.compile)))


if __name__ == "__main__":
    main()
