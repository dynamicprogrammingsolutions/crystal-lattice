# Add GitHub Actions iOS Continuous Deployment

Add a GitHub Actions workflow that runs verification and uploads iOS builds to TestFlight through fastlane.

## Requirements checklist

- [ ] Add a GitHub Actions workflow for iOS TestFlight deployment.
- [ ] Trigger manually with `workflow_dispatch`; optionally add tag-based release triggers after approval.
- [ ] Install Node 20 dependencies, Ruby/bundler dependencies, and CocoaPods.
- [ ] Run mobile verification before uploading.
- [ ] Configure Apple authentication and signing through GitHub secrets.
- [ ] Call the fastlane beta lane.
- [ ] Document all required GitHub secrets and environment protections.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/070-fastlane-ios-testflight.md

## Known Starting State

Current `.github/workflows` contains workflows for docs/CLI release, but no mobile iOS deployment workflow was found.

The app package expects:

- Node `>=20`
- React Native `0.82.1`
- npm scripts:
  - `npm run tsc`
  - `npm test`
  - `npm run lint`
  - `npm run pod-install`

Suggested workflow shape:

```yaml
on:
  workflow_dispatch:
```

Suggested job outline:

1. Checkout.
2. Setup Node 20 with npm cache.
3. Install dependencies from `mobile/crystal-lattice-control-rn`.
4. Setup Ruby and Bundler cache.
5. Install pods.
6. Run `npm run tsc`.
7. Run `npm test -- --runInBand`.
8. Run fastlane beta lane with App Store Connect API key and signing credentials.

Secrets to document depend on signing strategy, but likely include:

- App Store Connect API key ID
- App Store Connect issuer ID
- App Store Connect private key
- Apple team ID
- Match git URL/token and match password, if using `match`
- Or encrypted certificate/provisioning-profile secrets, if using manual signing assets

## Acceptance Criteria

- Workflow can be started manually from GitHub Actions.
- Workflow fails before upload if verification fails.
- Workflow does not expose signing material or App Store Connect keys in logs.
- Workflow uploads to TestFlight when secrets and App Store Connect app record are present.
