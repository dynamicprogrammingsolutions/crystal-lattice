# Validate Windows Compatibility And Host Architecture

Prove a supported React Native Windows compatibility path and decide the
macOS/shared/Windows package boundaries before broad implementation begins.

## Requirements checklist

- [ ] Current supported React Native Windows and React Native macOS version lines, support dates, New Architecture requirements, Visual Studio/SDK requirements, and package-manager constraints are recorded from official sources.
- [ ] The known React Native 0.81 macOS versus supported Windows version incompatibility is reproduced or disproved with concrete dependency evidence.
- [ ] A small Windows C++ host spike builds on Windows and renders shared React content using the selected supported RNW version.
- [ ] The spike demonstrates monorepo workspace resolution and a real request to a Crystal Lattice backend.
- [ ] A written architecture decision selects the host/package layout, upgrade strategy, initial architectures, native-module model, and fallback policy.
- [ ] The chosen path preserves a working macOS host and does not establish unsupported RNW as the production baseline.

Parent Task: tasks/20260820-windows-desktop-target/000-main.md

## Research and conclusions to preserve

- Current local macOS host: React Native 0.81.6 and react-native-macos 0.81.8.
- RNW versions match React Native minor versions.
- RNW 0.81 support ended June 30, 2026.
- Current RNW documentation uses 0.84 and the New Architecture.
- Recommended resolution: separate native host packages with a shared desktop application package using React/React Native peer dependencies.
- A throwaway RNW 0.81 build may be useful only as diagnostic evidence; it must not become the production target.

## Execution plan
Status: Draft

Recheck official versions/support and audit every direct desktop dependency.
On a Windows environment, create a disposable supported RNW C++ app, integrate
one small shared component plus the frontend SDK transport/backend, and produce
Debug and ReleaseBundle builds. Compare separate-host and one-package options,
including Metro, peer dependencies, native modules, test tooling, and upgrade
risk. Record the decision and migration boundaries.

### Implementation decisions and open questions

- Prefer a supported current RNW release over matching the old macOS minor.
- Prefer a separate Windows host even if a common minor becomes available, unless the spike proves a combined package simpler without coupling release cadences.
- Decide whether the shared package belongs under `packages/` or a desktop-owned shared directory based on public ownership and reuse.
- Confirm x64-first production while enabling ARM64 development from the local VM.

### Documentation

- Keep spike-only commands/results in this task.
- Record the accepted current host architecture in Windows development documentation only when the production host is created.

### Task checklist

- [ ] Recheck current RNW/RNM versions, support policy, New Architecture, and Windows prerequisites.
- [ ] Audit dependency platform/version compatibility.
- [ ] Prepare a Windows 11 development environment.
- [ ] Generate a disposable RNW C++ host.
- [ ] Render shared content and call a real backend.
- [ ] Build Debug and ReleaseBundle outputs.
- [ ] Compare package-layout options and write the architecture decision.
- [ ] Identify migration blockers and update downstream plans if necessary.

### Requirement verification

- Provide package-manager and build evidence for the compatibility conclusion.
- Provide a runnable Windows spike and successful backend response.
- Verify the selected production path uses a supported RNW line.
- Verify no macOS package or current behavior was broken by the spike.

### Additional implementation verification

- Test a path containing spaces and monorepo symlink/workspace resolution.
- Record Visual Studio, Windows SDK, Node, package-manager, RN, RNW, Hermes, and architecture versions.