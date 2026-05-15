# Isolate Bridge CLI Config And Dotenv Environment

Prevent app-private bridge settings and dotenv-loaded configuration values from leaking into `AgentApplication` and child subprocess environments. This task covers two related fixes: pass bridge/Bonjour CLI configuration explicitly instead of mutating `os.environ`, and parse dotenv files into an isolated config environment instead of loading them globally.

## Requirements checklist

- [x] Replace CLI-to-server bridge/Bonjour parametrization via `os.environ` with explicit process-local configuration for the normal `python -m agent_terminal_app ...` path.
- [x] Preserve direct `uvicorn agent_terminal_app.server:app` support via external environment variables, but avoid treating CLI-provided bridge values as ambient process env.
- [x] Change dotenv loading used by the CLI/config path from global `load_dotenv()` mutation to non-mutating `dotenv_values()`-style collection.
- [x] Ensure dotenv-derived values are available for config placeholder resolution where currently expected.
- [x] Ensure CLI-provided bridge identity/control variables such as `BRIDGE_URL` and `BRIDGE_SERVER_ID` are not added to `AgentApplication` env maps or subprocess environments in the normal CLI path; externally supplied process env remains unchanged.
- [x] Add focused regression tests for both bridge CLI config isolation and non-mutating dotenv behavior.

## Background

An investigation of a production bridge takeover found that `crystal-bridge.dynamicprogrammingsolutions.com` received duplicate `type=server` websocket connections for the same server id:

```text
d875e503-7569-4e19-94f1-654c841d3d9c
```

Nginx access logs on `irelandsrv` showed the takeover connection came from the user's current public IP, not an outside host:

```text
84.225.123.97 - - [30/Apr/2026:14:06:43 +0000] "GET /ws/websocket?type=server HTTP/1.1" 101 ... "Python/3.11 websockets/15.0.1"
84.225.123.97 - - [30/Apr/2026:14:06:45 +0000] "GET /ws/websocket?type=server HTTP/1.1" 101 ... "Python/3.11 websockets/15.0.1"
```

The running application command included:

```bash
LOG_LEVEL=info python -m agent_terminal_app \
  --host 0.0.0.0 \
  --port 8085 \
  --bridge-url wss://crystal-bridge.dynamicprogrammingsolutions.com/ws/websocket \
  --enable-bonjour \
  --bonjour-service-name "Crystal" \
  --server \
  --console \
  --bridge-display-name "crystal" \
  --log-file ./console.log \
  --bridge-server-id="d875e503-7569-4e19-94f1-654c841d3d9c"
```

Local logs showed the active bridge client was superseded:

```text
2026-04-30 16:06:43,534 WARNING agent_terminal_app.bridge_client - Bridge client superseded: server_id=d875e503-7569-4e19-94f1-654c841d3d9c display_name=crystal instance_id=fb3cd78d-90b6-4ee8-9684-3c6b1431d469 reason=new_connection
```

The likely root cause is environment propagation. The CLI currently converts bridge/Bonjour arguments into global process environment variables. A shell tool or test process launched from an ongoing request can inherit those values and accidentally run another `agent_terminal_app.server` instance with the same bridge identity.

## Current Code References

CLI bridge/Bonjour flags currently mutate `os.environ` in `application/python/agent_terminal_app/__main__.py`:

```text
application/python/agent_terminal_app/__main__.py:470-498
```

Relevant behavior:

```python
os.environ["ENABLE_BONJOUR"] = "1"
os.environ["BRIDGE_URL"] = args.bridge_url
os.environ["BRIDGE_SERVER_ID"] = args.bridge_server_id
```

The FastAPI startup hook creates the bridge client from environment variables:

```text
application/python/agent_terminal_app/server.py:434-488
```

Relevant behavior:

```python
client = bridge_mod.create_bridge_client_from_env()
if client is not None:
    _bridge_client = client
    _bridge_task = asyncio.create_task(client.run())
```

`BridgeClient` registers a server websocket using the configured `server_id`, `display_name`, and generated `instance_id`:

```text
application/python/agent_terminal_app/bridge_client.py:253-279
```

`BridgeClient` stops when the bridge sends `superseded`:

```text
application/python/agent_terminal_app/bridge_client.py:318-320
application/python/agent_terminal_app/bridge_client.py:374-394
```

The Elixir bridge intentionally defaults duplicate server ids to takeover:

```text
bridge-elixir/lib/bridge/server_registry.ex:57-108
bridge-elixir/lib/bridge/server_registry.ex:251-266
bridge-elixir/lib/bridge/server_channel.ex:117-119
```

`scripts/run_backend_server_for_ts_integration_tests.py` is a plausible accidental trigger because it imports `agent_terminal_app.server` and runs `uvicorn.run(server_mod.app, ...)` without clearing inherited bridge env vars:

```text
scripts/run_backend_server_for_ts_integration_tests.py:66
scripts/run_backend_server_for_ts_integration_tests.py:121-127
```

Dotenv loading currently mutates global process environment in `application/python/agent_terminal_app/__main__.py`:

```text
application/python/agent_terminal_app/__main__.py:171-216
application/python/agent_terminal_app/__main__.py:596
```

The helper uses `load_dotenv(..., override=False)`, which writes values into `os.environ`. That makes dotenv secrets visible to `AgentApplication`, tools, tests, and child subprocesses unless separately sanitized.

`AgentApplication` accepts `env_overrides` and already uses explicit env maps for placeholder resolution:

```text
core/python/agent_app/application_future.py:177-213
core/python/agent_app/config.py:23-77
```

However, `AgentApplication` also installs runtime env values into `os.environ` through `RuntimeEnvOverlay`:

```text
core/python/agent_app/runtime_env.py:13-98
```

This task should avoid broad plugin/tool changes. Keep the first fix in bridge/app wiring, and use isolated dotenv parsing for config inputs.

## Fix Direction 1: Explicit Bridge/Bonjour Runtime Config

Implement the normal CLI path without mutating `os.environ` for bridge/Bonjour CLI args.

Suggested shape:

1. Add small app-level config dataclasses or equivalent plain data structures in `application/python/agent_terminal_app/server.py` or a nearby app-owned module:

```python
@dataclass
class BonjourRuntimeConfig:
    enabled: bool
    service_name: str
    port: int

@dataclass
class ServerIntegrationRuntimeConfig:
    bonjour: BonjourRuntimeConfig | None = None
    bridge: bridge_mod.BridgeConfig | None = None
```

2. Add a process-local setter in `server.py`, for example:

```python
def configure_integrations(config: ServerIntegrationRuntimeConfig | None) -> None:
    ...
```

3. In `__main__.py`, parse CLI args into this explicit config and call the setter after importing `server_mod`, before starting uvicorn.

4. In `server.py` startup, prefer the explicit process-local config. Fall back to `os.environ` only for direct `uvicorn agent_terminal_app.server:app` usage.

5. Do not write these CLI-derived variables to `os.environ`:

```text
ENABLE_BONJOUR
BONJOUR_PORT
BONJOUR_SERVICE_NAME
BRIDGE_URL
BRIDGE_DISPLAY_NAME
BRIDGE_LOCATION
BRIDGE_LOCAL_HTTP_BASE
BRIDGE_SERVER_ID
BRIDGE_EXIT_ON_SUPERSEDED
BRIDGE_LOCAL_GUARD
BRIDGE_TAKEOVER_LOCAL
```

6. Consider clearing app-private bridge/Bonjour env vars immediately after reading them in the direct-env startup path as defense-in-depth. Do this only after considering compatibility for direct uvicorn users.

Important: preserve `SERVER_HOST` / `SERVER_PORT` behavior only as needed for current integration defaults. Prefer explicit local HTTP base/port in the explicit config path.

## Fix Direction 2: Non-Mutating Dotenv Loading For Config

Replace CLI/config dotenv loading that mutates `os.environ` with non-mutating parsing.

Suggested shape:

1. Replace or complement `_load_additional_dotenvs(config_path)` with a helper that returns a dict:

```python
def _collect_additional_dotenv_values(config_path: Path) -> dict[str, str]:
    ...
```

2. Use `dotenv_values()` from `python-dotenv` rather than `load_dotenv()`:

```python
from dotenv import dotenv_values
values = dotenv_values(path)
```

3. Preserve the current precedence semantics as closely as possible. Current search order is:

```text
1. <config_dir>/.env
2. ./.crystal/.env
3. ~/.crystal/.env
4. standard .env discovered from current directory/parents
```

Current `load_dotenv(..., override=False)` means earlier values win over later files and existing process env wins over all dotenv values. The new dict construction should respect that:

```python
base = dict(os.environ)
dotenv_values_collected = {}
# add each file only if key not already in base or collected
config_env_overrides = dotenv_values_collected
```

4. Pass collected dotenv values through `env_overrides` or an explicit config-env mechanism so config placeholder resolution still works.

5. Do not blindly include app-private bridge/Bonjour variables in `AgentApplication` `env_overrides`.

6. Keep provider/config secrets available for config resolution. Be cautious about whether they should be installed into `RuntimeEnvOverlay`; if avoiding that requires a larger design change, document the remaining risk and keep this task focused on removing global dotenv mutation.

## Tests To Add

Add focused tests in `application/python/tests` where practical.

Suggested cases:

1. CLI bridge config isolation:
   - Exercise the parsing/configure path or a helper extracted from `__main__.py`.
   - Assert CLI bridge args produce a `BridgeConfig` / explicit integration config.
   - Assert `os.environ` is not populated with `BRIDGE_URL` or `BRIDGE_SERVER_ID` by the CLI helper.

2. Server startup explicit config:
   - Configure `server.py` with explicit bridge config.
   - Patch `BridgeClient.run` or `bridge_mod.BridgeClient` to avoid network.
   - Call startup and assert the bridge client uses the explicit config.
   - Assert no `BRIDGE_*` env is required.

3. Direct env fallback still works:
   - Set `BRIDGE_URL` and related vars via monkeypatch.
   - Call startup or `create_bridge_client_from_env()`.
   - Assert a client is created for direct uvicorn compatibility.

4. Non-mutating dotenv:
   - Create temp config dir and `.env` files.
   - Call the new dotenv collection helper.
   - Assert returned values include expected keys.
   - Assert `os.environ` was not modified.
   - Assert existing `os.environ` values take precedence over dotenv file values.

5. Regression for `AgentApplication` bridge isolation:
   - Construct the relevant app path with bridge CLI config.
   - Assert `BRIDGE_URL` / `BRIDGE_SERVER_ID` are not present in the env map handed to `AgentApplication` or in process env after initialization.

## Non-Goals

- Do not modify plugin/tool-host subprocess environment behavior as the primary fix.
- Do not change bridge takeover policy in Elixir for this task.
- Do not remove direct env-based bridge configuration for direct uvicorn launches.
- Do not redesign all secret propagation or runtime env overlay behavior unless it is strictly required for the two fixes above.

## Execution plan

Added during completion after user approval.

1. Split application config placeholder environment from runtime process overlay:
   - Add an `AgentApplication` parameter for config-resolution-only environment values.
   - Use it for placeholder resolution only, leaving `env_overrides` as the values intentionally installed into `os.environ` by `RuntimeEnvOverlay`.
2. Replace CLI dotenv mutation with non-mutating collection:
   - Parse dotenv files with `dotenv_values()`.
   - Preserve current precedence: process env wins, earlier dotenv files win over later dotenv files.
   - Do not filter keys and do not remove or change existing process environment values.
3. Replace CLI bridge/Bonjour env mutation with explicit process-local server integration config:
   - Add server-owned runtime config objects and a `configure_integrations(...)` setter.
   - Have startup prefer explicit CLI config when set, while retaining env fallback for direct `uvicorn agent_terminal_app.server:app`.
   - Preserve the user's starting environment unchanged; if they explicitly set `BRIDGE_*`, subprocesses continue to inherit it.
4. Add focused regression tests:
   - Config-resolution-only env resolves placeholders without mutating `os.environ`.
   - Dotenv collection is non-mutating and respects precedence.
   - CLI integration config helpers do not populate `BRIDGE_*` env values.
   - Server startup uses explicit integration config and still supports direct env fallback.

## Notes

The built-in bash tool currently copies `os.environ` into subprocesses in non-streaming mode:

```text
core/python/agent_core/tool_hosts/bash_tool_plugin.py:144-153
```

Streaming mode uses `subprocess.Popen(...)` without an explicit env, so it also inherits process env:

```text
core/python/agent_core/tool_hosts/bash_tool_plugin.py:397-406
```

This reinforces why the bridge fix should prevent app-private values from entering process env in the first place.

## Completion Notes

Added during completion.

- Added `config_env` support to `AgentApplication` and config resolution so dotenv-parsed values can resolve `${env:...}` placeholders without being installed into process-global `os.environ`.
- Replaced CLI dotenv mutation with `_collect_additional_dotenv_values(...)`, using `dotenv_values()` / `find_dotenv(usecwd=True)` and preserving the previous precedence rules: starting process env wins, earlier dotenv files win over later dotenv files.
- Added explicit server integration runtime config in `agent_terminal_app.server` and wired the CLI to pass bridge/Bonjour settings through `configure_integrations(...)` instead of writing `BRIDGE_*`, `ENABLE_BONJOUR`, or `BONJOUR_*` values into `os.environ`.
- Preserved external environment behavior: values present when the process starts are neither removed nor sanitized, and direct env fallback for `uvicorn agent_terminal_app.server:app` still works.
- Added focused tests in `core/python/tests/test_application_layer_config.py`, `core/python/tests/test_application_runtime_env.py`, and `application/python/tests/test_cli_environment_isolation.py`.
- Verification run during completion:
  - `pytest core/python/tests/test_application_layer_config.py core/python/tests/test_application_runtime_env.py application/python/tests/test_cli_environment_isolation.py -q`
  - `ruff check core/python/agent_app/config.py core/python/agent_app/application_future.py core/python/tests/test_application_layer_config.py core/python/tests/test_application_runtime_env.py application/python/agent_terminal_app/__main__.py application/python/tests/test_cli_environment_isolation.py`
- Note: a broader `ruff check` including `application/python/agent_terminal_app/server.py` still reports pre-existing unused/redefined symbols unrelated to this task.