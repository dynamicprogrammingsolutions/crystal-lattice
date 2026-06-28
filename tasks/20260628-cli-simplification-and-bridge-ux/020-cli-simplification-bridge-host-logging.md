# CLI Simplification — Bridge, Host, Logging

Modify `__main__.py` so that `--console --server --enable-bonjour --enable-bridge`
is sufficient for a normal local development session. Integrate the project
profile system, add `--enable-bridge`, auto-bind to 0.0.0.0 for bonjour,
default to file logging, and make bridge-url an optional application config key.

Parent Task: tasks/20260628-cli-simplification-and-bridge-ux/000-main.md
Depends On: tasks/20260628-cli-simplification-and-bridge-ux/010-project-profile-persistence.md

---

## Requirements checklist

-- [x] Add `--enable-bridge` CLI flag: when set, resolve bridge URL and enable bridge registration
-- [x] Bridge URL resolution order: CLI `--bridge-url` > `.crystal/profile.json` > `~/.crystal/projects.json` > `application.bridge_url` in config.json > disabled
-- [x] Read `application.bridge_url` from the resolved config via `AgentApplication.get_application_config()`
-- [x] Auto-bind to `0.0.0.0` when `--enable-bonjour` is set and `--host` was not explicitly passed by the user
-- [x] `--host` always wins as the explicit override (even with `--enable-bonjour`)
-- [x] Use the project profile system (subtask 010) to resolve port, bridge-server-id, and project name
-- [x] Port: use persisted port from profile; if none, auto-select a free port and persist it
-- [x] Bridge-server-id: use persisted ID from profile; if none, generate a UUID and persist it
-- [x] Project name: use generated/persisted name from profile as the default `--bridge-display-name` and `--bonjour-service-name`
-- [x] Default log file: write to `.crystal/crystal.log` by default when no `--log-file` is given
-- [x] Add `--no-log-file` flag to disable default file logging
-- [x] When `--log-file` is used and `--fastapi-log-file` is not, route FastAPI/uvicorn logs to the same file
-- [x] Update `_build_server_integration_config()` to accept resolved profile values
- [ ] Update `_args()` test helper in `test_cli_environment_isolation.py` with new fields
-- [x] Update existing tests in `test_cli_environment_isolation.py` to pass with new arg structure
-- [x] Add tests for `--enable-bridge` resolving bridge URL from config/profile
-- [x] Add tests for auto-0.0.0.0 when bonjour is enabled without explicit `--host`
-- [x] Add tests for default log file path and `--no-log-file`
-- [x] Add tests for `--log-file` being used for fastapi when `--fastapi-log-file` is absent
-- [x] Update `application/python/README.md` CLI documentation

---

## Implementation notes

### Detecting whether `--host` was explicitly passed

`argparse` does not distinguish "user passed `--host 127.0.0.1`" from "default value" when using `default=`. Options:

1. Set `--host` default to `None` and resolve after parsing: if `None` and bonjour is enabled, use `0.0.0.0`; if `None` and bonjour is not enabled, use `127.0.0.1`.
2. Use a sentinel default.

Option 1 is cleanest. Change `--host` default from `"127.0.0.1"` to `None`, then resolve:

```python
effective_host = args.host
if effective_host is None:
    effective_host = "0.0.0.0" if args.enable_bonjour else "127.0.0.1"
```

### `--enable-bridge` flag

Add:
```python
parser.add_argument(
    "--enable-bridge",
    action="store_true",
    help="enable bridge registration (bridge URL resolved from CLI, profile, or config)",
)
```

When `--enable-bridge` is set:
1. If `args.bridge_url` is provided, use it.
2. Else if `.crystal/profile.json` has `bridge_url`, use it.
3. Else if `~/.crystal/projects.json` entry for this path has `bridge_url`, use it.
4. Else if `application.bridge_url` exists in the resolved config, use it.
5. Else: warn that bridge is enabled but no URL was found, and skip bridge registration.

Note: reading `application.bridge_url` from config requires the config to be loaded first. The config is loaded later in `main()` (after arg parsing). The bridge integration config is built via `_build_server_integration_config()` which currently runs *before* config loading. This may need reordering: load config first, then build integration config, or do a two-phase resolution (CLI/profile first, config-based fallback after config load).

### Bridge-server-id and port from profile

The profile manager (subtask 010) provides `port` and `bridge_server_id`. These should be resolved early in `main()`, before `_build_server_integration_config()` is called. CLI flags (`--port`, `--bridge-server-id`) override profile values.

### Project name as default display name

The profile's `name` field should be used as the default for:
- `--bridge-display-name` (when `--enable-bridge` and no explicit display name)
- `--bonjour-service-name` (when `--enable-bonjour` and no explicit service name)

### Default log file

Change `--log-file` default from `None` to `None` (keep), but add post-parse logic:

```python
log_file = args.log_file
if log_file is None and not args.no_log_file:
    log_file = str(Path(".crystal") / "crystal.log")
```

Add:
```python
parser.add_argument(
    "--no-log-file",
    action="store_true",
    help="disable default file logging (overrides the default .crystal/crystal.log)",
)
```

For fastapi log file fallback:
```python
fastapi_log_file = args.fastapi_log_file
if fastapi_log_file is None and log_file:
    fastapi_log_file = log_file
```

### Key files to modify

- `application/python/agent_terminal_app/__main__.py` — main changes
- `application/python/tests/test_cli_environment_isolation.py` — update `_args()` helper and existing tests
- `application/python/README.md` — update CLI docs

### Testing approach

- Test `--enable-bridge` with bridge URL from config (mock `AgentApplication.get_application_config()`).
- Test auto-`0.0.0.0` when bonjour enabled and `--host` not passed.
- Test that explicit `--host` wins over auto-0.0.0.0.
- Test default log file path resolution.
- Test `--no-log-file` disables default logging.
- Test `--log-file` used for fastapi when `--fastapi-log-file` absent.
- Mock the profile manager to avoid filesystem side effects in CLI tests.
---

## Completion Notes

Added during completion.

### What was done

1. **Extended `project_profile.py`** (subtask 010 module):
   - Added `bridge_url: str | None = None` to `ProjectProfile` dataclass.
   - Added `cli_bridge_url` parameter to `resolve()`.
   - Resolution: CLI > local override > user-level > None (never auto-generated, never persisted).
   - Added 6 bridge_url tests to `test_project_profile.py`.

2. **Modified `__main__.py`**:
   - Added `--enable-bridge` and `--no-log-file` CLI flags.
   - Changed `--host` default from `"127.0.0.1"` to `None` (auto-select).
   - Changed `--port` default from `8000` to `None` (profile-managed).
   - Added helper functions: `_resolve_effective_host()`, `_resolve_log_file()`,
     `_resolve_fastapi_log_file()`, `_read_bridge_url_from_config()`.
   - Modified `_build_server_integration_config()` to accept `profile`,
     `bridge_url_from_config`, `effective_host`, `effective_port`.
   - Bridge URL resolution: profile (includes CLI) > config `application.bridge_url` > skip with warning.
   - Profile name used as default for `--bonjour-service-name` and `--bridge-display-name`.
   - Default log file: `.crystal/crystal.log` (unless `--no-log-file`).
   - FastAPI log file defaults to main log file when `--fastapi-log-file` is absent.
   - Reordered `main()`: resolve profile → resolve host/log → configure logging →
     resolve config path → read bridge_url from config → build integration config → launch.
   - Replaced `args.host`/`args.port` with `effective_host`/`effective_port` in server launch.

3. **Updated `test_cli_environment_isolation.py`**:
   - Updated `_args()` helper with new fields (`enable_bridge`, `no_log_file`, `log_file`,
     `fastapi_log_file`, `host=None`, `port=None`).
   - Updated existing tests to pass `effective_host`/`effective_port`.
   - Added 21 new tests: host resolution (3), log file resolution (6), bridge URL from
     config (5), `--enable-bridge` behavior (7).

4. **Updated `application/python/README.md`**:
   - Added Quick Start section with simplified command.
   - Added Project Profiles section documenting `~/.crystal/projects.json` and `.crystal/profile.json`.
   - Updated Bonjour, Bridge, and Logging sections to show simplified usage.

### Design decisions

- **`_read_bridge_url_from_config`**: Reads the raw config JSON directly instead of creating
  a full `AgentApplication` instance (which would load plugins, discover models, etc.).
  `bridge_url` is a plain string that doesn't need placeholder resolution. If env-var
  expansion is needed, users can use `--bridge-url` or `.crystal/profile.json`.
- **Profile `bridge_url`**: Added to the profile manager as a non-auto-generated, non-persisted
  field. The profile manager resolves it (CLI > local > user-level > None), and `__main__.py`
  adds the config.json fallback.
- **`profile=None` handling**: `_build_server_integration_config()` falls back to
  `args.bridge_url` and `args.bridge_server_id` when `profile` is None (for tests and
  backward compatibility).

### Validation results

- `pytest test_project_profile.py` — 37 passed
- `pytest test_cli_environment_isolation.py` — 28 passed, 2 pre-existing failures
  (unrelated `UnboundLocalError` in `server.py:_on_shutdown`)
- `ruff check` — clean
- `black` — clean (1 file reformatted)
- `pyright` — 5 pre-existing errors in `_parse_contributed_command` (unchanged code, shifted line numbers)
