# Deployment Runbook

Document the repeatable release process for TestFlight builds, credential rotation, troubleshooting, and future maintainers.

## Requirements checklist

- [ ] Document how to run local verification.
- [ ] Document how to build/upload locally with fastlane.
- [ ] Document how to trigger the GitHub Actions TestFlight workflow.
- [ ] Document version/build-number rules.
- [ ] Document required GitHub secrets and where they come from.
- [ ] Document signing strategy and recovery steps for common failures.
- [ ] Document App Store Connect/TestFlight registration and metadata update steps.
- [ ] Link the landing page/privacy policy and explain privacy-answer ownership.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/100-external-testflight-readiness.md

## Suggested Location

Use the location that best matches existing docs after inspecting current repo conventions. Good candidates include:

- `mobile/crystal-lattice-control-rn/README.md`, if the mobile README is being cleaned up.
- A new `mobile/crystal-lattice-control-rn/docs/ios-testflight.md`, if the details are too long for the README.
- A root-level deployment doc only if broader release docs already live there.

## Required Content

Include concise commands and decision points:

```bash
cd mobile/crystal-lattice-control-rn
npm run tsc
npm test -- --runInBand
bundle exec fastlane ios beta
```

Include GitHub Actions instructions:

- Which workflow to run.
- Which branch/tag/environment to select.
- Which secrets are required.
- How to find the uploaded build in App Store Connect.
- What to do if build processing fails.

## Acceptance Criteria

- A maintainer who did not implement the setup can ship a TestFlight build by following the runbook.
- The runbook avoids committing secrets or private Apple credentials.
- Any steps requiring Apple portal access are clearly marked with the required role/permission.
