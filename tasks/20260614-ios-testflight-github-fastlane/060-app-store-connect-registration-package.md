# Prepare App Store Connect Registration Package

Assemble the metadata and review information required to register the app and submit a TestFlight build.

## Requirements checklist

- [x] Prepare app identity fields: name, bundle ID, SKU, primary language, category, age rating inputs, copyright.
- [x] Prepare support URL, marketing URL, and privacy policy URL.
- [x] Prepare TestFlight beta app description, what-to-test text, feedback email, and review notes.
- [ ] Prepare Apple reviewer testing instructions, including how to access a usable backend/bridge/cloud environment.
- [x] Confirm export compliance/encryption answers for network communication.
- [x] Identify screenshots/app previews needed for eventual App Store release, even if not needed for initial internal TestFlight.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/050-privacy-landing-page-compliance.md

## Registration Fields

| Field | Value |
| --- | --- |
| Platform | iOS |
| App name | Owner confirmation pending; the original `Crystal Lattice` name was unavailable and `Crystal Lattice Control` was recommended |
| Bundle ID | `com.dynamicprogrammingsolutions.crystallatticecontrolrn` |
| Numeric Apple ID | `6798401926` |
| SKU | `crystal-lattice-ios` |
| Primary language | English (U.S.) |
| Primary category | Developer Tools |
| Secondary category | Productivity |
| Legal entity | Dynamic Programming Solutions Kft. |
| Apple team ID | `73Q43R2PD4` |
| Version | `0.9.0` |
| Initial build number | `1` |
| First release | Internal TestFlight |
| Copyright | `2026 Dynamic Programming Solutions Kft.` |
| Feedback email | `support@dynamicprogrammingsolutions.com` |

The explicit App ID and App Store Connect app record were created successfully.
The owner reported no Apple warning or error. Developer name is expected to
default to the legal entity name but remains pending public or Apple Support
confirmation.

## URLs

| Purpose | URL |
| --- | --- |
| Privacy policy | `https://crystallattice.dev/privacy` |
| Support | `https://crystallattice.dev/support` |
| Marketing | `https://crystallattice.dev/mobile` |

Deploy and verify the support/privacy landing changes before entering these
values in App Store Connect.

## Suggested Age-Rating Inputs

Answer the live Apple questionnaire exactly as presented. Based on current app
behavior:

- Messaging/chat capability: **Yes**
- User-generated content: **Yes**; users create prompts and may display content
  produced by their configured agents/providers.
- Unrestricted web access/browser: **No**
- Advertising: **No**
- Gambling or contests: **No**
- In-app purchases: **No**
- Parental controls: **No**
- Age assurance: **No**

The app does not bundle mature content, but user-configured AI providers can
produce variable content. The account owner must answer any content-frequency
questions conservatively for the provider configurations offered to testers and
accept Apple's calculated rating.

## TestFlight Beta Description

> Crystal Lattice is a mobile client for self-hosted Crystal Lattice agent
> runtimes. Browse sessions, continue conversations, stream responses, use
> plugin-provided actions, attach files and images, and connect by local address,
> Bonjour discovery, a self-hosted bridge, or a self-hosted cloud connection.
> The app has no developer-operated account, analytics, advertising, production
> bridge, or public cloud-agent service.

## Internal “What To Test”

> Please test connection setup and reconnection with a self-hosted Crystal
> Lattice runtime. Verify session listing, opening and continuing a session,
> streamed responses, app navigation, plugin actions, image/document
> attachments, generated-file save/share actions, and reconnecting after the app
> has been backgrounded. Report the app version, iOS version, connection method,
> runtime version, steps to reproduce, and redacted error details to
> support@dynamicprogrammingsolutions.com.

## Review Notes

> Crystal Lattice is a client for environments operated by the user or the
> user's organization. Dynamic Programming Solutions Kft. does not operate a
> production bridge or public cloud-agent service. No account controlled by the
> developer is required. Internal testers must run or be given access to a
> compatible Crystal Lattice runtime. Local-network discovery prompts are
> expected when Bonjour is used. Camera, photo-library, and document access are
> requested only after the tester selects an attachment or save action.

## Reviewer Access Status

The first build is internal-only, so internal testers can use their own
self-hosted environment. External TestFlight review still needs an immediately
testable review path. That work belongs to
`tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md`.
Do not submit for external TestFlight review until that task supplies actionable
reviewer instructions.

## Export Compliance

The app uses standard platform networking for HTTP/HTTPS and WebSocket/WSS
connections. It does not implement custom cryptography and does not contain
non-exempt encryption functionality.

- Xcode declaration: `ITSAppUsesNonExemptEncryption = false`
- App Store Connect non-exempt encryption question: **No**
- Export compliance documentation upload: **Not expected for this build**

The account owner must re-evaluate this answer if custom encryption, VPN
functionality, secure messaging cryptography, or non-standard crypto libraries
are added.

## Eventual App Store Media

Prepare polished screenshots after the TestFlight UI is stable. Capture:

1. Connection methods / saved connections.
2. Sessions list.
3. Active conversation with streaming or a completed assistant response.
4. Plugin-provided actions or controls.
5. Attachment selection and preview.
6. Connection details for local/self-hosted operation.

At least one current iPhone screenshot set will be required for the eventual App
Store product page; App Store Connect will show the exact accepted display sizes
for the version. iPad screenshots are only needed if iPad distribution remains
enabled. App previews are optional.

## Manual Account Actions

- [x] Accept any pending Apple Developer/App Store Connect agreements.
- [x] Register the explicit App ID.
- [x] Create the App Store Connect app record with the fields above.
- [x] Save the Developer Tools and Productivity categories.
- [x] Enter the App Privacy answers from task `050`.
- [ ] Confirm the exact accepted App Store app name.
- [ ] Create an App Store Connect API key for fastlane.
- [ ] Complete reviewer access after task `085` before external testing.

## Implementation Notes

The automatic registration package was prepared on 2026-08-05. Apple-account
changes were intentionally not performed. The reviewer-access checklist remains
open until the external-review test path is implemented.

Owner confirmation received on 2026-08-05:

- Explicit App ID registered.
- App Store Connect app record created.
- Numeric Apple ID: `6798401926`.
- Categories saved: Developer Tools and Productivity.
- App Privacy saved.
- No Apple warning or error reported.

The identity/export declarations were verified in a successful Debug generic
iOS Simulator build. The built app reports the expected display name, bundle
identifier, `ITSAppUsesNonExemptEncryption = false`, and packaged privacy
manifests. Landing, TypeScript, Jest, plist, and scoped whitespace checks also
passed as recorded in task `050`.

## Acceptance Criteria

- A product/account owner can create or complete the App Store Connect app record from this package without guessing.
- TestFlight metadata is written in review-ready prose.
- Reviewer access instructions are actionable.
- Any Apple-account-only fields that cannot be completed by the agent are listed with owner/action required.
