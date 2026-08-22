# Document Android Release, Recovery, And Operations

Create the package-owned maintainer documentation needed to repeat Android
internal releases, promote approved builds, rotate credentials, and recover
from common Google Play/signing failures.

## Requirements checklist

- [ ] A maintainer can perform local verification, signed AAB build, and
      internal upload from documented prerequisites and commands.
- [ ] GitHub Actions variables, secrets, environment protections, and manual
      trigger behavior are documented without secret values.
- [ ] Version-name/version-code policy and track-promotion behavior are clear.
- [ ] Upload-key backup, loss, reset, and rotation procedures are actionable.
- [ ] Service-account/API credential creation, permission, rotation, and
      revocation procedures are actionable.
- [ ] Play App Signing ownership and the distinction between app-signing and
      upload keys are clear.
- [ ] Troubleshooting covers build, signing, API, Play edit, processing,
      reviewer, and rollout failures.
- [ ] Documentation describes current committed behavior and is discoverable
      from the mobile package without exposing task/approval internals.

Parent Task: tasks/20260820-android-google-play-github-fastlane/000-main.md
Depends On: tasks/20260820-android-google-play-github-fastlane/080-github-actions-android-cd.md
Depends On: tasks/20260820-android-google-play-github-fastlane/090-first-internal-testing-release.md
Depends On: tasks/20260820-android-google-play-github-fastlane/100-closed-and-production-readiness.md

## Required reading

Read the parent task's `Shared required reading`, then:

- `docs/development/repository/documentation.md`
- `docs/development/standards/documentation.md`
- `mobile/crystal-lattice-control-rn/README.md`
- Final Android fastlane lanes and GitHub workflow
- Android signing:
  https://developer.android.com/studio/publish/app-signing
- Upload-key reset:
  https://support.google.com/googleplay/android-developer/answer/9842756
- Google Play Developer API:
  https://developers.google.com/android-publisher/getting_started
- Manage service-account keys:
  https://cloud.google.com/iam/docs/keys-create-delete
- GitHub secret rotation:
  https://docs.github.com/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions

## Documentation placement

Preferred durable source:

```text
mobile/crystal-lattice-control-rn/docs/development/android-release.md
```

If the package development documentation structure is not yet present, create
the minimal useful index required by repository documentation policy and link
it from the mobile README or nearest package entry point. Do not create empty
placeholder pages.

The mobile README should contain only concise first commands and a link to the
detailed maintainer guide.

## Required runbook content

### Release prerequisites

- Required Node, Java, Ruby, Bundler, Android SDK, and Gradle versions.
- Play Console/Cloud/GitHub roles.
- Local ignored signing and API paths.
- Safe commands to validate tooling without deployment.

### Normal release

- Update/confirm version name.
- Select version code.
- Run verification.
- Build and inspect signed AAB.
- Trigger protected GitHub workflow.
- Confirm Play processing and internal track.
- Tester/install verification.
- Approved promotion procedure.

### Credential ownership and recovery

- App-signing key is held by Google Play App Signing.
- Upload key is company-controlled and backed up offline.
- Alias/fingerprint/expiration and password-manager records.
- Upload-key reset request procedure.
- Service-account scope, key rotation, and revocation.
- GitHub Environment secret replacement.
- Personnel offboarding checklist.

### Failure handling

- Version-code collision.
- Wrong upload certificate.
- Lost/corrupted keystore.
- Invalid service-account JSON or revoked API access.
- Play edit conflict/timeout.
- AAB processing or policy rejection.
- Missing native library/ABI.
- Manifest permission or SDK warning.
- Internal tester cannot opt in/install.
- Reviewer cannot access functionality.
- Staged rollout halt.

## Execution plan

Status: Draft

Write the guide after actual local and GitHub releases establish the real
commands and account behavior. Test commands from a clean shell and have a
second maintainer review the credential-recovery steps. Keep sensitive values in
the password manager/secret systems and use placeholders in documentation.

### Implementation decisions and open questions

- Decision: package-owned development documentation is the source of truth.
- Decision: README remains concise.
- Decision: no secret values, personal recovery data, task IDs, or temporary
  approval state in public/package documentation.
- Open question: named operational owners and support SLA belong in private
  company records if unsuitable for public repository documentation.

### Documentation

- Create/update the package development guide and its discoverability links.
- Validate links and commands.
- Keep current behavior synchronized with fastlane/workflow changes.

### Task checklist

- [ ] Draft the runbook from completed implementation.
- [ ] Add concise README entry and development-doc route.
- [ ] Validate local commands from a clean shell.
- [ ] Validate GitHub workflow instructions.
- [ ] Validate upload-key backup/reset instructions.
- [ ] Validate service-account rotation/revocation instructions.
- [ ] Add troubleshooting and promotion/halt procedures.
- [ ] Obtain second-maintainer review where available.

### Requirement verification

- First-success path: another maintainer can run verification and locate the
  signed AAB/internal workflow.
- Secret safety: documentation contains names/placeholders only.
- Recovery: reviewer can identify upload-key reset and service-account
  revocation steps without independent research.
- Discoverability: mobile package entry point reaches the guide.
- Current-state accuracy: commands and expected results match committed
  implementation and observed release behavior.

### Additional implementation verification

- Run repository documentation preparation/build if the package docs are
  published through the documentation site.
- Scan documentation for accidental credential material before commit.