# Cloud Script Authoring Guide

This guide explains how to create project-local Crystal Lattice cloud-agent
hooks. It is written for coding agents and humans who need to make an existing
project work in a fresh cloud runtime.

Use this guide together with the project's normal `AGENTS.md`, README, package
files, and tests. The project guidance should tell you how a fresh checkout is
set up; this guide tells you where to put that setup for the cloud-agent flow.

## Default Goal

Prefer the standard repo-local hooks:

```text
.cloud-agent/local-stage
.cloud-agent/install-cloud
.cloud-agent/validate-cloud
```

Most projects should not need a custom `.cloud-agent/cloud-agent.json`. Add a
project config only when the standard transfer profiles cannot describe the
project, for example when the cloud workspace must be assembled from multiple
repositories or a generated source bundle.

## Script Rules

Every hook should be executable and should start with:

```bash
#!/usr/bin/env bash
set -euo pipefail
```

Keep hooks repeatable and idempotent. They may be run more than once during
local validation. Prefer explicit checks over silent best-effort behavior.

Do not print secrets. Do not commit `.env` files or generated credentials.

After writing or modifying hook, harness, or profile shell scripts, run
`chmod +x` on them before finishing.

## Authoring Workflow

Use this order when creating or changing cloud-agent hooks:

1. Read the project guidance and package/test files.
2. Read this guide.
3. Read the bundled default profile scripts as the baseline for the normal
   transfer/setup behavior.
4. Decide whether the standard hooks are enough, or whether the project needs a
   custom `.cloud-agent/cloud-agent.json` transfer profile or container profile.
5. Write the hooks and any project config.
6. Make generated shell scripts executable.
7. Run cheap local checks first: shell syntax checks, JSON validation, and a
   no-Docker local harness for custom transfer/setup behavior.
8. Run `crystal-lattice validate-cloud --workspace-dir /path/to/project` as the
   final acceptance check when Docker is available.

Inspect cloud-agent plugin source only when this guide is unclear or
incomplete. If source inspection was necessary, report what was missing from
the guide.

## Default Profile Baseline

The default profile scripts are the reference implementation for the normal
cloud-agent transfer flow. Read them before creating custom transfer profiles,
and use them as the baseline when writing only the simple project hooks.

In a normal installed or local runtime, the default scripts are copied into:

```text
${CONFIG_DIR}/cloud-agent/profiles
```

Important baseline scripts:

```text
${CONFIG_DIR}/cloud-agent/profiles/transfer_up/working-tree-current-state/local_transfer_script
${CONFIG_DIR}/cloud-agent/profiles/transfer_up/working-tree-current-state/cloud_setup_script
${CONFIG_DIR}/cloud-agent/profiles/transfer_up/clean-head/local_transfer_script
${CONFIG_DIR}/cloud-agent/profiles/transfer_up/clean-head/cloud_setup_script
${CONFIG_DIR}/cloud-agent/profiles/sync_down/working-tree-patch/cloud_export_script
${CONFIG_DIR}/cloud-agent/profiles/sync_down/working-tree-patch/local_apply_script
```

For ordinary projects, keep those default transfer/setup scripts and create only
the three project hooks:

```text
.cloud-agent/local-stage
.cloud-agent/install-cloud
.cloud-agent/validate-cloud
```

For multi-repository or otherwise non-standard transfers, copy the relevant
default profile script logic into project-local custom profile scripts and
change only the parts needed for the project layout. Do not invent transfer
semantics without comparing against the default scripts.

## Local Stage Hook

`.cloud-agent/local-stage` runs on the local machine before the normal transfer
script. Use it to copy local-only files into the transfer stage.

Important environment variables:

```text
LOCAL_WORKSPACE_DIR  local project directory
TRANSFER_STAGE_DIR   directory for extra staged files
TRANSFER_DIR         whole transfer bundle directory
WORKING_DIR          local working directory
SESSION_ID           validation or cloud session id
```

Common `.env` staging pattern:

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${LOCAL_WORKSPACE_DIR:?}"
: "${TRANSFER_STAGE_DIR:?}"

if [ -f "${LOCAL_WORKSPACE_DIR}/.env" ]; then
  mkdir -p "${TRANSFER_STAGE_DIR}"
  cp "${LOCAL_WORKSPACE_DIR}/.env" "${TRANSFER_STAGE_DIR}/.env"
fi
```

Only stage files the cloud setup or install hook actually needs.

Do not use `local-stage` to copy an entire secondary git repository. If the
project needs multiple git repositories in the cloud workspace, create a custom
transfer profile instead.

## Install Hook

`.cloud-agent/install-cloud` runs inside the cloud runtime after the workspace
has been materialized. Use it to install dependencies and prepare tools for the
project.

Important environment variables:

```text
CLOUD_WORKSPACE_DIR  cloud project workspace
TRANSFER_DIR         whole transfer bundle directory
WORKING_DIR          cloud working directory
SESSION_ID           validation or cloud session id
```

`TRANSFER_STAGE_DIR` is a local-stage-only variable. Do not reference it from
`install-cloud` or `validate-cloud`. With the standard transfer profiles, files
that `local-stage` writes into `TRANSFER_STAGE_DIR` are copied into the cloud
workspace root, so a staged `.env` should be checked as
`${CLOUD_WORKSPACE_DIR}/.env` or simply `.env` after `cd "${CLOUD_WORKSPACE_DIR}"`.

Python venv pattern:

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${CLOUD_WORKSPACE_DIR:?}"

cd "${CLOUD_WORKSPACE_DIR}"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Python requirements pattern:

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${CLOUD_WORKSPACE_DIR:?}"

cd "${CLOUD_WORKSPACE_DIR}"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

npm pattern, if the selected runtime image has Node.js and npm:

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${CLOUD_WORKSPACE_DIR:?}"

cd "${CLOUD_WORKSPACE_DIR}"
npm install
```

If a project needs tools that are not present in the default runtime image,
define or select an appropriate container profile instead of making hooks
silently skip required setup.

## Container Profiles

Most projects should start with the default runtime profile and put
project-specific dependency installation in `.cloud-agent/install-cloud`.
Create a project-local container profile only when the runtime image itself
needs to change, for example:

- required apt packages are large or slow to install on every session
- a tool such as Node.js, pnpm, system libraries, database clients, browser
  runtimes, or Ollama should be
  preinstalled in the image
- large mutable data such as model files should live on a mounted directory
- dependency directories such as `node_modules` should be shared between cloud
  instances instead of copied into Docker layers

Container profiles live in `.cloud-agent/cloud-agent.json` under
`container_profiles`. `default_container_profile` selects one. The canonical
Crystal Lattice default config declares the standard `default-runtime` profile
explicitly; project configs only need to add or select a different profile when
the project runtime should change.

Image mode selects a prebuilt image:

```json
{
  "default_container_profile": "project-runtime",
  "container_profiles": {
    "project-runtime": {
      "label": "Project runtime",
      "image": "project-cloud-agent-runtime:latest"
    }
  }
}
```

Dockerfile mode builds a profile-provided Dockerfile. `mode` is optional; if a
profile has `dockerfile`, the resolver treats it as Dockerfile mode. `context`
can be a directory path or an explicit list of build-context entries.

```json
{
  "default_container_profile": "project-runtime",
  "container_profiles": {
    "project-runtime": {
      "label": "Project runtime",
      "image": "project-cloud-agent-runtime:latest",
      "dockerfile": "Dockerfile",
      "context": [
        {
          "source": ".cloud-agent/runtime/Dockerfile",
          "target": "Dockerfile"
        },
        {
          "source": "package.json",
          "target": "assets/package.json"
        },
        {
          "source": "package-lock.json",
          "target": "assets/package-lock.json"
        }
      ],
      "cache_mounts": [
        {
          "id": "node-modules",
          "target": "/cloud-agent/instance/workspace/node_modules",
          "scope": "connection"
        }
      ],
      "mounts": [
        {
          "id": "ollama-models",
          "target": "/cloud-agent/cache/ollama",
          "scope": "profile"
        }
      ]
    }
  }
}
```

Path rules are the same as other cloud-agent config paths. Use explicit env
placeholders such as `${env:WORKING_DIR}/.cloud-agent/runtime/Dockerfile`, or
relative paths such as `.cloud-agent/runtime/Dockerfile` when the project config
file lives in the project. Relative paths resolve from the current project
directory during normal config compilation.

The Dockerfile build has a hard project boundary. The Docker build context
cannot use project files implicitly. The project workspace is mounted only when
the runtime container starts. If a Dockerfile needs project-specific build
inputs, declare them explicitly in `context` entries or `build_assets`; those
files or directories are copied into the sanitized build context and included in
the build digest.

For portable custom runtimes, copy the default Dockerfile and edit the copy. The
default Dockerfile lives at:

```text
${env:BUILTIN_PLUGINS}/cloud-agent-app/src/cloud_agent_app/bundled_runtime/python/Dockerfile
```

Keep the default stages intact when possible. The default final runtime stage is
named `cloud-agent-runtime`, so project additions can append a cache-friendly
final stage:

```dockerfile
FROM cloud-agent-runtime AS project-runtime

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        nodejs \
        npm && \
    rm -rf /var/lib/apt/lists/*
```

That stage name is local to the same Dockerfile, so Docker can reuse cached
default stages without relying on an external image alias. Do not write
`FROM cloud-agent-runtime:latest` unless the deployment explicitly guarantees
that image tag is available to the builder.

Good build assets are stable package manifests, lockfiles, tool config files,
or small patch directories. Avoid volatile generated files, large source trees,
cache directories, local databases, `.env` files, credentials, or any secret.
They are allowed by the parser because projects differ, but they will cause
unnecessary rebuilds, larger uploads, unsafe images, or secret exposure.

Use `cache_mounts` for dependency caches or install outputs that can be shared
between instances. Use `mounts` for large mutable data that should not be part
of an image layer, such as Ollama models. Keep normal project source as the
runtime workspace mount unless a small, stable file is explicitly needed at
image build time.

## Validation Hook

`.cloud-agent/validate-cloud` runs after transfer, setup, install, and the
built-in runtime smoke check. Use it to prove the cloud workspace is usable.

Validation should be fast, repeatable, and as deterministic as practical. Run
the smallest useful check that proves the project works in the cloud runtime.
Prefer cheap local tests first. If the project genuinely depends on credentials
or a remote service that is intentionally made available in the cloud runtime,
validation may include one small smoke check that proves the connection and the
expected basic behavior. Avoid broad, flaky, high-latency, or unnecessarily
expensive external validation.

Example for a Python project:

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${CLOUD_WORKSPACE_DIR:?}"

cd "${CLOUD_WORKSPACE_DIR}"
test -d .venv
. .venv/bin/activate
python -m unittest discover -s tests -q
```

Example that requires a staged `.env`:

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${CLOUD_WORKSPACE_DIR:?}"

cd "${CLOUD_WORKSPACE_DIR}"
test -f .env
test -d .venv
. .venv/bin/activate
python -m unittest discover -s tests -q
```

Example that intentionally proves a transferred credential works:

```bash
#!/usr/bin/env bash
set -euo pipefail

: "${CLOUD_WORKSPACE_DIR:?}"

cd "${CLOUD_WORKSPACE_DIR}"
test -f .env
test -d .venv
. .venv/bin/activate
pytest -o addopts='' tests/test_fast_local_smoke.py -q
pytest -o addopts='' tests/test_provider_smoke.py::test_basic_connection -q -m "integration and api"
```

In that pattern, keep the external smoke as narrow as possible. One request or
one read-only connectivity check is usually enough.

## Using Project Guidance

Read normal project guidance before writing hooks:

- `AGENTS.md`
- README files
- package manifests such as `pyproject.toml`, `requirements.txt`, or
  `package.json`
- existing test directories and scripts

Translate "fresh checkout setup" into `.cloud-agent/install-cloud`. Translate
"local env file required" into `.cloud-agent/local-stage`. Translate "basic
cloud validation proof" into `.cloud-agent/validate-cloud`.

Do not put cloud-specific instructions into the project's `AGENTS.md` just to
make the hooks work. The cloud contract belongs here and in the generated
`.cloud-agent` files.

## Advanced Transfer Profiles

Create `.cloud-agent/cloud-agent.json` only when the standard profile family is
not enough. Examples:

- the cloud workspace must combine multiple local git repositories
- generated files must be included before the normal transfer step
- a project needs a custom sync-down strategy

Project config can override the default profile ids and script paths. Keep the
small standard hooks when possible, and add custom transfer/setup scripts only
for the behavior that cannot be expressed by the defaults.

When selecting a custom transfer profile, make the selected sync-down profile
compatible too. Either define a matching custom sync-down profile, or override
`working-tree-patch` / `branch-import` with a `compatible_transfer_up_profiles`
list that includes the custom transfer profile id.

Minimal custom transfer profile shape:

```json
{
  "default_transfer_up_profile": "multi-repo-working-tree-current-state",
  "sync_down_profiles": {
    "working-tree-patch": {
      "compatible_transfer_up_profiles": [
        "working-tree-current-state",
        "multi-repo-working-tree-current-state"
      ]
    }
  },
  "transfer_up_profiles": {
    "multi-repo-working-tree-current-state": {
      "label": "Working tree current state with sibling repositories",
      "local_stage_script": ".cloud-agent/local-stage",
      "local_transfer_script": ".cloud-agent/profiles/transfer_up/multi-repo-working-tree-current-state/local_transfer_script",
      "cloud_setup_script": ".cloud-agent/profiles/transfer_up/multi-repo-working-tree-current-state/cloud_setup_script",
      "install_script": ".cloud-agent/install-cloud",
      "validation_script": ".cloud-agent/validate-cloud",
      "compatible_sync_down_profiles": ["working-tree-patch"]
    }
  }
}
```

The profile id and script paths can be project-specific. Keep script paths
relative to the project root when the config file lives at
`.cloud-agent/cloud-agent.json`.

When adding custom profile scripts, document:

- what each script expects as input
- which environment variables it reads
- what files it writes into `TRANSFER_DIR`, `TRANSFER_STAGE_DIR`, or
  `CLOUD_WORKSPACE_DIR`
- how `crystal-lattice validate-cloud` proves the custom path works

Custom `cloud_setup_script` runs with the current working directory set to the
cloud workspace. Do not remove that directory while the script is running
inside it. If a setup script needs to replace `CLOUD_WORKSPACE_DIR`, first
change directory to its parent or clone/materialize into a temporary sibling
and move it into place.

For sibling git repositories, base the custom transfer scripts on the bundled
`working-tree-current-state` profile:

- the local transfer script should use git to export each repository's
  committed `HEAD`
- it should also capture each repository's current working-tree changes,
  including uncommitted edits
- the cloud setup script should materialize the repositories at the sibling
  paths expected by the project, then apply the captured working-tree changes

Keep the normal `.cloud-agent/install-cloud` and `.cloud-agent/validate-cloud`
hooks focused on dependency installation and tests. The multi-repo checkout
layout belongs in the custom transfer profile.

## Fast Local Tests

Before running Docker validation, create and run a fast local harness when you
generate non-trivial hooks or a custom transfer profile. The harness should run
without Docker and should use temporary directories so it does not mutate the
developer's working tree.

A useful harness usually does this:

1. Create temporary local workspace, transfer, stage, and cloud workspace
   directories.
2. Initialize any required git repositories in the temporary local workspace.
3. Execute `.cloud-agent/local-stage` with `LOCAL_WORKSPACE_DIR`,
   `TRANSFER_DIR`, and `TRANSFER_STAGE_DIR`.
4. Execute the selected `local_transfer_script` with `LOCAL_WORKSPACE_DIR` and
   `TRANSFER_DIR`.
5. Execute the selected `cloud_setup_script` with `CLOUD_WORKSPACE_DIR` and
   `TRANSFER_DIR`, and set the command's current working directory to
   `CLOUD_WORKSPACE_DIR` to match the real runtime.
6. Assert the resulting cloud workspace layout, copied local-only files,
   sibling repository placement, and preserved git working-tree state.

For simple standard hooks, cheap checks may be enough:

```bash
bash -n .cloud-agent/local-stage
bash -n .cloud-agent/install-cloud
bash -n .cloud-agent/validate-cloud
```

When `.cloud-agent/cloud-agent.json` is generated, validate it too:

```bash
python -m json.tool .cloud-agent/cloud-agent.json >/dev/null
```

For custom transfer profiles, prefer adding a project-local harness such as:

```text
.cloud-agent/test-hooks-local
```

Keep this harness under `.cloud-agent/` by default. Do not put local hook
harnesses in the project's normal test suite, because `.cloud-agent/validate-cloud`
usually runs that suite inside the cloud workspace, where local-only hook
scripts may not be present. Only add hook tests to the normal project test suite
when they are explicitly safe to run inside the cloud workspace.

The harness should execute the generated scripts directly with the documented
environment variables and assert the exact files, directories, and git state
expected in the cloud workspace.

Existing project tests in the Crystal Lattice source tree can be useful
examples when the installed source is available:

- `plugins/cloud-agent-app/tests/test_cloud_agent_app_plugin.py` has fast tests
  that execute bundled transfer/setup/sync scripts directly against temporary
  git repositories.
- `application/python/tests/test_cloud_validation_command_docker.py` has
  slower Docker-backed `validate-cloud` examples. Treat these as final
  validation examples, not as the inner loop.

Do not assume the target project is itself an AI application. The same hook
structure may be used for libraries, CLIs, web apps, mobile backends, data
pipelines, browser automation projects, SDKs, infrastructure tooling, or any
other repository that needs a reproducible cloud workspace.

## Local Validation

After writing hooks, run:

```bash
crystal-lattice validate-cloud --workspace-dir /path/to/project
```

The command uses local Docker, prepares the transfer bundle, runs setup and
install inside the runtime image, then calls the validation hook. A successful
run means the project hooks are compatible with the shared cloud-agent startup
contract.