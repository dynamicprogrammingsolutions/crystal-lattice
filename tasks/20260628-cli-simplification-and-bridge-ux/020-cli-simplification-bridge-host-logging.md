# CLI Simplification — Bridge, Host, Logging

Modify `__main__.py` so that `--console --server --enable-bonjour --enable-bridge`
is sufficient for a normal local development session. Integrate the project
profile system, add `--enable-bridge`, auto-bind to 0.0.0.0 for bonjour,
default to file logging, and make bridge-url an optional application config key.

Parent Task: tasks/20260628-cli-simplification-and-bridge-ux/000-main.md
Depends On: tasks/20260628-cli-simplification-and-bridge-ux/010-project-profile-persistence.md

---

## Requirements checklist

- [ ] Add `--enable-bridge` CLI flag: when set, resolve bridge URL and enable bridge registration
- [ ] Bridge URL resolution order: CLI `--bridge-url` > `.crystal/profile.json` > `~/.crystal/projects.json` > `application.bridge_url` in config.json > disabled
- [ ] Read `application.bridge_url` from the resolved config via `AgentApplication.get_application_config()`
- [ ] Auto-bind to `0.0.0.0` when `--enable-bonjour` is set and `--host` was not explicitly passed by the user
- [ ] `--host` always wins as the explicit override (even with `--enable-bonjour`)
- [ ] Use the project profile system (subtask 010) to resolve port, bridge-server-id, and project name
- [ ] Port: use persisted port from profile; if none, auto-select a free port and persist it
- [ ] Bridge-server-id: use persisted ID from profile; if none, generate a UUID and persist it
- [ ] Project name: use generated/persisted name from profile as the default `--bridge-display-name` and `--bonjour-service-name`
- [ ] Default log file: write to `.crystal/crystal.log` by default when no `--log-file` is given
- [ ] Add `--no-log-file` flag to disable default file logging
- [ ] When `--log-file` is used and `--fastapi-log-file` is not, route FastAPI/uvicorn logs to the same file
- [ ] Update `_build_server_integration_config()` to accept resolved profile values
- [ ] Update `_args()` test helper in `test_cli_environment_isolation.py` with new fields
- [ ] Update existing tests in `test_cli_environment_isolation.py` to pass with new arg structure
- [ ] Add tests for `--enable-bridge` resolving bridge URL from config/profile
- [ ] Add tests for auto-0.0.0.0 when bonjour is enabled without explicit `--host`
- [ ] Add tests for default log file path and `--no-log-file`
- [ ] Add tests for `--log-file` being used for fastapi when `--fastapi-log-file` is absent
- [ ] Update `application/python/README.md` CLI documentation

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