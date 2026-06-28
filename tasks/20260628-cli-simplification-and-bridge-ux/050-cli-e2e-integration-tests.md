# CLI E2E Integration Tests

Add end-to-end integration tests that verify the real CLI entrypoint
(`python -m agent_terminal_app`) behaves correctly for the simple run
scenarios introduced in subtasks 020 and 030: plain server, console+server,
Bonjour, and bridge.  Add a `--no-tty` flag so `--console` can be used in
non-interactive (CI/subprocess) contexts.

Parent Task: tasks/20260628-cli-simplification-and-bridge-ux/000-main.md
Depends On: tasks/20260628-cli-simplification-and-bridge-ux/020-cli-simplification-bridge-host-logging.md
Depends On: tasks/20260628-cli-simplification-and-bridge-ux/030-startup-output-improvements.md

---

## Requirements checklist

### Prerequisite: `--no-tty` flag

- [ ] Add `--no-tty` CLI flag to the argument parser in `__main__.py`
- [ ] `--console --server --no-tty`: start server in background, block until SIGINT/SIGTERM (replace `run_terminal()` with `threading.Event().wait()`), then run the existing `finally` cleanup
- [ ] `--console --no-tty` (without `--server`): print a message explaining there is nothing to do without a server, and exit
- [ ] `--server --no-tty` (without `--console`): no effect — server does not need a TTY
- [ ] Document `--no-tty` in `application/python/README.md`
- [ ] Unit test: `--no-tty` with `--console --server` blocks and terminates cleanly on SIGTERM

### Approach 1 — Python subprocess integration tests

- [ ] Create `application/python/tests/test_cli_e2e.py` marked `pytest.mark.integration`
- [ ] `test_server_only_startup_and_profile_persistence`: launch `--server`, verify startup summary in stdout, verify `/api/hello` responds, verify `~/.crystal/projects.json` created with port/name/bridge-server-id
- [ ] `test_second_run_reuses_persisted_port`: launch `--server` twice in same dir, verify second run reuses persisted port and bridge-server-id from profile
- [ ] `test_console_server_no_tty`: launch `--console --server --no-tty`, verify startup summary, verify server reachable, verify process terminates cleanly on SIGTERM
- [ ] `test_enable_bonjour_startup_summary`: launch `--server --enable-bonjour`, verify summary includes Bonjour line with service name
- [ ] `test_enable_bridge_startup_summary`: launch `--server --enable-bridge` with bridge URL in `.crystal/profile.json`, verify summary includes Bridge line
- [ ] `test_default_log_file_created`: launch `--server` (no `--log-file`), verify `.crystal/crystal.log` exists and contains log output
- [ ] `test_no_log_file_disables_logging`: launch `--server --no-log-file`, verify no `.crystal/crystal.log` created
- [ ] All tests use `tmp_path` for `HOME` and `cwd` to isolate profile files; set `PYTHONPATH` for source runs; clean up subprocess in `finally`

### Approach 3 — Docker Bonjour discovery test

- [ ] Create `application/python/tests/test_cli_bonjour_docker.py` marked `pytest.mark.integration` + `pytest.mark.docker`
- [ ] Create `application/python/tests/fixtures/bonjour-docker/docker-compose.yml` with two services on a shared network:
  - `server`: Python image with repo mounted, installs deps, runs `python -m agent_terminal_app --server --enable-bonjour --host 0.0.0.0`
  - `discoverer`: Python image with `zeroconf` installed, runs a discovery script
- [ ] Create `application/python/tests/fixtures/bonjour-docker/discover.py`: uses `zeroconf` to browse for `_http._tcp` services, prints discovered services as JSON, exits
- [ ] `test_bonjour_discoverable_from_another_container`: start compose stack, wait for server, run discovery, parse JSON, assert service name and port match the CLI's profile
- [ ] Skip if Docker is not available (`shutil.which("docker")`)
- [ ] Clean up compose stack in `finally` (`docker-compose down --remove-orphans -v`)

### Approach 4 — Bridge E2E with real CLI

- [ ] Add `startBackendViaCLI()` to `packages/frontend-sdk/src/integration/harness.ts`: spawns `python -m agent_terminal_app --server --enable-bridge --bridge-url <url> --no-tty` instead of the custom runner; captures stdout; polls `/api/hello`; returns `{ baseUrl, port, stdout, stop }`
- [ ] Create `packages/frontend-sdk/src/integration/__tests__/bridge.cli.e2e.integration.test.ts`
- [ ] Test: start bridge via `startBridgeDocker()`, start CLI via `startBackendViaCLI()` with `--enable-bridge --bridge-url <bridge-url>`, connect via `BridgeTransport`, wait for server in bridge registry, request pairing, read pairing code from captured stdout, submit pairing code, send proxied HTTP request, verify response
- [ ] Add npm script `integration:bridge:cli` to `packages/frontend-sdk/package.json`
- [ ] Document in `packages/frontend-sdk/src/integration/__tests__/README.md`

---

## Implementation notes

### `--no-tty` implementation

In `main()`, the `--console --server` branch currently does:

```python
try:
    run_terminal(logger=console_logger, app_instance=terminal_app)
finally:
    uvicorn_server.should_exit = True
    thread.join()
```

With `--no-tty`, replace `run_terminal(...)` with a blocking wait:

```python
if args.no_tty:
    # Non-interactive: block until SIGINT/SIGTERM, then clean up.
    stop_event = threading.Event()
    import signal
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    stop_event.wait()
else:
    run_terminal(logger=console_logger, app_instance=terminal_app)
```

The `--console` only branch:

```python
if args.no_tty:
    print("[agent_terminal_app] --no-tty with --console only has nothing to do without --server.")
    return
run_terminal(...)
```

### Python subprocess test harness

Reuse patterns from `test_binary_distribution_bundle_e2e_ollama.py`:

```python
def _reserve_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]

def _wait_for_server(base_url: str, process: subprocess.Popen) -> None:
    # Poll GET /api/hello until it responds
    ...

def _pythonpath_env() -> dict[str, str]:
    return {"PYTHONPATH": os.pathsep.join([
        str(ROOT / "core" / "python"),
        str(ROOT / "application" / "python"),
    ])}
```

Launch the CLI:

```python
server = subprocess.Popen(
    [python, "-m", "agent_terminal_app", "--server",
     "--host", "127.0.0.1", "--port", str(port)],
    cwd=str(workspace),
    env={**os.environ, "HOME": str(tmp_path / "home"),
         **_pythonpath_env()},
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
)
```

### Docker Bonjour test

The `docker-compose.yml` uses a custom network so mDNS multicast works
between containers.  The `server` service runs the CLI from source via
volume mount; the `discoverer` service runs a Python script that uses
`zeroconf.ServiceBrowser` to find `_http._tcp` services and prints them
as JSON.

The test:
1. Starts the compose stack (`docker-compose up -d`)
2. Waits for the server to be ready (polls `/api/hello` via port mapping)
3. Runs `docker-compose exec discoverer python /discover.py`
4. Parses the JSON output
5. Asserts the service name and port match
6. Tears down (`docker-compose down --remove-orphans -v`)

### Bridge E2E with real CLI

The existing `bridge.e2e.integration.test.ts` uses `startBackendServer()`
which spawns `scripts/run_backend_server_for_ts_integration_tests.py`
(a custom runner that bypasses `__main__.py`).  The new
`startBackendViaCLI()` function spawns the real CLI instead:

```typescript
export async function startBackendViaCLI(options: {
  bridgeUrl: string;
  serverId?: string;
  displayName?: string;
  cwd?: string;
  port?: number;
  startupTimeoutMs?: number;
}): Promise<StartedServer> {
  // Spawn: python -m agent_terminal_app --server --no-tty
  //   --enable-bridge --bridge-url <url>
  //   --host 127.0.0.1 --port <port>
  // Capture stdout for pairing codes and summary.
  // Poll /api/hello for readiness.
  // Return { baseUrl, port, stdout, stop }.
}
```

The test uses `startBridgeDocker()` for the bridge and
`startBackendViaCLI()` for the CLI, then connects via `BridgeTransport`
and verifies the full pairing + proxied request flow.

### Key files to create/modify

| File | Action |
|---|---|
| `application/python/agent_terminal_app/__main__.py` | Add `--no-tty` flag, modify console launch paths |
| `application/python/tests/test_cli_e2e.py` | New: Python subprocess integration tests |
| `application/python/tests/test_cli_bonjour_docker.py` | New: Docker Bonjour discovery test |
| `application/python/tests/fixtures/bonjour-docker/docker-compose.yml` | New: Docker compose for Bonjour test |
| `application/python/tests/fixtures/bonjour-docker/discover.py` | New: mDNS discovery script for Docker |
| `packages/frontend-sdk/src/integration/harness.ts` | Add `startBackendViaCLI()` function |
| `packages/frontend-sdk/src/integration/__tests__/bridge.cli.e2e.integration.test.ts` | New: Bridge E2E with real CLI |
| `packages/frontend-sdk/package.json` | Add `integration:bridge:cli` script |
| `packages/frontend-sdk/src/integration/__tests__/README.md` | Document new test |
| `application/python/README.md` | Document `--no-tty` flag |

### Markers and gating

- Python tests: `pytest.mark.integration` (excluded from default `pytest` run, run via `pytest -m integration`)
- Docker tests: `pytest.mark.integration` + `pytest.mark.docker` (run via `pytest -m 'integration and docker'`)
- TS tests: excluded from default `npm test`, run via dedicated npm script (`npm run integration:bridge:cli`)

### Validation

```bash
# Python integration tests (no Docker needed)
pytest application/python/tests/test_cli_e2e.py -m integration -v

# Docker Bonjour test
pytest application/python/tests/test_cli_bonjour_docker.py -m 'integration and docker' -v

# Bridge E2E with real CLI
cd packages/frontend-sdk && npm run integration:bridge:cli

# Lint + format
ruff check application/python/agent_terminal_app/__main__.py application/python/tests/test_cli_e2e.py application/python/tests/test_cli_bonjour_docker.py
black application/python/agent_terminal_app/__main__.py application/python/tests/test_cli_e2e.py application/python/tests/test_cli_bonjour_docker.py
pyright

# Existing tests still pass
pytest application/python/tests/test_cli_environment_isolation.py application/python/tests/test_project_profile.py -v
```