# CLI distribution verification

This application-owned specification defines the target verification contract
for the `crystal-lattice` command from source installation through the shipped
bundled-Python archive and the public default installer.

It covers:

- three independently executable smoke scenarios for source installation,
  direct archive use, and default installation;
- clean runtime state and default-configuration boot behavior;
- dynamic installation of a packaged plugin from both archive-based user
  workflows;
- credential-free startup and `.env`-based credential configuration;
- local root npm entry points;
- native release verification through the same npm entry points;
- immediate terminal command discovery after default installation;
- separation from config-specific optimized PyInstaller bundles.

The application package owns this contract because it owns the command,
runtime archive builder, installer, and archive smoke. Root npm scripts expose
maintainer entry points but do not own the behavior.

## Goals

- Detect plugin-installation and application-boot failures before bundling.
- Exercise the extracted archive directly so installer behavior cannot hide an
  archive-launch or archive-plugin-install defect.
- Exercise the public default installer independently so archive-smoke helper
  behavior cannot hide a download, staging, command-installation, or PATH
  defect.
- Verify that both archive-based workflows can dynamically install a packaged
  plugin into separate fresh caches.
- Let a newly installed CLI start normally without credentials or exported
  shell variables.
- Let a default installation place `crystal-lattice` in an existing suitable
  directory already present on PATH, so the current supported terminal can
  invoke it immediately by name.
- Verify that `.env` values reach config resolution without shell exports.
- Keep provider/tool request authentication with the package that owns that
  API contract.
- Run the direct archive and default-installer smokes on every native release
  target through the same root npm commands available to developers.
- Prefer simpler build, installation, and verification ownership; runtime
  reduction is accepted only when it preserves independent user-path coverage
  and does not introduce disproportionate orchestration.

## Non-goals

- Exercising a real model request in the distribution boot checks.
- Defining one provider's authentication protocol or anonymous API access.
- Inventorying direct environment-variable reads in individual plugins.
- Folding optimized PyInstaller bundle tests into the bundled-Python archive
  scenarios.
- Adding the slow local distribution commands to ordinary pull-request CI.
- Modifying shell profile files merely to make the command discoverable.
- Treating an explicit `BIN_DIR` override as a guarantee that the selected
  directory is already on PATH.

## Scenario names and historical terminology

The original work used “level 1”, “level 2”, and “level 3” as shorthand for
the increasing number of distribution transformations under test. The
numbers do not identify public products or permanent test names.

This specification and current documentation use these descriptive names:

| Current name | Historical shorthand | User workflow |
|---|---|---|
| Source-installation smoke | Level 1 | Install Core and the CLI into a fresh Python environment, then start the generated command. |
| Extracted-archive smoke | Level 2 | Unpack the shipped bundled-Python archive and run its launcher directly. |
| Default-installer smoke | Level 3 | Run the public installer with defaults, then invoke `crystal-lattice` by name from a terminal. |

Code identifiers may retain an old number temporarily during migration, but
new commands, tests, messages, and documentation use the descriptive names.

## Distribution boundaries

| Distribution | Purpose | Plugin behavior | Verification scope |
|---|---|---|---|
| Bundled-Python runtime archive | Shipped general CLI distribution | Default-config plugins are preinstalled; additional supported plugins may install dynamically | Source-installation, extracted-archive, and default-installer smokes |
| Optimized PyInstaller bundle | Config-specific frozen runtime | Selected plugins are frozen; arbitrary dynamic installation is rejected | Existing separate optimized-bundle suite |

## Active follow-up

The direct archive, public installer, isolated dynamic-plugin-installation,
PATH-discovery, shared npm/CI entry-point, terminology, and simplification
targets are tracked by `CLIDIST-020`, `CLIDIST-030`, `CLIDIST-040`,
`CLIDIST-050` through `CLIDIST-052`, and `CLIDIST-080` through
`CLIDIST-091` in the
[active task](../../../../../../tasks/20260908-cli-distribution-test-levels.md).
Current user and implementation documentation continues to describe the
previously delivered behavior until those requirements are implemented and
verified.

## Specification documents

- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)

## Current implementation documentation

- [CLI distribution implementation and verification](../../cli-distribution.md)
- [Application configuration](../../../configuration.md)
- [Configuration placeholders and `.env` loading](../../../configuration-placeholders.md)
