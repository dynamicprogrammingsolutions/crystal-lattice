# Config-Driven Packaging Plugin Discovery
Clean up packaging-time plugin discovery so the binary build, Python runtime
package build, and cloud runtime bundle build all use the real config loader
instead of raw JSON string heuristics.

## Requirements checklist

- [x] Move packaging-time plugin discovery onto `agent_app.config` resolved
  config helpers instead of scanning raw JSON strings.
- [x] Remove the binary build's dependency on the cloud-runtime bundle script
  by introducing a neutral packaging helper layer.
- [x] Make the binary build, Python runtime package build, and cloud runtime
  bundle build share the same built-in plugin selection and resource discovery
  logic.
- [x] Use structural `plugins` lists as the only source of truth for selected
  built-in plugins; do not treat arbitrary JSON strings or disabled specs as
  selected plugins.
- [x] Classify built-in plugins by resolved path under `BUILTIN_PLUGINS` so
  equivalent `path:`, `bash:`, alternate env-var, and absolute-path forms
  resolve consistently.
- [x] Apply exact-match cloud disabled-plugin pruning before computing cloud
  runtime build plugin closure when disabled specs are supplied.
- [x] Add regression tests covering default-config selection, disabled-plugin
  false-positive avoidance, alternate built-in spec forms, and packaged script
  inclusion.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/0130-explicit-runtime-context-config.md`

## Background

Current packaging-time plugin discovery is split across three scripts:

- `scripts/build_crystal_lattice_binary.py`
- `scripts/build_crystal_lattice_python_runtime_package.py`
- `scripts/build_cloud_runtime_plugin_bundle.py`

The dependency direction is currently wrong: the binary build imports generic
staging and plugin-selection helpers from the cloud-runtime bundle script.
That makes the earlier binary build depend on a later cloud-specific build
layer.

The current discovery heuristic in
`scripts/build_cloud_runtime_plugin_bundle.py` scans every JSON string and
treats any `path:${env:BUILTIN_PLUGINS}/...` value as a selected built-in
plugin. That is incorrect because:

- it does not read actual structural `plugins` lists;
- it ignores the real config loader and env-resolution rules;
- it does not treat equivalent path forms the same way;
- it can treat strings inside `disabled_plugins` as positive selections.

That bug surfaced when a disabled spec such as
`{"$raw": "path:${env:BUILTIN_PLUGINS}/message-export-actions"}`
caused `message-export-actions` to reappear in the source cloud runtime build
context even though it was not enabled by the selected plugin lists.

The cleanup should make packaging-time selection use the real config module for:

- loading raw config;
- resolving env placeholders;
- resolving mixins;
- structurally collecting declared plugin specs;
- exact-match pruning of disabled plugin specs where cloud-runtime packaging
  explicitly requests it.

## Execution plan

Added during task completion after user approval.

1. Extend `core/python/agent_app/config.py` with helpers that load a resolved
   config from disk, iterate structural plugin specs, iterate string leaves,
   and prune declared plugin specs by exact string equality.
2. Add a neutral script helper module for packaging-time plugin analysis and
   staging, and move generic helpers there from the cloud-runtime-specific
   script.
3. Change the binary build, Python runtime package build, and cloud runtime
   bundle build to import the neutral helper instead of depending on one
   another for plugin discovery.
4. Replace raw JSON string scanning with config-driven built-in plugin
   discovery based on structural plugin lists plus resolved-path classification
   under `BUILTIN_PLUGINS`.
5. Keep built-in resource discovery separate from plugin selection, but make it
   operate on resolved config values rather than `${env:BUILTIN_PLUGINS}`
   regexes in raw JSON.
6. Thread optional cloud disabled-plugin specs into source runtime build
   analysis so cloud-runtime packaging can prune selected built-in plugins
   before computing `bundled_plugins`, `local-projects.txt`, and
   `plugin_sources`.
7. Update packaging and cloud-runtime tests to cover the new source of truth
   and verify the packaged helper scripts are still included where needed.

## Completion Notes

Added during task completion.

- Added shared config-resolution helpers in `core/python/agent_app/config.py`
  for loading a resolved config from disk, structurally collecting declared
  plugin specs, iterating string leaves, and pruning plugin specs by exact
  string equality.
- Added `scripts/build_plugin_packaging_support.py` as the neutral packaging
  helper layer. The binary build, cloud runtime bundle builder, and bundled
  Python runtime package builder now all depend on that shared module instead
  of depending on one another for plugin discovery.
- Converted cloud runtime bundle discovery from raw `${env:BUILTIN_PLUGINS}`
  string scanning to structural plugin-list discovery plus resolved-path
  classification under the built-in plugins root.
- Kept resource discovery separate from plugin selection and made it operate on
  resolved config values while skipping `plugins` and `disabled_plugins`
  containers to avoid false positives from plugin specs.
- Threaded optional cloud disabled-plugin specs through source runtime context
  preparation so runtime packaging can prune the selected built-in closure
  before building `bundled_plugins` and `local-projects.txt`.
- Added regression coverage for:
  - structural plugin collection in the config module,
  - ignoring disabled raw strings as positive plugin selections,
  - equivalent built-in plugin path forms,
  - exact-match cloud disabled-plugin pruning in the cloud runtime bundle,
  - inclusion of the new shared helper script in source and bundled-Python
    packages.

Verification run during completion:

- `python -m py_compile` on the touched config, packaging, cloud runtime, and
  test modules
- `pytest core/python/tests/test_config_packaging_plugin_helpers.py application/python/tests/test_cloud_runtime_plugin_bundle_builder.py application/python/tests/test_python_runtime_package_builder.py application/python/tests/test_cloud_orchestrator_source_bundle.py -q`
- `pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q`