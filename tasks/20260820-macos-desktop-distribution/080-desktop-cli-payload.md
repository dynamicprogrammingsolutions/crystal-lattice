# Prepare The Desktop-Bundled CLI Payload

Adapt the existing bundled-Python CLI distribution into signed,
architecture-specific payloads suitable for installation alongside the desktop
application without coupling CLI lifetime to the GUI process.

## Requirements checklist

- [ ] ARM64 and AMD64 CLI payloads are built from the same repository source and pin an explicit CLI version for each desktop release.
- [ ] Each payload remains relocatable at the approved system installation root and starts without the desktop application running.
- [ ] Every executable, dylib, native Python extension, and other signable code item has a valid Developer ID Application signature suitable for PKG notarization.
- [ ] `crystal-lattice --version` reports the effective CLI version and installation diagnostics can distinguish desktop-bundled and standalone commands.
- [ ] Dynamic plugin installation and user-owned config, sessions, credentials, and plugin caches continue to use user locations rather than the read-only installed runtime.
- [ ] Standalone `~/.local` CLI installations can coexist without being deleted or overwritten.
- [ ] Architecture, relocation, signature, runtime-layout, default-plugin, and command smoke tests cover both payloads.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
Depends On: tasks/20260820-macos-desktop-distribution/070-app-only-release-acceptance.md

## Approved payload model

- Reuse `scripts/build_crystal_lattice_python_runtime_package.py`.
- Install the desktop-bundled runtime under a versioned system path beneath `/Library/Application Support/Crystal Lattice/CLI/`.
- Build one CLI payload per architecture.
- Do not copy both complete CLI runtimes into every installer.
- Do not invoke the public curl installer from a PKG script.

## Execution plan
Status: Draft

Extend the existing CLI package builder or add a narrow staging layer that
consumes its output. Define a version manifest linking desktop version, CLI
version, platform, architecture, and package layout. Add global version output,
stage the payload at the intended installation path, recursively identify and
sign native code inside-out, and run the existing plus new smoke tests from a
path containing spaces and from a read-only runtime.

### Implementation decisions and open questions

- Keep the existing CLI release archives unchanged unless a shared builder fix is required.
- The desktop release builds the pinned CLI from the same checked-out commit; it must not download a mutable `latest` CLI during packaging.
- Install only immutable runtime code system-wide; all mutable state remains user-owned.
- Define clear behavior when both `/usr/local/bin/crystal-lattice` and `~/.local/bin/crystal-lattice` exist, but do not rewrite user shell profiles.

### Documentation

- Update application/CLI user documentation with the desktop-bundled installation path, `--version`, coexistence, PATH diagnostics, and state ownership.
- Add CLI payload build/signing details to the owning CLI development documentation if a focused page exists or is justified.
- Update desktop release development documentation with the pinned-version and payload-consumption contract.

### Task checklist

- [ ] Define the desktop-to-CLI version manifest.
- [ ] Add user-facing CLI version reporting.
- [ ] Build ARM64 and AMD64 runtime payloads.
- [ ] Stage and execute each payload from the approved system-style path.
- [ ] Discover and sign all native code with Developer ID Application.
- [ ] Verify runtime layout, built-in plugins, dynamic plugin path, and user-state paths.
- [ ] Test coexistence with a standalone user-scoped CLI.
- [ ] Measure compressed/uncompressed size and record release impact.

### Requirement verification

- Run `crystal-lattice --help`, `--version`, and `--runtime-layout-json` from each staged payload with the desktop app stopped.
- Start a real local server from each architecture-appropriate payload and exercise the public HTTP API.
- Verify signatures and architecture for every discovered Mach-O file.
- Verify writes occur only in approved user/workspace locations.

### Additional implementation verification

- Test staging under a path containing spaces.
- Test dynamic plugin installation using the packaged interpreter.
- Compare staged payload contents against the existing CLI release package to detect accidental omissions.