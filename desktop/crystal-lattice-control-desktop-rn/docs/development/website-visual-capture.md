# Website visual capture

The Desktop website-visual harness produces deterministic macOS source
candidates from production React Native components.

Run:

```bash
npm run capture:website-visual:macos
```

The command:

1. builds a Release app in an isolated derived-data directory;
2. launches `DesktopWebsiteVisualHarness` with one deterministic visual kind;
3. renders the production agent picker beside the production session-plugins
   window;
4. asks the harness app to cache and encode its own content view after React
   has rendered;
5. writes light/dark PNG candidates under
   `artifacts/website-visual/`.

The harness-owned view export avoids screen-recording permission and does not
use static website mocks.

Current kinds:

- `agent-codex`: ordered agent descriptors with Codex selected and
  Codex-specific tool plugins;
- `agent-claude`: the same picker with Claude selected and Claude-specific
  tool plugins.

The fixture plugin entries are capture-only data. They use the real
`SessionPluginEntry` shape and production plugin-window component, and are not
included in normal application defaults.

Stable agent IDs remain authoritative. Display title, description, and order
come from the public descriptor contract, while picker submission continues to
send only the stable ID.