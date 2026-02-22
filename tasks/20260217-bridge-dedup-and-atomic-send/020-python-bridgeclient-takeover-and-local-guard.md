# Python BridgeClient: handle takeover + optional local single-instance guard

Parent Task: `tasks/20260217-bridge-dedup-and-atomic-send/000-main.md`

Depends On:
* `tasks/20260217-bridge-dedup-and-atomic-send/010-elixir-single-target-routing-and-takeover.md`

## Description

Once the Elixir bridge enforces “single active server connection per `server_id`”, the Python bridge client should:

1. gracefully stop itself when the bridge indicates it has been **superseded**
2. optionally prevent the “accidental double-run” on the same machine via a **local lockfile** keyed by `server_id`
3. improve observability (instance identifiers)

## Current behavior (code references)

`application/python/agent_terminal_app/bridge_client.py`:

* Connects to `.../ws/websocket?type=server` and joins `server:<server_id>`
* Message loop `_handle_messages` handles:
  * `pairing_requested`, `paired`
  * `http_request` and chunked variants
  * ignores other push events

There is currently no “superseded” handling.

## Proposed changes

### A) Handle `superseded` push from the bridge

Modify `BridgeClient._handle_messages` to include:

* `elif event == "superseded":`
  * log clearly: server_id, display_name, possibly new instance id
  * call `await self.stop()`
  * optionally print a user-facing message in non-test mode

Decide policy for the whole application:

* safest default: only stop the bridge client, keep FastAPI running.
* optional CLI/env: `BRIDGE_EXIT_ON_SUPERSEDED=1` to exit process.

### B) Send an `instance_id` during registration (observability)

Add a per-process UUID `instance_id` to the `register` payload:

* in `_register_server()` include `instance_id`.
* computed once in `__init__`.

Bridge side can log it and include in supersede payload.

### C) Optional local single-instance guard

Goal: prevent a common scenario where the user starts the server twice locally with the same bridge server id.

Add a lightweight lock:

* lockfile path: `~/.crystal/bridge_locks/<server_id>.lock` (or within configured `.crystal` dir)
* contents: pid, start timestamp, command line, port
* acquisition:
  * attempt atomic create (`O_EXCL`) at startup when bridge enabled
  * if exists and pid is alive:
    * default: fail fast with a clear error suggesting to stop the other process or use takeover flag
    * optional `--bridge-takeover-local` / `BRIDGE_TAKEOVER_LOCAL=1`:
      * send SIGTERM to old pid, wait briefly, then acquire lock

Important: this is “nice to have”; the bridge-level enforcement already fixes duplication. The local guard improves UX.

### D) Tests

Add tests under `application/python/tests`:

1. `test_bridge_client_superseded_stops`
   * Use `test_mode=True` and inject a fake websocket iterator that emits `{event: "superseded"}`.
   * Assert `_stopped` becomes true and `_close_ws` invoked.

2. `test_bridge_lockfile_blocks_second_instance` (if implemented)
   * Create lockfile pointing to a live pid (can use current pid).
   * Assert startup path raises/returns error.
   * If takeover enabled, assert it attempts to terminate the old pid (use monkeypatch).

## Acceptance criteria

* When the bridge pushes `"superseded"`, the Python bridge client stops its websocket loop and no longer forwards requests.
* Registration includes `instance_id` (visible in bridge logs).
* (Optional) second local process with same server id is blocked or explicitly takes over via flag.

## Checklist

- [x] Add `instance_id` to Python-side bridge registration payload.
- [x] Handle bridge `"superseded"` push by stopping the client (no reconnect loop).
- [x] Add opt-in local single-instance guard via lockfile (keyed by `server_id`).
- [x] Add opt-in `BRIDGE_EXIT_ON_SUPERSEDED=1` to terminate the whole process.
- [x] Wire new behavior via CLI flags in `python -m agent_terminal_app`.
- [x] Add Python tests covering `superseded` and local lock behavior.

## Plan (Implemented)

1. Update `application/python/agent_terminal_app/bridge_client.py`:
   - Generate a per-process UUID `instance_id`.
   - Include `instance_id` in the `register` payload.
   - Handle `event == "superseded"` by stopping the bridge client and not reconnecting.
   - Add optional `BRIDGE_EXIT_ON_SUPERSEDED=1` to terminate the whole process.
   - Add opt-in local lockfile guard under `~/.crystal/bridge_locks/<server_id>.lock`:
     - Atomic acquisition (`O_EXCL`).
     - Block when a live pid already owns the lock.
     - Optional `BRIDGE_TAKEOVER_LOCAL=1` to SIGTERM the old pid and take over.

2. Update `application/python/agent_terminal_app/__main__.py`:
   - Add CLI flags mapping to env vars:
     - `--bridge-exit-on-superseded` → `BRIDGE_EXIT_ON_SUPERSEDED=1`
     - `--bridge-local-guard` → `BRIDGE_LOCAL_GUARD=1`
     - `--bridge-takeover-local` → `BRIDGE_TAKEOVER_LOCAL=1`

3. Add tests under `application/python/tests`:
   - `superseded` stops the websocket loop and closes the socket.
   - Local guard blocks a second instance when a lockfile exists for a live pid.

## Implementation notes

- `application/python/agent_terminal_app/bridge_client.py`
  - Adds `BridgeConfig.exit_on_superseded`, `BridgeConfig.local_guard`, `BridgeConfig.takeover_local`.
  - Sends `instance_id` with `register` and logs it for observability.
  - Handles `"superseded"` push via `_handle_superseded()` and stops permanently.
  - Implements opt-in lockfile guard at `~/.crystal/bridge_locks/<server_id>.lock`.
  - Treats failed `register` replies as fatal (stops instead of retrying forever).
  - Fixes `_parse_optional_int` / `_parse_float` helper bugs so env overrides behave as expected.

- `application/python/agent_terminal_app/__main__.py`
  - Adds CLI flags for the new env-configured behaviors.

- `application/python/tests/test_bridge_client_superseded.py`
  - Regression tests for `superseded` handling and local lock guard.
