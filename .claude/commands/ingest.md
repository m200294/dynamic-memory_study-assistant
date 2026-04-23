---
description: Ingest external Codex/ChatGPT/voice-note sessions from inbox/.
---

Process external sessions waiting in `inbox/`.

This command may make LLM calls: `scripts/ingest.py` normalizes inbox files into
canonical session logs, and `compile.py` may update concept files afterward.

Do the following:

1. Run `uv run python scripts/ingest.py --compile`.
2. Show the command output to the user.
3. If any file failed, read the corresponding `inbox/failed/*.error.txt` file and
   explain the concrete fix needed in the inbox source.
4. Do not manually edit `sessions/` or `knowledge/` unless the user explicitly
   asks for a repair after seeing the failure.
