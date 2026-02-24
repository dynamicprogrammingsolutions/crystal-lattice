Update docs to describe the `multipartContent` core message key, per-type composer UI schema elements (`composer_attachment`), the empty-content rule, and the bridge JSON constraint.

## Step 1 — Prepare

1) Read task context:
- `tasks/20260215-multipart-upload/000-main.md`
- `tasks/20260215-multipart-upload/080-docs-and-compat.md`

2) Identify where message schemas and plugin UI schema are documented today:
- `TYPES_AND_PROTOCOLS.md`
- `docs/api/core-sdk.md` (and/or related docs under `docs/`)
- `core/python/agent_core/types.py` docstrings (for terminology)

3) Review any server/API docs that mention message append payloads:
- `application/python/agent_terminal_app/server_endpoints_parity.md` (optional)

4) Share a plan with the user listing:
- Which docs you will update
- The exact additions (message schema, UI schema element schema, constraints)

Do not change docs yet.

## Step 2 — Complete (after user approval)

1) Update docs with the finalized contract.

2) Ensure examples are minimal and avoid over-specifying part schemas (core remains extensible).
