# CLI distribution verification

This application-owned specification defines the target verification contract
for the `crystal-lattice` command from source installation through the shipped
bundled-Python archive and its installed wrapper.

It covers:

- three ordered test levels that isolate source/bootstrap, archive-build, and
  installer defects;
- clean runtime state and default-configuration boot behavior;
- credential-free startup and `.env`-based credential configuration;
- local root npm entry points;
- the native release-archive smoke boundary;
- separation from config-specific optimized PyInstaller bundles.

The application package owns this contract because it owns the command,
runtime archive builder, installer, and archive smoke. Root npm scripts expose
maintainer entry points but do not own the behavior.

## Goals

- Detect plugin-installation and application-boot failures before bundling.
- Detect archive-construction and relocatability failures independently of the
  installer.
- Detect staging, replacement, wrapper, and installed-command failures after
  archive behavior is known to work.
- Let a newly installed CLI start normally without credentials or exported
  shell variables.
- Require real credentials only when an invoked provider or tool calls an API
  that requires them.
- Run the shipped archive smoke on every native release target without adding
  another CI workflow or matrix.

## Non-goals

- Exercising a real model request in the distribution boot checks.
- Defining one provider's authentication protocol or anonymous API access.
- Folding optimized PyInstaller bundle tests into the bundled-Python archive
  levels.
- Adding the slow local distribution commands to ordinary pull-request CI.
- Changing the public installer download or publication protocol.

## Distribution boundaries

| Distribution | Purpose | Plugin behavior | Verification scope |
|---|---|---|---|
| Bundled-Python runtime archive | Shipped general CLI distribution | Default-config plugins are preinstalled; additional supported plugins may install dynamically | Levels 1–3 and release archive smoke |
| Optimized PyInstaller bundle | Config-specific frozen runtime | Selected plugins are frozen; arbitrary dynamic installation is rejected | Existing separate optimized-bundle suite |

## Specification documents

- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)

## Current implementation documentation

- [CLI distribution implementation and verification](../../cli-distribution.md)
- [Application configuration](../../../configuration.md)
- [Configuration placeholders and `.env` loading](../../../configuration-placeholders.md)

## Active delivery

The active work is tracked in
`tasks/20260908-cli-distribution-test-levels.md`.
The current implementation has structural archive and installed-command
checks, but it does not yet provide all three boot levels or a
default-configuration boot in the release archive smoke.