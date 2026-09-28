# Crystal Lattice Mobile - React Native

This is the React Native mobile client for Crystal Lattice. It connects to the Crystal Lattice terminal/HTTP app directly, through local network discovery, through a bridge service, or through supported cloud connection links.

## Features

- 🔍 **Multiple Connection Methods:**
  - On-device Python agent with an OpenAI-compatible proxy (iOS proof of concept)
  - Manual address entry (IP + port)
  - Automatic Bonjour/mDNS discovery
  - Bridge service connection for cross-network access
- 📂 **Connections Screen:**
  - Saves successful connections (manual, discovery, bridge)
  - Lets you reconnect with a single tap instead of re-entering details or pairing codes (when the bridge still knows about the pairing)
- 📡 Connect to discovered services
- ✅ Execute GET and PUT requests
- 🔐 Secure pairing with bridge servers
- 🎨 Adapter architecture for unified interface
- 📱 Cross-platform (iOS and Android)

## Technology Stack

- **React Native**: 0.82.1
- **mDNS Library**: `react-native-zeroconf`
- **WebSocket**: Native WebSocket API with polyfills
- **Service Type**: `_http._tcp`
- **Bridge Protocol**: Phoenix WebSocket control with optional HTTP v1 proxy
  transport

## Prerequisites

### iOS
- Follow the [React Native Environment Setup](https://reactnative.dev/docs/set-up-your-environment) guide (select "React Native CLI" → "iOS")
- This includes: Node.js, Xcode, CocoaPods, and iOS Simulator setup
- **Physical device recommended** for network testing (simulators may have mDNS issues)

### Android
- Follow the [React Native Environment Setup](https://reactnative.dev/docs/set-up-your-environment) guide (select "React Native CLI" → "Android")
- This includes: Node.js, JDK, Android Studio, Android SDK, and emulator setup
- **Physical device strongly recommended** for network testing (emulators are unreliable for mDNS/Bonjour discovery)

### Detox E2E tests

- Install AppleSimUtils for iOS Simulator control:
  ```bash
  brew tap wix/brew
  brew trust wix/brew
  brew install applesimutils
  ```
- Create an iOS Simulator and Android AVD, or use the local defaults:
  - iOS: `iPhone 17 Pro`
  - Android: `Medium_Phone_API_36.1`
- Override those names when needed:
  ```bash
  export DETOX_IOS_DEVICE="iPhone 16 Pro"
  export DETOX_ANDROID_AVD="Pixel_8_API_35"
  ```

## Installation

1. **Navigate to the React Native app directory:**
   ```bash
   cd mobile/crystal-lattice-control-rn
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Prepare the embedded Python runtime and install iOS Pods:**
   ```bash
   npm run pod-install
   ```

## Running the App

Start Metro from the app root (not `ios/`):

```bash
cd mobile/crystal-lattice-control-rn
npm run start
```

### iOS

**Option 1: Using CLI**
```bash
npx react-native run-ios
```

**Option 2: Using Xcode**
```bash
open ios/CrystalLatticeControlRN.xcworkspace
```
Then click the Run button in Xcode.

### On-device Python agent

The iOS app includes a proof-of-concept embedded Python agent. Start an
API-key-protected OpenAI-compatible proxy backed by Ollama, then choose
**Connections → New connection → On-device Python Agent** and enter its URL,
model, and API key.

Simulator URLs can use `127.0.0.1`. A physical iPhone must use the Mac's LAN
address. See
[Embedded Python runtime](docs/development/embedded-python-runtime.md) for
proxy, build, test, persistence, background, and security details.

### Running on Physical iOS Device

**Important:** Physical device is required for reliable mDNS testing (simulator is unreliable).

1. **Connect your iPhone/iPad** via USB to your Mac

2. **Open the workspace in Xcode:**
   ```bash
   cd mobile/crystal-lattice-control-rn
   open ios/CrystalLatticeControlRN.xcworkspace
   ```

3. **Configure Code Signing:**
   - In Xcode, select the **CrystalLatticeControlRN** project in the left sidebar
   - Select the **CrystalLatticeControlRN** target (under "Targets")
   - Click the **Signing & Capabilities** tab
   - Check **"Automatically manage signing"**
   - Select your **Team** from the dropdown (use your Apple ID)
     - If no team is shown, click "Add Account..." and sign in with your Apple ID
     - Free Apple ID works for development

4. **Select your device:**
   - At the top of Xcode, click the device selector (next to the scheme)
   - Choose your connected iPhone/iPad from the list

5. **Trust your device:**
   - First time: On your device, go to **Settings → General → VPN & Device Management**
   - Tap your Apple ID and tap **Trust**

6. **Build and Run:**
   - Click the ▶️ (Play) button in Xcode, or press **⌘R**
   - App will install and launch on your device

**Troubleshooting Signing:**
- **"Could not launch" error:** Trust your developer certificate on device (step 5)
- **"No profiles" error:** Ensure you selected a Team in step 3
- **"Failed to register bundle identifier":** Change the Bundle ID in Signing & Capabilities to something unique (e.g., add your initials)

**Alternative: CLI with device**
```bash
npx react-native run-ios --device "Your iPhone Name"
```
This requires code signing to be configured in Xcode first (steps 2-3 above).

## TestFlight with fastlane

The iOS release workflow uses Ruby 3.4.10, Bundler, App Store Connect API-key
authentication, and a private git-backed `fastlane match` repository.

Install the pinned Ruby version with your preferred version manager, then run:

```bash
bundle install
bundle exec fastlane lanes
```

Available lanes:

```bash
bundle exec fastlane ios verify
bundle exec fastlane ios setup_signing
bundle exec fastlane ios build
bundle exec fastlane ios beta
```

- `verify` runs the build-number tests, TypeScript validation, and Jest.
- `setup_signing` is a one-time or intentional maintenance operation that can
  create/update the App Store certificate and provisioning profile in the
  private match repository.
- `build` synchronizes signing assets read-only and creates
  `build/ios/CrystalLattice.ipa`.
- `beta` verifies, archives, and uploads an internal TestFlight build.

Copy `fastlane/.env.example` to `fastlane/.env` for local use and replace the
placeholders. The local `.env`, fastlane reports, build directory, API private
key, certificates, and provisioning profiles must not be committed.

Required release variables:

- `MATCH_GIT_URL`
- `MATCH_PASSWORD`
- `APP_STORE_CONNECT_KEY_ID`
- `APP_STORE_CONNECT_ISSUER_ID`
- Either `APP_STORE_CONNECT_KEY_PATH` or `APP_STORE_CONNECT_KEY_CONTENT`

Git authentication for the private signing repository is supplied through
standard match variables such as `MATCH_GIT_BASIC_AUTHORIZATION` or
`MATCH_GIT_PRIVATE_KEY`.

One-time credential setup:

1. Create an empty private GitHub repository for signing assets, for example
   `dynamicprogrammingsolutions/crystal-lattice-ios-signing`, initialized with a
   `main` branch.
2. In App Store Connect, open **Users and Access → Integrations → Team Keys**,
   generate a key named `Crystal Lattice fastlane` with the **App Manager** role,
   and download its `.p8` file. Apple only offers the private key download once.
3. Record the key ID and issuer ID in a password manager.
4. Generate a strong match encryption password, for example:

   ```bash
   openssl rand -base64 32
   ```

5. Copy `fastlane/.env.example` to the ignored `fastlane/.env`, set the signing
   repository URL, match password, API key ID, issuer ID, and absolute `.p8`
   filepath.
6. Confirm that the local SSH key or other configured match git authentication
   can clone the private signing repository.

The first signing bootstrap should be run locally with write access:

```bash
cp fastlane/.env.example fastlane/.env
MATCH_READONLY=false bundle exec fastlane ios setup_signing
```

Normal build and CI execution must use `MATCH_READONLY=true`.

Build numbers are selected in this order:

1. `IOS_BUILD_NUMBER`, when explicitly set.
2. The greater of `GITHUB_RUN_NUMBER` and the latest TestFlight build plus one.
3. The latest TestFlight build plus one when outside GitHub Actions.

The archive receives the build number as an Xcode build-setting override, so a
local fastlane build does not modify the checked-in Xcode project version.

The App Store listing is identified by numeric Apple ID `6798401926`; the bundle
identifier remains `com.dynamicprogrammingsolutions.crystallatticecontrolrn`.

### GitHub Actions TestFlight deployment

The `iOS TestFlight` workflow is manual-only. Open the repository's **Actions**
tab, select **iOS TestFlight**, and choose **Run workflow**.

The workflow selects Xcode 26.6 on the `macos-26` runner. CocoaPods applies the
React Native `fmt` consteval compatibility patch during installation so the
native dependency compiles with that Apple clang release.

The workflow has two modes:

- `upload_to_testflight = false` is the safe default. It verifies the mobile
  package and creates a signed IPA on the ephemeral runner without uploading or
  retaining it.
- `upload_to_testflight = true` runs the same verification and calls
  `fastlane ios beta` to upload an internal TestFlight build. An optional
  changelog can be supplied in the dispatch form.

Required repository variables:

| Variable | Value |
| --- | --- |
| `IOS_APP_IDENTIFIER` | `com.dynamicprogrammingsolutions.crystallatticecontrolrn` |
| `IOS_APPLE_TEAM_ID` | `73Q43R2PD4` |
| `IOS_APP_STORE_APPLE_ID` | `6798401926` |
| `IOS_MATCH_GIT_URL` | `git@github.com:dynamicprogrammingsolutions/crystal-lattice-ios-signing.git` |
| `IOS_MATCH_GIT_BRANCH` | `main` |

Required encrypted repository secrets:

| Secret | Purpose |
| --- | --- |
| `IOS_APP_STORE_CONNECT_KEY_ID` | App Store Connect API key ID |
| `IOS_APP_STORE_CONNECT_ISSUER_ID` | App Store Connect issuer ID |
| `IOS_APP_STORE_CONNECT_KEY_CONTENT` | Base64-encoded `.p8` API private key |
| `IOS_MATCH_PASSWORD` | Decrypts the match signing repository |
| `IOS_MATCH_GIT_PRIVATE_KEY` | Read-only SSH deploy private key for the match repository |

The matching public deploy key must be registered read-only on the private
`crystal-lattice-ios-signing` repository. Do not reuse a personal SSH key or a
deploy key with write access.

The organization currently uses GitHub Free and this repository is private.
Protected environments, environment secrets, and required deployment reviewers
are therefore unavailable for this workflow. Current protections are:

- Manual dispatch only; there are no push or tag triggers.
- Repository write access is required to start the workflow.
- Signing-repository access is read-only and limited to one repository.
- Match is always read-only on CI.
- GitHub serializes iOS runs so two signing/upload jobs cannot overlap.

If the repository gains a GitHub plan that supports environments for private
repositories, create a protected `ios-testflight` environment, move the five
secrets into it, require an authorized reviewer, and attach the release job to
that environment.

To rotate credentials:

1. Generate a replacement App Store Connect API key or signing deploy key.
2. Replace the corresponding GitHub secret.
3. Run the workflow with uploading disabled.
4. Remove the superseded key only after the build-only run succeeds.

### Android

**Option 1: Using CLI**
```bash
npx react-native run-android
```

**Option 2: Using Android Studio**
1. Open the `android` folder in Android Studio
2. Wait for Gradle sync to complete
3. Click the Run button

**Note:** Make sure you have an emulator running or a device connected via USB with USB debugging enabled.

## Running Detox tests

The transcript scroll suite launches a deterministic 300-message harness that
uses the same production inverted FlatList viewport and chevron controls as the
normal chat screen. The E2E builds bundle JavaScript and do not require Metro.
The transcript-range suite mounts the production chat screen with a
deterministic backend and verifies that Show older/newer preserves an
overlapping message at the same visual viewport offset after the loaded range
is replaced.

Build and run on iOS:

```bash
npm run detox:build:ios
npm run detox:test:bridge-transport:ios
npm run detox:test:connections-settings:ios
npm run detox:test:transcript:ios
npm run detox:test:transcript-range:ios
```

Build and run on Android:

```bash
npm run detox:build:android
npm run detox:test:bridge-transport:android
npm run detox:test:connections-settings:android
npm run detox:test:transcript:android
npm run detox:test:transcript-range:android
```

The deterministic session-list harness exercises application-derived row
presentation, server ordering, ordinary action fallback, and dialog prefill:

```bash
npm run detox:test:session-list:ios
npm run detox:test:session-list:android
```

The website visual harness renders the production chat background and session
settings modal with deterministic coding-agent configuration. The iOS capture
command builds the app, runs the scenario, and writes reviewed-candidate inputs
under `artifacts/website-visual/`:

```bash
npm run detox:capture:website-visual:ios
```

The scenario itself is also available on both platforms when a current build
already exists:

```bash
npm run detox:test:website-visual:ios
npm run detox:test:website-visual:android
```

The focused human-time telemetry suite runs the real release app against a
spawned backend and verifies that foreground time with a real session open
reaches the duration-tracking SQLite store:

```bash
npm run detox:build:ios
npm run detox:test:human-time:ios

npm run detox:build:android
npm run detox:test:human-time:android
```

See [Human time telemetry](docs/development/human-time-telemetry.md) for the
two-tier coverage split, Python/plugin prerequisites, and the focused
real-backend integration command.

The Connections/Settings harness renders the production Connections screen,
global and server settings modals, action menus, and markdown renderer. It
verifies native action applicability, modal transitions, persisted display and
pin preferences, and representative typography/card geometry.

The Android test command prepares and stops the selected AVD before Detox starts
it in read-only mode. This acknowledges Android's one-time immersive-mode
confirmation so it cannot steal window focus during automation. The build script
also creates the standard ignored Android debug keystore when it is missing.

Failure artifacts are written below `artifacts/detox/`. Logs and screenshots are
retained for failures; iOS also retains failure videos. The Android E2E build
uses the dedicated `e2e` build type so Detox can use localhost WebSocket traffic
without changing the production release manifest.

## Usage

### Method 1: Manual Connection

1. **Start a server** (see server options below)
2. **Get the server's IP address:**
   ```bash
   # macOS/Linux
   ifconfig | grep "inet "
   
   # Or if server is running locally
   localhost or 127.0.0.1
   ```
3. **In the app:**
   - Select "Manual Address"
   - Enter host (e.g., `192.168.1.100`)
   - Enter port (default: `8080`)
   - Tap "Connect"

### Method 2: Automatic Discovery (Bonjour)

**Requirements:** Device must be on the same WiFi network as the server.

1. **Start a server:**
   ```bash
   # Node.js server
   cd ../server-node && npm start
   
   # OR Python server
   cd ../server-python && python bonjour_server.py
   
   # OR Swift server
   cd ../server-swift && ./BonjourServer
   ```

2. **In the app:**
   - Select "Automatic Discovery"
   - Wait for services to appear
   - Tap on a service to connect

### Method 3: Bridge Connection (Cross-Network)

**Requirements:** Bridge service running and server registered with bridge.

1. **Start the bridge service:**
   ```bash
   cd ../bridge-elixir
   docker-compose up -d
   ```

2. **Start a server with bridge connection:**
   ```bash
   cd ../server-python
   python bonjour_server.py --bridge ws://localhost:4000/ws/websocket
   ```

3. **In the app:**
   - Select "Bridge Service"
   - Enter bridge URL (default: `ws://localhost:4000/ws/websocket`)
     - For iOS device testing bridge on Mac: use Mac's IP address
     - Example: `ws://192.168.1.100:4000/ws/websocket`
   - Select a transport. `WebSocket` is the stable default; `HTTP` and
     `Hybrid` are experimental opt-ins.
   - Tap "Connect to Bridge"
   - Select a server from the list
   - Tap to request pairing
   - **Check the server terminal** for the 6-digit pairing code
   - Enter the code in the app
   - Tap "Submit Code"

HTTP mode uses plain HTTP for pairing and all backend requests, including
event polling. Hybrid mode uses plain HTTP for pairing and normal requests,
while exact `GET /events` polling stays on the existing WebSocket transport.
The selected mode is saved with the connection. Older saved connections have
no mode field and continue to use WebSocket.

4. **Make requests:**
   - Once connected, tap "GET /api/data" or "PUT /api/data"
   - View responses in the app

5. **Disconnect:**
   - Tap "Disconnect" to go back and choose another connection method

## Configuration

### iOS Permissions

The app is already configured with required iOS permissions in `ios/CrystalLatticeControlRN/Info.plist`:

```xml
<key>NSBonjourServices</key>
<array>

    <string>_http._tcp</string>
</array>
<key>NSLocalNetworkUsageDescription</key>
<string>This app discovers local Bonjour services on your network</string>
<key>NSAllowsLocalNetworking</key>
<true/>
```

### Android Permissions

The app is already configured with required Android permissions in `android/app/src/main/AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
<uses-permission android:name="android.permission.CHANGE_WIFI_MULTICAST_STATE" />
```

## Architecture

### Transport + Backend Pattern

The app uses the shared SDK (`@crystal-lattice/frontend-sdk`) to provide a unified interface for different connection methods:

```typescript
interface Transport {
  request<T>(req: { method: 'GET'|'POST'|'PUT'|'PATCH'|'DELETE'; path: string; body?: any }): Promise<{ status: number; data: T }>;
}

interface AgentBackend {
  listSessions(): Promise<SessionSummary[]>;
  listMessages(sessionId: string): Promise<{ messages: IndexedMessage[] }>;
  // ...
}
```

**Implementations used by the mobile app:**
- `FetchTransport`: Used for manual and discovery connections (standard HTTP/fetch)
- `BridgeTransport`: Used for bridge connections (Phoenix/WebSocket-based)

## Testing

Run the default mobile Jest suite from the app root:

```bash
cd mobile/crystal-lattice-control-rn
npm test
```

Fast component tests live under `__tests__/` and use React Native Testing Library through
`src/testUtils/renderWithMobileProviders.tsx`. Use this tier for generic UI behavior such as
rendering settings controls, pressing chips/buttons, text input changes, and callback behavior.
These tests should use small in-memory fixtures and should not start a backend.

Real-backend component integration tests live under `__integration__/` and run explicitly:

```bash
cd mobile/crystal-lattice-control-rn
npm run test:components:integration
```

This tier starts a real FastAPI backend with the shared frontend SDK integration harness,
connects through `FetchTransport` and `RestAgentBackend`, creates real sessions, and then
renders only the mobile component under test. Use it when the source of truth is backend or
plugin code, such as plugin-provided settings UI schema or session override persistence.

The real-backend tier is heavier than default Jest because it starts Python/FastAPI and may
install path plugin dependencies into a temporary plugin cache on first run. Keep it explicit
in CI until runtime and cache behavior are known to be stable.
- `RestAgentBackend`: Implements `AgentBackend` on top of a `Transport`

### Key Components

- **App.tsx**: Main component with UI, state management, and connection logic
- **Transport**: Abstract request interface for all connection types
- **RestAgentBackend**: The backend adapter used by screens (wraps a `Transport`)
- **FetchTransport**: HTTP-based transport (manual + discovery)
- **BridgeTransport**: WebSocket-based transport (bridge mode)
- **react-native-zeroconf**: Native module for mDNS service discovery
  - iOS: Uses `NSNetServiceBrowser` (Bonjour)
  - Android: Uses `NsdManager` (Network Service Discovery)

### Flow Diagrams

**Manual Connection Flow:**
1. User enters host and port
2. FetchTransport validates connection
3. RestAgentBackend uses FetchTransport for requests

**Discovery Flow:**
1. User taps "Start Discovery"
2. `Zeroconf.scan('http', 'tcp', 'local.')` starts browsing
3. `resolved` event fires for each discovered service
4. User selects service → FetchTransport connects
5. RestAgentBackend uses FetchTransport for requests

**Bridge Flow:**
1. User enters bridge WebSocket URL
2. BridgeTransport connects via WebSocket
3. Lists available servers from bridge (showing display name, computer name,
   and the bridge `server_id` so you can distinguish servers with the same
   name)
4. User selects server → requests pairing
5. Server displays 6-digit code (5 min TTL)
6. User submits code → pairing complete
7. RestAgentBackend proxies requests through BridgeTransport
8. Bridge forwards requests to server via session
9. The app stores a connection record (including the bridge URL, server id, and pairing token) so you can reconnect from the Connections screen without re-entering the 6-digit code, as long as the bridge still has the pairing

## Troubleshooting

### iOS Issues

**No services found:**
- Ensure you're testing on the same WiFi network as the server
- Check that local network permission was granted (iOS 14+)
- Try restarting the app
- Verify `NSBonjourServices` is correctly configured

**Permission prompt not showing:**
- Delete and reinstall the app
- Check Xcode console for permission errors

**URLSession timeout:**
- Ensure `NSAllowsLocalNetworking` is set to `true`
- Check that the server is running and accessible

### Android Issues

**No services found:**
- Test on a physical device (emulators may have network issues)
- Ensure all permissions are granted in Android settings
- Check that WiFi is enabled and connected
- Some Android 10+ devices may require location permission for network scanning

**Multicast issues:**
- Some routers block multicast traffic
- Try disabling firewall temporarily
- Check WiFi router settings for mDNS/Bonjour support

### Bridge Connection Issues

**Cannot connect to bridge:**
- Ensure bridge service is running: `cd ../bridge-elixir && docker-compose ps`
- Check bridge URL is correct (use Mac IP for device testing)
- Verify network connectivity between device and bridge

**No servers available:**
- Check that servers are registered: `curl http://localhost:4000/health`
- Ensure server was started with `--bridge` flag
- Restart server with bridge connection

**Pairing fails:**
- Code expires after 5 minutes - request new pairing
- Maximum 3 attempts - server needs to generate new code
- Check server terminal for correct code
- Ensure code is exactly 6 digits

**WebSocket connection drops:**
- Bridge automatically reconnects
- Check docker logs: `docker-compose logs -f`
- Verify firewall isn't blocking WebSocket connections

### General Issues

**Service discovered but connection fails:**
- Check that the server port matches (default: 8080)
- Verify the server is advertising `_http._tcp` service type
- Look at Metro bundler logs for error messages

**App crashes on start:**
- Clear Metro cache: `npx react-native start --reset-cache`
- Rebuild the app: `cd ios && rm -rf build && pod install && cd ..`

**Mixed connection method issues:**
- Always disconnect before switching methods
- Back button properly cleans up connections
- Check console logs for adapter state

## Development

### Running Metro Bundler Separately

```bash
npx react-native start
```

Then in another terminal:
```bash
npx react-native run-ios
# or
npx react-native run-android
```

### Debugging

**Enable Debug Mode:**
- iOS: Shake device or press ⌘D in simulator → "Debug"
- Android: Shake device or press ⌘M in emulator → "Debug"

**View Logs:**
```bash
# iOS
npx react-native log-ios

# Android
npx react-native log-android
```

## Differences from Native iOS App

| Feature | Native iOS | React Native |
|---------|-----------|--------------|
| Language | Swift | TypeScript/JavaScript |
| UI Framework | SwiftUI | React Native |
| Discovery API | Network framework | react-native-zeroconf |
| Platform Support | iOS only | iOS + Android |
| Connection Methods | Discovery only | Manual, Discovery, Bridge |
| Build Tool | Xcode | Metro bundler |
| Package Manager | CocoaPods | npm |
| Bridge Support | No | Yes (WebSocket) |

## Project Structure

```
mobile/crystal-lattice-control-rn/
├── App.tsx                 # Main app component with adapters
├── src/
│   └── types/
│       └── react-native-zeroconf.d.ts  # Type declarations
├── ios/
│   └── CrystalLatticeControlRN/
│       └── Info.plist      # iOS permissions
├── android/
│   └── app/src/main/
│       └── AndroidManifest.xml  # Android permissions
├── package.json            # Dependencies (includes WebSocket polyfill)
└── README.md              # This file
```

## Related Documentation

- [Home, Watchlist, and recent sessions](docs/home.md)
- [Mobile frontend hosting](docs/development/frontend-hosting.md)
- [Bridge transport guide](../../packages/frontend-sdk/docs/bridge-transports.md)
- [React Native Documentation](https://reactnative.dev/)
- [react-native-zeroconf GitHub](https://github.com/balthazar/react-native-zeroconf)
- [Project Root README](../../README.md)

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
