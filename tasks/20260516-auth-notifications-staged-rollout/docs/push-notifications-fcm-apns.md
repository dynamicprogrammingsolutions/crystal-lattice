# Push Notifications: FCM And APNs

This document explains the push-notification concepts used by the staged rollout plan. It is written for humans who need to understand what the services and keys are before implementation or deployment work starts.

## What a push notification is

A push notification is a message delivered to a mobile device by the operating system on behalf of a trusted push provider.

Why that matters:

- A backgrounded or terminated app usually cannot keep arbitrary network activity alive forever.
- The operating system trusts its push provider:
  - Apple devices trust APNs
  - Android devices usually trust FCM
- The push provider is what lets a backend ask the OS to show or deliver a notification later.

## The main services

### APNs

APNs stands for Apple Push Notification service.

It is Apple’s official push service for iPhone and iPad apps. If an iOS app needs reliable remote notifications for irregular events, APNs is the standard delivery path.

### FCM

FCM stands for Firebase Cloud Messaging.

It is Google’s push-notification service. It delivers messages to Android devices directly and can also act as the provider path for iOS when the app is configured with Firebase plus APNs credentials.

### Why use FCM for both Android and iOS

Using FCM as the single bridge-side sending API is often simpler because:

- the backend sends to one provider API
- Android delivery is direct through FCM
- iOS delivery can flow through Firebase to APNs
- backend secrets and code paths are simpler

## Important terms

### Device token

On Apple platforms, the app receives a device token from APNs. This token identifies the app instance to Apple’s push system.

### Registration token

With Firebase, the app usually receives an FCM registration token. This token identifies the app instance to Firebase messaging.

In practice, teams often just say "push token" for both.

### Provider

The provider is the service that actually delivers the push:

- APNs for Apple delivery
- FCM for Android delivery and optionally as the backend send API for both platforms

### Payload

The payload is the JSON data sent in the notification request. It should be kept small and should avoid sensitive contents unless there is a deliberate reason.

### Deep link

A deep link is the app route or URI used when the user taps the notification, for example to open a specific server or session.

## How the full delivery path works

Common FCM-first flow:

1. Mobile app asks the OS/Firebase SDK for permission and a token.
2. Mobile app sends that token to the product backend.
3. Product backend stores the token.
4. Later, the backend sends a push request to FCM.
5. FCM delivers:
   - directly to Android devices
   - to APNs for iOS devices when configured
6. The OS shows the notification or wakes the app according to the payload and platform rules.

## Why token storage matters

Push tokens can change. This is called token refresh or rotation.

If the product only stores the token on the laptop/server and that process is offline when the phone refreshes its token, the system can lose the current address for that device.

That is why the staged rollout recommends bridge-side token persistence once push is added.

## Keys, credentials, and signing methods

### Firebase service account

A Firebase/Google service account is a server-side identity used by the backend to call FCM HTTP v1.

The backend authenticates to Google and receives an OAuth access token for sending.

This credential belongs on the server side only.

### APNs Auth Key (`.p8`)

Apple supports token-based provider authentication using an APNs Auth Key.

The key is created in Apple Developer and identified by:

- Team ID
- Key ID
- the `.p8` private key file

When sending directly to APNs, the backend signs a JWT using this private key. Apple verifies that JWT and allows the notification request if it is valid.

### JWT

JWT means JSON Web Token.

In the APNs context, it is a signed token the sender creates to authenticate itself to Apple.

In the auth/OIDC context, JWTs are also used as user/session bearer tokens. Same term, different purpose.

### Why “signing” matters

Signing proves who created a token or request.

Examples:

- APNs provider token: signed by the backend using the Apple `.p8` key
- authentik-issued access token: signed by authentik using its signing key

Signing is different from encryption:

- signing proves integrity and authorship
- encryption hides contents

## Manual setup steps for push infrastructure

### Firebase / FCM

- [Manual] Create or choose a Firebase project.
- [Manual-preferred] Register Android and iOS apps in Firebase.
- [Manual] Download app config files.
- [Manual or CLI] Create service account credentials or workload identity for server-side FCM sending.

### Apple / APNs

- [Manual] Join Apple Developer if not already enrolled.
- [Manual] Enable Push Notifications for the iOS app ID.
- [Manual] Create an APNs Auth Key.
- [Manual] Upload the APNs key into Firebase if using Firebase for iOS delivery.

## What this staged plan assumes

Stage 2 assumes:

- the bridge is the remote push sender
- the bridge stores push tokens
- pairing can authorize initial token registration
- login/identity can be layered in later

It also assumes push is optional:

- self-hosters may choose not to configure Firebase or APNs at all
- local polling notifications should still provide value without push
- the software should degrade cleanly when push credentials are not configured

## What push does not solve by itself

Push does not tell the product which user owns the token. The product must still decide how to bind tokens to:

- a pairing
- a server
- a device
- later, a user identity
