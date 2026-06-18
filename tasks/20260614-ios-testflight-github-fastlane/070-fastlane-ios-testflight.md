# Add fastlane For iOS Build And TestFlight Upload

Add fastlane configuration so the iOS app can be built, signed, archived, and uploaded to TestFlight repeatably.

## Requirements checklist

- [ ] Add/confirm Ruby dependency setup for fastlane under `mobile/crystal-lattice-control-rn`.
- [ ] Add iOS fastlane configuration with lanes for verification/build/beta upload.
- [ ] Choose and implement signing strategy: recommended `fastlane match`, or a documented manual secret/profile approach.
- [ ] Use App Store Connect API key authentication for upload.
- [ ] Implement build-number incrementing that works locally and in GitHub Actions.
- [ ] Verify the lane can archive locally when credentials are available.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/060-app-store-connect-registration-package.md

## Known Starting State

Current files:

- `mobile/crystal-lattice-control-rn/Gemfile` exists.
- No `fastlane/` directory was found under the mobile app during the audit.
- No `eas.json`, Codemagic, or Bitrise config was found for this app.

Likely files to add:

- `mobile/crystal-lattice-control-rn/fastlane/Fastfile`
- `mobile/crystal-lattice-control-rn/fastlane/Appfile`
- Possibly `mobile/crystal-lattice-control-rn/fastlane/Matchfile`, if using `match`

Suggested lanes:

- `ios verify`: run app verification such as typecheck/tests/lint where appropriate.
- `ios build`: archive without upload.
- `ios beta`: archive and upload to TestFlight with `pilot`.

Suggested fastlane actions:

- `app_store_connect_api_key`
- `increment_build_number` or explicit build number from CI
- `match` or documented certificate/profile import
- `build_app`
- `pilot`

## Acceptance Criteria

- fastlane configuration is checked in and documented.
- Sensitive credentials are not committed.
- A maintainer with proper Apple credentials can run the beta lane locally.
- The lane archives the `CrystalLatticeControlRN` scheme from the correct workspace.
