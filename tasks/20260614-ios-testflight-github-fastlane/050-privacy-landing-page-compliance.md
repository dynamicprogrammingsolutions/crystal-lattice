# Validate Privacy, Landing Page, And Compliance Inputs

Confirm the public landing page and privacy policy are suitable for App Store Connect, and prepare privacy/compliance answers from actual app behavior.

## Requirements checklist

- [x] Locate and verify the landing page source and public deployed URL.
- [x] Verify the privacy policy is part of the landing page and has a stable URL or anchor suitable for App Store Connect.
- [x] Audit actual app data flows and permissions against App Store privacy questions.
- [x] Revalidate `PrivacyInfo.xcprivacy` against current app code, React Native SDKs, and native dependencies.
- [x] Prepare a short privacy/compliance answer sheet for App Store Connect.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/010-preflight-audit.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/040-ios-identity-metadata.md

## Known Starting State

The user stated:

- The app icon exists as SVG and is used by the landing page and splash screen.
- The privacy policy is part of the landing page.

The app currently includes capabilities and dependencies that should be considered in privacy answers:

- Local network discovery via Bonjour/mDNS (`react-native-zeroconf`, `_http._tcp`, local network permission).
- Manual server connection by host/port.
- Bridge and cloud connection flows, including pairing/token-like connection records.
- Saved connections through local storage/cache.
- Sessions/messages UI and cached messages.
- Camera/photo/document attachment flows.
- Photo saving/export/sharing flows.

The privacy manifest exists at:

- `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/PrivacyInfo.xcprivacy`

Previously observed manifest entries:

- `NSPrivacyAccessedAPICategoryFileTimestamp` with reasons `C617.1` and `3B52.1`
- `NSPrivacyAccessedAPICategoryUserDefaults` with reason `CA92.1`
- `NSPrivacyAccessedAPICategorySystemBootTime` with reason `35F9.1`
- `NSPrivacyCollectedDataTypes` empty
- `NSPrivacyTracking` false

## Acceptance Criteria

- Public privacy policy URL is confirmed and usable in App Store Connect.
- App Store privacy answers are based on actual app behavior, not guesses.
- Any mismatch between `PrivacyInfo.xcprivacy`, SDK manifests, and app behavior is fixed or clearly documented.
- If the app collects/transmits user content to user-configured servers, bridge, or cloud endpoints, the App Store privacy notes explain this accurately.

## Verified URLs And Landing State

- Production landing page: `https://crystallattice.dev/`
- Marketing page: `https://crystallattice.dev/mobile`
- Privacy policy: `https://crystallattice.dev/privacy`
- Terms: `https://crystallattice.dev/terms`
- Support source route added by this task: `https://crystallattice.dev/support`

On 2026-08-05 the landing changes were deployed from `main` by GitHub Actions
run `31000951408`. The production landing, mobile, privacy, support, and terms
routes all returned HTTP 200 after the CloudFront invalidation. The support URL
and revised privacy content are ready for App Store Connect.

## Confirmed Operating Model

The product owner confirmed:

- Dynamic Programming Solutions Kft. operates no production bridge.
- Dynamic Programming Solutions Kft. operates no public cloud-agent service.
- Bridge and cloud deployments are self-hosted by users.
- The product-operated services do not retain bridge/cloud user data because no
  such production services exist.
- The app contains no analytics, crash reporting, advertising, or tracking
  service.
- Support email correspondence is retained as business correspondence.

## App Data Flow Audit

The mobile app:

- Connects to manual HTTP endpoints, Bonjour-discovered endpoints, self-hosted
  bridges, or self-hosted cloud-orchestrator endpoints.
- Stores saved connection records, including bridge pairing tokens and cloud
  connection tokens, in local `AsyncStorage`.
- Stores cached session summaries, message display/cache state, pinned actions,
  and UI preferences locally.
- Allows users to choose camera photos, photo-library images, and documents as
  attachments.
- Sends chosen messages and attachments to the user's selected self-hosted
  runtime; the runtime may send them to the AI provider configured by the user.
- Allows users to save generated images/files or share them through operating
  system interfaces.
- Does not include analytics, advertising, telemetry, or cross-app tracking
  SDKs.

## Privacy Manifest Audit

The app manifest remains valid:

- Tracking: `false`
- App-declared collected data types: empty
- File timestamp reasons: `C617.1`, `3B52.1`
- User defaults reason: `CA92.1`
- System boot time reason: `35F9.1`

These values cover the aggregated React Native, AsyncStorage, camera-roll,
image-picker, Folly, Boost, and glog manifests present in the installed native
dependencies. Camera Roll and Image Picker also package their own privacy
resource bundles describing photos/videos or other data used for app
functionality. No additional app-level required-reason API was found.

## App Store Connect Privacy Answer Sheet

Recommended answers based on the confirmed operating model:

- Does the developer or its third-party partners collect data from this app?
  **No — Data Not Collected.**
- Is data used for tracking? **No.**
- Does the app use third-party advertising? **No.**
- Does the app use analytics or telemetry? **No.**
- Does the app require an account operated by the developer? **No.**
- Does the app transmit user content off the phone? **Yes, only to a runtime,
  bridge, cloud environment, or AI provider selected/configured by the user.**
- Does Dynamic Programming Solutions Kft. receive or retain that transmitted
  content? **No.**
- Are camera/photo/document permissions used? **Yes, only after user action for
  attachments, saving, or sharing.**
- Is connection information stored on device? **Yes, for app functionality,
  including self-hosted endpoint details and reconnect tokens.**
- Is support correspondence collected outside the app? **Yes, when a user
  voluntarily emails support; it is retained as business correspondence.**

The account owner must make the final App Store Connect attestation and revisit
these answers if a production bridge, public cloud service, analytics, crash
reporting, or other developer-operated data flow is introduced.

## Implementation Notes

- Updated the privacy policy effective date to 2026-08-05.
- Added explicit sections for local storage, self-hosted bridge/cloud
  connections, attachments, generated files, and support correspondence.
- Added a dedicated support page and footer links.
- Added in-app Privacy Policy and Support links to the pre-connection screen.
- Added `ITSAppUsesNonExemptEncryption = false` because the app uses standard
  platform HTTPS/WSS/TLS and contains no custom or non-exempt cryptography.

## Completion Notes

Completed the source, app-flow, permission, privacy-manifest, App Store privacy
answer, deployment, and public-route verification on 2026-08-05.

Verification completed on 2026-08-05:

- `yarn build` in `landing_page`: passed; five static routes generated.
- `npm run tsc` in the mobile app: passed.
- `npm test -- --runInBand` in the mobile app: 26 suites and 110 tests passed.
- `xcodebuild` Debug generic iOS Simulator build: passed.
- `plutil -lint` for `Info.plist` and `PrivacyInfo.xcprivacy`: passed.
- Built app inspection confirmed `ITSAppUsesNonExemptEncryption = false`, the
  app privacy manifest, and React Native/dependency privacy bundles.
- `git diff --check` for the scoped changes: passed.
- GitHub Actions `Deploy Static Sites` run `31000951408`: passed in 2m53s.
- Production `/`, `/mobile`, `/privacy`, `/support`, and `/terms`: HTTP 200.
- Production privacy page: effective date and support contact verified.
- Production mobile page: `Crystal Lattice` title and image alt text verified.
