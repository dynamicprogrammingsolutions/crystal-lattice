# Produce Separate Combined App-And-CLI PKG Outputs

Add signed, notarized PKG installers that install the universal desktop
application plus one matching CLI runtime, while retaining the app-only DMG as
an independent output.

## Requirements checklist

- [ ] An Apple Silicon PKG installs the universal app and ARM64 CLI payload.
- [ ] An Intel PKG installs the universal app and AMD64 CLI payload.
- [ ] Both PKGs install a working `crystal-lattice` command in `/usr/local/bin` without modifying user shell profiles.
- [ ] The command runs independently when the desktop app has never launched or is not running.
- [ ] Package identifiers, receipts, versioning, ownership, permissions, upgrade behavior, and removal instructions are stable and documented.
- [ ] Developer ID Application signs executable code and Developer ID Installer signs each final PKG.
- [ ] Each PKG is notarized, stapled, Gatekeeper-valid, checksummed, and clearly named by architecture.
- [ ] Building PKGs does not remove, overwrite, or weaken the app-only DMG output.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
Depends On: tasks/20260820-macos-desktop-distribution/080-desktop-cli-payload.md

## Approved installation layout

```text
/Applications/Crystal Lattice Control.app
/Library/Application Support/Crystal Lattice/CLI/<cli-version>/<architecture>/...
/usr/local/bin/crystal-lattice
```

The exact wrapper target and version-directory switching mechanism may be
refined, but the installation must remain system-wide, deterministic, and
independent of the GUI process.

## Execution plan
Status: Draft

Build component payload roots for the app, CLI runtime, and terminal entry.
Use stable package identifiers and a distribution/product package definition
to produce one PKG per CLI architecture. Ensure scripts are minimal,
idempotent, offline, and do not download code. Sign executable content before
package creation, sign the flat PKG with Developer ID Installer, notarize,
staple, validate, and exercise fresh install and upgrade paths.

### Implementation decisions and open questions

- Keep the app universal even though the PKG is architecture-labeled by its CLI payload.
- Prefer a small wrapper at `/usr/local/bin/crystal-lattice` over an external symlink when it provides clearer missing/moved-runtime errors and stable upgrade switching.
- Package scripts must not infer a login user’s home directory or mutate user-owned CLI installations.
- Preserve the most recent known-good runtime until the new package install succeeds; define cleanup of obsolete system runtime versions explicitly.

### Documentation

- Add current combined-installer installation, PATH, upgrade, coexistence, and removal guidance to desktop user documentation.
- Add package layout, identifiers, build, signing, notarization, receipt, and recovery details to desktop release development documentation.
- Keep CLI-specific state ownership and coexistence detail in application/CLI documentation.

### Task checklist

- [ ] Define package identifiers, components, payload roots, permissions, and version mapping.
- [ ] Build ARM64 and Intel PKGs while preserving the DMG build.
- [ ] Verify fresh installation and command availability.
- [ ] Verify the CLI works with the app stopped/never launched.
- [ ] Verify upgrade from an older combined PKG.
- [ ] Verify coexistence with `~/.local/bin/crystal-lattice`.
- [ ] Sign, notarize, staple, and validate both PKGs.
- [ ] Generate checksums, manifests, and removal instructions.

### Requirement verification

- Install each PKG on the matching architecture and verify app launch, `command -v`, `crystal-lattice --version`, runtime layout, and local server startup.
- Inspect package signatures, receipts, installed ownership/permissions, and Gatekeeper assessment.
- Rebuild the DMG and confirm it remains app-only and valid.

### Additional implementation verification

- Test paths and wrapper diagnostics after a failed/incomplete runtime switch in a controlled staging environment.
- Confirm installer scripts make no network requests.
- Verify uninstall instructions remove system-owned files without touching user state.