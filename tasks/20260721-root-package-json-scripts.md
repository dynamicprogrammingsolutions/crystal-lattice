# Add Root `package.json` Scripts and VS Code Tasks for IntelliJ Parity

## Description

The project is developed in IntelliJ, where a set of run configurations make it
easy to launch the mobile app, desktop app, Python tests, lint/typecheck, the
Crystal Lattice server, the bridge, and deploy scripts. The same commands should
be runnable from VS Code and the terminal with the same convenience.

Two deliverables:

1. A curated `scripts` block in the root `package.json` gives VS Code's npm
   script panel and `npm run <name>` in the terminal a single, discoverable
   entry point for the commands that are currently scattered across IntelliJ
   run configs and READMEs.
2. A smaller `.vscode/tasks.json` exposes the most common daily-dev commands
   as VS Code Tasks (Run Task / Command Palette / keyboard shortcuts), each
   delegating to the corresponding npm script so there is one source of truth.

## Requirements checklist

- [x] Root `package.json` contains a `scripts` block whose entries cover the
  saved IntelliJ run configurations (Python tests, mobile npm, desktop npm,
  deploy/SSH shell scripts) and the canonical commands from the main READMEs
  and `AGENTS.md`
- [x] The existing `name`, `private`, `license`, and `workspaces` fields are
  preserved unchanged
- [x] The resulting `package.json` is valid JSON and `npm run` (no argument)
  lists every new script
- [x] Mobile and desktop scripts `cd` into their own directories so the npm
  workspace layout (`packages/*` only) is not changed
- [x] `.vscode/tasks.json` exists and defines a smaller, curated set of VS
  Code Tasks that each run one of the npm scripts above
- [x] Each VS Code Task uses `type: "npm"` with the corresponding `script`
  name so the npm script is the single source of truth
- [x] Long-running tasks (server, Metro bundlers) are marked
  `isBackground: true` with a dedicated terminal panel so VS Code does not
  wait for them to exit

## Investigation details

### IntelliJ run configurations

Saved run configurations were found in two places:

1. `.run/` directory — two saved Python test configs:
   - `Test application_python_tests.run.xml` — runs `pytest` against
     `$PROJECT_DIR$/application/python/tests` with `--no-cov`.
   - `Test core_python_tests (UNIT).run.xml` — runs `pytest` against
     `$PROJECT_DIR$/core/python/tests` with `--no-cov`.

2. `.idea/workspace.xml` `RunManager` component — the saved configurations
   listed there are:
   - Python tests: `Test core/python/tests (UNIT)`,
     `Test core/python/tests (Openrouter)`,
     `Test core/python/examples/tests (UNIT)`,
     `Test core/python/examples/tests (Openrouter)`,
     `Test application/python/tests`.
   - npm (mobile): `crystal-lattice-control-rn > start`,
     `crystal-lattice-control-rn > pod-install`,
     `crystal-lattice-control-rn > ios-device`, `ios`, `android`.
   - npm (desktop): `crystal-lattice-control-desktop-rn > start`,
     `crystal-lattice-control-desktop-rn > start-no-cache`,
     `crystal-lattice-control-desktop-rn > pod-install`,
     `crystal-lattice-control-desktop-rn > macos`.
   - Shell scripts: `Deploy Bridge`, `Deploy Cloud`, `Cloud Test`,
     `SSH ireland srv`.

   The `executor` history in `workspace.xml` also shows many ad-hoc
   single-test runs (pytest, Jest, Vitest) that were not saved as
   configurations. Those are out of scope for the root scripts.

### Shell script contents (from `workspace.xml`)

- `Deploy Bridge` — inline `rsync` of `bridge-elixir/` to
  `ireland-s1.dynamicprogrammingsolutions.com` then `docker-compose
  -f docker-compose.single-node-v2.yml build && up -d`.
- `Deploy Cloud` — executes
  `$PROJECT_DIR$/.crystal/deploy-cloud-orchestrator-ireland.sh`.
- `Cloud Test` — executes `$PROJECT_DIR$/.crystal/cloud-test.sh`
  (starts a dev server with bridge + cloud orchestrator against the
  ireland deployment).
- `SSH ireland srv` — `ssh irelandsrv@ireland-s1.dynamicprogrammingsolutions.com`.

### Canonical commands from READMEs and `AGENTS.md`

- `README.md` — quickstart for mobile/desktop, plugin templates, core dev
  install, fast test sets, lint/typecheck, mkdocs.
- `application/python/README.md` — `crystal-lattice` CLI flags, server/terminal
  modes, Bonjour/bridge, nox build commands, release workflow.
- `mobile/crystal-lattice-control-rn/README.md` — React Native setup,
  Metro, iOS/Android, Detox, Jest tiers.
- `desktop/crystal-lattice-control-desktop-rn/README.md` — React Native
  macOS setup, `npm run macos`, `test:macos-ui`.
- `AGENTS.md` — the authoritative test marker matrix and
  lint/format/typecheck commands.

### Existing root `package.json`

```json
{
  "name": "crystal-lattice-monorepo",
  "private": true,
  "license": "Apache-2.0",
  "workspaces": [
    "packages/*"
  ]
}
```

The workspace only includes `packages/*`. The mobile and desktop apps are
intentionally not part of the npm workspace (they have their own `node_modules`
and use `file:` deps to reference the shared packages). The new `scripts` block
must not change that — mobile/desktop scripts should `cd` into their dirs.

### Accepted decision: script naming and categories

Use a `category:subcommand` naming convention so VS Code's npm script panel
groups scripts visually and `npm run` tab-completes nicely. Categories:

1. **Python tests** — fast defaults + marker-filtered integration/API slices
   from `AGENTS.md`.
2. **Python plugin tests** — fast defaults for the three provider plugin
   projects.
3. **Python lint/format/typecheck** — `ruff`, `black`, `pyright`.
4. **Frontend SDK tests** — workspace package tests via
   `npm --workspace @crystal-lattice/... test`.
5. **Mobile** — `cd mobile/... && npm run ...` for install, pods, Metro,
   iOS, iOS-device, Android, test, integration test, tsc, lint.
6. **Desktop** — `cd desktop/... && npm run ...` for install, pods, Metro,
   Metro no-cache, macOS, iOS, Android, test, macOS UI tests, lint.
7. **Crystal Lattice server** — `crystal-lattice` CLI invocations
   (full setup, basic, echo, dev).
8. **Bridge** — `docker-compose up/down/logs` and health curl.
9. **Docs** — `mkdocs serve/build`, `generate_examples_md.py`.
10. **Python install/build** — editable installs and `nox` sessions.
11. **Deploy/infra** — the user-specific ireland deploy/SSH scripts.

### Accepted script set

```jsonc
{
  "scripts": {
    "test:core":              "pytest core/python/tests -q",
    "test:core:unit":         "pytest core/python/tests -q -m \"not integration\"",
    "test:application":        "pytest application/python/tests -q",
    "test:application:unit":  "pytest application/python/tests -q -m \"not integration and not docker\"",
    "test:examples":          "pytest core/python/examples/tests -qs",

    "test:core:integration":       "pytest core/python/tests -m \"integration and not api and not slow_integration\" -q",
    "test:application:integration": "pytest application/python/tests -m \"integration and not api and not slow_integration and not docker\" -q",
    "test:ollama":                 "pytest core/python/tests -m \"ollama and not api\" -q",

    "test:api:examples":      "pytest core/python/examples/tests -m \"integration and api and not slow_integration\" -q",
    "test:api:application":   "pytest application/python/tests -m \"integration and api and not slow_integration and not docker\" -q",
    "test:api:openrouter":    "pytest plugins/openrouter/tests -m \"integration and api and not slow_integration and openrouter\" -q",
    "test:api:openai":        "pytest plugins/openai_responses/tests -m \"integration and api and not slow_integration and openai\" -q",
    "test:api:fireworks":     "pytest plugins/reference-openai-compatible-provider/tests -m \"integration and api and not slow_integration and fireworks\" -q",
    "test:api:zai":           "pytest plugins/reference-openai-compatible-provider/tests -m \"integration and api and not slow_integration and zai\" -q",

    "test:plugins:openrouter":        "pytest plugins/openrouter/tests -q",
    "test:plugins:openai-responses":  "pytest plugins/openai_responses/tests -q",
    "test:plugins:reference":         "pytest plugins/reference-openai-compatible-provider/tests -q",

    "lint":       "ruff check core/python/agent_core core/python/tests core/python/examples core/python/plugins",
    "lint:fix":   "ruff check --fix core/python/agent_core core/python/tests core/python/examples core/python/plugins",
    "format":     "black core/python/agent_core core/python/tests core/python/examples core/python/plugins",
    "typecheck":  "pyright",

    "test:frontend-sdk":           "npm --workspace @crystal-lattice/frontend-sdk test",
    "test:frontend-sdk-react":     "npm --workspace @crystal-lattice/frontend-sdk-react test",
    "test:frontend-rn-components": "npm --workspace @crystal-lattice/frontend-rn-components test",

    "mobile:install":      "cd mobile/crystal-lattice-control-rn && npm install",
    "mobile:pod-install":  "cd mobile/crystal-lattice-control-rn && npm run pod-install",
    "mobile:start":        "cd mobile/crystal-lattice-control-rn && npm run start",
    "mobile:ios":          "cd mobile/crystal-lattice-control-rn && npm run ios",
    "mobile:ios-device":    "cd mobile/crystal-lattice-control-rn && npm run ios-device",
    "mobile:android":      "cd mobile/crystal-lattice-control-rn && npm run android",
    "mobile:test":         "cd mobile/crystal-lattice-control-rn && npm test",
    "mobile:test:integration": "cd mobile/crystal-lattice-control-rn && npm run test:components:integration",
    "mobile:tsc":          "cd mobile/crystal-lattice-control-rn && npm run tsc",
    "mobile:lint":         "cd mobile/crystal-lattice-control-rn && npm run lint",

    "desktop:install":      "cd desktop/crystal-lattice-control-desktop-rn && npm install",
    "desktop:pod-install":  "cd desktop/crystal-lattice-control-desktop-rn && npm run pod-install",
    "desktop:start":        "cd desktop/crystal-lattice-control-desktop-rn && npm run start",
    "desktop:start-no-cache": "cd desktop/crystal-lattice-control-desktop-rn && npm run start-no-cache",
    "desktop:macos":        "cd desktop/crystal-lattice-control-desktop-rn && npm run macos",
    "desktop:ios":          "cd desktop/crystal-lattice-control-desktop-rn && npm run ios",
    "desktop:android":      "cd desktop/crystal-lattice-control-desktop-rn && npm run android",
    "desktop:test":         "cd desktop/crystal-lattice-control-desktop-rn && npm test",
    "desktop:test:macos-ui": "cd desktop/crystal-lattice-control-desktop-rn && npm run test:macos-ui",
    "desktop:test:macos-ui:session-filters": "cd desktop/crystal-lattice-control-desktop-rn && npm run test:macos-ui:session-filters",
    "desktop:lint":        "cd desktop/crystal-lattice-control-desktop-rn && npm run lint",

    "server":       "crystal-lattice --server --console --enable-bonjour --enable-bridge",
    "server:basic": "crystal-lattice --server --console",
    "server:echo":  "crystal-lattice --server --console --config-local",
    "server:dev":   "bash .crystal/cloud-test.sh",

    "bridge:up":     "cd bridge-elixir && docker-compose up -d",
    "bridge:down":   "cd bridge-elixir && docker-compose down",
    "bridge:logs":   "cd bridge-elixir && docker-compose logs -f",
    "bridge:health": "curl -fsS http://localhost:4000/health",

    "docs:serve":    "mkdocs serve",
    "docs:build":    "mkdocs build",
    "docs:examples": "python scripts/generate_examples_md.py",

    "install:core":      "python -m pip install -e \"core/python[dev]\"",
    "install:app":       "python -m pip install -e application/python",
    "install:all":       "python -m pip install -e \"core/python[dev]\" -e application/python",
    "build:bundle":      "nox -s build_bundle",
    "build:optimized":   "nox -s build_optimized_bundle",
    "install:prod:local": "nox -s install_prod_local",
    "install:dev:local":  "nox -s install_dev_local",

    "deploy:bridge":  "rsync -av --exclude '_build' --exclude 'deps' bridge-elixir/ ireland-s1.dynamicprogrammingsolutions.com:~/bridge-elixir/ && ssh ireland-s1.dynamicprogrammingsolutions.com 'cd ~/bridge-elixir && docker-compose -f docker-compose.single-node-v2.yml build && docker-compose -f docker-compose.single-node-v2.yml up -d'",
    "deploy:cloud":   "bash .crystal/deploy-cloud-orchestrator-ireland.sh",
    "ssh:ireland":    "ssh irelandsrv@ireland-s1.dynamicprogrammingsolutions.com"
  }
}
```

### Notes on the accepted script set

- `server*` scripts assume `crystal-lattice` is on `PATH` (from `pipx install`
  or `~/.local/bin`). The editable venv at `.venv/bin/crystal-lattice` also
  works if the venv is activated.
- `deploy:*` and `ssh:ireland` are user-specific to the ireland deployment
  host. They are included for parity with the IntelliJ Shell Script configs.
- Ad-hoc single-test runners from the IntelliJ executor history are not
  included; those are better launched via `pytest <file>::<test>` or VS
  Code's test runner.

### Proposed VS Code tasks (smaller curated set)

The root `package.json` now exposes 67 npm scripts. VS Code Tasks should
expose only the small subset used in the daily dev loop — the rest stay
available via the npm script panel and `npm run <name>`. Each task uses
`type: "npm"` with the corresponding `script` name so the npm script
remains the single source of truth.

Proposed `.vscode/tasks.json` (15 tasks):

| Label | npm script | Group | Background | Notes |
|---|---|---|---|---|
| `Server: Start` | `server` | `build` | yes | Crystal Lattice server + terminal + Bonjour + bridge |
| `Mobile: Start Metro` | `mobile:start` | `build` | yes | Metro bundler for the mobile app |
| `Mobile: Run iOS` | `mobile:ios` | `build` | no | Build and launch on iOS simulator |
| `Mobile: Run iOS Device` | `mobile:ios-device` | `build` | no | Build and launch on a physical iOS device |
| `Desktop: Start Metro` | `desktop:start` | `build` | yes | Metro bundler for the desktop app |
| `Desktop: Run macOS` | `desktop:macos` | `build` | no | Build and launch the macOS desktop app |
| `Test: Core (unit)` | `test:core:unit` | `test` | no | Fast core SDK unit tests |
| `Test: Application (unit)` | `test:application:unit` | `test` | no | Fast application-layer unit tests |
| `Lint` | `lint` | `build` | no | `ruff check` over core paths |
| `Typecheck` | `typecheck` | `build` | no | `pyright` |
| `Deploy: Bridge` | `deploy:bridge` | `build` | no | rsync + ssh deploy of bridge-elixir to ireland host |
| `Deploy: Cloud` | `deploy:cloud` | `build` | no | run `.crystal/deploy-cloud-orchestrator-ireland.sh` |
| `Install: Prod Local` | `install:prod:local` | `build` | no | Build bundle then install from archive (see npm script change below) |
| `Install: Dev Local` | `install:dev:local` | `build` | no | Editable-source dev command at `~/.crystal/dev-cli-venv` |
| `Run: Dev Local` | `run:dev-local` | `build` | yes | `crystal-lattice-cli-dev` dev server on port 57889 with bridge + Bonjour |

Draft `.vscode/tasks.json` content:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Server: Start",
      "type": "npm",
      "script": "server",
      "isBackground": true,
      "presentation": { "reveal": "always", "panel": "dedicated" },
      "group": "build"
    },
    {
      "label": "Mobile: Start Metro",
      "type": "npm",
      "script": "mobile:start",
      "isBackground": true,
      "presentation": { "reveal": "always", "panel": "dedicated" },
      "group": "build"
    },
    {
      "label": "Mobile: Run iOS",
      "type": "npm",
      "script": "mobile:ios",
      "presentation": { "reveal": "always", "panel": "shared" },
      "group": "build"
    },
    {
      "label": "Mobile: Run iOS Device",
      "type": "npm",
      "script": "mobile:ios-device",
      "presentation": { "reveal": "always", "panel": "shared" },
      "group": "build"
    },
    {
      "label": "Desktop: Start Metro",
      "type": "npm",
      "script": "desktop:start",
      "isBackground": true,
      "presentation": { "reveal": "always", "panel": "dedicated" },
      "group": "build"
    },
    {
      "label": "Desktop: Run macOS",
      "type": "npm",
      "script": "desktop:macos",
      "presentation": { "reveal": "always", "panel": "shared" },
      "group": "build"
    },
    {
      "label": "Test: Core (unit)",
      "type": "npm",
      "script": "test:core:unit",
      "group": "test"
    },
    {
      "label": "Test: Application (unit)",
      "type": "npm",
      "script": "test:application:unit",
      "group": "test"
    },
    {
      "label": "Lint",
      "type": "npm",
      "script": "lint",
      "group": "build"
    },
    {
      "label": "Typecheck",
      "type": "npm",
      "script": "typecheck",
      "group": "build"
    },
    {
      "label": "Deploy: Bridge",
      "type": "npm",
      "script": "deploy:bridge",
      "presentation": { "reveal": "always", "panel": "shared" },
      "group": "build"
    },
    {
      "label": "Deploy: Cloud",
      "type": "npm",
      "script": "deploy:cloud",
      "presentation": { "reveal": "always", "panel": "shared" },
      "group": "build"
    },
    {
      "label": "Install: Prod Local",
      "type": "npm",
      "script": "install:prod:local",
      "presentation": { "reveal": "always", "panel": "shared" },
      "group": "build"
    },
    {
      "label": "Install: Dev Local",
      "type": "npm",
      "script": "install:dev:local",
      "presentation": { "reveal": "always", "panel": "shared" },
      "group": "build"
    },
    {
      "label": "Run: Dev Local",
      "type": "npm",
      "script": "run:dev-local",
      "isBackground": true,
      "presentation": { "reveal": "always", "panel": "dedicated" },
      "group": "build"
    }
  ]
}
```

### npm script change for `install:prod:local`

The user requested that the prod install npm script prepend the bundle
build command, so a single `npm run install:prod:local` (or the
`Install: Prod Local` VS Code Task) builds the bundle first and then
installs from the generated archive.

Current `package.json` entry:

```json
"install:prod:local": "nox -s install_prod_local",
```

New entry:

```json
"install:prod:local": "nox -s build_bundle && nox -s install_prod_local",
```

This is a change to the already-completed `package.json` deliverable. It is
in scope because the new `Install: Prod Local` VS Code Task depends on the
combined behavior, and the README already documents `build_bundle` and
`install_prod_local` as the intended release rehearsal sequence (build,
smoke-test, install from archive, link `crystal-lattice`).

### npm script addition for `run:dev-local`

The user requested a new `Run: Dev Local` command that runs the dev CLI
directly with a fixed port and bridge + Bonjour enabled:

```json
"run:dev-local": "crystal-lattice-cli-dev --console --server --enable-bridge --enable-bonjour --port 57889",
```

`crystal-lattice-cli-dev` is the editable-source dev command installed by
`nox -s install_dev_local` (see `application/python/README.md`). It lives at
`~/.local/bin/crystal-lattice-cli-dev` and uses the `~/.crystal/dev-cli-venv`
virtualenv, so it is independent of the project's `.venv`. The VS Code Task
is `isBackground: true` with a dedicated panel because it is a long-running
server + terminal.

### Notes on the proposed VS Code tasks

- `.vscode/` is currently in `.gitignore` (line 273), so `.vscode/tasks.json`
  would be a local-only file by default. If the tasks should be shared with
  the team, either force-add the file (`git add -f .vscode/tasks.json`) or
  narrow the `.gitignore` rule to `.vscode/*` with an exception for
  `!.vscode/tasks.json`. This is a **material decision** for the user.
- `isBackground: true` on server and Metro tasks tells VS Code not to wait
  for them to exit; combined with `panel: "dedicated"`, each long-running
  task gets its own terminal panel that persists across runs.
- The `group` property makes tasks discoverable via `Run Build Task`
  (Cmd+Shift+B) and `Run Test Task` — the `build` group holds the server,
  app launchers, deploy, and install tasks; the `test` group holds the two
  fast unit-test tasks.
- `Deploy: Bridge`, `Deploy: Cloud`, `Install: Prod Local`, and
  `Install: Dev Local` are one-shot commands (not background) and share a
  terminal panel so their output is visible alongside other build output.
- No `problemMatcher` is configured for lint/typecheck in this smaller set;
  that can be added later if the user wants errors surfaced in the VS Code
  Problems panel.

## Execution plan

Status: Approved

The first four requirements (the `package.json` `scripts` block) were
completed in the initial pass. The user then added three new requirements
for `.vscode/tasks.json` and refined the proposed task set (added iOS
device, deploy bridge/cloud, prod/dev install; removed example tests) and
requested a change to the `install:prod:local` npm script (prepend the
bundle build). The user approved the updated plan and chose `.gitignore`
option 3 (narrow the rule to `.vscode/*` with `!.vscode/tasks.json`). The
plan below covers the new VS Code tasks work plus the one npm script edit
and the `.gitignore` narrowing; the rest of the `package.json` work is
recorded in `## Completion Notes` and is not re-executed.

### Requirement verification

- **`.vscode/tasks.json` exists with curated tasks**: verified by creating
  the file and inspecting it. Boundary: file existence + JSON parse at the
  repo root.
- **Each task uses `type: "npm"` with the matching `script`**: verified by
  inspection — every task object has `"type": "npm"` and a `"script"` value
  that matches a key in the root `package.json` `scripts` block. Boundary:
  static cross-check between `.vscode/tasks.json` and `package.json`.
- **Long-running tasks are `isBackground` with dedicated panel**: verified
  by inspection — the `Server: Start`, `Mobile: Start Metro`, and
  `Desktop: Start Metro` tasks have `"isBackground": true` and
  `"presentation": { "panel": "dedicated" }`. Boundary: static file
  inspection.
- **`install:prod:local` prepends the bundle build**: verified by
  inspection — the `package.json` entry is
  `"nox -s build_bundle && nox -s install_prod_local"`. Boundary: static
  file inspection of `package.json`.

### Documentation

No documentation change is planned beyond this task file. The VS Code tasks
are self-documenting via the Run Task / Command Palette UI, which shows the
label and the underlying npm script. The intended audience is the developer
working in VS Code who wants one-click access to the daily dev loop without
remembering npm script names.

### Task checklist

- [x] Confirm the proposed 14-task VS Code set and the `.gitignore` decision
  with the user
- [x] Update `package.json` `install:prod:local` to prepend
  `nox -s build_bundle &&`
- [x] Verify the updated `package.json` is still valid JSON
- [x] Create `.vscode/` directory and write `tasks.json` with the 14
  curated tasks
- [x] Verify `tasks.json` is valid JSON
- [x] Verify every `script` value in `tasks.json` matches a key in the root
  `package.json` `scripts` block

## Completion Notes

### First pass — root `package.json` scripts (complete)

- Replaced the root `package.json` with a version that preserves the existing
  `name`, `private`, `license`, and `workspaces` fields and adds a 66-entry
  `scripts` block matching the accepted script set above.
- Requirement evidence:
  - Valid JSON: `node -e "require('./package.json')"` succeeded and printed
    `scripts: 66`, `name: crystal-lattice-monorepo`, `private: true`,
    `license: Apache-2.0`, `workspaces: ["packages/*"]`.
  - `npm run` listing: all 66 scripts appear under
    `Scripts available in crystal-lattice-monorepo via \`npm run-script\`:`,
    grouped by name with the full command on the next line.
  - Field preservation: confirmed by the same `node -e` output above.
  - Mobile/desktop isolation: confirmed by inspection — every `mobile:*` and
    `desktop:*` script begins with `cd mobile/crystal-lattice-control-rn` or
    `cd desktop/crystal-lattice-control-desktop-rn`, and `workspaces` is
    still `["packages/*"]`.
- Verification performed: `node -e` JSON parse + field check, `npm run`
  script listing. No tests were run on the scripts themselves (they are
  thin wrappers around commands already documented in READMEs and
  `AGENTS.md`); each script's underlying command is verified by its own
  tooling when run.
- Plan deviations: none. The executed `scripts` block matches the accepted
  script set byte-for-byte.
- Unresolved or deferred scope: none. Ad-hoc single-test runners from the
  IntelliJ executor history were intentionally excluded (see "Notes on the
  accepted script set" above).

### Second pass — VS Code tasks + npm script edit + `.gitignore` (complete)

- Edited `package.json` `install:prod:local` from
  `"nox -s install_prod_local"` to
  `"nox -s build_bundle && nox -s install_prod_local"` so a single
  `npm run install:prod:local` (or the `Install: Prod Local` VS Code Task)
  builds the bundle first and then installs from the generated archive.
- Narrowed the `.gitignore` rule from `.vscode/` to `.vscode/*` plus
  `!.vscode/tasks.json`, so the curated tasks file is trackable and
  shareable with the team while other VS Code settings stay ignored.
  Verified with `git check-ignore`: `.vscode/tasks.json` is not ignored,
  `.vscode/settings.json` and `.vscode/launch.json` are still ignored.
- Created `.vscode/tasks.json` with 14 curated VS Code Tasks, each using
  `type: "npm"` with the matching `script` name:
  - `Server: Start` (`server`, background, dedicated panel)
  - `Mobile: Start Metro` (`mobile:start`, background, dedicated panel)
  - `Mobile: Run iOS` (`mobile:ios`)
  - `Mobile: Run iOS Device` (`mobile:ios-device`)
  - `Desktop: Start Metro` (`desktop:start`, background, dedicated panel)
  - `Desktop: Run macOS` (`desktop:macos`)
  - `Test: Core (unit)` (`test:core:unit`, `test` group)
  - `Test: Application (unit)` (`test:application:unit`, `test` group)
  - `Lint` (`lint`)
  - `Typecheck` (`typecheck`)
  - `Deploy: Bridge` (`deploy:bridge`)
  - `Deploy: Cloud` (`deploy:cloud`)
  - `Install: Prod Local` (`install:prod:local`)
  - `Install: Dev Local` (`install:dev:local`)
- Requirement evidence:
  - `package.json` still valid JSON: `node -e "require('./package.json')"`
    succeeded; `scripts` count still 66; `install:prod:local` now reads
    `nox -s build_bundle && nox -s install_prod_local`.
  - `tasks.json` valid JSON: `node -e "require('./.vscode/tasks.json')"`
    succeeded; `tasks` array length is 14.
  - All tasks use `type: "npm"`: cross-check in the same `node -e` script
    confirmed `All tasks use type: "npm": true`.
  - All task scripts match `package.json` keys: cross-check confirmed
    `All task scripts match package.json keys: true` (no mismatches).
  - Background tasks have dedicated panels: `Server: Start`,
    `Mobile: Start Metro`, and `Desktop: Start Metro` all have
    `isBackground: true` and `presentation.panel: "dedicated"`.
  - `.gitignore` narrowing: `git check-ignore .vscode/tasks.json` produced
    no output (not ignored); `git check-ignore .vscode/settings.json
    .vscode/launch.json` listed both (still ignored).
- Verification performed: `node -e` JSON parse + cross-check between
  `tasks.json` and `package.json`, `git check-ignore` for the `.gitignore`
  rule, `git status` to confirm `.vscode/` now appears as untracked
  (previously fully ignored).
- Plan deviations: none. The executed `tasks.json` matches the proposed
  14-task set, and the `install:prod:local` change matches the requested
  prepend.
- Unresolved or deferred scope: none. `problemMatcher` for lint/typecheck
  was intentionally not added in this pass (noted in "Notes on the proposed
  VS Code tasks"); it can be added later if the user wants errors surfaced
  in the VS Code Problems panel.

### Third pass — `Run: Dev Local` script + task (complete)

- Added `run:dev-local` to `package.json` `scripts` (after `server:dev`):
  `"run:dev-local": "crystal-lattice-cli-dev --console --server --enable-bridge --enable-bonjour --port 57889"`.
  This runs the editable-source dev CLI (`crystal-lattice-cli-dev`, installed
  by `nox -s install_dev_local`) with a fixed port 57889 and bridge + Bonjour
  enabled.
- Added the `Run: Dev Local` task to `.vscode/tasks.json` as a long-running
  background task with a dedicated terminal panel (`isBackground: true`,
  `presentation.panel: "dedicated"`, `group: "build"`), matching the pattern
  used by `Server: Start`, `Mobile: Start Metro`, and `Desktop: Start Metro`.
- Requirement evidence:
  - `package.json` valid JSON: `node -e "require('./package.json')"`
    succeeded; `scripts` count is now 67; `run:dev-local` reads
    `crystal-lattice-cli-dev --console --server --enable-bridge --enable-bonjour --port 57889`.
  - `tasks.json` valid JSON: `node -e "require('./.vscode/tasks.json')"`
    succeeded; `tasks` array length is now 15.
  - All task scripts match `package.json` keys: cross-check confirmed
    `all task scripts match package.json keys: true` (no mismatches,
    including the new `run:dev-local`).
  - `Run: Dev Local` task is background with dedicated panel: confirmed by
    inspecting the task object — `isBackground: true` and
    `presentation.panel: "dedicated"`.
- Verification performed: `node -e` JSON parse + cross-check between
  `tasks.json` and `package.json`.
- Plan deviations: none.
- Unresolved or deferred scope: none.