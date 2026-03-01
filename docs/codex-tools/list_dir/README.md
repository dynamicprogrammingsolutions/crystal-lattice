# `list_dir`

Lists entries under an absolute directory path.

## Handler behavior (implementation notes)

- Requires `dir_path` to be absolute.
- Traverses breadth-first up to `depth` levels (default depth is 2 in the handler).
- Sorts entries by a normalized name key and returns a slice by 1-indexed `offset` and `limit`.
- Includes a header line: `Absolute path: <path>`.
- If there are more results beyond the selected slice, appends a `More than <N> entries found` line.
