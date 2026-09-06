This is the Crystal Lattice Control **desktop** frontend (React Native macOS), bootstrapped using [`@react-native-community/cli`](https://github.com/react-native-community/cli) and `react-native-macos`.

## Versions

- Desktop: `react-native@0.81.5` + `react-native-macos@0.81.1` (`desktop/crystal-lattice-control-desktop-rn/package.json:1`)
- Mobile (reference): `react-native@0.82.1` (`mobile/crystal-lattice-control-rn/package.json:1`)

## Monorepo shared packages

This app imports workspace packages via `file:` dependencies:

- `@crystal-lattice/frontend-sdk`
- `@crystal-lattice/frontend-sdk-react`
- `@crystal-lattice/frontend-rn-components`

Metro + TS are configured to handle symlinks (`desktop/crystal-lattice-control-desktop-rn/metro.config.js:1`, `desktop/crystal-lattice-control-desktop-rn/tsconfig.json:1`).

## User documentation

- [Home, Watchlist, History, status, and session tabs](docs/home-and-session-navigation.md)

## Development documentation

- [Desktop development](docs/development/index.md)

# Getting Started

> **Note**: Make sure you have completed the [Set Up Your Environment](https://reactnative.dev/docs/set-up-your-environment) guide before proceeding.

## Step 1: Start Metro

First, you will need to run **Metro**, the JavaScript build tool for React Native.

To start the Metro dev server, run the following command from the root of your React Native project:

```sh
# Using npm
npm start

# OR using Yarn
yarn start
```

## Step 2: Build and run your app

With Metro running, open a new terminal window/pane from the root of your React Native project, and use one of the following commands to build and run your Android or iOS app:

### Android

```sh
# Using npm
npm run android

# OR using Yarn
yarn android
```

### iOS

For iOS, remember to install CocoaPods dependencies (this only needs to be run on first clone or after updating native deps).

The first time you create a new project, run the Ruby bundler to install CocoaPods itself:

```sh
bundle install
```

Then, and every time you update your native dependencies, run:

```sh
bundle exec pod install
```

For more information, please visit [CocoaPods Getting Started guide](https://guides.cocoapods.org/using/getting-started.html).

```sh
# Using npm
npm run ios

# OR using Yarn
yarn ios
```

### macOS

macOS builds require Xcode and CocoaPods.

```sh
cd macos
pod install
cd ..
npm run macos
```

If you prefer using Bundler to pin CocoaPods versions, use `bundle exec pod install --project-directory=macos` instead.

#### Troubleshooting: `bundle install` fails building `json`

If you see an error like `extconf failed` while installing `json`, you are likely using the system Ruby (`/usr/bin/ruby`) which may not ship buildable headers on newer macOS/Xcode SDKs.

Recommended fix: install a modern Ruby and retry:

```sh
brew install ruby
echo 'export PATH="/opt/homebrew/opt/ruby/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

cd desktop/crystal-lattice-control-desktop-rn
rm -rf vendor/bundle
gem install bundler
bundle install
bundle exec pod install --project-directory=macos
```

Alternative (skip Bundler):

```sh
brew install cocoapods
pod install --project-directory=macos
```

If everything is set up correctly, you should see your new app running in the Android Emulator, iOS Simulator, or your connected device.

This is one way to run your app — you can also build it directly from Android Studio or Xcode.

### Desktop transient UI

On macOS, anchored transient controls such as action menus and session filters
must use the native `NSPopover` bridge. Do not present these controls through
React Native `Modal` or the shared modal-backed dropdown surface. Keep reusable
content in shared React components and mount that content in the desktop
popover root.

### macOS UI tests

The desktop app uses the existing XCUITest target on the host Mac rather than
Detox. Run all macOS UI tests with:

```sh
npm run test:macos-ui
```

Run the focused native session-filter popover test with:

```sh
npm run test:macos-ui:session-filters
```

The focused command launches a deterministic harness that renders the
production sessions panel and shared filter controls.

### Inspect agent instructions

Crystal Lattice compiles project guidance into the effective
developer/system message used by an agent session. To include task-file
guidance:

1. Open the active chat.
2. Select **Settings**.
3. In the **Session settings** window, enable **Include TASKS Guidance**.

Open the chat's session actions and select **Show compiled system message** to
display the effective message in a separate action-display window. Inspection
does not send a model request, save the session, or add to the conversation.
Lengthy prompts scroll inside the window. Check that the expected project
instructions and, when enabled, task guidance are present.

## Step 3: Modify your app

Now that you have successfully run the app, let's make changes!

Open `App.tsx` in your text editor of choice and make some changes. When you save, your app will automatically update and reflect these changes — this is powered by [Fast Refresh](https://reactnative.dev/docs/fast-refresh).

When you want to forcefully reload, for example to reset the state of your app, you can perform a full reload:

- **Android**: Press the <kbd>R</kbd> key twice or select **"Reload"** from the **Dev Menu**, accessed via <kbd>Ctrl</kbd> + <kbd>M</kbd> (Windows/Linux) or <kbd>Cmd ⌘</kbd> + <kbd>M</kbd> (macOS).
- **iOS**: Press <kbd>R</kbd> in iOS Simulator.

## Congratulations! :tada:

You've successfully run and modified your React Native App. :partying_face:

### Now what?

- If you want to add this new React Native code to an existing application, check out the [Integration guide](https://reactnative.dev/docs/integration-with-existing-apps).
- If you're curious to learn more about React Native, check out the [docs](https://reactnative.dev/docs/getting-started).

# Troubleshooting

If you're having issues getting the above steps to work, see the [Troubleshooting](https://reactnative.dev/docs/troubleshooting) page.

# Learn More

To learn more about React Native, take a look at the following resources:

- [React Native Website](https://reactnative.dev) - learn more about React Native.
- [Getting Started](https://reactnative.dev/docs/environment-setup) - an **overview** of React Native and how setup your environment.
- [Learn the Basics](https://reactnative.dev/docs/getting-started) - a **guided tour** of the React Native **basics**.
- [Blog](https://reactnative.dev/blog) - read the latest official React Native **Blog** posts.
- [`@facebook/react-native`](https://github.com/facebook/react-native) - the Open Source; GitHub **repository** for React Native.

## Transcript scroll diagnostics

Desktop transcript navigation and content-follow diagnostics are disabled by
default. Enable concise lifecycle logging before the app is registered:

```js
globalThis.CLC_DEBUG_CHAT_SCROLL_COORDINATOR = true;
```

Lifecycle mode reports navigation start/completion, bounded content-follow
lease start/renewal/expiration, interaction cancellation, and operation
timeouts. Repeated lease renewals are rate-limited so streaming logs remain
copyable.

For frame-level native observations and correction writes, additionally set:

```js
globalThis.CLC_DEBUG_CHAT_SCROLL_COORDINATOR_VERBOSE = true;
```

Verbose mode is intended for focused manual or harness runs and should
normally remain disabled.

The entry point emits one `[chatScrollBootstrap]` line when lifecycle
diagnostics are enabled. Each mounted transcript then emits one
`configuration` event. Check both lines before interpreting a trace:

```text
maxEdgeCorrections=60
manualBottomConvergenceMaxMs=15000
initialBottomConvergenceMaxMs=15000
```

Far FlatList item-anchor navigation additionally reports:

```text
listAnchorStarted
listAnchorProgress
listAnchorCompleted
listAnchorStopped
```

The start event includes the effective `timeoutMs` and `maxAttempts`. These
settings can be configured before application modules are loaded:

```js
globalThis.CLC_FLATLIST_MAX_EDGE_CORRECTIONS = 60;
globalThis.CLC_FLATLIST_ITEM_ANCHOR_TIMEOUT_MS = 15000;
globalThis.CLC_FLATLIST_ITEM_ANCHOR_MAX_ATTEMPTS = 200;
```

### Stable-geometry manual detachment

The coordinator classifies movement away from a pinned bottom using native
event-to-event bottom gaps and geometry revisions.

An unexplained movement with stable content/viewport geometry reports:

```text
awayMotionCandidate
reason=stableGeometryAwayMotion
```

The event includes bottom-gap and offset deltas, geometry revisions, active
operation details, and whether the movement opposed a recent programmatic
target.

An accepted candidate immediately reports:

```text
manualBottomDetached
reason=stableGeometryAwayMotion
```

It latches `manuallyDetached` affinity, clears any follow lease, and cancels
the active content-follow operation. Semantic content changes cannot reattach
the transcript.

Stable manual movement back toward the bottom that crosses into the measured
bottom threshold reports:

```text
manualBottomReattachCandidate
manualBottomReattached
```

This changes affinity back to `pinned` without issuing a scroll command or
starting a lease. The next semantic content change can then use normal bounded
following. Active or recent programmatic navigation cannot trigger this
manual-return transition. Successful explicit bottom navigation also
reattaches after convergence.

A candidate that is compatible with a recent programmatic target is retained
as a diagnostic but reports:

```text
awayMotionDetachSuppressed
reason=recentProgrammaticMovementNotOpposed
```

An away movement observed while layout or semantic content is still settling
reports:

```text
awayMotionIgnored
reason=geometryChanged|recentGeometryChange|semanticContentPending
```

Candidate output is rate-limited to four lines per second and ignored output
to two lines per second so a short manual gesture remains copyable.

## License

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
