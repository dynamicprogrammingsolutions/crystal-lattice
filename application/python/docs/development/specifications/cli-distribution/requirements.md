# CLI distribution verification requirements

These requirements track the live implementation of the
[CLI distribution verification specification](index.md).

| ID | Requirement | Implementation | Verification | Documentation | Evidence |
|---|---|---|---|---|---|
| CLIDIST-001 | The shipped bundled-Python runtime and config-specific optimized PyInstaller bundle remain distinct distributions with separate plugin policies and test suites. | Implemented | Automated | Documented | Runtime-layout and frozen dynamic-install tests; [current implementation](../../cli-distribution.md) |
| CLIDIST-010 | Level 1 boots the default config from a fresh lean Core/application venv and clean files, dynamically installing default `path:` plugins into the clean config-owned cache. | Implemented | Automated | Documented | `test_cli_distribution_levels.py::test_level_1_clean_python_environment_boots_default_config`; `npm run test:cli:clean-env` passed on macOS ARM64 |
| CLIDIST-020 | Level 2 validates and boots a current-platform bundled-Python archive with the default config and proves its preinstalled default plugins do not populate the user cache. | Implemented | Automated | Documented | Extended runtime-archive smoke and level-2 integration; `npm run test:cli:bundle` passed on macOS ARM64 |
| CLIDIST-030 | Level 3 installs the archive through staging replacement, creates the platform wrapper, and boots that installed command with the default config. | Implemented | Automated | Documented | `test_cli_distribution_levels.py::test_level_3_installed_wrapper_boots_default_config`; override and independent-build root runs passed on macOS ARM64 |
| CLIDIST-040 | Root npm commands independently run levels 1, 2, and 3 through the repository Python environment. | Implemented | Automated | Documented | `package.json`; `test_repo_run_script.py`; all three root commands passed on macOS ARM64 |
| CLIDIST-050 | The existing native release-archive smoke boots the default config in addition to structural and portability checks, without another CI workflow or matrix. | Implemented | Unverified | Documented | Smoke script passed directly on macOS ARM64; unchanged release matrix inspection complete; native GitHub matrix pending |
| CLIDIST-060 | A new default config starts and exposes all configured agents when its external `${env:...}` values are absent from the process and discovered `.env` files. | Implemented | Automated | Documented | Shared boot helper plus levels 1–3 passed; [configuration guide](../../../configuration.md) |
| CLIDIST-061 | Normal CLI use does not require shell exports: the CLI loads credentials from documented config, project, user, and discovered `.env` files without mutating the process environment. | Implemented | Automated | Documented | `test_cli_environment_isolation.py`; `test_application_layer_config.py`; [placeholder guide](../../../configuration-placeholders.md) |
| CLIDIST-062 | Distribution startup performs no provider/tool API request, synthesizes no credential, and leaves request authentication to the selected provider or tool contract. | Implemented | Automated | Documented | Shared boot helper calls only local readiness and agent-list endpoints; levels 1–3 passed without dummy values |
| CLIDIST-063 | The config loader classifies each unresolved `${env:...}` reference as a nonfatal `env_missing` warning with its variable and config path; independently invalid resolved structures retain their normal fatal validation. | Implemented | Automated | Documented | `agent_app.config.resolve_placeholders`; `test_config_env_substitution.py`; `test_application_config_errors.py`; [placeholder guide](../../../configuration-placeholders.md) |
| CLIDIST-070 | Archive construction completes in an isolated build environment before archive-consuming tests start and cannot install or upgrade packages in the repository test environment. | Implemented | Automated | Documented | Root runner waits for isolated Nox build; two archive builds passed and repository `pip freeze` hash remained unchanged |
| CLIDIST-071 | The default local archive build provisions an `uv`-managed Python 3.11 runtime equivalent to the release runtime family; explicit runtime and prebuilt-archive overrides remain optional. | Implemented | Automated | Documented | Nox provisioned managed CPython 3.11.16; archive portability and boot smoke passed |
| CLIDIST-072 | Boot-probe cleanup owns the full process tree on POSIX and Windows, applies bounded graceful and forced termination, and verifies that the server port closes. | In progress | Unverified | Pending | Shared helper and POSIX helper test implemented; native Windows evidence pending |

## Current-state note

All requirements have local macOS ARM64 evidence. Native release-matrix
execution remains pending for CLIDIST-050 and the Windows portion of
CLIDIST-072.
