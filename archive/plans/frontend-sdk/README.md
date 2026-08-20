# Frontend SDK extraction plan

This plan proposes extracting shared “business logic” from the existing React Native client (`mobile/crystal-lattice-control-rn/`) into a reusable TypeScript SDK package named `@crystal-lattice/frontend-sdk` (and an optional React binding package `@crystal-lattice/frontend-sdk-react`).

The goal is to enable multiple frontends (mobile RN, desktop RN macOS, VS Code extension, future web UI, etc.) to share:

- Backend API semantics (sessions/messages/events/plugins/actions)
- Connection/adapters (direct HTTP and bridge)
- Headless controllers/state machines (chat + sessions + plugins)
- Common domain types (messages, events, UI schema)

…while keeping each frontend implementation mostly “representation + platform glue”.

This plan also explicitly keeps the door open for an **in-process backend** in some frontends (e.g. VS Code extension) that calls a future TypeScript version of `agent_core`/`agent_app` directly, instead of using the Python REST API.

## Deliverables

- `packages/frontend-sdk/` → `@crystal-lattice/frontend-sdk` (no React, no React Native imports)
- `packages/frontend-sdk-react/` → `@crystal-lattice/frontend-sdk-react` (optional; React hooks/adapters)
- `desktop/` directory containing a macOS React Native frontend (initially can reuse mobile UI)
- Mobile RN app updated to depend on the SDK and become “thin UI”

## Documents

- `plans/frontend-sdk/01-goals-and-non-goals.md`
- `plans/frontend-sdk/02-proposed-interfaces.md`
- `plans/frontend-sdk/03-extraction-map.md`
- `plans/frontend-sdk/04-migration-phases.md`
- `plans/frontend-sdk/05-terminal-and-vscode-alignment.md`
- `plans/frontend-sdk/06-sdk-module-structure.md`
- `plans/frontend-sdk/07-example-usage.md`
- `plans/frontend-sdk/08-ui-representation-boundaries.md`
- `plans/frontend-sdk/09-chat-persistence-scroll-and-reconcile.md`
- `plans/frontend-sdk/proposed-interfaces.ts`

## License

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
