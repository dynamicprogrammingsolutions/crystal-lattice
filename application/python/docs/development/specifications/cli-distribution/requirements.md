# CLI distribution verification requirements

These requirements track the live implementation of the
[CLI distribution verification specification](index.md).

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| CLIDIST-001 | The shipped bundled-Python runtime and config-specific optimized PyInstaller bundle remain distinct distributions with separate plugin policies and test suites. | Implemented | Automated | Documented | Runtime-layout and frozen dynamic-install tests; [current implementation](../../cli-distribution.md) |
| CLIDIST-010 | Level 1 boots the default config from a fresh lean Core/application venv and clean files, dynamically installing default `path:` plugins into the clean config-owned cache. | Not started | Unverified | Pending | `tasks/20260908-cli-distribution-test-levels.md` |
| CLIDIST-020 | Level 2 validates and boots a current-platform bundled-Python archive with the default config and proves its preinstalled default plugins do not populate the user cache. | Not started | Unverified | Pending | Existing smoke is structural only; `tasks/20260908-cli-distribution-test-levels.md` |
| CLIDIST-030 | Level 3 installs the archive through staging replacement, creates the platform wrapper, and boots that installed command with the default config. | Not started | Unverified | Pending | Existing installer checks layout and help only; `tasks/20260908-cli-distribution-test-levels.md` |
| CLIDIST-040 | Root npm commands independently run levels 1, 2, and 3 through the repository Python environment. | Not started | Unverified | Pending | `tasks/20260908-cli-distribution-test-levels.md` |
| CLIDIST-050 | The existing native release-archive smoke boots the default config in addition to structural and portability checks, without another CI workflow or matrix. | Not started | Unverified | Pending | `.github/workflows/release-crystal-lattice-cli.yml`; `tasks/20260908-cli-distribution-test-levels.md` |
| CLIDIST-060 | A new default config starts and exposes all configured agents when its external `${env:...}` values are absent from the process and discovered `.env` files. | Implemented | Unverified | Documented | Placeholder fatality boundary in `agent_app`; [configuration guide](../../../configuration.md); distribution-level automated evidence pending |
| CLIDIST-061 | Normal CLI use does not require shell exports: the CLI loads credentials from documented config, project, user, and discovered `.env` files without mutating the process environment. | Implemented | Unverified | Documented | Partial coverage in `test_cli_environment_isolation.py` and `test_application_layer_config.py`; focused complete evidence pending; [placeholder guide](../../../configuration-placeholders.md) |
| CLIDIST-062 | Distribution startup performs no provider/tool API request, synthesizes no credential, and leaves request authentication to the selected provider or tool contract. | Not started | Unverified | Documented | Three-level boot probe pending in `tasks/20260908-cli-distribution-test-levels.md`; provider authentication is explicitly out of scope |
| CLIDIST-063 | The config loader classifies each unresolved `${env:...}` reference as a nonfatal `env_missing` warning with its variable and config path; independently invalid resolved structures retain their normal fatal validation. | Not started | Unverified | Pending | `agent_app.config.resolve_placeholders`; focused loader coverage pending in `tasks/20260908-cli-distribution-test-levels.md` |

## Current-state note

Credential-free startup and `.env` loading already exist, but distribution
tests do not yet preserve them as acceptance contracts. Explicit warning
classification, the three level commands, archive boot smoke, and
installed-wrapper boot remain target behavior until their requirement rows
carry passing automated evidence.
