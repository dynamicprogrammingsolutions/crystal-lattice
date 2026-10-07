# Confirm macOS Release Contract And Preflight

Audit the current desktop, CLI, website, release, and signing state and record
the final release contract before changing production metadata or automation.

## Requirements checklist

- [x] The release contract records the approved product identity, bundle ID, versioning, deployment target, architectures, and Apple team and identifies any conflict with the current project.
- [ ] The release contract defines the app-only DMG and architecture-specific app-plus-CLI PKGs as separate maintained products.
- [ ] An evidence-backed preflight report covers sandbox, hardened-runtime, entitlements, privacy, native dependency, CLI-runtime, download-hosting, and clean-machine constraints.
- [ ] The preflight report separates every manual Apple/GitHub prerequisite from automatically implementable work without exposing secrets.
- [ ] A concrete gap list and dependency map lets downstream subtasks proceed without repeating discovery.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md

## Reconciliation — October 7, 2026

Progress: partially fulfilled through
`tasks/20260928-universal-macos-desktop-fastlane-release.md`. Its approved
contract and published `0.9.0 (4)` metadata establish the app name, bundle ID,
team, macOS 14 minimum and universal architectures. Remaining work is the
combined-installer contract, CLI/workspace constraints, manual Installer
prerequisites and final gap/dependency report. Reuse the app audit evidence.

The retained execution plan remains Draft for that remaining work.

## Decisions and requirement questions

- Decision: product name is `Crystal Lattice Desktop`, following the approved September release.
- Decision: use `com.dynamicprogrammingsolutions.crystallatticecontrol.macos` unless Apple or an existing registered identifier creates a verified conflict.
- Decision: target macOS 14.0, universal GUI output, app-only DMG, and ARM64/Intel combined PKGs.
- Decision: direct distribution does not use Mac App Store submission.
- Requirement question: none currently blocks planning. If the bundle ID is already registered to an incompatible target or macOS 14.0 is unsupported by an essential dependency, stop and request a scope decision.

## Research and supporting facts

The template/signing findings below are historical August starting points.
The September task records their app-only resolution; they are not current
release blockers.

- Current project values include template product/bundle naming and Apple Development signing.
- The Xcode and Podfile deployment targets conflict.
- Hardened Runtime is enabled, but the existing entitlement file is not assigned.
- App Sandbox is optional for direct distribution but affects file access, workspace onboarding, and global profile discovery.
- Apple, GitHub, fastlane, and runner behavior may change; use current official documentation during execution.

## Execution plan
Status: Draft

Inspect the current worktree and generated build settings without mutating
production configuration. Confirm package-local guidance first. Run read-only
Xcode, Ruby, Node, CocoaPods, asset, signing, CLI-package, workflow, landing,
privacy, support, and download-infrastructure checks. Record exact current
values, conflicts, credential prerequisites, runner requirements, and release
boundaries in this task.

### Implementation decisions and open questions

- Recommend App Sandbox only if attachment, download, selected-workspace persistence, local network access, and profile discovery all pass with least-privilege entitlements.
- If sandboxing blocks approved behavior, document the security tradeoff and use Hardened Runtime without App Sandbox for direct distribution.
- Confirm whether one workflow with independent DMG/PKG jobs or separate workflows provides the clearest protected-environment and publication boundaries; defer implementation to subtasks 060 and 100.

### Documentation

- Do not publish speculative findings as current user behavior.
- Record durable release-maintainer findings in the future desktop release development page only when implementation makes them current.

### Task checklist

- [ ] Read the desktop README/development index and affected package guidance.
- [ ] Inspect Xcode target, workspace, schemes, configurations, metadata, assets, entitlements, and dependency targets.
- [ ] Inspect CLI package layouts, sizes, architectures, launchers, tests, and publication workflow.
- [ ] Inspect current GitHub Actions, signing repository assumptions, download infrastructure, landing routes, privacy, and support content.
- [ ] Verify current official Apple/GitHub/fastlane guidance.
- [ ] Record the final preflight matrix and any blocking discrepancies.

### Requirement verification

- Review the recorded contract against every requirement in the parent task.
- Verify the audit cites concrete project settings, files, commands, or official sources for each identified constraint.
- Confirm downstream task dependencies and manual prerequisites are explicit.

### Additional implementation verification

- Run `xcodebuild -showBuildSettings` and `xcodebuild -list` against the actual workspace/scheme.
- Confirm no credential value is printed or committed during inspection.