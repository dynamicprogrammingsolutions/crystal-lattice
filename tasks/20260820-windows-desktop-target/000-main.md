# Add A Windows Desktop Target And Automated Distribution

Create a production Windows host for Crystal Lattice Control that reuses the
desktop application’s shared React/state/backend behavior while implementing
Windows-native hosting, platform adapters, packaging, automated builds, native
testing, and release acceptance. Preserve the existing macOS application and
prepare platform boundaries that a later Linux host can reuse.

## Requirements checklist

- [ ] A supported React Native Windows host builds and runs without forcing the macOS host onto an incompatible or unsupported React Native version.
- [ ] Shared desktop application behavior is owned by a platform-neutral package or boundary consumed by both macOS and Windows hosts.
- [ ] Platform-specific menus, popovers/transient surfaces, file selection, text input, scroll metrics, theme integration, and window management have explicit Windows implementations or approved functional fallbacks.
- [ ] Core connections, sessions, messages, streaming, settings, plugins, notifications, attachments, persistence, and keyboard/accessibility behavior work on Windows.
- [ ] Required secondary-window and multiwindow behavior works through a maintained Windows host implementation without depending on unsupported React Native Windows architecture.
- [ ] Native Windows unit/component and end-to-end UI testing covers production UI and multiwindow behavior.
- [ ] Release builds produce signed, installable Windows packages for the approved architectures with clean installation and upgrade behavior.
- [ ] GitHub Actions verifies shared code, builds Windows targets, runs native tests, packages, signs, and publishes release outputs without exposing credentials.
- [ ] A documented workflow supports daily ARM64 testing from the current Apple Silicon Mac and native x64 acceptance on remote or physical Windows.
- [ ] Existing macOS behavior and tests remain supported throughout the extraction and Windows implementation.
- [ ] Current user and maintainer documentation explains supported Windows installation, development, testing, release, and platform differences.

## Roadmap status updates

Roadmap:
[Open Source and iOS Release](../../roadmaps/open-source-and-ios-release.md)

Instructions:
[Updating a roadmap through CSV](../../roadmaps/docs/updating-roadmaps.md)

Do not read the linked roadmap or instructions, inspect roadmap state, or
update the roadmap as part of routine task execution or completion. Do so only
when the user explicitly requests a roadmap status update, for example:
“update the task status in the roadmap as per the instructions in the main
task.”

That explicit request authorizes reading the linked files, updating the
authored CSV and generated Markdown, and synchronizing the configured Google
Sheet as required by the instructions. It does not authorize unrelated roadmap
changes. If the user limits the request to local files, do not mutate the
sheet.

## Subtasks

- [ ] `tasks/20260820-windows-desktop-target/010-windows-compatibility-architecture-spike.md`
- [ ] `tasks/20260820-windows-desktop-target/020-extract-shared-desktop-application.md`
- [ ] `tasks/20260820-windows-desktop-target/030-bootstrap-react-native-windows-host.md`
- [ ] `tasks/20260820-windows-desktop-target/040-windows-core-feature-parity.md`
- [ ] `tasks/20260820-windows-desktop-target/050-windows-native-host-parity.md`
- [ ] `tasks/20260820-windows-desktop-target/060-windows-native-testing.md`
- [ ] `tasks/20260820-windows-desktop-target/070-windows-msix-signing.md`
- [ ] `tasks/20260820-windows-desktop-target/080-windows-github-actions.md`
- [ ] `tasks/20260820-windows-desktop-target/090-windows-release-acceptance.md`

## Research snapshot

Research was performed on August 20, 2026. The completing agent has internet
access and must recheck current official React Native Windows, React Native
macOS, Microsoft, Appium, Visual Studio, Windows App SDK, GitHub Actions, MSIX,
and signing guidance before implementation.

### Current repository state

- The existing host is `desktop/crystal-lattice-control-desktop-rn`.
- Current dependencies:
  - `react`: `19.1.4`
  - `react-native`: `0.81.6`
  - `react-native-macos`: `0.81.8`
  - `@crystal-lattice/react-native-mac-text-view`: local macOS-only package
- The existing native host uses legacy bridge/view-manager APIs such as `RCT_EXPORT_METHOD`, `RCTBridgeModule`, and `RCTViewManager`.
- `DesktopWindowManager` has 18 TypeScript consumers.
- Four files consume the custom macOS text-view surface.
- Seven files consume the macOS scroll-metrics bridge.
- Twelve files contain direct `Platform.OS` behavior.
- `index.js` registers 17 React roots, including the main application, native UI harnesses, secondary windows, and popover content.
- The macOS host implements:
  - multiple main and secondary `NSWindow` instances;
  - `NSPopover` transient surfaces;
  - application/Dock menus and native menu events;
  - native attachment selection;
  - system-theme events;
  - custom checkbox/select/text-view/scroll-metrics bridges;
  - native XCUITest harnesses.

### Discovered compatibility constraint

- Current React Native Windows documentation targets the 0.84 line.
- React Native Windows versions match the corresponding React Native minor version.
- React Native Windows 0.81 reached end of support on June 30, 2026.
- Installing a supported React Native Windows 0.84 host into the existing React Native 0.81/macOS package would create an incompatible React Native peer/version boundary.
- Using React Native Windows 0.81 might enable a throwaway compatibility experiment, but it is not an acceptable production foundation because it is unsupported.

### Recommended architecture

Do not add `react-native-windows` directly to the current macOS package.
Create a separate Windows native host that consumes extracted shared desktop
application code:

```text
packages/frontend-desktop-app/
    shared React components, state, orchestration, and platform contracts

desktop/crystal-lattice-control-desktop-rn/
    existing React Native macOS host

desktop/crystal-lattice-control-windows-rn/
    new React Native Windows host
```

The exact shared package name may change after ownership inspection, but the
separate-host/version boundary is the recommended solution.

The shared package should treat `react` and `react-native` as peer dependencies
so each native host resolves its compatible version. Significant platform
behavior should use `.macos.ts[x]` and `.windows.ts[x]` implementations behind
small contracts rather than scattered `Platform.OS` branching.

Recommended platform contracts:

```text
DesktopWindowHost
DesktopTransientHost
DesktopMenuHost
DesktopFilePicker
DesktopTextView
DesktopScrollMetrics
DesktopThemeHost
DesktopTestHost
```

### React Native Windows implementation constraints

- Current React Native Windows uses the New Architecture and Windows App SDK.
- New Windows native modules use Codegen and C++ TurboModules.
- Native UI components use Fabric component views.
- The current New Architecture does not provide the old Windows-specific React `Flyout` and `Popup` components.
- Arbitrary WinUI/XAML controls inside custom Fabric components are not documented as production-ready.
- Functional React overlays/modals are therefore the recommended first Windows implementation for transient UI; native Windows presentation should follow where it provides necessary accessibility, keyboard, anchoring, or window behavior.
- Separate Windows React-root windows are a high-risk host capability and require a focused spike before generic parity work.

### Build, packaging, and testing conclusions

- Windows native development/building requires Windows; it cannot run directly under macOS.
- Use Windows 11 ARM in Parallels on the current Apple Silicon Mac for daily ARM64 development and manual testing.
- Use GitHub `windows-2025` and a real/remote x64 Windows system for native x64 build and acceptance.
- GitHub currently documents `windows-11-arm` hosted runners; reverify repository/plan availability at implementation time.
- Use MSIX for the first maintained Windows package, with x64 first and ARM64 added as soon as the host path is stable.
- Prefer Azure Artifact Signing or another publicly trusted production code-signing path; self-signed packages are test-only.
- The closest Windows native UI automation equivalent to XCUITest is Appium with the Windows driver and Windows UI Automation.
- Microsoft currently recommends Appium for Windows App SDK UI testing, but the underlying WinAppDriver server is not actively developed. Pin the stack and keep the test-host interface replaceable.
- Reliable full desktop UI automation may need a persistent interactive self-hosted Windows runner or disposable Windows VM even if short smoke tests run on GitHub-hosted runners.

### Linux follow-up

Linux implementation is out of scope. The shared/platform boundaries created
here must not assume Windows/macOS are the only hosts. A later Linux task must
choose its renderer/host independently; current React Native documentation
lists React Native Skia as a community out-of-tree Linux option rather than a
first-party equivalent of React Native Windows.

## Out of scope

- Implementing or releasing the Linux desktop host.
- Bundling the Crystal Lattice CLI into the Windows installer.
- Microsoft Store submission unless separately approved.
- Automatic Windows application updates beyond normal package upgrade behavior.
- Replacing all platform-appropriate Windows UI with macOS-identical visuals.

## Reference links

- React Native Windows getting started: https://microsoft.github.io/react-native-windows/docs/getting-started
- React Native Windows support policy: https://microsoft.github.io/react-native-windows/support
- React Native Windows New Architecture: https://microsoft.github.io/react-native-windows/docs/new-architecture
- React Native Windows native modules: https://microsoft.github.io/react-native-windows/docs/native-platform-modules
- React Native Windows dependencies: https://microsoft.github.io/react-native-windows/docs/rnw-dependencies
- React Native Windows CLI: https://microsoft.github.io/react-native-windows/docs/run-windows-cli
- React Native platform-specific code: https://reactnative.dev/docs/platform-specific-code
- Windows App SDK testing: https://learn.microsoft.com/windows/apps/develop/testing/
- Appium Windows driver: https://github.com/appium/appium-windows-driver
- MSIX packaging: https://learn.microsoft.com/windows/apps/package-and-deploy/packaging/
- MSIX signing: https://learn.microsoft.com/windows/msix/package/sign-msix-package-guide
- GitHub-hosted runners: https://docs.github.com/actions/reference/runners/github-hosted-runners
- Windows on Apple Silicon Mac: https://support.microsoft.com/windows/options-for-using-windows-11-with-mac-computers-with-apple-m1-m2-and-m3-chips
- React Native out-of-tree platforms: https://reactnative.dev/docs/out-of-tree-platforms

## Execution plan
Status: Draft

Execute the subtasks in numeric order. Treat subtask 010 as a mandatory
architecture gate: do not perform a broad shared-code move or generate the
production Windows host until a supported compatibility combination and host
layout have been demonstrated. Preserve a passing macOS consumer after every
shared extraction step.

Deliver a functional single-window Windows application before investing in
full native secondary-window parity. Keep the early Windows fallback surfaces
accessible and production-quality rather than adding test-only shortcuts.
After native parity, establish repeatable Windows UI automation, then package,
sign, automate, and complete human acceptance.

### Implementation decisions and open questions

- Recommendation: separate macOS and Windows host packages consuming a shared desktop app package.
- Recommendation: use supported RNW 0.84 or the current supported successor at implementation time; do not release on unsupported RNW 0.81.
- Recommendation: use the RNW C++ application template and C++/WinRT native host code.
- Recommendation: x64 is the first production architecture; ARM64 is developed/tested early because the available local Mac runs Windows ARM.
- Recommendation: use functional shared React overlays for early popover/menu parity and add native presentation selectively.
- Material open question for 010: whether the current React Native macOS host can be upgraded to a common supported minor by execution time. Even if it can, retain separate native host projects unless a one-package approach proves materially safer.
- Material open question for 050: whether current RNW APIs can host multiple React roots in independent Windows App SDK windows without maintaining a custom fork.
- Material open question for 060: whether GitHub-hosted runner UI sessions are reliable enough for the full Appium suite or only smoke tests.

### Documentation

- Shared desktop contracts and implementation guidance belong with the package that owns the extracted shared application.
- Windows installation, first use, support, and troubleshooting belong under the Windows host’s public documentation.
- Windows native hosting, testing, packaging, signing, CI, and release runbooks belong under the Windows host’s `docs/development/`.
- Existing macOS documentation should change only where shared ownership or setup actually changes.
- Public documentation must describe current delivered behavior and omit task identifiers, phases, target-only claims, and internal approval state.
- Generated build, package, documentation-site, and release output must not be edited directly.

### Task checklist

- [ ] Complete compatibility and architecture spike.
- [ ] Extract shared application code while keeping macOS green.
- [ ] Bootstrap the supported Windows host and connect to a real backend.
- [ ] Complete core single-window Windows parity.
- [ ] Complete native Windows window/menu/transient-host parity.
- [ ] Add native Windows test infrastructure and production selectors.
- [ ] Produce signed installable Windows packages.
- [ ] Add protected GitHub Actions build/release automation.
- [ ] Complete ARM64 and x64 release acceptance.
- [ ] Keep this main checklist synchronized with subtask evidence.

### Requirement verification

- Verify shared behavior through both real macOS and Windows consumers rather than shared-package mocks alone.
- Verify Windows host support status and version compatibility against current official documentation at execution time.
- Verify native host parity through production windows, menus, transient surfaces, file selection, text/scroll behavior, keyboard, accessibility, and lifecycle.
- Verify package and automation requirements using downloadable signed packages installed on clean Windows systems.
- Verify manual-from-Mac guidance by performing the documented ARM64 VM workflow on this Apple Silicon Mac.

### Additional implementation verification

- Exercise high DPI, text scaling, high contrast, keyboard-only navigation, multiple monitors, sleep/resume, network reconnect, file picker, clipboard, and window restoration.
- Track build/test duration and Windows runner consumption.
- Confirm shared extraction introduces no hidden dependency on the macOS-only text-view package or native bridge.