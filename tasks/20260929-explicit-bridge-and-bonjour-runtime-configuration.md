# Explicit Bridge and Bonjour Runtime Configuration

Remove implicit bridge and Bonjour configuration through inherited process
environment variables. The terminal application and its internally hosted
FastAPI service will start these integrations only from explicit process-local
runtime configuration assembled from CLI arguments, project/profile data,
application configuration, and documented defaults.

This task also gives every bridge transport control that was previously
environment-only an explicit, documented application-configuration
equivalent.

## Requirements checklist

- [x] **EBC-001:** An internally hosted FastAPI service starts a bridge client
  only when an explicit `BridgeConfig` is present in
  `ServerIntegrationRuntimeConfig`; ambient `BRIDGE_*`, `SERVER_HOST`,
  `SERVER_PORT`, and `PORT` values cannot activate or configure that client.
- [x] **EBC-002:** An internally hosted FastAPI service starts Bonjour
  advertising only when an explicit `BonjourRuntimeConfig` is present;
  ambient `ENABLE_BONJOUR`, `BONJOUR_*`, and `SERVER_PORT` values cannot
  activate or configure it.
- [x] **EBC-003:** Normal CLI bridge and Bonjour behavior remains available
  through the existing flags, project/profile fields, `application.bridge_url`,
  effective server host/port, and built-in defaults. Existing URL and identity
  precedence remains compatible except that implicit environment fallbacks are
  removed.
- [x] **EBC-004:** The application configuration exposes typed settings and
  defaults for all bridge client controls that currently have no non-environment
  configuration equivalent: WebSocket maximum message size, HTTP timeout,
  legacy HTTP chunk size, legacy HTTP chunking threshold, maximum adapter body
  size, and bridge debug logging.
- [x] **EBC-005:** Invalid explicit bridge application settings produce a
  field-specific configuration/startup error instead of silently using an
  environment value or an unrelated fallback.
- [x] **EBC-006:** Direct `uvicorn agent_terminal_app.server:app` startup no
  longer activates bridge or Bonjour integrations from environment variables.
  Embedders and test runners that need either integration use the explicit
  server integration configuration API.
- [x] **EBC-007:** Shell tools may continue inheriting the caller's ordinary
  environment, but inherited bridge and Bonjour variable names have no implicit
  effect on Crystal Lattice child CLI/server processes.
- [x] **EBC-008:** Current bridge and Bonjour usage, the complete application
  configuration schema and defaults, precedence, validation, restart
  requirements, embedding contract, and removal of environment-based startup
  are documented for users and maintainers.

## Scope

In scope:

- the Python terminal application's CLI-to-server integration configuration;
- FastAPI startup and `run_api()` integration wiring;
- Python bridge-client configuration construction;
- the maintained default application configuration;
- Python tests and the frontend SDK's Python backend/bridge integration
  harness where it currently relies on inherited environment variables;
- current user, developer, generated-reference, and bridge-connectivity
  specification documentation.

Out of scope:

- Elixir bridge-service deployment environment variables such as
  `BRIDGE_HTTP_MAX_BODY_BYTES`;
- frontend integration-runner controls such as `BRIDGE_E2E_MODE`,
  `BRIDGE_E2E_URL`, and `RUN_AWS_BRIDGE_TESTS`;
- changing the bridge server-ID conflict policy;
- changing the frontend bridge transport modes or TypeScript SDK public API;
- making bridge or Bonjour configuration hot-reload while their network
  lifecycles remain process-owned.

## Proposed decisions for approval

Approval of this task's execution plan approves the following public
configuration decisions:

1. Preserve the existing `application.bridge_url` key and its current
   activation rule: a configured URL does not itself enable registration;
   `--enable-bridge` or `--bridge-url` is still required.
2. Add a nested `application.bridge` object for the six settings that currently
   have only environment controls:

   ```json
   {
     "application": {
       "bridge_url": "wss://bridge.example/ws/websocket",
       "bridge": {
         "ws_max_size_bytes": 16777216,
         "http_timeout_seconds": 120.0,
         "http_chunk_size_bytes": 921600,
         "http_chunk_threshold_bytes": 262144,
         "http_max_body_bytes": 10485760,
         "debug": false
       }
     }
   }
   ```

3. `ws_max_size_bytes` accepts a positive integer or `null`; `null` means no
   WebSocket library message-size limit. Byte-size and timeout values otherwise
   must be positive finite numbers of their documented integer/number types,
   and `debug` must be a JSON boolean.
4. `http_chunk_threshold_bytes` preserves the existing single-threshold
   contract and supplies both legacy request/response threshold fields in
   `BridgeConfig`. Documentation will describe the behavior actually exercised
   by the adapter and will not claim an ineffective request-side operation.
5. Bridge application settings are process-start settings. Changing the config
   through application reload does not reconnect the bridge or restart
   Bonjour; a process restart is required.
6. The ordinary placeholder system remains available when a user deliberately
   writes a placeholder in configuration. There is no longer any implicit,
   specially named `BRIDGE_*` or `BONJOUR_*` environment contract in the Python
   terminal application.

There are no unresolved requirement questions. Implementation may resolve
local naming and factoring details as long as the documented JSON contract and
precedence above remain unchanged.

## Current findings

- The CLI already builds `ServerIntegrationRuntimeConfig`, but its builder
  still reads Bonjour metadata, bridge metadata/control values, transport
  limits, and host/port fallbacks from `os.getenv()`.
- FastAPI startup independently falls back to `ENABLE_BONJOUR` and
  `create_bridge_client_from_env()` when explicit integration configuration is
  absent.
- `create_bridge_client_from_env()` is the remaining production owner of the
  complete Python `BRIDGE_*` environment contract.
- `run_api()` and combined server/console startup write `SERVER_HOST` and
  `SERVER_PORT` so the environment fallbacks can infer local integration
  addresses. No other maintained Python application consumer requires those
  writes.
- `BridgeConfig` already owns the intended defaults:
  16 MiB WebSocket maximum, 120-second HTTP timeout, 900 KiB chunk size,
  256 KiB chunk threshold, 10 MiB adapter body maximum, and debug disabled.
- The legacy `request_chunking_threshold_bytes` field is assigned but is not
  currently read by `BridgeClient`; implementation must avoid documenting an
  effect that does not exist.
- The frontend SDK bridge E2E currently passes Python server bridge settings
  through environment variables to a custom direct FastAPI runner. A separate
  real-CLI bridge harness already exists and passes explicit bridge flags.
- The completed
  `tasks/20260430-isolate-bridge-cli-config-and-dotenv-env.md` intentionally
  preserved externally supplied process environment and direct-uvicorn
  fallback. This task supersedes that compatibility choice without rewriting
  its historical completion record.

## Execution plan
Status: Approved

Implement one explicit configuration path from the CLI or embedding caller to
the server-owned integration lifecycle. Configuration files and profiles may
help the CLI construct that object, but FastAPI startup and `BridgeClient`
will not inspect ambient environment variables.

First, introduce a focused parser for the new `application.bridge` settings.
It will read the already resolved application configuration, apply the
documented defaults, validate types and ranges, and return an immutable
settings value suitable for constructing `BridgeConfig`. Reuse the
`BridgeConfig` defaults as the canonical constants, or centralize shared
constants so the default config, parser, and runtime cannot drift.

Keep `application.bridge_url` compatible. Replace the raw bridge-URL-only
config read with extraction from the already resolved runtime configuration so
the URL and transport settings are interpreted from one explicit source.
Preserve URL precedence (CLI/project profile before application config) and
the existing requirement to explicitly enable bridge registration.

Next, remove environment reads from the CLI integration builder. Bonjour port
and name will come from CLI/profile/effective server values. Bridge display
metadata, local/public HTTP bases, stable ID, lifecycle flags, and transport
settings will come from their existing explicit sources, the new application
settings, or documented defaults. Remove environment parser helpers that
become unused.

Make FastAPI startup consume only `ServerIntegrationRuntimeConfig`. Absence of
an explicit bridge or Bonjour member means that integration is disabled.
Delete `create_bridge_client_from_env()` and the direct environment fallback.
Remove `SERVER_HOST`/`SERVER_PORT` writes whose sole purpose was supporting
that fallback. Retain the explicit integration setter for embedded runtimes.

Migrate test infrastructure rather than preserving a test-only environment
path. The custom frontend SDK Python runner will accept explicit bridge
arguments/options and call `configure_integrations(...)`, or bridge scenarios
will use the existing real-CLI launcher where that gives the correct boundary.
Generic backend scenarios will stop injecting integration-only host, port, and
bridge environment variables.

Add focused unit, CLI, server-lifecycle, and assembled bridge tests. The key
regression will populate every former Python bridge/Bonjour environment
variable, start a child-style server without explicit integrations, and prove
that no bridge client or Bonjour registration is created. Explicit bridge and
Bonjour paths must still work and carry custom application transport settings
into the actual `BridgeConfig`.

Update current user/developer documentation and the portable bridge
specification in the same change. Generated default-config documentation will
be refreshed through its maintained preparation/build source, not edited
directly.

### Implementation decisions and open questions

- Approved plan decision: use `application.bridge` with the six keys and
  defaults shown above; retain `application.bridge_url`.
- Approved plan decision: do not add six new CLI flags. These advanced
  transport controls are application configuration, while existing
  user-facing identity, location, URL, and lifecycle controls retain their
  current CLI flags.
- Approved plan decision: direct uvicorn environment activation is removed,
  not deprecated. Explicit embedding configuration is the replacement.
- Approved plan decision: do not sanitize shell subprocess environments.
  Safety comes from making internal service activation/configuration explicit.
- Implementation check: confirm whether the unused
  `request_chunking_threshold_bytes` member should remain as an internal
  compatibility field or be removed. This may not alter the approved
  application key or documented effective behavior.
- No requirement questions remain open.

### Documentation

- Update `application/python/README.md` with:
  - explicit bridge and Bonjour activation sources;
  - a complete `application.bridge` JSON example;
  - field types, units, defaults, and validation;
  - precedence and process-restart behavior;
  - removal of Python `BRIDGE_*`/`BONJOUR_*` runtime configuration.
- Update `application/python/docs/configuration.md` with the maintained
  application schema and a link to bridge operation guidance.
- Update
  `application/python/docs/development/bridge-server-adapter.md` with the
  explicit lifecycle/embedding contract and verification boundaries.
- Correct the environment-based example in
  `application/python/agent_terminal_app/bonjour.py` and the package-local
  `AGENTS.md` statement that bridge/Bonjour flags map through environment
  variables.
- Extend
  `docs/development/specifications/bridge-connectivity/technical-spec.md` and
  `requirements.md` with explicit Python server integration configuration,
  defaults, and inherited-environment isolation.
- Add the defaults to
  `application/python/agent_terminal_app/default_config/config.json` and
  regenerate/validate the prepared default-config reference through
  `docs_site/scripts/prepare_mkdocs_site.py`.
- Leave historical task completion records and archived integration plans
  unchanged.

### Task checklist

- [x] Add and validate the `application.bridge` settings model/parser.
- [x] Add the six documented settings and defaults to the maintained default
  configuration.
- [x] Build bridge and Bonjour runtime configuration without implicit
  environment reads.
- [x] Remove FastAPI bridge and Bonjour environment fallback startup.
- [x] Remove the obsolete bridge environment factory and parsing helpers.
- [x] Remove integration-only `SERVER_HOST`/`SERVER_PORT` process writes.
- [x] Migrate Python and frontend SDK integration harnesses to explicit
  integration configuration.
- [x] Add focused inherited-environment isolation and explicit-config tests.
- [x] Run relevant Python and frontend SDK unit/integration verification.
- [x] Update user, developer, specification, package-guidance, and generated
  default-config documentation.
- [x] Record implementation evidence and any approved deviations in this task.

### Requirement verification

- **EBC-001, EBC-002, EBC-007:** A focused server-lifecycle regression sets
  every former Python bridge/Bonjour activation, identity, metadata, transport,
  and host/port environment variable, supplies no explicit integration config,
  runs startup, and asserts that neither `BridgeClient` nor Bonjour
  registration is invoked. A CLI subprocess case exercises the same condition
  through the normal server entrypoint.
- **EBC-003:** Existing and updated CLI/profile/config tests prove explicit
  bridge URL/identity precedence, effective host/port derivation, explicit
  Bonjour values, disabled-by-default behavior, and successful explicit
  integration construction.
- **EBC-004, EBC-005:** Parameterized configuration tests cover every field's
  default, custom value, accepted nullable WebSocket limit, wrong JSON type,
  non-finite/zero/negative bounds, and propagation into `BridgeConfig`.
- **EBC-006:** A direct FastAPI/uvicorn-style startup test with populated
  former environment variables proves no integration starts; an explicit
  embedding test proves `configure_integrations(...)` still starts each
  requested integration.
- **EBC-008:** Inspect the maintained docs and specification, run docs-site
  preparation and build, and verify the generated default-config reference
  contains the new application object and no current Python instructions
  advertise environment-based bridge/Bonjour startup.

### Additional implementation verification

- Run the focused application suites for CLI environment isolation, bridge
  client behavior, server startup/shutdown, project profiles, and CLI E2E.
- Run the full default application Python test suite.
- Run frontend SDK default tests and the production SDK-to-FastAPI integration
  boundary affected by the runner change.
- Run the real local bridge E2E (Docker-backed where available) to prove
  explicit Python registration, pairing, and proxied requests still work.
- Run Ruff, Black check, and targeted Pyright for changed Python files.
- Validate the maintained default config as JSON and run documentation-site
  preparation/build.
- Search maintained production Python for `os.getenv()`/`os.environ` access to
  the removed `BRIDGE_*`, `BONJOUR_*`, `ENABLE_BONJOUR`, `SERVER_HOST`,
  `SERVER_PORT`, and `PORT` integration contract, allowing only unrelated or
  clearly documented non-runtime occurrences.

## Implementation Notes

- The parser accepts the existing `application.bridge_url` from the resolved
  config and validates the six new settings in `application.bridge`. It
  preserves `BridgeConfig` defaults through shared constants and reports the
  exact field path on invalid input. The unused internal
  `request_chunking_threshold_bytes` member remains for compatibility; the
  single application threshold is assigned to both legacy fields, and the
  user guide describes the effective response-side behavior.
- The CLI always passes its explicit integration selection to FastAPI.
  FastAPI and the CLI integration builder no longer inspect bridge/Bonjour
  environment variables. The old direct-uvicorn environment factory and
  integration-only host/port writes were removed. Shell subprocess environment
  inheritance was not changed.
- The frontend SDK's custom backend runner now receives explicit bridge
  arguments and calls `configure_integrations(...)`. Its bridge scenarios use
  those arguments. The real CLI bridge test uses a small ordinary
  `application.bridge` config, avoiding unrelated default-provider installation
  while exercising production CLI startup and the complete bridge flow.
- Initial `pytest` collection imported a separately installed main checkout;
  tests were rerun with this worktree's `application/python:core/python` first
  on `PYTHONPATH`. The new CLI subprocess regression initially timed out
  bootstrapping the machine's user-level plugin config; it now supplies an
  explicit minimal config and passes.
- The opt-in broad `test_cli_e2e.py` run had eight existing scenarios fail
  because they select this machine's `~/.crystal/config.json`, which references
  missing `plugins/cost-tracking` and `plugins/duration-tracking` paths in this
  worktree and installs many unrelated plugins. The two new CLI subprocess
  cases passed. The real CLI bridge integration test separately passed with a
  minimal valid config.
- The first real CLI bridge E2E attempt used a pyenv shim that did not resolve
  `python` in its temporary workspace; a retry with the actual interpreter
  reached default-config plugin installation and timed out. The test now uses
  a minimal valid config, and the real CLI bridge E2E passes.
- `docs_site/scripts/build_mkdocs_site.py` also refreshed two unrelated Core
  reference snapshots. Those incidental diffs were removed. The maintained
  default-config snapshot was kept because it is generated from the config
  changed by this task.

## Completion Notes

The Python bridge and Bonjour integrations now start only from explicit
process-local configuration. The six formerly environment-only bridge
transport controls have typed `application.bridge` keys with defaults and
field-specific validation. Normal CLI flags/profile/config behavior remains,
and direct ASGI embedding can pass the same explicit integration object.
Inherited environment variables cannot register a child server with the
parent's bridge identity.

Requirement evidence:

- **EBC-001, EBC-002, EBC-006, EBC-007:** server startup tests with all former
  integration variables set prove no implicit bridge/Bonjour activation;
  explicit Bonjour and bridge tests prove requested integrations still start;
  a real child CLI subprocess with inherited variables boots local-only.
  Production-source inspection finds no integration environment reads.
- **EBC-003:** CLI/profile precedence tests, the child CLI subprocess tests,
  and the real CLI→Elixir bridge→frontend pairing/proxy E2E passed.
- **EBC-004, EBC-005:** parser tests cover defaults, custom values, `null`
  WebSocket limit, invalid types/bounds, default-config parity, and propagation
  into `BridgeConfig`. The CLI subprocess rejects an invalid timeout with exit
  code 2 and the exact field path.
- **EBC-008:** application README/configuration guide, bridge maintainer
  guide, package guidance, portable bridge specification, default JSON config,
  and generated default-config reference were updated. Docs preparation and
  MkDocs build succeeded with existing unrelated warnings.

Verification performed:

- Full default application Python suite: **502 passed, 1 skipped, 100
  deselected**.
- Focused configuration/isolation tests after final additions: **57 passed**.
- Two new CLI subprocess integration tests: **2 passed**.
- Frontend SDK unit tests: **351 passed**.
- Real custom-runner bridge E2E: **5 passed**.
- Real CLI bridge E2E: **1 passed**, using an explicit minimal config.
- Documentation preparation tests: **15 passed**; preparation and MkDocs build
  completed.
- Targeted Ruff (excluding existing duplicate-route diagnostics in
  `server.py`), Black check, and targeted Pyright passed. Full `server.py`
  checks still report existing duplicate route definitions and an unrelated
  action-id type error. The repository has no installed TypeScript compiler
  for a standalone `tsc` command; Vitest executed the changed frontend
  integration TypeScript.
- The broad opt-in CLI integration file was attempted and had **8 failures**
  from this machine's external user config/plugin paths; its two new
  child-process cases passed separately against explicit configs. Those
  failures do not count as a passing broad CLI run.

There is no deferred implementation scope. The older CLI integration fixture's
dependency on external user configuration is a separate test-infrastructure
issue.