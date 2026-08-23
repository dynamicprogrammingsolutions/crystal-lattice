# Prepare Closed Testing And Production Readiness

Resolve the additional product, policy, review, media, quality, and operational
requirements needed before any release leaves the Google Play internal testing
track.

## Requirements checklist

- [ ] Google Play App content, Data safety, content rating, target audience,
      privacy, app access, and required declarations are complete and current.
- [ ] Store listing copy and all required graphics/screenshots are accepted and
      accurately represent the app.
- [ ] Reviewers have a reliable testable path from task `085`.
- [ ] Closed-testing requirements applicable to the developer-account type are
      identified and satisfied.
- [ ] Pre-launch reports, Android vitals/SDK warnings, permission findings, and
      device-compatibility issues are resolved or explicitly accepted.
- [ ] Release notes, country/device availability, pricing, staged rollout, and
      support readiness are approved.
- [ ] Production promotion is a separate explicit human-approved operation with
      rollback/stop controls.
- [ ] Current target API and Google Play policy requirements are revalidated at
      the actual submission date.

Parent Task: tasks/20260820-android-google-play-github-fastlane/000-main.md
Depends On: tasks/20260820-android-google-play-github-fastlane/085-google-play-review-testable-mode.md
Depends On: tasks/20260820-android-google-play-github-fastlane/090-first-internal-testing-release.md

## Required reading

Read the parent task's `Shared required reading`, then:

- Outputs from tasks `030`, `050`, `060`, `085`, and `090`
- Production access/testing requirements for new personal accounts:
  https://support.google.com/googleplay/android-developer/answer/14151465
- Prepare and roll out a release:
  https://support.google.com/googleplay/android-developer/answer/9859348
- Staged rollouts:
  https://support.google.com/googleplay/android-developer/answer/6346149
- Pre-launch reports:
  https://support.google.com/googleplay/android-developer/answer/9842757
- Android vitals:
  https://developer.android.com/topic/performance/vitals
- Target API requirements:
  https://support.google.com/googleplay/android-developer/answer/11926878
- Families/target audience:
  https://support.google.com/googleplay/android-developer/answer/9285070

## Readiness boundary

Successful internal testing does not imply production readiness.

Before closed testing or production:

- Verify whether the organization account is subject to any mandatory testing
  period or tester-count rule.
- Complete Data safety even if internal-only testing was exempt.
- Complete reviewer/app access with the exact submitted build.
- Provide final listing assets and current screenshots.
- Resolve policy warnings that do not block internal testing.
- Approve distribution countries/regions and device availability.
- Establish support response and incident ownership.

## Recommended promotion model

1. Internal testing for release engineering and trusted maintainers.
2. Closed testing for selected external/organization testers after reviewer
   access and compliance are complete.
3. Production through a small staged rollout.
4. Expand only after crash/ANR, support, and functional signals are acceptable.

Do not let the ordinary internal-upload workflow accept `production` as a free
form input. Promotion should use a separate protected workflow/lane with
required approval.

## Execution plan

Status: Draft

At execution time, refresh all Google policy and target-API requirements from
official sources because they change. Use the exact candidate build in closed
testing and reviewer validation. Prepare a release review packet and obtain
explicit owner approval before production rollout.

### Implementation decisions and open questions

- Decision: production is not authorized by this task's creation or internal
  release success.
- Recommendation: begin production with a small staged percentage and explicit
  halt criteria.
- Open question: production countries/regions.
- Open question: tablet/large-screen distribution and screenshot claims.
- Open question: support SLA and incident owner.
- Open question: rollout percentage/duration and success thresholds.

### Documentation

- Update public store listing/privacy/support content with current delivered
  behavior only.
- Document production promotion, halt, and rollback in the Android release
  runbook.
- Keep internal approval/evidence out of public user docs.

### Task checklist

- [ ] Revalidate account-specific testing requirements.
- [ ] Complete all App content/Data safety/rating declarations.
- [ ] Finalize and upload listing media.
- [ ] Complete review-mode and reviewer instructions.
- [ ] Run closed test and collect human feedback.
- [ ] Review pre-launch, vitals, SDK, permission, and device findings.
- [ ] Approve countries/devices/support/rollout plan.
- [ ] Prepare protected promotion mechanism.
- [ ] Obtain explicit production approval.

### Requirement verification

- Compliance: saved Play Console declarations and policy status.
- Listing: live/preview listing with accepted media and accurate copy.
- Reviewability: reviewer scenario completed on candidate build.
- Quality: pre-launch report plus closed-test physical-device evidence.
- Promotion control: workflow/lane cannot promote without protected approval.
- Production: Play Console staged rollout evidence only after explicit approval.

### Additional implementation verification

- Test halt/rollback procedure before broad rollout.
- Verify upload-key/service-account rotation does not require app-signing-key
  replacement.