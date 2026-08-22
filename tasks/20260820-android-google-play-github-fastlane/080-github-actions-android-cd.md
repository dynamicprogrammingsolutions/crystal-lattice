# Add GitHub Actions Android Internal-Testing Deployment

Add a protected GitHub Actions workflow that verifies, signs, and uploads
Android builds to the Google Play internal testing track through fastlane.

## Requirements checklist

- [ ] A manually triggered GitHub Actions workflow deploys Android to Play
      internal testing.
- [ ] The workflow uses a compatible Ubuntu runner, Node 20, Java 17, Ruby
      3.4.10, locked Bundler dependencies, and Gradle wrapper.
- [ ] Verification must pass before signing or upload.
- [ ] Upload keystore and Google Play credentials are reconstructed only in
      temporary runner files and are not exposed in logs or artifacts.
- [ ] A protected GitHub Environment controls release secrets and approvals.
- [ ] Concurrent deployments cannot race on version codes or Play edits.
- [ ] Build logs and a safe AAB artifact are retained with appropriate
      retention, while secrets and keystores are never uploaded.
- [ ] Automatic tag/push deployment remains disabled until separately approved.

Parent Task: tasks/20260820-android-google-play-github-fastlane/000-main.md
Depends On: tasks/20260820-android-google-play-github-fastlane/070-fastlane-google-play-release.md

## Required reading

Read the parent task's `Shared required reading`, then:

- `.github/workflows/public-ci.yml`
- `.github/workflows/release-crystal-lattice-cli.yml`
- `mobile/crystal-lattice-control-rn/fastlane/Fastfile`
- GitHub Java setup:
  https://github.com/actions/setup-java
- GitHub Node setup:
  https://github.com/actions/setup-node
- Ruby setup:
  https://github.com/ruby/setup-ruby
- Gradle setup:
  https://github.com/gradle/actions/tree/main/setup-gradle
- GitHub environments:
  https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment
- GitHub secrets:
  https://docs.github.com/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions

## Proposed workflow

Recommended file:

```text
.github/workflows/deploy-android-google-play.yml
```

Initial trigger:

```yaml
on:
  workflow_dispatch:
    inputs:
      version_name:
        required: false
      version_code:
        required: false
      changelog:
        required: false
```

Recommended job:

- Runner: current supported `ubuntu-latest` or pinned supported Ubuntu image.
- Environment: `android-google-play`.
- Permissions: `contents: read`; add `id-token: write` only if/when federated
  authentication is implemented.
- Concurrency: one Android Play deployment at a time.

## GitHub Environment configuration

Environment variables:

```text
ANDROID_PACKAGE_NAME=com.dynamicprogrammingsolutions.crystallatticecontrolrn
ANDROID_VERSION_NAME=0.9.0
GOOGLE_PLAY_TRACK=internal
```

Environment secrets:

```text
ANDROID_UPLOAD_KEYSTORE_BASE64
ANDROID_UPLOAD_STORE_PASSWORD
ANDROID_UPLOAD_KEY_ALIAS
ANDROID_UPLOAD_KEY_PASSWORD
GOOGLE_PLAY_SERVICE_ACCOUNT_JSON
```

Recommended environment controls:

- Required reviewer from authorized release maintainers.
- No branch other than `main` for deployment.
- Manual trigger only.
- Secret access limited to this environment/job.

## Workflow sequence

1. Checkout the exact commit.
2. Setup Node 20 with npm cache.
3. Setup Java 17 and Gradle cache.
4. Setup Ruby 3.4.10 with Bundler cache.
5. `npm ci`.
6. Run Android fastlane verification.
7. Decode the upload keystore to a temporary file with `0600` permissions.
8. Write service-account JSON to a temporary file with `0600` permissions.
9. Export only required file paths/password variables.
10. Run `bundle exec fastlane android internal`.
11. Upload the AAB and safe logs as workflow artifacts if useful.
12. Delete temporary credential files in an `always()` cleanup step.

## Execution plan

Status: Draft

Implement the workflow after local signed build and Play credential validation
pass. Use pinned major action versions and inspect current release notes/security
guidance at execution time. Mask sensitive values and avoid shell tracing.
Exercise the workflow manually before enabling any additional trigger.

### Implementation decisions and open questions

- Decision: Ubuntu runner, not macOS.
- Decision: GitHub Environment `android-google-play`.
- Decision: manual trigger only for the initial workflow.
- Decision: no production-track input in the initial workflow.
- Open question: artifact retention period and whether internal AAB retention is
  needed after Play accepts the upload.
- Open question: organization/repository plan support for required environment
  reviewers must be verified; if unavailable, preserve manual trigger and
  restricted repository access and document the limitation.

### Documentation

- Document every GitHub variable/secret, secure creation command, rotation, and
  owner.
- Do not place secret values in README, task files, workflow defaults, or logs.
- Add a concise mobile README pointer to the package-owned release runbook.

### Task checklist

- [ ] Create environment and non-secret variables.
- [ ] Add the workflow.
- [ ] Add cache/toolchain setup.
- [ ] Add verification-before-secret-use ordering where practical.
- [ ] Add secure temporary credential reconstruction and cleanup.
- [ ] Add concurrency and least-privilege permissions.
- [ ] Configure secrets through secure prompts.
- [ ] Run workflow manually.
- [ ] Inspect logs for masking and verify Play internal release.

### Requirement verification

- Workflow syntax: GitHub accepts and lists the workflow.
- Toolchain: logs show intended Node/Java/Ruby/Gradle versions.
- Gating: intentional verification failure prevents upload.
- Secret handling: no credential content in logs/artifacts; temp files cleaned.
- Deployment: successful run maps to the expected Play internal release.
- Concurrency: overlapping trigger is queued or cancelled according to the
  documented policy.

### Additional implementation verification

- Verify forks and pull requests cannot access deployment secrets.
- Verify workflow cannot select closed/open/production tracks.
- Review GitHub Actions usage and cache storage after the first run.