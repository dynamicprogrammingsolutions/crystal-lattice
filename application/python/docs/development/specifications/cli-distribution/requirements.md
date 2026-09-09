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
| CLIDIST-061 | Normal CLI use does not require shell exports: the CLI loads credentials from documented config, project, user, and discovered `.env` files without mutating the process environment. | Implemented | Automated | Documented | `test_cli_environment_isolation.py`; `test_application_layer_config.py`; [placeholder guide](../../../configuration-placeholders.md) |
| CLIDIST-062 | Distribution startup performs no provider/tool API request, synthesizes no credential, and leaves request authentication to the selected provider or tool contract. | In progress | Unverified | Documented | Shared API-free boot helper implemented; three distribution levels pending |
| CLIDIST-063 | The config loader classifies each unresolved `${env:...}` reference as a nonfatal `env_missing` warning with its variable and config path; independently invalid resolved structures retain their normal fatal validation. | Implemented | Automated | Documented | `agent_app.config.resolve_placeholders`; `test_config_env_substitution.py`; `test_application_config_errors.py`; [placeholder guide](../../../configuration-placeholders.md) |
| CLIDIST-070 | Archive construction completes in an isolated build environment before archive-consuming tests start and cannot install or upgrade packages in the repository test environment. | Not started | Unverified | Pending | Isolated Nox build and root orchestration pending in `tasks/20260908-cli-distribution-test-levels.md` |
| CLIDIST-071 | The default local archive build provisions an `uv`-managed Python 3.11 runtime equivalent to the release runtime family; explicit runtime and prebuilt-archive overrides remain optional. | Not started | Unverified | Pending | Nox runtime provisioning pending in `tasks/20260908-cli-distribution-test-levels.md` |
| CLIDIST-072 | Boot-probe cleanup owns the full process tree on POSIX and Windows, applies bounded graceful and forced termination, and verifies that the server port closes. | In progress | Unverified | Pending | Shared helper and POSIX helper test implemented; native Windows evidence pending |

## Current-state note

Credential-free startup and `.env` loading already exist, but distribution
tests do not yet preserve them as acceptance contracts. Explicit warning
classification, the three level commands, archive boot smoke, and
installed-wrapper boot remain target behavior until their requirement rows
carry passing automated evidence.
