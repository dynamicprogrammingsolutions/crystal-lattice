# Test Real LLM Calls, Tool Calls, And Plugins

Validate that an installed release artifact can run a real LLM call, observe a tool call, load one custom user-side plugin, and enable one bundled plugin outside the default config closure.

## Requirements checklist

- [ ] Start from a clean binary install and clean user config/session directory.
- [ ] Configure one real provider API key.
- [ ] Run one real LLM request successfully.
- [ ] Observe at least one tool call.
- [ ] Install/enable a custom user-side plugin outside bundled plugins.
- [ ] Exercise the custom user-side plugin.
- [ ] Install/enable a bundled plugin that is not in the default config closure.
- [ ] Exercise the bundled non-default plugin.
- [ ] Confirm user plugin/cache state is outside the installed bundle.
- [ ] Confirm no behavior depends on source checkout paths.
- [ ] Record exact prompts, config snippets, commands, outputs, and UX notes.

Parent Task: `tasks/20260614-binary-release-e2e-manual-test/000-main.md`

Depends On:

- `tasks/20260614-binary-release-e2e-manual-test/010-define-manual-test-matrix.md`
- `tasks/20260614-binary-release-e2e-manual-test/050-test-release-artifacts-on-all-platforms.md`

## Context

The bundled-Python runtime package includes:

- a packaged Python runtime
- repo-shaped `core/python`
- repo-shaped `application/python`
- built-in plugin source trees under `plugins/`
- `preinstalled-plugins.json` for the default config plugin closure

Default-config plugin projects are installed into the packaged Python runtime during bundle creation. Other bundled plugin source trees should still be available for lazy installation when referenced by user config.

This task must prove both paths:

1. Default/preinstalled runtime behavior works.
2. Additional user/bundled plugin installation works after the binary has been installed.

## Clean Runtime Setup

Use test-owned paths. Do not rely on the developer's normal `~/.crystal` unless intentionally testing that default.

Suggested environment shape:

```bash
TEST_ROOT="$(mktemp -d)"
INSTALL_ROOT="$TEST_ROOT/opt/crystal-lattice-cli"
BIN_DIR="$TEST_ROOT/bin"
CRYSTAL_HOME="$TEST_ROOT/crystal-home"
mkdir -p "$CRYSTAL_HOME"
```

If the app supports explicit config/session flags or environment variables, use them and record the final command. If not, record exactly which default user paths are touched.

## Real LLM And Tool Call

Use the provider/API key chosen in `010-define-manual-test-matrix.md`.

Record:

```text
Provider:
Agent/config used:
API key variable or auth method:
Prompt:
Observed assistant response:
Observed tool call:
Where the tool call was visible:
```

The prompt should strongly request a task that needs a tool. Prefer a harmless file/list/read operation or another deterministic local tool selected by the final matrix.

## Custom User-Side Plugin

The custom plugin must not be loaded from the bundled `plugins/` directory and must not depend on the source checkout.

Recommended approach:

- create a tiny plugin in a temporary directory, or copy an existing test fixture into a temporary directory outside the repo
- reference it from user config with a `path:` plugin spec
- run the installed binary and exercise the plugin

Record:

```text
Custom plugin source path:
Config/plugin spec:
Install/cache location:
Action/tool/feature exercised:
Observed result:
```

## Bundled Non-Default Plugin

Use the bundled plugin selected in `010-define-manual-test-matrix.md`.

The test should prove that a bundled plugin not preinstalled by default can still be referenced from the installed bundle and used.

Record:

```text
Bundled plugin name:
Bundle source path:
Config/plugin spec:
Install/cache behavior:
Action/tool/feature exercised:
Observed result:
```

## Failure Modes To Watch

Record any of these explicitly:

- plugin install tries to use the system Python instead of packaged Python
- plugin source path points to the original repo checkout
- user plugin cache writes inside the immutable installed bundle
- tool call is hidden or impossible to confirm
- provider config requires undocumented manual edits
- default config includes placeholders that are confusing for a release user
