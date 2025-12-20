I’ll break this into protocol changes, bridge service, mobile app, and terminal app.

---

**1. Protocol & data model changes**

Goal: introduce a **persistent pairing token** that outlives any individual WebSocket session, and a way for the app to **resume** without re‑entering the 6‑digit code.

- **New concept: `pairing_token`**
    - High‑entropy string (e.g. `UUID.uuid4()` or 32 random bytes base64).
    - Tied to a `(server_id, client_id)` pair in the bridge.
    - Stored only in memory (ETS) in the bridge process for Stage 1.
    - Lifetime: as long as the bridge node stays up (or until explicit cleanup if we add it later).

- **First‑time pairing (existing flow, extended)**
    - App:
        - Connects to bridge `?type=app`, joins `app:<client_id>`.
        - Lists servers, chooses one.
        - Sends `pair_request` → server shows 6‑digit code.
        - Sends `pair_submit` with code.
    - Bridge:
        - Validates code via `PairingManager`.
        - `SessionManager.create_session(...)` creates a `session_id`.
        - **New:** create or fetch a `pairing_token` for `(server_id, client_id)`.
        - Reply to app with:
            - Existing: `session_id`
            - New: `pairing_token`
    - App:
        - Stores `session_id` (for HTTP routing) and `pairing_token` (for future resume) in memory.

- **New operation: Resume by pairing token**
    - New Phoenix channel event on `app:<client_id>`:
        - Event: `"resume_session"`
        - Payload: `{ "pairing_token": "...", "server_id": "..." }` (server_id optional but helpful for validation).
    - Bridge’s `AppChannel`:
        - Lookup `(server_id, client_id')` by `pairing_token`.
        - Optionally update stored `client_id` to the current socket’s `client_id` if we allow client ID rotation.
        - Check that `server_id` is currently registered in `ServerRegistry`.
        - Create a new `session_id` via `SessionManager.create_session`.
        - Assign `:session_id` on socket, subscribe to necessary PubSub topics.
        - Reply with `{:ok, %{session_id: session_id}}`.
    - App:
        - Receives new `session_id`.
        - Reuses this for all subsequent HTTP requests.

- **Sessions remain ephemeral**
    - We don’t try to “keep session alive” across disconnects.
    - Sessions are still:
        - Deleted on channel termination (`AppChannel.terminate`).
        - Cleaned up after idle `SESSION_TIMEOUT`.
    - Only the **mapping** `(pairing_token → server_id, client_id, metadata)` persists.

This keeps the security and behavior of sessions unchanged; the only persistent secret is the `pairing_token`.

---

**2. Bridge service (`bridge-elixir`) changes**

Files: `bridge-elixir/lib/bridge/*.ex`

2.1 **New module: persistent pairing manager**

- Create `Bridge.PersistentPairingManager` (name can be adjusted):

    - ETS tables (all in memory):
        - `:bridge_pairings_by_token`:
            - Key: `pairing_token` (string).
            - Value: struct `%Pairing{token, server_id, client_id, created_at, last_used_at}`.
        - Optionally (for efficiency) `:bridge_pairings_by_key`:
            - Key: `{server_id, client_id}`.
            - Value: `pairing_token`.

    - Public API:
        - `create_or_get_token(server_id, client_id) :: {:ok, token}`
            - Look up existing token for `(server_id, client_id)`.
            - If none, generate new `pairing_token`, insert into tables.
        - `get_by_token(token) :: {:ok, pairing} | {:error, :not_found}`
        - `touch(token)` (optional) to update `last_used_at` for metrics/cleanup.

    - Cleanup (Stage 1):
        - Optional:
            - Periodic sweep using a configurable TTL (e.g. many hours or days) like `SessionManager`.
        - Or:
            - No TTL; rely on bridge process lifetime. Simple and fine for Stage 1.

2.2 **Wire into `AppChannel.pair_submit`**

- File: `bridge-elixir/lib/bridge/app_channel.ex`

- In `handle_in("pair_submit", params, socket)`:

    - After `PairingManager.validate_code(...)` succeeds and `ServerRegistry.get_server/1` returns `{:ok, server_info}`:
        - Call `{:ok, pairing_token} = Bridge.PersistentPairingManager.create_or_get_token(server_id, client_id)`.
        - Call `Bridge.SessionManager.create_session(...)` as today.
        - Assign `:session_id` to the socket, subscribe to `tunnel:app:<client_id>`.
        - **Change reply:**
            - From: `{:reply, {:ok, %{session_id: session_id}}, socket}`
            - To:   `{:reply, {:ok, %{session_id: session_id, pairing_token: pairing_token}}, socket}`

    - This is backward compatible: older clients ignore extra fields.

2.3 **New `resume_session` handler**

- Also in `AppChannel`:

    - Add:

      ```elixir
      def handle_in("resume_session", %{"pairing_token" => token} = params, socket) do
        client_id = socket.assigns.client_id
  
        case Bridge.PersistentPairingManager.get_by_token(token) do
          {:ok, %{server_id: server_id} = pairing} ->
            # Optional: if params contain "server_id", validate it matches pairing.server_id
            # Optional: update stored client_id to current client_id
  
            case Bridge.ServerRegistry.get_server(server_id) do
              {:ok, server_info} ->
                {:ok, session_id} =
                  Bridge.SessionManager.create_session(server_id, client_id, server_info.node, node())
  
                socket = assign(socket, :session_id, session_id)
                Phoenix.PubSub.subscribe(Bridge.PubSub, "tunnel:app:#{client_id}")
  
                {:reply, {:ok, %{session_id: session_id}}, socket}
  
              {:error, :not_found} ->
                {:reply, {:error, %{reason: "server_not_found"}}, socket}
            end
  
          {:error, :not_found} ->
            {:reply, {:error, %{reason: "invalid_pairing_token"}}, socket}
        end
      end
      ```

    - Decide how strict to be about `client_id`:
        - Stage 1 (simpler): don’t enforce; treat `pairing_token` as the main secret.
        - Optionally log when `client_id` changes for the same token.

2.4 **No changes to `SessionManager` or `ServerChannel` semantics**

- Sessions:
    - Still created per connection.
    - Still removed on `AppChannel.terminate`.
    - Still have `SESSION_TIMEOUT`.
- Server registration:
    - `ServerChannel.terminate` still unregisters servers.
- Persistent pairings:
    - Only depend on `Bridge.PersistentPairingManager`; they’re independent of session lifecycle.

2.5 **Tests**

- New tests for `PersistentPairingManager` (e.g. `test/bridge/persistent_pairing_manager_test.exs`):
    - Create token for `(server_id, client_id)`, fetch by token.
    - Repeated `create_or_get_token` returns same token.
- Extend WebSocket / integration tests if practical:
    - Update `websocket_test.exs` (currently `@tag :skip`, but can still serve as reference):
        - After successful `pair_submit`, assert that reply JSON contains `pairing_token`.
        - Add a “resume” test:
            - Pair once.
            - Close app connection.
            - Open a new app client (maybe with new client_id).
            - Send `resume_session` with `pairing_token`.
            - Verify you get a new `session_id` and can issue `http_request`.

---

**3. Mobile app (`mobile/crystal-lattice-control-rn`) changes**

Files: `mobile/crystal-lattice-control-rn/App.tsx` (BridgeAdapter + connection UI)

3.1 **Extend `BridgeAdapter` state & API**

- Add fields to `BridgeAdapter`:

    - `private pairingToken: string | null = null;`
    - `private reconnecting: boolean = false;`
    - `private stopped: boolean = false;` (flag to avoid reconnect after explicit disconnect).

- Update constructor:
    - `this.stopped = false;` and maintain across reconnects.

3.2 **Store `pairing_token` on first pairing**

- In `async submitPairingCode(serverId, code, serverName)`:

    - Today:

      ```ts
      const response = await this.sendMessage('pair_submit', {...});
      this.sessionId = response.session_id;
      this.serverId = serverId;
      this.serverName = serverName;
      ```

    - Change to:

      ```ts
      const response = await this.sendMessage(
        `app:${this.clientId}`,
        'pair_submit',
        { server_id: serverId, code }
      );
  
      this.sessionId = response.session_id;
      this.pairingToken = response.pairing_token || null;
      this.serverId = serverId;
      this.serverName = serverName;
      ```

- No app‑level persistence yet: `pairingToken` remains in memory only.

3.3 **Add a “resume session” helper**

- Inside `BridgeAdapter`:

    - New method:

      ```ts
      private async resumeSessionIfPossible(): Promise<void> {
        if (!this.pairingToken || !this.serverId) {
          // No way to resume; caller will handle failure.
          this.sessionId = null;
          return;
        }
  
        const response = await this.sendMessage(
          `app:${this.clientId}`,
          'resume_session',
          { pairing_token: this.pairingToken, server_id: this.serverId }
        );
  
        this.sessionId = response.session_id;
      }
      ```

    - Any failure here should bubble up as an error; caller (connect/reconnect) can decide to surface a UI error or require re‑pairing.

3.4 **Refactor `connect()` to be reusable and reconnect‑friendly**

- Separate concerns:

    - `connect()` is used for:
        - Initial app/bridge handshake.
        - Reconnect after transient disconnects (without re‑pairing).

- Plan:

    - Extract core logic into `private async openWebSocket(): Promise<void>`:

        - Creates `WebSocket` to `this.bridgeUrl?type=app`.
        - Sets up `onopen`, `onmessage`, `onerror`, `onclose`.
        - On `onopen`:
            - Join `app:<clientId>` channel via `joinChannel()`.
            - If `this.pairingToken` and `this.serverId` are set:
                - Call `resumeSessionIfPossible()` and treat failure as fatal here.
            - Mark some `this.hasConnectedOnce = true`.

    - `connect()` then becomes:

      ```ts
      async connect(): Promise<void> {
        this.stopped = false;
        await this.openWebSocket();
      }
      ```

3.5 **Automatic reconnect logic**

- Inside `openWebSocket()`:

    - In `onclose`:

        - Distinguish between:
            - Initial connection attempt (before `hasConnectedOnce`).
            - Later disconnects during normal use.

        - For initial attempts:
            - Keep existing behavior: reject `connect()` promise.

        - For later disconnects:

          ```ts
          this.sessionId = null;
    
          if (!this.stopped && this.pairingToken && this.serverId) {
            // Schedule background reconnect with small backoff.
            this.scheduleReconnect();
          }
          ```

    - Implement `scheduleReconnect()`:

      ```ts
      private scheduleReconnect(delayMs = 1000) {
        if (this.reconnecting || this.stopped) return;
        this.reconnecting = true;
  
        setTimeout(async () => {
          this.reconnecting = false;
          try {
            await this.openWebSocket();
          } catch (e) {
            // Optionally increase delay and retry.
            this.scheduleReconnect(Math.min(delayMs * 2, 30000));
          }
        }, delayMs);
      }
      ```

- Also use reconnect on demand:

    - Modify `sendMessage`:

        - Before checking `this.ws.readyState`, if `!this.ws || this.ws.readyState !== WebSocket.OPEN`:
            - If `this.stopped`, reject immediately.
            - Otherwise call `await this.openWebSocket()` (which will resume session if possible).
        - Then continue to construct message and register response handler.

This ensures:
- If the WebSocket drops while the app is backgrounded, the next HTTP call will transparently reconnect and resume.
- If you want proactive reconnect, you can also call `bridgeAdapter.connect()` or a new `bridgeAdapter.reconnectIfNeeded()` from app lifecycle handlers.

3.6 **Respect explicit disconnect**

- In `disconnect()`:

    - Today:

      ```ts
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
      this.sessionId = null;
      this.serverId = null;
      ```

    - Extend:

      ```ts
      this.stopped = true;
      // Optionally clear pairingToken here or keep it for future manual resume.
      ```

    - For Stage 1:
        - You might keep `pairingToken` so that, if the user reconnects “to the same server” within this app run, you can resume without re‑pairing.
        - Or clear it for stricter semantics. Either is acceptable; make the choice explicit.

3.7 **App‑level integration**

- `App.tsx`:

    - No large UI changes in Stage 1.
    - Optional enhancement:
        - Subscribe to `AppState` events and on transition to `active`:
            - If `connectionMethod === 'bridge'` and `adapter` is a `BridgeAdapter`, call a `reconnectIfNeeded()` method.
        - This makes reconnection more eager (not only on user actions).

- Behavior after Stage 1:
    - User pairs once per app run.
    - Screen off → WebSocket closed.
    - On wake / next request:
        - BridgeAdapter reconnects WebSocket.
        - Sends `resume_session` with `pairing_token`.
        - Gets a fresh `session_id`.
        - HTTP requests work without re‑entering 6‑digit code.

---

**4. Terminal app (Python `agent_terminal_app`) – automatic reconnection**

Files: `application/python/agent_terminal_app/bridge_client.py`

4.1 **Reconnect loop in `BridgeClient.run`**

- Current behavior:
    - Single attempt:
        - `websockets.connect(...)`
        - `_join_channel()`, `_register_server()`, `_handle_messages()`
    - On error or close: log and exit `run()`.

- Target:

    - Wrap connection block in a loop honoring `self._stopped`:

      ```python
      async def run(self) -> None:
          if websockets is None:
              ...
              return
  
          ws_url = f"{self.config.bridge_url}?type=server"
          backoff = 1.0
  
          while not self._stopped:
              try:
                  self._ws = await websockets.connect(ws_url)
                  self._connected = True
                  backoff = 1.0  # reset backoff
  
                  await self._join_channel()
                  await self._register_server()
                  await self._handle_messages()
              except asyncio.CancelledError:
                  raise
              except Exception:
                  log.exception("Bridge client error; will retry")
                  if not self.test_mode:
                      print("[bridge] error in bridge client; will retry shortly")
              finally:
                  await self._close_ws()
                  self._connected = False
  
              if self._stopped:
                  break
  
              await asyncio.sleep(backoff)
              backoff = min(backoff * 2, 30.0)
      ```

    - `_handle_messages()` should return when the WebSocket closes or `self._stopped` becomes `True`.

4.2 **Ensure `stop()` cooperates**

- `stop()` already sets `_stopped = True` and closes the WebSocket.
- With the loop:
    - After `_close_ws()` the loop sees `_stopped` and breaks.
- Ensure no extra tasks are created:
    - Startup code in `server.py` continues to create one background task per process.

4.3 **No protocol changes needed on server side**

- Server still registers with the same `server_id`.
- On reconnection, `ServerRegistry` simply sees a new registration and updates ETS.
- Persistent pairing tokens live purely in Elixir; Python does not need to know about them.

4.4 **Tests**

- If feasible, add tests that:
    - Simulate a failing connection (e.g., invalid URL) and ensure `run()` does not crash but retries.
    - Simulate a close after some messages and verify that `run()` attempts a reconnect.

---

**5. Stage 1 summary**

After implementing Stage 1:

- **Bridge**:
    - Maintains an in‑memory mapping from a high‑entropy `pairing_token` to `server_id` (and optionally `client_id`).
    - Supports a `resume_session` message that re‑establishes a fresh `session_id` without re‑pairing.

- **Mobile app**:
    - Stores `pairing_token` after the first pairing within the current app run.
    - Transparently reconnects the WebSocket and calls `resume_session` if the bridge connection drops (e.g., screen off/on).
    - Still requires a new 6‑digit pairing if the app process is killed or the bridge restarts (since storage is in‑memory only).

- **Terminal app**:
    - Automatically reconnects to the bridge with exponential backoff when the WebSocket fails, without needing a full server restart.

---

**Stage 2 – High‑level plan (connections screen + reconnect)**

Stage 2 builds on Stage 1’s primitives; no need to implement yet, just plan.

**Goals**

- Add a **Connections** screen in the mobile app:
    - Shows a list of known connections (manual, discovery, bridge).
    - Tapping a connection reconnects and navigates straight to the Sessions tab.
    - “New connection” button opens the existing method‑selection / connection flow.

**High‑level steps**

1. **Model connection records**

    - Introduce a `ConnectionRecord` type in the mobile app:

      ```ts
      type ConnectionMethod = 'manual' | 'discovery' | 'bridge';
 
      interface BaseConnectionRecord {
        id: string;          // internal UUID
        method: ConnectionMethod;
        name: string;        // display label for list
        lastUsedAt: number;  // timestamp
      }
 
      interface ManualConnectionRecord extends BaseConnectionRecord {
        method: 'manual';
        host: string;
        port: number;
      }
 
      interface DiscoveryConnectionRecord extends BaseConnectionRecord {
        method: 'discovery';
        host: string;
        port: number;
        serviceName: string;
      }
 
      interface BridgeConnectionRecord extends BaseConnectionRecord {
        method: 'bridge';
        bridgeUrl: string;
        serverId: string;
        serverName: string;
        pairingToken: string;   // comes from Stage 1
      }
 
      type ConnectionRecord =
        | ManualConnectionRecord
        | DiscoveryConnectionRecord
        | BridgeConnectionRecord;
      ```

    - Stage 2 can still keep these only in memory, or optionally persist to `AsyncStorage` for true cross‑restart reuse.

2. **Add a `ConnectionsScreen` component**

    - New screen in `mobile/crystal-lattice-control-rn/src`:
        - Props:
            - `connections: ConnectionRecord[]`
            - `onSelectConnection(record: ConnectionRecord)`
            - `onNewConnection()`
        - Renders:
            - List of saved connections with:
                - `name`, method icon/label, last used.
            - “New Connection” button at top or bottom.

3. **Restructure App navigation**

    - Current `App.tsx` has:
        - `screen: 'method' | 'connecting' | 'connected'`.
        - “Method” screen directly shows manual/discovery/bridge options.

    - Target:
        - `screen: 'connections' | 'method' | 'connecting' | 'connected'`.
        - Startup:
            - If there are known connections → show `ConnectionsScreen`.
            - Else → go straight to `'method'`.

    - Flows:
        - “New connection” from `ConnectionsScreen`:
            - Set `screen = 'method'`.
        - Successful connection (any method):
            - Create/update a `ConnectionRecord` and push into `connections` state.
            - Set `screen = 'connected'` and render `ConnectedRoot`.

4. **Reconnect from existing connection**

    - In `onSelectConnection(record)`:

        - For manual:
            - Instantiate new `HttpAdapter(host, port, name)`.
            - Call `connect()` as in `connectManual`.
            - On success, set `adapter` and `screen = 'connected'`.

        - For discovery:
            - Same as manual, using stored host/port from previous resolved service.

        - For bridge:
            - Instantiate new `BridgeAdapter(bridgeUrl)`.
            - Call `connect()` (Stage 1 version with auto‑resume support).
            - After WebSocket open + channel join:
                - Call `resumeSessionIfPossible()` with stored `pairingToken` / `serverId`.
            - On success:
                - Set `adapter` and `screen = 'connected'`.
            - On failure:
                - Show an error:
                    - e.g. “Cannot resume this connection – you may need to pair again.”
                    - Optionally offer a button to go to the bridge method flow and re‑pair.

5. **Navigate into sessions**

    - `ConnectedRoot` already has a Sessions tab and defaults to it.
    - No big changes required; once `screen = 'connected'` and `adapter` set, user lands on sessions and can use it as today.

6. **Optional persistence**

    - After Stage 1 is stable, decide whether Stage 2 should:
        - Keep connections only for the lifetime of the app process (simpler).
        - Or persist to disk using `AsyncStorage` so connections (and for bridge, `pairingToken`) survive app restarts.

    - If you choose persistence:
        - Be explicit about security of `pairingToken` at rest on device.
        - Add migration logic in `useEffect` to load saved connections on app startup.

---

If you want, next I can take Stage 1 and translate this plan into specific code diffs for `bridge-elixir` (new manager + `AppChannel` changes), `BridgeAdapter` in `App.tsx`, and `BridgeClient.run` in Python.