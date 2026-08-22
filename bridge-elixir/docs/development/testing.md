# Bridge service testing

## Test ownership

Use the smallest boundary that can observe the behavior:

| Boundary | Owns |
| --- | --- |
| Elixir unit/route tests | Registries, pairing/session state, channel routing, credentials, transfer state, limits, cleanup, compression/edge configuration |
| Python adapter tests | Legacy/v2 local forwarding, raw bytes, headers, task tracking, cancellation |
| Frontend SDK unit tests | Mode factory, URL derivation, exact routing, parsing, timeouts, no fallback |
| SDK bridge E2E | Real SDK → Elixir → Python → FastAPI behavior |
| Two-node bridge E2E | No-affinity registration, pairing, and raw transfer |
| Hosted edge E2E | TLS edge, real WebSocket/HTTP forwarding, gzip, HTTP/2 configuration |
| Native mobile tests | Mode selection, saved/default behavior, and rollback |

Do not duplicate the full large-payload matrix in Elixir, Python, SDK, and
mobile tests. State-machine failure cases belong in focused tests; one
production-adapter E2E proves the assembled path.

## Elixir suite

```bash
cd bridge-elixir
mix test
```

The suite covers:

- server registration, replication messages, takeover, rejection, and PID
  cleanup;
- pairing code shape, success, invalid attempts, cancellation, and signed
  credential validation;
- legacy session/resume and concurrent full/chunked request handling;
- HTTP v1 capability, pairing, raw request/response, transfer credentials,
  timeout, and response byte limit;
- CloudFront and HAProxy edge settings.

## Two-node integration

```bash
cd bridge-elixir
./run-integration-tests.sh
```

The runner starts or reuses the Docker/HAProxy cluster, then runs:

- legacy server registration, cluster-visible discovery, pairing, and resume;
- HTTP pairing through HAProxy;
- a 1.2 MB raw request and 900 KB raw response;
- HAProxy log assertions proving that one transfer's proxy, request download,
  and response upload span both bridge nodes.

Use `make docker-down` after manual runs.

## Frontend SDK E2E

From the repository root:

```bash
npm --workspace @crystal-lattice/frontend-sdk run integration:bridge
```

Docker mode covers five production-adapter cases:

- legacy large request/response;
- HTTP-only large JSON, raw binary, gzip, token resume, and events;
- hybrid normal HTTP plus event-only WebSocket routing;
- bridge restart/recovery;
- legacy concurrent slow/fast requests.

Optional AWS scripts and external mode are documented in
`packages/frontend-sdk/src/integration/__tests__/README.md`.

## Focused package suites

```bash
pytest application/python/tests/test_bridge_client_chunked_http.py \
  application/python/tests/test_bridge_client_local_request.py \
  application/python/tests/test_bridge_client_http_transfer.py -q

npm --workspace @crystal-lattice/frontend-sdk test

npm --workspace crystal-lattice-control-rn test
```

Use the mobile package's Detox bridge-transport scripts for both supported
simulators when bridge connection UI or persistence changes.

## Focused safety coverage

The opt-in baseline combines broad E2E evidence with deterministic state tests
that E2E cannot reliably inspect:

- atomic active-transfer saturation;
- request byte limits;
- frontend/server/request-consumer/response-uploader loss;
- complete token/server/direction/expiry mismatch cases;
- Python cancellation during each I/O phase and task-map cleanup;
- complete saved mobile mode/token reconstruction.

Physical-device network checks and a bounded load/soak run are required only
before a separately approved permanent default switch.
