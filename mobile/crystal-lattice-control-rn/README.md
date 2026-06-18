# Bonjour Service Discovery - React Native

This is a React Native implementation of the Bonjour service discovery example. It provides the same functionality as the native iOS app but works on both iOS and Android.

## Features

- 🔍 **Multiple Connection Methods:**
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
- **Bridge Protocol**: Phoenix WebSocket protocol

## Prerequisites

### iOS
- Follow the [React Native Environment Setup](https://reactnative.dev/docs/set-up-your-environment) guide (select "React Native CLI" → "iOS")
- This includes: Node.js, Xcode, CocoaPods, and iOS Simulator setup
- **Physical device recommended** for network testing (simulators may have mDNS issues)

### Android
- Follow the [React Native Environment Setup](https://reactnative.dev/docs/set-up-your-environment) guide (select "React Native CLI" → "Android")
- This includes: Node.js, JDK, Android Studio, Android SDK, and emulator setup
- **Physical device strongly recommended** for network testing (emulators are unreliable for mDNS/Bonjour discovery)

## Installation

1. **Navigate to the React Native app directory:**
   ```bash
   cd mobile/crystal-lattice-control-rn
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Install iOS Pods:**
   ```bash
   cd ios && pod install && cd ..
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

### Running on Physical iOS Device

**Important:** Physical device is required for reliable mDNS testing (simulator is unreliable).

1. **Connect your iPhone/iPad** via USB to your Mac

2. **Open the workspace in Xcode:**
   ```bash
   cd react-native-app
   open ios/CrystalLatticeControlRN.xcworkspace
   ```

3. **Configure Code Signing:**
   - In Xcode, select the **BonjourExampleRN** project in the left sidebar
   - Select the **BonjourExampleRN** target (under "Targets")
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
   - Tap "Connect to Bridge"
   - Select a server from the list
   - Tap to request pairing
   - **Check the server terminal** for the 6-digit pairing code
   - Enter the code in the app
   - Tap "Submit Code"

4. **Make requests:**
   - Once connected, tap "GET /api/data" or "PUT /api/data"
   - View responses in the app

5. **Disconnect:**
   - Tap "Disconnect" to go back and choose another connection method

## Configuration

### iOS Permissions

The app is already configured with required iOS permissions in `ios/BonjourExampleRN/Info.plist`:

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
react-native-app/
├── App.tsx                 # Main app component with adapters
├── src/
│   └── types/
│       └── react-native-zeroconf.d.ts  # Type declarations
├── ios/
│   └── BonjourExampleRN/
│       └── Info.plist      # iOS permissions
├── android/
│   └── app/src/main/
│       └── AndroidManifest.xml  # Android permissions
├── package.json            # Dependencies (includes WebSocket polyfill)
└── README.md              # This file
```

## Related Documentation

- [React Native Documentation](https://reactnative.dev/)
- [react-native-zeroconf GitHub](https://github.com/balthazar/react-native-zeroconf)
- [Project Root README](../README.md)
- [Bonjour Explained](../BONJOUR_EXPLAINED.md)
- [Troubleshooting Guide](../TROUBLESHOOTING.md)

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
