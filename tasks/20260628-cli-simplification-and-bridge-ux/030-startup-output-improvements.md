# Startup Output Improvements

Improve what is printed when the terminal/server starts: show the actual
network-reachable IP when bound to 0.0.0.0, show bonjour service name and
bridge URL, and remove redundant prints.

Parent Task: tasks/20260628-cli-simplification-and-bridge-ux/000-main.md
Depends On: tasks/20260628-cli-simplification-and-bridge-ux/010-project-profile-persistence.md
Depends On: tasks/20260628-cli-simplification-and-bridge-ux/020-cli-simplification-bridge-host-logging.md

---

## Requirements checklist

- [ ] When bound to `0.0.0.0`, detect and show the actual network-reachable LAN IP address
- [ ] Show a consolidated startup summary with connection info for each enabled method:
  - Direct HTTP: `http://<lan-ip>:<port>` (or `http://127.0.0.1:<port>` if localhost)
  - Bonjour: service name (and note that it's discoverable)
  - Bridge: bridge URL
- [ ] Remove the redundant `print(f"Setting terminal title to: {title}")` line in `_set_terminal_title()`
- [ ] Remove the separate `[agent_terminal_app] Bonjour enabled:` print
- [ ] Remove the separate `[agent_terminal_app] Bridge enabled:` print
- [ ] Keep `[agent_terminal_app] Using config:` and `[agent_terminal_app] Using sessions dir:` (or consolidate into the summary)
- [ ] Refactor the startup summary into a testable helper function
- [ ] Add unit tests for the summary formatting (all combinations: localhost, 0.0.0.0, bonjour on/off, bridge on/off)

---

## Implementation notes

### Current redundant prints in `__main__.py`

1. `_set_terminal_title()` (line ~190):
   ```python
   print(f"Setting terminal title to: {title}")
   ```
   This is debug noise. Remove the print; keep the title-setting logic.

2. Lines ~830-840 (after `configure_integrations`):
   ```python
   if integration_config is not None and integration_config.bonjour is not None:
       print("[agent_terminal_app] Bonjour enabled: ...")
   if integration_config is not None and integration_config.bridge is not None:
       print("[agent_terminal_app] Bridge enabled: ...")
   ```
   These should be replaced by the consolidated summary.

3. Lines ~900:
   ```python
   print(f"[agent_terminal_app] Using config: {config_path}")
   print(f"[agent_terminal_app] Using sessions dir: {session_root}")
   ```
   These can be kept or folded into the summary.

### LAN IP detection

`bonjour.py` already has `_get_local_ip()` (line ~52) that connects a UDP socket to a non-routable address to discover the preferred outbound interface IP. Reuse this (or factor it into a shared utility) for the startup summary.

Consider making `_get_local_ip()` a public function (rename to `get_local_ip()` or add a public wrapper) so `__main__.py` can import it without reaching into a private name.

### Proposed summary format

```
[crystal-lattice] Starting iocharts
  Config:    /Users/.../.crystal/config.json
  Sessions:  /Users/.../.crystal/sessions
  HTTP:      http://192.168.1.42:8090
  Bonjour:   iocharts (discoverable on local network)
  Bridge:    wss://crystal-bridge.dynamicprogrammingsolutions.com/ws/websocket
```

Only show lines for methods that are active. If bound to `127.0.0.1`, show `http://127.0.0.1:<port>`. If bound to `0.0.0.0`, resolve the LAN IP and show `http://<lan-ip>:<port>`.

### Testable helper

Create a function like:

```python
def _format_startup_summary(
    *,
    project_name: str,
    config_path: Path,
    session_root: Path,
    host: str,
    port: int,
    bonjour_service_name: Optional[str],
    bridge_url: Optional[str],
) -> str:
    ...
```

This can be unit-tested with a mocked `get_local_ip()` without needing to start a server.

### Key files to modify

- `application/python/agent_terminal_app/__main__.py` — remove redundant prints, add summary
- `application/python/agent_terminal_app/bonjour.py` — make `_get_local_ip()` public if needed
- `application/python/tests/test_cli_environment_isolation.py` or a new test file — add summary tests

### Testing approach

- Test `_format_startup_summary()` with:
  - localhost binding (127.0.0.1)
  - 0.0.0.0 binding (mock `get_local_ip()` to return a fixed IP)
  - bonjour on, bridge off
  - bonjour off, bridge on
  - both on
  - both off (server-only or console-only)
- Verify the summary string contains expected substrings.
- Verify `_set_terminal_title()` no longer prints.