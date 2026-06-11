# Stage 2: Bridge Push Delivery

Add APNs/FCM-backed remote push delivery through the bridge while keeping notification production on the laptop/server and preserving direct-IP/local-polling behavior from Stage 1.

## Requirements checklist

- [ ] Define how the mobile app registers push tokens and how the bridge stores them.
- [ ] Add local server or bridge-client polling for pending push-worthy notifications.
- [ ] Add a bridge-side push-delivery path that can send to Android and iOS.
- [ ] Decide token lookup keys, multiple-device behavior, refresh behavior, and revocation behavior.
- [ ] Document Firebase, APNs, keys, secrets, and deployment requirements clearly.
- [ ] Preserve pairing-based authorization first; do not require authentik login yet.
- [ ] Keep push delivery optional so bridge deployments without FCM/APNs credentials continue working as before.

Parent Task: `tasks/20260516-auth-notifications-staged-rollout/000-main.md`
Depends On: `tasks/20260516-auth-notifications-staged-rollout/010-local-notification-polling.md`

## Stage intent

This stage expands the Stage 1 notification model into actual remote push delivery. The laptop/server remains the source of notification intent. The bridge becomes the sender to APNs/FCM and the persistent store for push tokens.

This stage must not turn push into a required dependency. Self-hosters should be able to:

- skip push entirely
- deploy only local polling notifications
- run the bridge without provider credentials
- receive a graceful "push disabled" behavior instead of broken startup or failed core bridge behavior

## Decisions captured from research

- Bridge-side token persistence is preferred because token refresh may happen while the laptop/server is offline.
- Pairing can remain the initial authorization layer for push-token registration.
- The bridge does not need user-login identity yet to send notifications.
- The local server or bridge client can poll the local notification endpoint every 5-15 seconds when active.
- A separate 5-minute cadence is only for platform scheduler wake-up scenarios on the mobile app.
- Later evolution to long-poll or NDJSON is acceptable; do not over-design that in the first push version.
- The recommended first push transport is:
  - bridge sends through FCM HTTP v1
  - Firebase handles iOS delivery onward to APNs
- Direct APNs plus direct FCM remains a future option if more control is needed.

## Current code references

- Bridge client lifecycle and message loop:
  - `application/python/agent_terminal_app/bridge_client.py:146-214`
  - `application/python/agent_terminal_app/bridge_client.py:292-319`
- Existing local HTTP adapter inside bridge client:
  - `application/python/agent_terminal_app/bridge_client.py:618-656`
- Bridge app/server channel pairing and session model:
  - `bridge-elixir/lib/bridge/app_channel.ex:64-180`
  - `bridge-elixir/lib/bridge/server_channel.ex:11-42`
- Mobile app currently lacks push SDK dependencies:
  - `mobile/crystal-lattice-control-rn/package.json:16-40`

## Recommended architecture for this stage

### Notification ownership

- Laptop/server creates notification records.
- Mobile app registers push tokens.
- Bridge persists push tokens.
- Bridge client polls the laptop/server for push-worthy notifications and forwards send requests to the bridge.
- Bridge sends remote pushes to providers.

### Suggested token model

Persist one row per device token in the bridge:

- `token_id`
- `platform`
- `provider`
- `push_token`
- `server_id`
- `paired_client_id` or equivalent pairing scope
- optional future fields:
  - `user_sub`
  - `device_id`
  - `device_label`
- `updated_at`
- `last_success_at`
- `last_error`
- `revoked_at`

### Multiple-token policy

Decide explicitly whether:

- one pairing can have many devices
- one device can be paired to many servers
- a new token replaces an old token for the same device
- a logout/unpair revokes one token or all tokens in the scope

## Ordered implementation steps

1. Finalize notification record shape from Stage 1.
2. Define push-token registration API contract.
3. Add mobile push SDK and token-registration code.
4. Add bridge-side token persistence and admin/debug visibility.
5. Add a bridge-client local polling loop for push-worthy notifications.
6. Add bridge-side send-to-FCM path.
7. Add open/tap deep-link handling in the mobile app.
8. Add token refresh, invalid-token cleanup, and retries.
9. Add feature flags or config checks so push codepaths stay inactive when credentials are absent.

## Manual vs CLI / agent steps

### Firebase / FCM project setup

- [Manual] Create or choose a Google Cloud / Firebase project for notifications.
- [Manual-preferred] Enable Firebase Cloud Messaging for the project in the Firebase console.
- [Manual-preferred] Register the Android app in Firebase using the package name from the mobile app.
- [Manual-preferred] Register the iOS app in Firebase using the bundle identifier from the mobile app.
- [Manual] Download `google-services.json` for Android.
- [Manual] Download `GoogleService-Info.plist` for iOS.
- [Agent/CLI] Add those files into the project once the human provides them.
- [Manual or CLI] Create a service account for FCM HTTP v1 sending.
  - Preferred human path: Firebase / Google Cloud Console.
  - Possible automation path: `gcloud iam service-accounts create`, `gcloud projects add-iam-policy-binding`, and key or workload-identity setup.
- [Agent/CLI] Wire bridge deployment to use the service account credentials or workload identity.

### Apple push prerequisites for iOS delivery through Firebase

- [Manual] Enroll in the Apple Developer Program if not already enrolled.
- [Manual] Confirm the iOS app bundle identifier in the Apple Developer portal.
- [Manual] Enable Push Notifications capability for the app ID.
- [Manual] Create an APNs Auth Key (`.p8`) in Apple Developer.
- [Manual] Record the Apple Team ID and Key ID.
- [Manual] Upload the APNs Auth Key into Firebase for the iOS app.
- [Agent/CLI] After a human supplies the resulting Firebase app config files, wire them into the repo and build config.

### Android app prerequisites

- [Agent/CLI] Add Firebase Messaging dependencies and Android manifest/service changes.
- [Manual] Validate Android 13+ notification permission prompts on real devices.
- [Agent/CLI] Add notification channels and deep-link handling code.

### iOS app prerequisites

- [Agent/CLI] Add Firebase Messaging iOS dependencies, capability wiring, and token handling code.
- [Manual] Verify entitlements and push capability in Xcode / Apple portal if automatic signing does not fully cover it.
- [Manual] Validate on a real iPhone because APNs delivery cannot be fully trusted in simulators.

### Bridge deployment prerequisites

- [Agent/CLI] Add push-token persistence to the bridge database/storage layer.
- [Agent/CLI] Add bridge config for FCM sender credentials.
- [Manual] Deploy credentials securely to production secret storage.
- [Agent/CLI] Implement rotation-friendly secret loading.
- [Agent/CLI] Ensure the bridge can start and operate normally when push credentials are omitted.

## Suggested push registration flow

Initial pairing-based flow:

1. Mobile app obtains FCM registration token.
2. Mobile app sends the token to the bridge in a pairing-scoped request.
3. Bridge stores the token under that pairing scope.
4. Laptop/server marks a notification as push-worthy.
5. Bridge client polls local `/notifications`.
6. Bridge client sends a push-send request to the bridge.
7. Bridge looks up all matching tokens and sends pushes.

## Open design questions to settle during implementation

- What exact pairing key should be used for token lookup?
- Should the bridge client send raw token values back on each send request, or only a logical recipient key?
  - Current recommendation: bridge should look up tokens by logical key, not receive raw token values every time.
- Should notification acknowledgement clear only local polling visibility, or also suppress future pushes?
- How will stale paired-device tokens be pruned if the device disappears without unpairing?
- What is the exact runtime behavior when push support is disabled?
  - recommended answer: registration endpoints can report "push unavailable" cleanly, while non-push notification paths continue to work

## Recommended human docs for this stage

- `tasks/20260516-auth-notifications-staged-rollout/docs/push-notifications-fcm-apns.md`
