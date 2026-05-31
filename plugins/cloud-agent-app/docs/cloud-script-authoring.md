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

Keep hooks deterministic and idempotent. They may be run more than once during
local validation. Prefer explicit checks over silent best-effort behavior.

Do not print secrets. Do not commit `.env` files or generated credentials.

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
TRANSFER_STAGE_DIR   staged local-only files copied by local-stage
TRANSFER_DIR         whole transfer bundle directory
WORKING_DIR          cloud working directory
SESSION_ID           validation or cloud session id
```

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
prefer documenting or selecting an appropriate container profile instead of
making hooks silently skip required setup.

## Validation Hook

`.cloud-agent/validate-cloud` runs after transfer, setup, install, and the
built-in runtime smoke check. Use it to prove the cloud workspace is usable.

Validation should be deterministic and provider-free. It should not call hosted
LLM APIs.

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

## Using Project Guidance

Read normal project guidance before writing hooks:

- `AGENTS.md`
- README files
- package manifests such as `pyproject.toml`, `requirements.txt`, or
  `package.json`
- existing test directories and scripts

Translate "fresh checkout setup" into `.cloud-agent/install-cloud`. Translate
"local env file required" into `.cloud-agent/local-stage`. Translate "basic
test command" into `.cloud-agent/validate-cloud`.

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

When adding custom profile scripts, document:

- what each script expects as input
- which environment variables it reads
- what files it writes into `TRANSFER_DIR`, `TRANSFER_STAGE_DIR`, or
  `CLOUD_WORKSPACE_DIR`
- how `crystal-lattice validate-cloud` proves the custom path works

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

## Local Validation

After writing hooks, run:

```bash
crystal-lattice validate-cloud --workspace-dir /path/to/project
```

The command uses local Docker, prepares the transfer bundle, runs setup and
install inside the runtime image, then calls the validation hook. A successful
run means the project hooks are compatible with the shared cloud-agent startup
contract.