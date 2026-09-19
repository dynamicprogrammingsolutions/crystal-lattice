# TG-05: FastAPI multi-consumer query capability

## Project

- Base repository: FastAPI CRUD Async
- Base revision: `4fa7ae952ece61e228135285de1b6a5ff65a1dc8`
- Kind: public API plus independently maintained first-party consumers

## Purpose

Test when technical component and layer boundaries are justified. The fixture
contains a public service, a reusable Python client package, and a CLI
application with distinct compatibility and ownership boundaries.

## Derived starting state

The fixed fixture adds:

- a small `notes_client` package that consumes the existing collection API;
- a `notes` CLI using that package;
- contract fixtures shared only for current note-object behavior.

The new advanced query capability is absent.

## Natural request

> Add one supported notes-query capability across the public API, reusable
> Python client, and CLI. It must support bounded pagination, stable sorting,
> and optional text filtering while preserving current unparameterized API and
> client behavior. The public contract must be stable before consumers rely on
> it, and the CLI must prove the production client-to-service path. Plan the
> work and create the appropriate task structure without implementing it.

The prompt describes ownership and independent consumers but does not prescribe
subtasks or task count.

## Approved outcomes

- `QUERY-1`: one approved public query contract defines filter, sort,
  pagination, validation, response compatibility, and total count.
- `QUERY-2`: the FastAPI service implements and verifies the contract through
  production HTTP and real storage behavior.
- `QUERY-3`: the reusable Python client exposes the query capability without
  leaking transport details and preserves current calls.
- `QUERY-4`: the CLI exposes the supported query behavior and proves the real
  CLI → client package → HTTP service crossing.
- `QUERY-5`: public API, client package, and CLI documentation describe only
  behavior available in their respective delivery.

## Reviewed coherent partition

```text
010: Approve and publish the shared query contract
020: Deliver the FastAPI service capability
030: Deliver the reusable Python client capability
040: Deliver the CLI workflow and production integration
```

- `020` and `030` depend on `010` and may proceed independently against the
  approved contract.
- `040` depends on `020` and `030`.
- Each component owns its implementation, focused tests, compatibility, and
  documentation.

These technical boundaries are valid because every completed child has
independent consumers, ownership, compatibility, and acceptance.

## Acceptable alternatives

- Contract approval may remain in the parent when the contract is short and
  still has one clear maintained owner.
- Service and client may be one child only if the fixture gives them one owner
  and no independent release or compatibility boundary.
- A separate end-to-end child is justified only if production integration is
  an independently maintained deliverable rather than unfinished verification
  for the CLI slice.

## Fragmentation examples

Within the service capability, separate model, query, route, unit-test,
integration-test, documentation, and review tasks are phase fragmentation.
Within the SDK, transport, models, error mapping, tests, and docs remain one
package capability unless one is an independently published contract.

## Overpacking example

Combining service, reusable client, and CLI into one child hides separate
package ownership and compatibility and prevents independent delivery.

## Important crossings

- HTTP route to real storage behavior for query semantics.
- Python client transport to the production API.
- CLI through the actual client package and HTTP service.

## Semantic review questions

- Did the agent recognize valid component boundaries without splitting each
  component into phases?
- Are service and SDK independently usable before the CLI lands?
- Does the integration owner prove the real consumer path?