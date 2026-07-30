# Project Profile Persistence System

Create a profile manager that persists per-project settings (port,
bridge-server-id, project name) so the CLI can auto-configure without
requiring the user to repeat flags every run.

Parent Task: tasks/20260628-cli-simplification-and-bridge-ux/000-main.md

---

## Requirements checklist

- [x] Create a `ProjectProfileManager` (or equivalent module) that reads and writes per-project settings
- [x] Store settings in a single user-level file `~/.crystal/projects.json`, keyed by absolute project path
- [x] Support a project-local override file `.crystal/profile.json` (same keys, higher priority)
- [x] Auto-generate project name from the current directory basename
- [x] Disambiguate duplicate project names by prepending parent directory names (e.g. `iocharts` → `frontend-iocharts` → `dev-frontend-iocharts`)
- [x] Auto-select a free port (bind to port 0, read assigned port) and persist it for the same directory
- [x] On subsequent runs, try the persisted port; if occupied, pick a new free port and update the file
- [x] Auto-generate and persist a stable `bridge_server_id` (UUID) per directory
- [x] Resolution order: CLI flag > `.crystal/profile.json` > `~/.crystal/projects.json` entry > built-in default
- [x] The `~/.crystal/projects.json` file must be human-readable and user-editable (pretty-printed JSON)
- [x] Unit tests for project name generation (including disambiguation)
- [x] Unit tests for port selection and persistence (including occupied-port fallback)
- [x] Unit tests for bridge-server-id persistence
- [x] Unit tests for override resolution order (CLI > local > user-level)

---

## Implementation notes

### File format: `~/.crystal/projects.json`

```json
{
  "projects": {
    "/Users/ferenci84/Dev/Kuhar_Balint/iocharts": {
      "name": "iocharts",
      "port": 8090,
      "bridge_server_id": "b19cb3bf-eccb-42b8-879f-ead70eaf7db9"
    },
    "/Users/ferenci84/Dev/Kuhar_Balint/iocharts-frontend": {
      "name": "frontend-iocharts",
      "port": 8091,
      "bridge_server_id": "a1b2c3d4-..."
    }
  }
}
```

### File format: `.crystal/profile.json` (project-local override)

```json
{
  "name": "my-custom-name",
  "port": 9000,
  "bridge_server_id": "custom-id"
}
```

Any subset of keys may be present; only the keys that exist override the user-level entry.

### Project name disambiguation algorithm

1. Start with the current directory basename (e.g. `iocharts`).
2. Check all existing entries in `~/.crystal/projects.json` for a matching `name` with a *different* absolute path.
3. If a collision exists, prepend the parent directory basename: `frontend-iocharts`.
4. Keep prepending parent names until no collision: `dev-frontend-iocharts`, etc.
5. If the path is at the filesystem root and no parent remains, append a numeric suffix: `iocharts-2`.

### Port auto-selection

- Use `socket.socket` to bind to `0.0.0.0:0`, read `getsockname()[1]`, close the socket.
- This gives a port the OS considers free at that moment.
- Persist it immediately so a subsequent run can try it.
- On the next run, attempt to bind to the persisted port; if it fails (already in use), pick a new free port and update the file.
- There is a small TOCTOU window between the check and the actual uvicorn bind; this is acceptable for a dev CLI. If uvicorn fails to bind, the error will surface naturally.

### Where to put the code

- Create a new module: `application/python/agent_terminal_app/project_profile.py`.
- This keeps the profile logic separate from `__main__.py` and testable in isolation.
- `__main__.py` will import and use it in subtask 020.

### Testing

- Tests in `application/python/tests/test_project_profile.py`.
- Use `tmp_path` for the user-level file and `monkeypatch.chdir` for the project directory.
- Test name generation with no collisions, with collisions requiring one parent, and with collisions requiring multiple parents.
- Test port persistence: first call picks a port, second call returns the same port (mock the bind to succeed).
- Test occupied-port fallback: mock the bind to fail on the persisted port, verify a new port is chosen and the file updated.
- Test bridge-server-id generation and persistence.
- Test override resolution: CLI value > local `.crystal/profile.json` > user-level `~/.crystal/projects.json`.
- Test that the user-level file is pretty-printed JSON (readable, sorted keys).

---

## Execution plan

Added during completion.

### Approach

Single-pass implementation of the `project_profile.py` module with
comprehensive unit tests, followed by lint/format/typecheck validation.

1. Create `application/python/agent_terminal_app/project_profile.py` with:
   - `ProjectProfile` frozen dataclass (`name`, `port`, `bridge_server_id`)
   - `ProjectProfileManager` class with `resolve()` entry point
   - Module-level helpers: `_find_free_port`, `_try_bind`,
     `_generate_unique_name`, `_load_user_file`, `_save_user_file`,
     `_load_local_override`, `_is_valid_port`, `_is_valid_str`
2. Create `application/python/tests/test_project_profile.py` with 31 tests
   covering name generation, port selection/persistence, bridge-server-id,
   resolution order, file format, and error handling.
3. Validate: `pytest`, `ruff check`, `black`, `pyright`.

### Design decisions

- **Error handling**: If a profile file exists but contains invalid JSON
  or a non-object top-level value, a clear `RuntimeError` is raised (per
  user request). Missing files are treated as empty (no error).
- **Persistence rule**: Only values not provided by CLI or local override
  are persisted to the user-level file. CLI/local override values are
  per-run explicit choices and are never written.
- **Port fallback for local override**: If a local-override port is
  occupied, a free port is used for the current run but is NOT persisted
  (the user explicitly chose that port; silently changing their file
  would be confusing).
- **Port fallback for user-level**: If a user-level port is occupied, a
  new free port is picked and the user-level file is updated.
- **Type validation**: `_is_valid_port` rejects bool/zero/negative;
  `_is_valid_str` rejects non-string/empty. Invalid types in either file
  cause the setting to fall through to the next priority level.

---

## Completion Notes

Added during completion.

### What was done

- Created `application/python/agent_terminal_app/project_profile.py` — a
  self-contained module with `ProjectProfile` dataclass and
  `ProjectProfileManager` class.
- Created `application/python/tests/test_project_profile.py` — 31 unit tests,
  all passing.

### Key implementation details

- `ProjectProfileManager.resolve()` is the single entry point. It accepts
  optional `cli_name`, `cli_port`, `cli_bridge_server_id` keyword args and
  returns a `ProjectProfile`.
- Resolution priority per setting: CLI > local override (`.crystal/profile.json`)
  > user-level (`~/.crystal/projects.json`) > built-in default.
- Name disambiguation: basename → prepend parent names → numeric suffix at
  filesystem root or when all parents exhausted.
- Port selection: bind to `0.0.0.0:0` for free port; `_try_bind()` checks
  if a persisted port is still available.
- User-level file written as `json.dumps(data, indent=2, sort_keys=True)`
  with trailing newline.
- Corrupt JSON (parse error or non-object top-level) raises `RuntimeError`
  with file path, line/column, and error message.
- No changes to `__main__.py`, `server.py`, or any existing files — purely
  additive (confirmed via `git status`).

### Validation results

- `pytest application/python/tests/test_project_profile.py` — 31 passed
- `ruff check` — clean
- `black --check` — clean
- `pyright` — 0 errors, 0 warnings
- Existing tests: 2 pre-existing failures in
  `test_cli_environment_isolation.py` (unrelated `UnboundLocalError` in
  `server.py:_on_shutdown` line 513, `_agent_app` not defined) — not caused
  by this change.

### What remains for subtask 020

- Import `ProjectProfileManager` in `__main__.py`.
- Wire `resolve()` output into `_build_server_integration_config()` and
  the uvicorn/server launch path.
- Add `--enable-bridge` flag and auto-bridge-url resolution.
- Auto-select host (`0.0.0.0` when bonjour enabled, no explicit `--host`).
- Default log file to `.crystal/crystal.log`.