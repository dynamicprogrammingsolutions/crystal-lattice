# Release The Reviewed macOS Desktop Tester Update

Publish a fresh universal app-only DMG containing the approved Desktop product
changes, using the existing Fastlane/GitHub Actions/CDN path. Source/native
capture evidence does not establish that those changes exist in the currently
downloadable `0.9.0 (4)` application.

## Requirements checklist

- [ ] An approved committed main revision containing the selected Desktop
  changes is released with an intentional new marketing version/build as one
  universal Apple Silicon/Intel app-only DMG.
- [ ] The app preserves Crystal Lattice Desktop identity, the supported
  deployment target and existing supported connection/session behavior, and
  the selected changes work with the approved compatible runtime.
- [ ] Existing Developer ID signing, Hardened Runtime, notarization, stapling,
  strict bundle inspection and checksum verification succeed without exposing
  credentials or weakening the established release policy.
- [ ] The exact reviewed candidate is published under new immutable CDN
  paths; `0.9.0` remains available and published outputs identify the same
  source/version/build/checksum.
- [ ] The public artifact passes installed-app checks for the selected
  changes and explicit human Apple Silicon acceptance. Both native slices
  are verified automatically and Intel feedback remains traceable.
- [ ] Maintained website release metadata and current installation/release
  guidance refer to the verified new artifact after approved publication.

## Scope and unresolved decisions

This follow-up tracking was approved on October 7, 2026. Its implementation,
source/version selection, commit and publication approvals remain separate.

**HUMAN JUDGMENT:** choose the exact reviewed Desktop changes/source revision,
new marketing version/build, compatible runtime release and final acceptance.
Do not infer approval of other pending work from its presence in main.

**DEPENDENCY QUESTION:** if a selected feature needs a server API absent from
the supported released CLI, identify the compatible release or coordinate a
separately approved CLI update before claiming the feature in a public build.

## Supporting evidence and ownership

- Baseline:
  `tasks/20260928-universal-macos-desktop-fastlane-release.md` released
  `0.9.0 (4)` from `1a04b8689eab0821727be2c3efc9213e57ebafe7`.
- Its candidate run `36633536807` and publication run `36685765746` establish
  the working manual build/review/exact-candidate publication path.
- Coordinates with:
  `tasks/20260930-homepage-getting-started-and-waitlist/018-homepage-visuals-product-improvements.md`.
  Selected product changes may be released after their own review without
  waiting for every website image or the waitlist.
- Later CLI/PKG/onboarding work remains in
  `tasks/20260820-macos-desktop-distribution/000-main.md`; this update is
  app-only and does not change its remaining requirements.
- Website data is owned by
  `landing_page/src/content/releases/desktop.yaml`. A landing-source push
  triggers the existing site workflow, so metadata promotion is a publication
  boundary.

## Execution plan

Status: Draft

Reuse the package-owned Fastlane lanes and manual desktop workflow. First
select and approve a committed source and compatible runtime, then align the
single version source and candidate/publisher validation expectations.
Existing workflow validation uses `0.9.0`; inspect and update those expectations
for the approved new version rather than relabeling or overwriting old assets.

Build and retain a candidate without publication. Check the actual installed
Release application against the approved changes through the public backend.
Review that candidate's exact source and checksum. Publish that same artifact,
verify its public download, and only then promote website metadata.

### Steps and human boundaries

1. **AGENT:** Inspect current release settings and the reviewed changes.
   Prepare the exact source/runtime/version proposal and compatibility gaps.
2. **HUMAN JUDGMENT:** Approve the included changes, runtime and version/build.
   Remaining first-release human acceptance stays in its own record.
3. **AGENT:** Align version settings, build/publisher validation and maintained
   release guidance. Preserve secure signing, immutable publication and
   independent DMG operation.
4. **AGENT:** Run relevant verification and installed-candidate/native checks.
   Use existing UI-automation permission where available.
   **HUMAN if required:** resolve a new OS permission or credential-owner
   boundary through its secure interface.
5. **AGENT + EXPLICIT COMMIT AUTHORIZATION:** Commit only the approved release
   changes. Prepare a clean main candidate using the existing build-only
   workflow and read-only signing credentials.
6. **AGENT:** Verify source cleanliness, bundle metadata, both architectures,
   entitlements, signatures, notarization, staple and checksum.
7. **AGENT + HUMAN:** Install the actual candidate without Metro, connect to
   the approved runtime and exercise the selected picker/menu/message/session
   changes and relaunch. **HUMAN JUDGMENT:** accept Apple Silicon behavior.
8. **HUMAN PUBLICATION APPROVAL:** Review candidate run, source, version/build,
   checksum and findings. Approve publication of that exact artifact.
9. **AGENT:** Publish through the existing workflow/CDN, independently download
   and verify it, and preserve the previous version.
10. **AGENT + HUMAN SITE APPROVAL:** Update the maintained release data to the
    verified artifact. Review the public controls, then authorize the
    publishing commit/push and verify production links.

### Implementation decisions and open questions

- Approved: retain the universal app-only path and existing infrastructure.
- Open: selected source/features, version/build and runtime compatibility.
- Preserve the first DMG's automated universal checks/Intel-feedback approach;
  no future CLI/PKG acceptance is inferred from it.
- Routine signing reuses existing credentials. Any new owner credential,
  certificate rotation or policy change needs its explicit approval.
- Candidate build, release publication and website publication remain
  distinct reviewable boundaries.

### Documentation

- Update package-owned release/installation guidance and maintained website
  metadata to verified current behavior.
- Keep source/version/checksum evidence in this task; public copy describes
  the delivered app and any real runtime compatibility requirement.

### Task checklist

- [ ] **AGENT + HUMAN:** Select and approve source, runtime and version/build.
- [ ] **AGENT:** Align release settings and verify the selected changes.
- [ ] **HUMAN as needed:** Resolve actual permission/credential boundaries.
- [ ] **AGENT + HUMAN:** Commit approved changes and produce a clean candidate.
- [ ] **AGENT:** Inspect universal/security/notarization/checksum evidence.
- [ ] **AGENT + HUMAN:** Verify the installed candidate and accept its behavior.
- [ ] **HUMAN:** Approve exact-candidate publication.
- [ ] **AGENT:** Publish, download and independently verify the new artifact.
- [ ] **AGENT + HUMAN:** Promote website metadata and verify production links.

### Requirement verification

- Requirements 1–3: clean workflow evidence and inspection of the actual
  archived/installed Release app, with public-backend/native checks for each
  approved changed behavior.
- Requirement 4: candidate/run metadata plus fresh CDN download agree on the
  approved source/version/build/checksum; old assets remain available.
- Requirement 5: installed candidate/public-artifact checks and recorded human
  Apple Silicon acceptance; universal slice checks and later Intel feedback.
- Requirement 6: generated production HTML and live download/metadata checks
  after the approved site publication.

### Additional implementation verification

- Verify candidate selection cannot rebuild/substitute a different artifact.
- Check compatibility against the approved released runtime rather than only
  an unreleased development server or screenshot harness.