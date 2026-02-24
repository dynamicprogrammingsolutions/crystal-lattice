# Elixir bridge: single-target routing + takeover/reject for duplicate server_id

Parent Task: `tasks/20260217-bridge-dedup-and-atomic-send/000-main.md`

## Description

Fix the core duplication bug at the bridge level.

Today, the bridge routes `http_request` and chunked `http_request_*` from app → server using PubSub broadcast to `"tunnel:server:<server_id>"`. Every server websocket that registered that `server_id` subscribes to this topic, so N server connections receive the same request.

This subtask changes routing to **deliver each request to exactly one** active server connection for the `server_id` by:

* enforcing **single active `channel_pid` per `server_id`** in `Bridge.ServerRegistry`
* replacing PubSub fan-out with direct `send(channel_pid, ...)`
* implementing a clear policy for “duplicate register”:
  * **takeover** (recommended default): new server supersedes old
  * **reject** (optional/configurable): refuse registration when already registered
* ensuring cleanup even on abnormal disconnect using `Process.monitor/1`

## What we already know (code references)

### Fan-out subscription

`bridge-elixir/lib/bridge/server_channel.ex`:

* `handle_in("register", ...)` subscribes:
  * `Phoenix.PubSub.subscribe(Bridge.PubSub, "tunnel:server:#{server_id}")`
  * `Phoenix.PubSub.subscribe(Bridge.PubSub, "pairing:#{server_id}")`

### Fan-out broadcast

`bridge-elixir/lib/bridge/app_channel.ex`:

* `handle_in("http_request", ...)` does:
  * `Phoenix.PubSub.broadcast(Bridge.PubSub, "tunnel:server:#{session.server_id}", {:http_request, request})`

The chunked request handlers (`http_request_init/chunk/end`) also broadcast to `tunnel:server:<server_id>`.

### Server registry is not enough

`bridge-elixir/lib/bridge/server_registry.ex` stores an ETS `:set` keyed by `server_id` (so it overwrites), but it does not prevent multiple server channel processes from being subscribed.

## Proposed changes

### A) ServerRegistry: track and own the active channel pid (with monitor)

Modify `bridge-elixir/lib/bridge/server_registry.ex`:

* Store per `server_id`:
  * `channel_pid`
  * `monitor_ref`
  * `connected_at`
  * optionally `instance_id` (sent from Python) for logging/debug

Add new API (suggested):

* `register_server(server_id, info, opts \\ [])` returns one of:
  * `{:ok, :registered}`
  * `{:ok, {:took_over, old_pid}}`
  * `{:error, :already_registered}`

Implementation sketch:

1. Look up existing server entry by `server_id`.
2. If none: monitor new pid, insert, ok.
3. If existing pid is same: refresh metadata and ok.
4. If existing pid is alive and different:
   * if takeover enabled:
     * replace ETS entry with new pid + new monitor
     * demonitor old
     * return `{:ok, {:took_over, old_pid}}`
   * else reject: return error.

Also handle `{:DOWN, monitor_ref, :process, pid, reason}`:

* Remove matching entries so dead pids don’t remain “registered”.

### B) ServerChannel: remove PubSub subscription for tunnel:server

Modify `bridge-elixir/lib/bridge/server_channel.ex`:

* On register:
  * **Do not** subscribe to `tunnel:server:<server_id>`.
  * Keep `pairing:<server_id>` subscription (or route it directly too—see below).

* After successful register:
  * if takeover happened:
    * force-close old channel pid (preferred) OR send it a `{:superseded, ...}` message.

Add handling for takeover notifications:

* `handle_info({:superseded, new_pid, server_id}, socket)`:
  * `push(socket, "superseded", %{server_id: server_id, reason: "new_connection"})`
  * stop/terminate.

### C) AppChannel: route http_request directly to active server pid

Modify `bridge-elixir/lib/bridge/app_channel.ex` for:

* `handle_in("http_request", ...)`
* `handle_in("http_request_init", ...)`
* `handle_in("http_request_chunk", ...)`
* `handle_in("http_request_end", ...)`

Replace:

* `Phoenix.PubSub.broadcast(..., "tunnel:server:#{session.server_id}", {:http_request, request})`

With:

1. `Bridge.ServerRegistry.get_server(session.server_id)`
2. `send(server_info.channel_pid, {:http_request, request})`

If server not found:

* return `{:error, %{reason: "server_not_found"}}` (or `server_disconnected`).

Note: the response path should remain:

* server sends `http_response*` to ServerChannel
* ServerChannel broadcasts to `tunnel:request:<request_id>`
* AppChannel awaits and/or pushes chunked response events

### D) Pairing flow: remove pairing PubSub fan-out or ensure single server

Currently `Bridge.PairingManager` broadcasts `{:pairing_requested, ...}` to `"pairing:<server_id>"`.

To avoid duplicate pairing banners if multiple server channels exist briefly:

* Preferred: route pairing directly via registry pid as well.
  * In `Bridge.PairingManager.create_pairing_request/2`, instead of PubSub broadcast, look up `server_id` in registry and `send(channel_pid, {:pairing_requested, ...})`.
* Same for `Bridge.SessionManager.create_session` which broadcasts `{:paired, ...}`.

If you keep PubSub for pairing, it’s less severe than HTTP duplication, but still confusing.

### E) Config toggles

Add env/config option:

* `BRIDGE_SERVER_ID_CONFLICT_POLICY=takeover|reject` (default takeover)

## Tests

Add/extend tests in `bridge-elixir/test/...`:

1. **Duplicate register takeover**
   * Start two server channel processes registered under same `server_id`.
   * Verify second register triggers takeover.
   * Verify the old server channel receives `"superseded"` push and terminates, OR is no longer the target.

2. **No duplicate http_request delivery**
   * With two server connections, send a single `http_request` from app.
   * Assert only one server channel receives `handle_info({:http_request, ...})`.

3. **Chunked events routing**
   * Send `http_request_init/chunk/end`.
   * Assert only one server receives all chunk events.

4. **DOWN cleanup**
   * Register server, kill pid, ensure registry removed entry.

## Acceptance criteria

* With two server websocket connections using same `server_id`, the bridge forwards each incoming request to exactly one server.
* Under takeover policy, registering the second server actively supersedes/terminates the first.
* Under reject policy, second register fails with a clear error.
* Chunked request events follow the same single-target semantics.

## Execution plan (confirmed)

- [x] Update `Bridge.ServerRegistry` to enforce a single active `channel_pid` per `server_id`.
- [x] Add `Process.monitor/1` and `{:DOWN, ...}` cleanup so dead server channels are unregistered.
- [x] Implement conflict policy `BRIDGE_SERVER_ID_CONFLICT_POLICY=takeover|reject` (default `takeover`).
- [x] Change unregister to be pid-aware (`unregister_server(server_id, channel_pid)`) to prevent old disconnects from deleting new registrations.
- [x] Replace app→server PubSub broadcast with direct `send(channel_pid, ...)` for `http_request` and `http_request_{init,chunk,end}`.
- [x] Remove server-side subscription to `tunnel:server:<server_id>`.
- [x] Implement takeover notification (`{:superseded, ...}`) so the old server channel can close itself.
- [x] Route pairing notifications directly to the active server channel (no PubSub fan-out) for `pairing_requested` and `paired`.
- [x] Add/extend Elixir tests covering takeover, reject, single-target routing, and `:DOWN` cleanup.

## Implementation notes

- Single-target routing is now enforced by directing app→server messages to the active `channel_pid` from `Bridge.ServerRegistry`.
  - Updated: `bridge-elixir/lib/bridge/app_channel.ex`
  - Removed all broadcasts to `tunnel:server:<server_id>`.

- `Bridge.ServerRegistry` now owns active connection selection and cleanup:
  - Updated: `bridge-elixir/lib/bridge/server_registry.ex`
  - `register_server/3` returns `{:ok, :registered}` / `{:ok, {:took_over, old_pid}}` / `{:error, :already_registered}`.
  - `unregister_server/2` only unregisters if the stored pid matches.
  - Cluster unregistration broadcast now includes the pid: `{:server_unregistered, server_id, channel_pid}` to avoid late deletes clobbering newer registrations.
  - Uses `Process.monitor/1` and removes registry entries on `{:DOWN, ...}` when still current.

- `Bridge.ServerChannel` no longer subscribes to per-server PubSub topics for request delivery.
  - Updated: `bridge-elixir/lib/bridge/server_channel.ex`
  - Handles `{:superseded, server_id, new_pid}` by pushing a `"superseded"` event and terminating.

- Pairing flow now avoids PubSub fan-out:
  - Updated: `bridge-elixir/lib/bridge/pairing_manager.ex`, `bridge-elixir/lib/bridge/session_manager.ex`
  - Pairing/session notifications are delivered with direct `send/2` to the active server channel pid.

- Tests added/updated:
  - Added: `bridge-elixir/test/bridge/single_target_routing_test.exs`
  - Updated: `bridge-elixir/test/bridge/server_registry_test.exs`, `bridge-elixir/test/bridge/pairing_manager_test.exs`, `bridge-elixir/test/bridge/session_manager_test.exs`
  - `mix test` passes.
