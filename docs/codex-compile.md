# Codex Compile Fallback

`./codex_compile` is the fallback path for when Claude-powered semantic scripts
are unavailable.

It asks Codex to:

1. Convert direct `inbox/*.md` files into canonical `sessions/week-NN/*.md`
   files.
2. Apply the evidence rule to update `knowledge/concepts/*.md`.
3. Update week summaries, index, and log files.
4. Run local validation.
5. Regenerate deterministic `probe_history` and `knowledge/progress.md`.

Do not use this command if you only want the deterministic progress rebuild.
For that, run:

```bash
uv run python scripts/compile.py --progress-only
```
