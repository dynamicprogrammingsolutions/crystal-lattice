# Website visual capture

The Desktop website-visual harness produces deterministic macOS source
candidates from production React Native components.

## Session actions through the real backend

From the Desktop package:

```bash
PYTHON=/path/to/configured/python npm run capture:session-actions:macos
```

Use a Python environment with the local core/application dependencies installed.
The integration harness otherwise selects the repository `.venv` when present.
This focused command captures the Session actions scene in both themes using
one isolated backend and session. It:

1. loads `landing_page/visual_assets/runtime/session-actions/config.json`,
   including the actual title, generated-title, and summarization plugins;
2. creates the sample conversation through the public API using the
   production frontend SDK, without a provider request;
3. builds the current source in an isolated Debug derived-data directory;
4. starts the production `ChatPane` with `RestAgentBackend` and opens its
   actual native Session actions menu;
5. verifies the contributed rows and records their native frames;
6. exports named window/popover PNG and geometry attachments with
   `xcresulttool`, then stops the backend and the capture instance it started.

Outputs are under `artifacts/website-session-actions/`: `contract.json`,
`light-window.png`, `light-popover.png`, `light-geometry.json`, and matching
dark files, plus the native result bundle. The contract retains the actual
schema, configuration excerpt, and source fingerprints. A lock prevents
concurrent runs of this producer. It does not clear other capture directories.

The command overrides `CLC_APP_BUNDLE_IDENTIFIER` with the dedicated
`com.dynamicprogrammingsolutions.crystallatticecontrol.website-capture`
identity. Ordinary builds retain their existing release identity. Native
checks refuse to terminate an existing capture instance; teardown closes only
the instance started by that test. Run native UI automation sequentially.

The window and separately owned popover are exported independently with their
actual positions. The landing compositor combines those pixels without
capturing unrelated desktop windows. XCTest attachments avoid giving the
sandboxed test runner write permission to the source checkout. The visible
title is Crystal Lattice Desktop; harness identifiers remain accessibility
and test metadata.

Both capture roots use the deterministic capture theme, including the
separately mounted Actions popover. The native owner supplies its capture
appearance only when the website harness is enabled. The Debug harness uses
its freshly bundled JavaScript and does not connect to a resident Metro server.

## Plugin and report batch through HTTP and native UI

From the Desktop package:

```bash
PYTHON=/path/to/configured/python npm run capture:proof-batch:macos
```

This captures Session actions, Message actions, Session list, Compiled system
message, and the combined illustrative costs/ChatGPT report together. Install
the capture-only report package once from the repository root:

```bash
python -m pip install --no-deps -e landing_page/visual_assets/runtime/proof-batch/fixture-plugin
```

Use that Python interpreter for `PYTHON`. The producer uses the same
isolated Debug bundle identity and sequential XCTest automation as the focused
producer above. Keep the Mac unlocked while it runs; an OS lock blocks native
window automation. It leaves existing user app instances alone.

The maintained configs live under
`landing_page/visual_assets/runtime/proof-batch/`, with the first scene using
the existing `session-actions/config.json`. The producer starts four isolated
local backends, seeds sessions/messages and pin/status/title state through the
public API, and verifies the production SDK responses. Message relationships
retain the actual `$message.index` bindings. The production `SessionsPanel`
renders the list; pin/archive/status are its genuine star/bar controls.

Report actions run through `DesktopGlobalDisplayLayer`, which opens the real
`ActionDisplayWindow`. Separately mounted report windows receive the capture
theme only in the website harness. The compiled-message example resolves
`{{CODEX_DEFAULT_BEGINNING}}` from a pinned public Codex excerpt through the
feature's normal file variables. The capture-only application plugin under
`landing_page/visual_assets/runtime/proof-batch/fixture-plugin/` reads its
`reports.json` and renders three days of claude/zai costs, ChatGPT estimates,
and a weekly percentage change. Its two-decimal currency formatter belongs to
the fixture, not the production cost or authentication plugins.

The report configuration uses the deterministic Echo provider. It needs no
credentials or account journal and sends no inference request. The $550 weekly
equivalence is explicitly an illustrative screenshot assumption. Earlier real
cost-store/journal report sources remain retained alternatives.

Under `artifacts/website-proof-batch/`, each scene retains its public contract,
source fingerprints, both theme PNGs, and measured native geometry. Reports
also retain genuine 360px-wide content windows and the unobscured owning
conversation. XCTest attachments are exported only after the combined test
passes; partial failed captures do not become accepted input. The first scene
is also copied to the legacy `website-session-actions/` root so its existing
composition recipe can refresh the real icon.

The landing catalog processes these sources separately. Review the actual
homepage before promoting any visual or publishing. Fixtures can be refreshed
without accepting or publishing the generated images.

## Agent-picker view exports

Run:

```bash
npm run capture:website-visual:macos
```

The command:

1. builds a Release app in an isolated derived-data directory;
2. launches `DesktopWebsiteVisualHarness` with one deterministic visual kind;
3. renders the production two-pane agent picker and its selected-agent
   default-plugin preview;
4. asks the harness app to cache and encode its own content view after React
   has rendered;
5. writes light/dark PNG candidates under
   `artifacts/website-visual/`.

The harness-owned view export avoids screen-recording permission and does not
use static website mocks.

Capture roots use `buildDesktopCaptureTheme()` rather than the operator's
native accent. Light candidates use standard blue `#007AFF`; dark candidates
use `#0A84FF`. The override is used by
`DesktopWebsiteVisualHarness` and capture-mounted Actions popovers. Ordinary application roots and standalone
windows continue to use `useDesktopTheme()` and follow the macOS appearance
and accent. The producer passes `-clcWebsiteVisualTheme light|dark` explicitly;
the harness does not depend on asynchronous system appearance propagation
before exporting the view.

Current kinds:

- `agent-codex`: ordered agent descriptors with Codex selected and
  Codex-specific tool plugins;
- `agent-claude`: the same picker with Claude selected and Claude-specific
  tool plugins.

The fixture plugin entries are capture-only data. They use the real
`AgentPluginEntry` contract and production picker component, and are not
included in normal application defaults.

Stable agent IDs remain authoritative. Display title, description, and order
come from the public descriptor contract, while picker submission continues to
send only the stable ID. The capture harness supplies a deterministic
in-process backend; ordinary windows use the active REST, bridge, or in-process
connection backend through `agentPickerCoordinator`.

The compact picker capture uses a centered 1000 × 700 content area and the
optional `compactPluginPreview` spacing. Its default is false in ordinary
picker windows. This changes capture presentation, not agent metadata or
plugin availability.
