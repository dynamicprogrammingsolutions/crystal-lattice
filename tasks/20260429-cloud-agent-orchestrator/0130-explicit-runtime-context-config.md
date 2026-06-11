# Explicit Runtime Context Config
Make the default cloud runtime Docker build explicit in config, including the
Dockerfile, runtime entrypoint, and staged build context inputs.

## Requirements checklist

- [x] Add explicit `application.cloud_agent.container_profiles.default-runtime`
  to the canonical default config.
- [x] Support list-mode `container_profiles.<id>.context` entries with
  `{source, target}` staging.
- [x] Add a single dynamic runtime env anchor,
  `CLOUD_RUNTIME_BUILD_CONTEXT`, for generated or bundled runtime context
  directories.
- [x] Keep Dockerfile and `runtime.py` references explicit through
  `${env:BUILTIN_PLUGINS}` in default config.
- [x] Remove hidden plugin injection of the default container profile.
- [x] Materialize source-layout cloud runtime context from the active config
  before cloud start/validation uses `CLOUD_RUNTIME_BUILD_CONTEXT`.
- [x] Make the default Dockerfile extension-friendly by naming its final stage
  `cloud-agent-runtime`.
- [x] Update custom runtime guidance to recommend copying the default
  Dockerfile and appending a project stage such as
  `FROM cloud-agent-runtime AS project-runtime`.
- [x] Slim `cloud_script_author_codex_message` so detailed instructions live in
  the authoring guide.
- [x] Remove obsolete `application/python/agent_terminal_app/default_config.json`
  and update live references/tests to the canonical
  `application/python/agent_terminal_app/default_config/config.json`.
- [x] Verify source, bundled, Docker validation, and real API cloud-script
  author behavior.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`

Depends On: `tasks/20260429-cloud-agent-orchestrator/0124-dockerfile-container-profiles.md`

## Background

The Dockerfile container profile work moved runtime Dockerfile ownership into
the cloud-agent plugin and added Dockerfile-mode staging. The remaining cleanup
is to make the default runtime build understandable from config rather than
hidden in plugin default-injection logic.

Current generated default runtime build contexts contain:

- `Dockerfile`
- `runtime.py`
- `python_lib/`
- `cloud-runtime-plugin-bundle/`
- `plugin_sources/`

The context is assembled by
`scripts/build_crystal_lattice_binary.py:320-355`. That function copies the
plugin-owned `Dockerfile` and `runtime.py`, stages `python_lib`, builds
`cloud-runtime-plugin-bundle`, and copies selected local plugin sources.

The plugin-owned default runtime Dockerfile currently expects those top-level
paths. See
`plugins/cloud-agent-app/src/cloud_agent_app/bundled_runtime/python/Dockerfile:38-59`:
it copies `plugin_sources`, `cloud-runtime-plugin-bundle`, `python_lib`, and
`runtime.py`.

Current container staging only accepts a directory-style `context`; it copies
the directory contents and then applies `build_assets`. See
`plugins/cloud-agent-app/src/cloud_agent_app/cloud_agent_container.py:24-74`.
That is too coarse for the default runtime because the default context is a
composition of static plugin assets and generated runtime inputs.

Current plugin init hides the default runtime profile in
`plugins/cloud-agent-app/src/cloud_agent_app/cloud_agent_app_plugin.py:108-169`.
This task should remove that hidden profile creation and make the default come
from canonical config instead.

Runtime config placeholder resolution already supports application-provided env
overrides. `RuntimeLayout.env_overrides()` currently contributes
`BUILTIN_PLUGINS` in
`application/python/agent_terminal_app/runtime_layout.py:74-86`, and
`build_config_resolution_env()` applies env overrides after process env in
`core/python/agent_app/config.py:34-59`.

## Target Default Config

Add this profile under `application.cloud_agent` in
`application/python/agent_terminal_app/default_config/config.json`:

```json
{
  "default_container_profile": "default-runtime",
  "container_profiles": {
    "default-runtime": {
      "label": "Default Crystal Lattice cloud agent runtime",
      "mode": "dockerfile",
      "image": "cloud-agent-runtime:latest",
      "dockerfile": "Dockerfile",
      "context": [
        {
          "source": "${env:BUILTIN_PLUGINS}/cloud-agent-app/src/cloud_agent_app/bundled_runtime/python/Dockerfile",
          "target": "Dockerfile"
        },
        {
          "source": "${env:BUILTIN_PLUGINS}/cloud-agent-app/src/cloud_agent_app/bundled_runtime/python/runtime.py",
          "target": "runtime.py"
        },
        {
          "source": "${env:CLOUD_RUNTIME_BUILD_CONTEXT}/python_lib",
          "target": "python_lib"
        },
        {
          "source": "${env:CLOUD_RUNTIME_BUILD_CONTEXT}/cloud-runtime-plugin-bundle",
          "target": "cloud-runtime-plugin-bundle"
        },
        {
          "source": "${env:CLOUD_RUNTIME_BUILD_CONTEXT}/plugin_sources",
          "target": "plugin_sources"
        }
      ]
    }
  }
}
```

`dockerfile` is the staged relative Dockerfile path. The first context entry
copies the plugin-owned Dockerfile into that staged path.

## Context Schema

Keep the existing directory-style context shape:

```json
{
  "dockerfile": ".cloud-agent/runtime/Dockerfile",
  "context": ".cloud-agent/runtime"
}
```

Add list-mode context:

```json
{
  "dockerfile": "Dockerfile",
  "context": [
    {
      "source": ".cloud-agent/runtime/Dockerfile",
      "target": "Dockerfile"
    },
    {
      "source": "package.json",
      "target": "assets/package.json"
    }
  ]
}
```

Rules:

- `source` follows the normal env-placeholder and relative path rules.
- `target` is a safe relative path inside the staged Docker build context.
- entries may be files or directories.
- entries are copied in order into an empty staged context.
- the staged context, Dockerfile path, target, and build args are included in
  the digest.
- `build_assets` may remain as supplemental staged entries for compatibility,
  but new multi-root examples should prefer list-mode `context`.

## Runtime Context Env

Add only one new dynamic env anchor:

```text
CLOUD_RUNTIME_BUILD_CONTEXT
```

For bundled/PyInstaller layouts, it should point at the packaged
`cloud_runtime` context root from the runtime layout. For source layout, it
should point at a generated context directory under `build/`, materialized
before cloud start or local validation stages the Dockerfile context.

Do not add separate env vars for Dockerfile or `runtime.py`; those should be
direct `${env:BUILTIN_PLUGINS}` references.

## Dockerfile Cache Guidance

Change the default runtime Dockerfile final stage from:

```dockerfile
FROM runtime-base
```

to:

```dockerfile
FROM runtime-base AS cloud-agent-runtime
```

For custom runtimes, documentation should recommend copying the default
Dockerfile, preserving the default stages where possible, and appending a
project-specific final stage:

```dockerfile
FROM cloud-agent-runtime AS project-runtime

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        nodejs \
        npm && \
    rm -rf /var/lib/apt/lists/*
```

This keeps Docker build-cache reuse local to one Dockerfile and avoids relying
on a deployment-local image alias such as `cloud-agent-runtime:latest`.

## Execution plan

Added during task completion after user approval.

1. Replace the current draft default profile tweak with the full explicit
   `default-runtime` profile shown above in the canonical default config only.
2. Add `CLOUD_RUNTIME_BUILD_CONTEXT` to runtime-layout env overrides, deriving
   it from packaged `cloud_runtime` paths for bundled layouts and from a
   source-generated context path for source layouts.
3. Make source-layout cloud start/validation materialize the generated runtime
   context from the active `AgentApplication` config before staging container
   context entries.
4. Extend container profile resolution to accept `context` as either a string
   or a list of `{source, target}` entries, resolving env placeholders and
   relative paths for each source.
5. Extend build-context staging to support list-mode context entries, retain
   existing string-context behavior, and include staged entries in the digest.
6. Remove the cloud-agent plugin's hidden default runtime profile injection and
   update tests so missing container profiles fail clearly instead of being
   silently invented.
7. Rename the default Dockerfile final stage to `cloud-agent-runtime` and add
   cache-friendly custom-runtime docs/examples.
8. Slim `cloud_script_author_codex_message` to guide/example references plus
   minimal must-not-miss instructions; move detailed guidance into
   `cloud-script-authoring.md`.
9. Delete obsolete `application/python/agent_terminal_app/default_config.json`
   and update live tests/docs/package code that still reference it.
10. Run focused tests first, then Docker/bundled validation and the real API
    installed-bundle cloud-script-author scenarios.

## Completion Notes

Added during task completion and follow-up review.

- Focused fast validations were run for runtime-layout env wiring, default
  config assertions, runtime plugin-bundle staging, and cloud-agent plugin
  container/runtime behavior.
- Additional focused integration coverage was run for default-config effective
  agent configs, and targeted unit coverage was added for request-local source
  runtime-context materialization, sanitized orchestrator container payloads,
  and live Docker build output during local validation.
- Slow Docker-marked and hosted real-API validation suites were intentionally
  left to the separate follow-up runs already planned for this task family.

Follow-up continuation plan added during completion after review:

11. Add regression coverage proving the canonical default config and a
    project-level `.cloud-agent/cloud-agent.json` both support list-mode
    `container_profiles.<id>.context`.
12. Resolve list-mode `context` entries into `context_entries` in
    `cloud_agent_profiles.py`, keeping existing string-mode behavior.
13. Thread the active `AgentApplication` config path into source-layout cloud
    runtime context preparation instead of hardcoding the canonical default
    config path.
14. Remove `_with_plugin_defaults()` default container-profile injection and
    update tests/docs to require the explicit config-owned default runtime
    profile.
15. Re-run focused cloud-agent tests, Docker validation coverage, and the
    installed-bundle cloud-script-author E2E command.

## Verification targets

- `python -m json.tool application/python/agent_terminal_app/default_config/config.json`
- Runtime layout tests covering `CLOUD_RUNTIME_BUILD_CONTEXT`.
- Cloud profile resolver and staging tests for string context and list context.
- Default config effective integration test.
- Local Docker validation tests for the default runtime profile.
- Installed-bundle validation test.
- Real API installed-bundle cloud-script-author tests with saved ChatGPT auth.

## Completion Notes

Added during task completion.

Implemented:

- Canonical default config now declares `default-runtime` explicitly with
  list-mode context entries.
- `RuntimeLayout.env_overrides()` now exposes `CLOUD_RUNTIME_BUILD_CONTEXT`.
- Container profile resolution and staging now support `context` as either a
  directory string or a list of `{source, target}` entries.
- Hidden cloud-agent plugin default container profile injection was removed.
- Source-layout runtime context materialization now happens when a Dockerfile
  profile references `CLOUD_RUNTIME_BUILD_CONTEXT`, using the active
  `AgentApplication` config path.
- The default runtime Dockerfile final stage is now named
  `cloud-agent-runtime`.
- Authoring docs now recommend copying the default Dockerfile and appending a
  project stage such as `FROM cloud-agent-runtime AS project-runtime` for
  cache-friendly custom runtimes.
- The cloud-script-author developer message was reduced to guide/example
  references and minimal must-not-miss instructions.
- Obsolete `application/python/agent_terminal_app/default_config.json` was
  deleted.
- The installed-bundle real API authoring test now emits a live trace during
  `/events` polling: it prints the first user message, assistant reasoning,
  assistant content, and tool progress counts (`sent` / `completed`) while
  suppressing tool payload output. It also prints a `[validate-cloud] starting`
  phase marker before the post-authoring validation command.
- Runtime context sanitization now excludes `.plugin_cache`, `.venv`,
  `.crystal`, and `auth`. This fixed a local generated context that had grown
  to about 2.6 GiB because `python_lib/agent_terminal_app/.plugin_cache` was
  copied into the Docker build context; after the fix, the same generated
  context was about 18 MiB.
- The slow optional-plugin install test in
  `application/python/tests/test_cloud_runtime_plugin_bundle_builder.py` was
  switched from `message-export-actions` to a tiny fixture application plugin
  under `application/python/tests/fixtures/optional_plugins/_test-small-app`
  that depends only on `tomli-w`. The frozen bundled-archive rejection test was
  switched to `gemini-compaction-feature`.

Verification completed:

- `python -m json.tool application/python/agent_terminal_app/default_config/config.json`
- `python -m py_compile` for touched runtime/plugin modules and the installed
  bundle real API test file.
- `PYTHONPATH=core/python:application/python:plugins/cloud-agent-app/src pytest application/python/tests/test_cloud_script_author_prompt.py plugins/cloud-agent-app/tests/test_cloud_script_authoring_docs.py application/python/tests/test_runtime_layout.py application/python/tests/test_cloud_runtime_plugin_bundle_builder.py::test_cloud_runtime_context_sanitizer_excludes_private_generated_state -q`
  passed (`13 passed`).
- `PYTHONPATH=core/python:application/python:plugins/cloud-agent-app/src pytest application/python/tests/test_cloud_runtime_plugin_bundle_builder.py -q`
  passed (`6 passed`).
- `PYTHONPATH=core/python:application/python:plugins/cloud-agent-app/src pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q`
  passed (`46 passed`).
- `PYTHONPATH=core/python:application/python:plugins/cloud-agent-app/src pytest application/python/tests/test_default_config_effective_agent_configs.py -q -m integration`
  passed once after the default config changes (`1 passed`). Later reruns timed
  out while reinstalling/downloading `feature-web-context` dependencies, not in
  cloud profile resolution.
- Source runtime context preparation completed:
  `PYTHONPATH=core/python:application/python:plugins/cloud-agent-app/src python scripts/prepare_cloud_runtime_build_context.py --output tmp/explicit-runtime-context-check --config application/python/agent_terminal_app/default_config/config.json`.
- `CRYSTAL_LATTICE_BUNDLE_ARCHIVE=dist/crystal-lattice/crystal-lattice-cli-v0.1.0-darwin-arm64.tar.gz PYTHONPATH=core/python:application/python:plugins/cloud-agent-app/src pytest application/python/tests/test_binary_distribution_optional_plugin_install.py -q -m integration`
  passed (`1 passed`).
- `RUN_CLOUD_SCRIPT_AUTHOR_BUNDLE_E2E=1 CHATGPT_CREDENTIALS=$HOME/.crystal/auth/chatgpt-auth.json CLOUD_SCRIPT_AUTHOR_NO_PROGRESS_TIMEOUT=420 CRYSTAL_LATTICE_BUNDLE_ARCHIVE=tmp/crystal-lattice-python-runtime-v0.1.0-darwin-arm64-current.tar.gz PYTHONPATH=core/python:application/python:plugins/cloud-agent-app/src pytest application/python/tests/test_cloud_script_author_installed_bundle_real_api.py::test_installed_bundle_cloud_script_author_generates_valid_hooks -s -m 'integration and api and docker'`
  passed (`1 passed in 464.22s`) and showed the intended live authoring trace.
- `git diff --check` passed.

Verification not completed in this stage:

- `application/python/tests/test_cloud_validation_command_docker.py -m 'integration and docker'`
  did not complete within the 10-minute tool window. Before the sanitizer fix,
  the generated Docker context transferred about 2.6 GiB. After the sanitizer
  fix, Docker context transfer was about 17 MiB, but the build still exceeded
  the tool window because the Ubuntu apt mirror was downloading packages at
  roughly tens of KiB/s.
- Full `application/python/tests/test_cloud_runtime_plugin_bundle_builder.py`
  also exceeded the 10-minute tool window; the new focused sanitizer regression
  test passed.
- Installed-bundle validation and real API cloud-script-author scenarios were
  not rerun after this implementation and remain the open verification follow-up.

Follow-up implementation update:

- `cloud_agent_profiles.py` now resolves Dockerfile-mode `context` as either a
  directory string or a list of resolved `context_entries`.
- `cloud_agent_app_plugin.py` now requires explicit config-owned container
  profiles and no longer injects `default-runtime` behind the scenes.
- Source-layout runtime context preparation now threads the active
  `AgentApplication` config path into
  `prepare_source_cloud_runtime_build_context(...)` when container sources
  reference `CLOUD_RUNTIME_BUILD_CONTEXT`.
- Focused plugin/application tests now cover list-mode context resolution, the
  explicit container-profile requirement, and active-config runtime-context
  preparation.

Follow-up verification update:

- `pytest plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py -q`
  passed (`45 passed`).
- `pytest application/python/tests/test_runtime_layout.py application/python/tests/test_cloud_script_author_prompt.py application/python/tests/test_default_config_effective_agent_configs.py -q`
  passed (`7 passed, 1 deselected`).
- Rebuilt bundled runtime archive with
  `python scripts/build_crystal_lattice_python_runtime_package.py`, producing
  `dist/crystal-lattice-python-runtime/crystal-lattice-python-runtime-v0.1.0-darwin-arm64.tar.gz`.
- The installed-bundle cloud-script-author E2E no longer fails at startup with
  `application.cloud_agent.container_profiles.<id>.context must be a non-empty string`.
- The installed-bundle cloud-script-author E2E still remains open because the
  request later timed out on "no observable progress" after startup.