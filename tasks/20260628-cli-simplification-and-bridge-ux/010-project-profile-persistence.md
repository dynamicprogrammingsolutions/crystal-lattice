# Project Profile Persistence System

Create a profile manager that persists per-project settings (port,
bridge-server-id, project name) so the CLI can auto-configure without
requiring the user to repeat flags every run.

Parent Task: tasks/20260628-cli-simplification-and-bridge-ux/000-main.md

---

## Requirements checklist

- [ ] Create a `ProjectProfileManager` (or equivalent module) that reads and writes per-project settings
- [ ] Store settings in a single user-level file `~/.crystal/projects.json`, keyed by absolute project path
- [ ] Support a project-local override file `.crystal/profile.json` (same keys, higher priority)
- [ ] Auto-generate project name from the current directory basename
- [ ] Disambiguate duplicate project names by prepending parent directory names (e.g. `iocharts` → `frontend-iocharts` → `dev-frontend-iocharts`)
- [ ] Auto-select a free port (bind to port 0, read assigned port) and persist it for the same directory
- [ ] On subsequent runs, try the persisted port; if occupied, pick a new free port and update the file
- [ ] Auto-generate and persist a stable `bridge_server_id` (UUID) per directory
- [ ] Resolution order: CLI flag > `.crystal/profile.json` > `~/.crystal/projects.json` entry > built-in default
- [ ] The `~/.crystal/projects.json` file must be human-readable and user-editable (pretty-printed JSON)
- [ ] Unit tests for project name generation (including disambiguation)
- [ ] Unit tests for port selection and persistence (including occupied-port fallback)
- [ ] Unit tests for bridge-server-id persistence
- [ ] Unit tests for override resolution order (CLI > local > user-level)

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