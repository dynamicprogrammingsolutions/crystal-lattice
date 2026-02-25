# `grep_files`

Searches files using `rg` (ripgrep) and returns matching file paths.

## Handler behavior (implementation notes)

- Uses `rg --files-with-matches --sortr=modified --regexp <pattern>`.
- Enforces limits: default 100, max 2000; rejects `pattern==""` and `limit==0`.
- If `rg` returns exit code 1 (no matches), returns success=false with `No matches found.`
- Wraps operational failures as tool errors (e.g. `rg timed out after 30 seconds`, `failed to launch rg: ...`).
