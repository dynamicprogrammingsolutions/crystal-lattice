fastlane documentation
----

# Installation

Make sure you have the latest version of the Xcode command line tools installed:

```sh
xcode-select --install
```

For _fastlane_ installation instructions, see [Installing _fastlane_](https://docs.fastlane.tools/#installing-fastlane)

# Available Actions

## Mac

### mac verify

```sh
[bundle exec] fastlane mac verify
```

Run verification required before a macOS desktop release

### mac build

```sh
[bundle exec] fastlane mac build
```

Build and inspect an unsigned universal Release archive

### mac setup_signing

```sh
[bundle exec] fastlane mac setup_signing
```

Create or update Developer ID signing assets locally

### mac release

```sh
[bundle exec] fastlane mac release
```

Build, sign, notarize, staple, and validate the universal DMG

----

This README.md is auto-generated and will be re-generated every time [_fastlane_](https://fastlane.tools) is run.

More information about _fastlane_ can be found on [fastlane.tools](https://fastlane.tools).

The documentation of _fastlane_ can be found on [docs.fastlane.tools](https://docs.fastlane.tools).
