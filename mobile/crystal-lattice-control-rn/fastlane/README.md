fastlane documentation
----

# Installation

Make sure you have the latest version of the Xcode command line tools installed:

```sh
xcode-select --install
```

For _fastlane_ installation instructions, see [Installing _fastlane_](https://docs.fastlane.tools/#installing-fastlane)

# Available Actions

## iOS

### ios verify

```sh
[bundle exec] fastlane ios verify
```

Run mobile verification required before an iOS release

### ios setup_signing

```sh
[bundle exec] fastlane ios setup_signing
```

Create or update App Store signing assets in the private match repository

### ios build

```sh
[bundle exec] fastlane ios build
```

Create a signed App Store Connect IPA without uploading it

### ios beta

```sh
[bundle exec] fastlane ios beta
```

Verify, archive, and upload an internal TestFlight build

----

This README.md is auto-generated and will be re-generated every time [_fastlane_](https://fastlane.tools) is run.

More information about _fastlane_ can be found on [fastlane.tools](https://fastlane.tools).

The documentation of _fastlane_ can be found on [docs.fastlane.tools](https://docs.fastlane.tools).
