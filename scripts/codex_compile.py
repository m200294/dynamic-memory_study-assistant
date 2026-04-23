"""
One-command Codex fallback for the study memory compiler.

Normal use:
    ./codex_compile

This is for the "Claude usage is exhausted" path. It launches Codex with a
purpose-built prompt that asks Codex to do the semantic work that Claude's
flush.py / ingest.py / compile.py normally do. After Codex returns, this driver
runs local validation, rebuilds derived probe history/progress, and marks
session files as compiled in scripts/state.json.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from config import INBOX_DIR, ROOT_DIR, SUBJECT_NAME, now_iso  # noqa: E402
from utils import file_hash, list_sessions, load_state, save_state  # noqa: E402


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT_DIR))


def inbox_files() -> list[Path]:
    if not INBOX_DIR.exists():
        return []
    return sorted(p for p in INBOX_DIR.glob("*.md") if p.is_file())


def pending_session_files() -> list[Path]:
    state = load_state()
    pending: list[Path] = []
    for session in list_sessions():
        state_entry = state.get("ingested", {}).get(rel(session), {})
        if state_entry.get("hash") != file_hash(session):
            pending.append(session)
    return pending


def build_prompt(*, force_all: bool = False) -> str:
    inbox = inbox_files()
    sessions = list_sessions() if force_all else pending_session_files()

    inbox_block = "\n".join(f"- {rel(p)}" for p in inbox) or "- (none)"
    sessions_block = "\n".join(f"- {rel(p)}" for p in sessions) or "- (none)"

    scope = (
        "all existing session logs"
        if force_all
        else "only uncompiled or changed session logs"
    )

    return f"""You are running Codex as the {SUBJECT_NAME} memory compiler fallback.

Claude usage may be exhausted. Do the semantic work directly in the repository.

## Critical restrictions

- Do not run `scripts/flush.py`.
- Do not run `scripts/ingest.py`.
- Do not run `scripts/compile.py`, except `scripts/compile.py --progress-only`.
- Those scripts normally call `claude-agent-sdk`; this fallback exists to avoid
  needing Claude for the semantic compile path.
- Do not revert unrelated user changes.

## First read

Read these before editing:

- `AGENTS.md`
- `CLAUDE.md`
- `.claude/skills/deep-encoding/SKILL.md`
- `docs/codex-compile.md`
- `scripts/validate.py`
- `scripts/compile.py` for the target knowledge-file shapes and evidence rule.

## Work to process

Inbox files to ingest:

{inbox_block}

Session logs to compile ({scope}):

{sessions_block}

If both lists are empty, run validation only and report that there is nothing to
compile.

## Step 1: Ingest inbox files, if any

For every direct `inbox/*.md` file:

1. Read the inbox frontmatter and body.
2. Convert it into one canonical session log under `sessions/week-NN/`.
3. Use `session_id` equal to the sha256 hex digest of the original inbox file
   bytes. If an existing `sessions/**/*.md` already has that `session_id`, do
   not create a duplicate.
4. For revise sessions, capture structured Q&A evidence in `concepts[].probes`.
5. Validate the resulting session log against `scripts/validate.py`.
6. If successful, move the original inbox file to `inbox/processed/`.
7. If you cannot produce a valid canonical session log, move the original file
   to `inbox/failed/` and write a sibling `.error.txt` explaining the concrete
   problem.

## Step 2: Compile session logs into knowledge

Compile {scope}. Apply the same evidence rule as `scripts/compile.py`:

- Create missing `knowledge/concepts/<slug>.md` files.
- For existing concept files, change a Bloom rating only when the session gives
  evidence. No evidence means no rating change.
- Always bump `last_revised` to the session date when the concept appears.
- Do not manually curate `probe_history`; it is rebuilt locally afterward.
- Update `knowledge/index.md`.
- Update touched `knowledge/weeks/week-NN.md` files.
- Append a clear entry to `knowledge/log.md`.
- Do not update `knowledge/progress.md` manually.

Use canonical frontmatter. Keep YAML valid. Preserve useful existing concept
body content and add concise new nuance rather than rewriting from scratch.

## Step 3: Local checks

Run:

```bash
uv run python scripts/validate.py --all
uv run python scripts/compile.py --progress-only
uv run python scripts/validate.py --all
```

If any check fails, fix the files and rerun it.

## Final response

Summarize:

- inbox files processed / failed
- session logs created or compiled
- concepts created or updated
- validation result
"""


def run_command(command: list[str], *, input_text: str | None = None) -> None:
    env = os.environ.copy()
    env.setdefault("UV_CACHE_DIR", "/tmp/uv-cache")
    env["STUDY_PIPELINE_CODEX_FALLBACK"] = "1"
    result = subprocess.run(
        command,
        input=input_text,
        text=True,
        cwd=str(ROOT_DIR),
        env=env,
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def run_codex(prompt: str, model: str | None = None) -> None:
    command = ["codex", "exec", "--full-auto", "-C", str(ROOT_DIR), "-"]
    if model:
        command[2:2] = ["--model", model]
    run_command(command, input_text=prompt)


def validate_and_regenerate() -> None:
    run_command(["uv", "run", "python", "scripts/validate.py", "--all"])
    run_command(["uv", "run", "python", "scripts/compile.py", "--progress-only"])
    run_command(["uv", "run", "python", "scripts/validate.py", "--all"])


def mark_compiled(*, compiler: str = "codex") -> None:
    state = load_state()
    ingested = state.setdefault("ingested", {})
    for session in list_sessions():
        ingested[rel(session)] = {
            "hash": file_hash(session),
            "compiled_at": now_iso(),
            "cost_usd": 0.0,
            "compiled_by": compiler,
        }
    save_state(state)


def ensure_no_unprocessed_inbox() -> None:
    remaining = inbox_files()
    if not remaining:
        return
    print("Codex compile left inbox files unprocessed:", file=sys.stderr)
    for path in remaining:
        print(f"  - {rel(path)}", file=sys.stderr)
    print("Move them to processed/failed or rerun before marking compiled.", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Codex study memory compiler fallback")
    parser.add_argument("--print-prompt", action="store_true", help="Print the Codex prompt only")
    parser.add_argument("--status", action="store_true", help="Show pending inbox/session work")
    parser.add_argument("--all", action="store_true", help="Ask Codex to recompile all sessions")
    parser.add_argument("--model", help="Optional model to pass to codex exec")
    parser.add_argument(
        "--skip-agent",
        action="store_true",
        help="Only run validation/progress/state marking after a manual Codex compile",
    )
    args = parser.parse_args()

    inbox = inbox_files()
    pending = list_sessions() if args.all else pending_session_files()

    if args.status:
        print("Inbox files:")
        print("\n".join(f"  - {rel(p)}" for p in inbox) or "  (none)")
        print("Session logs to compile:")
        print("\n".join(f"  - {rel(p)}" for p in pending) or "  (none)")
        return

    prompt = build_prompt(force_all=args.all)
    if args.print_prompt:
        print(prompt)
        return

    if not inbox and not pending and not args.skip_agent:
        print("Nothing to compile. Running validation only.", flush=True)
        run_command(["uv", "run", "python", "scripts/validate.py", "--all"])
        return

    if not args.skip_agent:
        run_codex(prompt, model=args.model)

    ensure_no_unprocessed_inbox()
    validate_and_regenerate()
    mark_compiled()
    print("Codex compile complete.")


if __name__ == "__main__":
    main()
