# Add Continuous CLI Development Releases From Main

Publish uniquely identified, installable CLI development builds from protected
`main` without weakening stable release semantics or production publication
controls.

## Requirements checklist

- [ ] Eligible pushes to protected `main` can produce a tested, uniquely identified multi-platform CLI development release.
- [ ] Stable tag releases, stable `latest.txt`, and the default installer channel remain unchanged.
- [ ] Development archive names, runtime manifests, Python package metadata, GitHub release tags, installer output, and CLI-reported version/build identity agree.
- [ ] Each development release records its GitHub build number and source commit.
- [ ] Development releases use a separate installer marker/channel and are clearly labeled as prereleases.
- [ ] Only protected `main` and a protected development-release environment can obtain GitHub/AWS publication authority.
- [ ] Retries are idempotent, superseded builds are cancelled where safe, and retention bounds ongoing Actions/storage cost.
- [ ] Any deduplication mechanism cannot skip a change that affects the packaged runtime.

Parent Task: tasks/20260804-open-source-public-release/000-main.md
Depends On:

- `tasks/20260804-open-source-public-release/040-minimum-ci-and-automation-hardening.md`
- `tasks/20260804-open-source-public-release/080-post-publication-validation-and-early-adopter-intake.md`

## Current release boundary

- The existing workflow builds and smoke-tests Linux, macOS Intel, macOS ARM,
  and Windows bundled-Python archives.
- Stable publication currently requires a
  `crystal-lattice-cli-v<project.version>` tag.
- The workflow publishes a GitHub Release, uploads archives to the
  CloudFront-backed download endpoint, and updates stable `latest.txt`.
- The archive builder accepts a version override for filenames and
  `runtime-package.json`, but `application/python/pyproject.toml` remains the
  Python package metadata source. A development release must not expose
  conflicting archive and embedded package versions.
- The installer already accepts an explicit `VERSION`, making a separate
  development channel feasible without changing the stable default.
- The current AWS OIDC role is release-tag oriented. Main-branch development
  publication requires a separately reviewed branch/environment trust path.

## Delivery options

### Option A: Release every protected-main push

Every push to `main` runs tests and the native build matrix, then publishes a
unique development prerelease.

Example identity:

```text
Version: 0.2.0.dev123
Tag: crystal-lattice-cli-v0.2.0.dev123
Build: 123
Commit: a174609b...
```

Advantages:

- Simple, predictable behavior.
- Every main commit has downloadable binaries.
- Easy source-to-binary traceability.
- No risk that a hand-maintained path list omits a packaged input.

Costs:

- Documentation-only and unrelated commits still run the four-platform build.
- GitHub prereleases and S3 objects accumulate.
- Rapid main pushes can waste runner time without concurrency control.

Recommendation: use this for the initial implementation. Add cancellation
before publication and an explicit retention policy. Measure actual cost before
adding deduplication.

### Option B: Release only when selected paths change

Use workflow path filters or a changed-path gate for the CLI, core,
release/build scripts, bundled configuration, and included plugins.

Advantages:

- Avoids obvious documentation-only or unrelated builds.
- Easy to understand when the packaged input boundary is small and stable.

Risks:

- The bundled runtime spans core, application, packaging scripts,
  configuration, and selected plugins.
- An incomplete path list can silently skip a release after a material runtime
  change.
- The path list becomes another release-critical manifest that must stay
  synchronized with packaging behavior.

Recommendation: do not use as the initial gate unless the task first derives
and tests a canonical package-input manifest from the bundle builder.

### Option C: Deduplicate by packaged-input fingerprint

Compute a deterministic fingerprint over the exact source/configuration inputs
staged into the CLI bundle and compare it with the last successful development
release.

Advantages:

- Most accurate avoidance of no-op rebuilds.
- Can ignore unrelated repository changes without relying on a manually
  maintained path list.
- Produces durable provenance for why two commits share or do not share a
  binary build.

Costs and risks:

- Requires a canonical, tested definition of bundle inputs.
- Requires persistent publication metadata and careful behavior for missing,
  partial, or failed prior releases.
- Adds retry, cache, and race-condition complexity.

Recommendation: treat this as the preferred later optimization if continuous
build cost becomes material. It is not required for the first development
release channel.

## Recommended design

- Preserve the current stable tag workflow and stable `latest.txt`.
- Add a trusted `main` development-release path using Option A initially.
- Derive the development version as
  `<next-stable-version>.dev<github.run_number>`.
- Record the full source SHA in release notes and package build metadata.
- Keep retries on the same logical development version; use run-attempt
  information only as operational metadata.
- Publish immutable versioned archives and a GitHub prerelease.
- Add `latest-dev.txt` or an equivalently explicit development marker.
- Extend the installer with an opt-in development channel while retaining exact
  `VERSION` installation.
- Add or improve `crystal-lattice --version` so the installed binary reports
  version, build number, and source commit.
- Use a dedicated protected environment such as `cli-development-release`.
- Use a separate or explicitly reviewed AWS OIDC trust statement restricted to
  protected `main` and the development download prefix.
- Cancel superseded main builds before publication; never interrupt an active
  publication transaction.
- Start with a small retention target, such as the newest 10-20 development
  releases, and preserve any build explicitly retained for investigation.

## Execution plan
Status: Draft

First verify the release cadence and costs observed after public publication.
Choose the next stable version line that owns `.devN` builds, the development
environment name, and retention count.

Refactor or extend the release workflow so stable tags and main development
builds share test/build logic but have separate publication conditions,
environments, markers, and release classifications. Avoid a privileged
`workflow_run` path when a direct trusted `push` trigger is sufficient.

Implement one version-injection mechanism that keeps Python metadata, staged
runtime metadata, filenames, installer selection, and displayed CLI identity
consistent. Prefer a temporary build-tree transformation or another explicit
build input over mutating the source checkout.

Add tests for generated versions, archive names, manifests, installer channel
selection, idempotent retries, stable/development marker separation, and
publication conditions. Exercise the development flow first against the test
download profile, then require explicit owner approval before enabling
production development publication.

### Implementation decisions and open questions

- Recommendation: start with Option A.
- Recommendation: preserve stable releases and add a separate development
  prerelease/channel.
- Recommendation: use PEP 440-compatible `.devN` versions and record commit SHA
  separately.
- Recommendation: defer Option C until observed cost justifies its complexity.
- Question: what is the next stable version base for development builds?
- Question: should development releases publish to the production download
  domain under a separate marker/prefix, or remain on the testing domain
  initially?
- Question: what retention count should apply to GitHub prereleases and S3
  archives?
- Question: should the installer option be named `CHANNEL=development`,
  `CRYSTAL_LATTICE_RELEASE_CHANNEL=development`, or both?

### Documentation

- Update the CLI release runbook with stable and development channels.
- Document exact-version and development-channel installation.
- Document build identity, retention, promotion, rollback, and cost ownership.

### Task checklist

- [ ] Review post-publication release cadence and costs.
- [ ] Resolve development version base, environment, domain/prefix, and retention questions.
- [ ] Implement consistent build/version identity.
- [ ] Add protected-main development build and prerelease publication.
- [ ] Add the separate development installer marker/channel.
- [ ] Add idempotency, concurrency, retention, and optional deduplication controls.
- [ ] Validate against the test download profile.
- [ ] Obtain owner approval before enabling production development publication.

### Requirement verification

- A protected-main commit produces matching development release identity across
  the installed CLI and every published artifact.
- Stable installs continue to resolve only stable `latest.txt`.
- Development installs resolve the explicit development marker/channel.
- An untrusted pull request cannot reach either stable or development
  publication authority.
- Re-running a build does not create a second logical version, and superseded
  pre-publication runs do not publish stale assets.

### Additional implementation verification

- Verify all four native archives and the installer against the test download
  profile.
- Verify the AWS OIDC subject/environment restriction for protected `main`.
- Verify retention does not delete stable releases or retained investigation
  builds.
- If Option B or C is adopted, prove with tests that every staged bundle input
  contributes to the change detector.