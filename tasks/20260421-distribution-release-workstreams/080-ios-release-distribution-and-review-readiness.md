# iOS Release Distribution And Review Readiness

Prepare the React Native iOS app for TestFlight and App Store distribution, while making its companion-app positioning clear enough for App Review.

## Requirements checklist

- [ ] Finalize iOS versioning, signing, and archive/upload workflow.
- [ ] Improve onboarding or empty states so the no-server case is understandable and non-broken.
- [ ] Draft App Store / TestFlight metadata and review notes that explain the desktop/server dependency.
- [ ] Document the recommended path for TestFlight-first release and later public or unlisted App Store release.

Parent Task: `tasks/20260421-distribution-release-workstreams/000-main.md`

## Current state

- iOS bundle/version settings already exist in `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN.xcodeproj/project.pbxproj:260-314`.
- `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/Info.plist:29-45` already declares Bonjour and local-network permissions, which aligns with the app's discovery flow.
- The app's connection model is companion-oriented today, with transport selection and connection setup in `mobile/crystal-lattice-control-rn/App.tsx:46-143` and health-check/disconnect UI in `mobile/crystal-lattice-control-rn/src/ConnectionScreen.tsx:6-74`.

## Proposed solution from conversation

- Use App Store Connect plus TestFlight as the first public-facing iOS release path.
- Keep the app as a companion client; it does not need to become fully standalone to be App Store eligible.
- Make the dependency on the desktop/server component explicit in three places:
  - in-app onboarding / empty state copy,
  - the App Store description,
  - App Review notes.
- Emphasize that the app is available to any user who runs the open-source server component, so it should not be framed as a private closed-group app.
- Ensure the disconnected state is graceful, informative, and actionable, rather than looking like a broken or inaccessible product.
- Plan for internal TestFlight first, then external TestFlight, then decide between public and unlisted App Store release once messaging is polished.

## Deliverables

- iOS signing/archive/upload checklist.
- UX copy or implementation notes for first-run / no-server states.
- App Store metadata and review-note draft focused on companion-app positioning.