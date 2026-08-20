# Add Native Windows Test Infrastructure

Create the Windows equivalent of the macOS XCUITest coverage, including native
unit tests, production-root harnesses, Appium/UI Automation flows, package
smokes, and a reliable interactive runner strategy.

## Requirements checklist

- [ ] Windows native modules and host registries have focused native unit tests.
- [ ] Production entity rows, action triggers, menus, dialogs, popovers, windows, and controls expose stable accessibility/test identifiers.
- [ ] Deterministic test roots exercise production components rather than harness-only copies.
- [ ] Appium Windows UI automation covers main-window startup, connection/session/chat flow, menus/transient UI, and secondary-window lifecycle.
- [ ] Multiwindow tests switch among real Windows and verify submit/cancel/focus/close behavior.
- [ ] Test tooling versions and the WinAppDriver dependency are pinned, diagnosed, and replaceable.
- [ ] Short native smoke tests run in routine CI and the full suite has a documented persistent/self-hosted or disposable interactive Windows runner.
- [ ] Failed collection, driver startup, teardown, open handles, or background processes fail the test run.
- [ ] Manual native test instructions work from the Apple Silicon Mac through a Windows 11 ARM VM.

Parent Task: tasks/20260820-windows-desktop-target/000-main.md
Depends On: tasks/20260820-windows-desktop-target/050-windows-native-host-parity.md

## Research conclusions

- The closest practical Windows equivalent to XCUITest is Appium 3 with the Windows driver and Windows UI Automation.
- Microsoft currently recommends Appium for Windows App SDK UI testing.
- The Appium Windows driver uses WinAppDriver, whose server is not actively developed; version pinning and an abstraction around driver startup are required.
- GitHub-hosted runners may support short launch tests, but a persistent interactive desktop session may be required for reliable full UI automation.

## Execution plan
Status: Draft

Define the Windows native test pyramid and selectors. Add native C++ tests for
host logic, deterministic React roots for production components, and Appium
tests that install/launch the real application and operate through UI
Automation. Establish a small GitHub-hosted smoke slice and a full-suite runner
with a documented clean/reset lifecycle. Reuse backend simulator/public API
fixtures where they cross the real frontend adapter.

### Implementation decisions and open questions

- Prefer Appium as the initial UI automation layer while isolating driver-specific startup/session code.
- Do not accept screenshot-only or coordinate-only automation when stable accessibility selectors are possible.
- Decide hosted versus self-hosted full-suite placement with measured evidence rather than assuming hosted UI sessions are reliable.
- If WinAppDriver blocks required behavior, investigate current maintained alternatives and present the migration cost before switching.

### Documentation

- Add Windows native/UI test setup, driver versions, selectors, commands, runner/session requirements, debugging, and cleanup to Windows development docs.
- Keep test harness details out of public user documentation.

### Task checklist

- [ ] Define the Windows test pyramid and acceptance boundaries.
- [ ] Add stable production accessibility/test identifiers.
- [ ] Add native C++ host/module tests.
- [ ] Add deterministic production-root integration harnesses.
- [ ] Pin/install Appium Windows tooling and driver lifecycle.
- [ ] Add main-window and multiwindow UI tests.
- [ ] Add package install/launch smoke tests.
- [ ] Establish hosted smoke and full interactive runner commands.
- [ ] Verify cleanup, teardown, and failure reporting.
- [ ] Run the manual VM workflow from the current Mac.

### Requirement verification

- Run collected native unit, integration, and UI tests successfully on Windows.
- Verify UI tests select production controls through UI Automation identifiers.
- Verify multiwindow tests operate real secondary windows and detect duplicate/missing events.
- Verify the full test environment can be reset and rerun without manual residue.

### Additional implementation verification

- Exercise high DPI, high contrast, keyboard-only, multiple monitors, slow backend, and reconnect cases in targeted suites.
- Record test duration and flake rate before making suites required.