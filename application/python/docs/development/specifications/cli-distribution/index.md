# CLI distribution verification

This application-owned specification defines the target distribution and
verification contract for the `crystal-lattice` command from source
installation through the shipped bundled-Python archives and public Bash and
PowerShell installers.

It covers:

- three independently executable smoke scenarios for source installation,
  direct archive use, and default installation;
- clean runtime state and default-configuration boot behavior;
- dynamic installation of a packaged plugin from both archive-based user
  workflows;
- credential-free startup and `.env`-based credential configuration;
- local root npm entry points;
- application-owned maintainer script placement;
- structured progress for long local build, install, and smoke operations;
- native release verification through the same npm entry points;
- immediate terminal command discovery after default installation;
- native archives for macOS, Linux, and Windows on AMD64 and ARM64;
- native PowerShell installation without Git Bash, WSL, Python, or
  administrator privileges;
- manual archive download and direct-launch behavior;
- public publication of both installers and every native archive;
- separation from config-specific optimized PyInstaller bundles.

The application package owns this contract because it owns the command,
runtime archive builder, installer, and archive smoke. Root npm scripts expose
maintainer entry points but do not own the behavior.

## Goals

- Detect plugin-installation and application-boot failures before bundling.
- Exercise the extracted archive directly so installer behavior cannot hide an
  archive-launch or archive-plugin-install defect.
- Exercise each public default installer independently so archive-smoke helper
  behavior cannot hide a download, staging, command-installation, or PATH
  defect.
- Verify that both archive-based workflows can dynamically install a packaged
  plugin into separate fresh caches.
- Let a newly installed CLI start normally without credentials or exported
  shell variables.
- Let a default Bash installation place `crystal-lattice` in an existing
  suitable directory already present on PATH, so the current supported
  terminal can invoke it immediately by name.
- On native Windows, provide a no-admin PowerShell installation path that
  prefers an existing suitable command directory and otherwise establishes a
  conventional per-user command directory and PATH entry.
- Ship and natively verify macOS, Linux, and Windows archives for both AMD64
  and ARM64.
- Let users select and run a downloaded archive manually without depending on
  either installer.
- Verify that `.env` values reach config resolution without shell exports.
- Keep provider/tool request authentication with the package that owns that
  API contract.
- Run the direct archive and default-installer smokes on every native release
  target through the same root npm commands available to developers.
- Keep application-only build, install, release, and smoke entry points with
  the application package while retaining genuinely cross-runtime packaging
  primitives at the repository root.
- Give long-running maintainer and installer commands immediate numbered
  progress, visible child-process output, and explicit boot-wait status.
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
- Providing a separate native batch-file installer for `cmd.exe`; the
  PowerShell installer creates a command that subsequent PowerShell and
  `cmd.exe` terminals can resolve.
- Publishing Homebrew, Winget, Chocolatey, Scoop, npm, pipx, or other
  package-manager channels without a separately owned and verified release
  process.
- Moving the cloud-orchestrator/runtime packaging primitive cluster merely to
  eliminate every CLI-related filename from the root `scripts/` directory.

## Scenario names and historical terminology

The original work used “level 1”, “level 2”, and “level 3” as shorthand for
the increasing number of distribution transformations under test. The
numbers do not identify public products or permanent test names.

This specification and current documentation use these descriptive names:

| Current name | Historical shorthand | User workflow |
|---|---|---|
| Source-installation smoke | Level 1 | Install Core and the CLI into a fresh Python environment, then start the generated command. |
| Extracted-archive smoke | Level 2 | Unpack the shipped bundled-Python archive and run its launcher directly. |
| Default Bash-installer smoke | Level 3 | Run the public Bash installer with defaults, then invoke `crystal-lattice` by name from a Bash-compatible terminal. |
| Default PowerShell-installer smoke | Level 3 native-Windows path | Run the public PowerShell installer with defaults, then invoke `crystal-lattice` by name from PowerShell and a fresh `cmd.exe`. |

Code identifiers may retain an old number temporarily during migration, but
new commands, tests, messages, and documentation use the descriptive names.

## Distribution boundaries

| Distribution | Purpose | Plugin behavior | Verification scope |
|---|---|---|---|
| Bundled-Python runtime archive | Shipped general CLI distribution | Default-config plugins are preinstalled; additional supported plugins may install dynamically | Source-installation, extracted-archive, and default-installer smokes |
| Optimized PyInstaller bundle | Config-specific frozen runtime | Selected plugins are frozen; arbitrary dynamic installation is rejected | Existing separate optimized-bundle suite |

## Specification documents

- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)

## Current implementation documentation

- [CLI distribution implementation and verification](../../cli-distribution.md)
- [Application configuration](../../../configuration.md)
- [Configuration placeholders and `.env` loading](../../../configuration-placeholders.md)

## Related query contract

The
[session and message data query specification](../session-data-query/index.md)
adds one-shot session enumeration and per-session message projection. This
distribution specification owns only proof that those commands execute through
every supported source, archive, and installer entry point.
