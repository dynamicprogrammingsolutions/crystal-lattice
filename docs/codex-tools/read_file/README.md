# `read_file`

Reads a local file with line-number prefixes.

## Handler behavior (implementation notes)

- Requires `file_path` to be absolute; rejects relative paths.
- Line numbers are **1-indexed**.
- Returns each line as `L<line>: <content>`.
- Truncates overly long single lines (Codex uses a per-line cap of 500 bytes-at-char-boundary).
- Two modes:
  - `slice`: reads `[offset, offset+limit)`.
  - `indentation`: expands around an anchor line using indentation heuristics (best-effort for many languages).
