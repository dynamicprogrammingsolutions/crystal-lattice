# Distribution And Release Workstreams

Create a complete distribution plan and implementation path for the Python desktop/server components and the React Native mobile app, so releases can be built in CI and installed by end users through standard channels.

## Task checklist

- [x] `tasks/20260421-distribution-release-workstreams/010-python-packaging-and-cli.md`
- [x] `tasks/20260421-distribution-release-workstreams/020-cross-platform-binary-builds.md`
- [x] `tasks/20260421-distribution-release-workstreams/030-github-releases-and-ci.md`
- [x] `tasks/20260421-distribution-release-workstreams/040-curl-installer.md`
- [x] `tasks/20260421-distribution-release-workstreams/045-readme-quickstart-revision.md`
- [ ] `tasks/20260421-distribution-release-workstreams/050-homebrew-distribution.md`
- [x] `tasks/20260421-distribution-release-workstreams/055-aws-fargate-external-bridge.md`
- [ ] `tasks/20260421-distribution-release-workstreams/060-npm-global-installer.md`
- [ ] `tasks/20260421-distribution-release-workstreams/070-android-release-distribution.md`
- [ ] `tasks/20260421-distribution-release-workstreams/080-ios-release-distribution-and-review-readiness.md`

## Context summary

- Python packaging exists in `core/python/pyproject.toml:5-43` and `application/python/pyproject.toml:5-29`; the installable CLI distribution is now `crystal-lattice-cli`, with the `crystal-lattice` console script targeting `agent_terminal_app.__main__:main`.
- `crystal-lattice-cli` currently depends on `agent-core>=0.3.0` and requires Python `>=3.10`; if we want users to avoid managing Python versions, binary packaging needs to bundle the interpreter and dependencies.
- The mobile app already has stable package identifiers and basic release metadata anchors:
  - Android package/version settings in `mobile/crystal-lattice-control-rn/android/app/build.gradle:75-107`.
  - iOS bundle/version settings in `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN.xcodeproj/project.pbxproj:260-314`.
  - iOS local network / Bonjour permissions in `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/Info.plist:29-45`.
- The React Native app is a companion client today, not a standalone experience. The current connection flow and health-check UI live in `mobile/crystal-lattice-control-rn/App.tsx:46-143` and `mobile/crystal-lattice-control-rn/src/ConnectionScreen.tsx:6-74`.

## Recommended sequencing

1. Land Python packaging and CLI entrypoint work first so all downstream release channels target one stable command.
2. Standardize binary build outputs and release asset naming before adding installers.
3. Add tag-driven GitHub Releases CI next, then layer `curl`, Homebrew, and optional npm distribution on top of those release assets.
4. Prepare Android and iOS release workflows in parallel once product messaging and companion-app positioning are settled.

## Release assumptions captured from planning

- Preferred desktop/server distribution stack:
  - PyPI for source/venv installs.
  - PyInstaller-style bundled binaries for Linux, macOS, and Windows.
  - GitHub Releases as the canonical binary host.
  - Optional convenience channels built on top of GitHub Releases: `curl | bash`, Homebrew, npm global install.
- Preferred mobile release posture:
  - Android via Play Console and signed `.aab` bundles.
  - iOS via TestFlight first, with public or unlisted App Store release as a later decision.
  - Public iOS distribution is acceptable even if the app remains a companion client, as long as the dependency on the desktop/server component is clearly explained and the no-server state is handled gracefully.