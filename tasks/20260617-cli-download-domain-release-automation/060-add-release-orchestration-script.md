# Add Release Orchestration Script

Add a maintainer-facing script that validates release state, creates/pushes the release tag, watches GitHub Actions, and smoke-tests the configured download endpoint after the GitHub matrix publishes artifacts.

## Requirements checklist

- [x] Add `deploy/aws-cli-downloads/release.sh`.
- [x] Validate requested version against `application/python/pyproject.toml`.
- [x] Validate release tag name `crystal-lattice-cli-v<version>`.
- [x] Check git status unless explicitly bypassed.
- [x] Optionally run local fast tests or document why skipped.
- [x] Create and push the release tag only when explicitly requested.
- [x] Watch/report the GitHub Actions release workflow run.
- [x] Report GitHub Release URL when available.
- [x] Run or print `smoke.sh` command for the configured download profile.
- [x] Document release orchestration in the README.
- [ ] Test in no-op/dry-run mode.
- [ ] Test against the testing profile before any production use.

Parent Task: `tasks/20260617-cli-download-domain-release-automation/000-main.md`

Depends On:

- `tasks/20260617-cli-download-domain-release-automation/040-add-github-oidc-role-and-vars-setup.md`
- `tasks/20260617-cli-download-domain-release-automation/050-update-release-workflow-to-use-configured-download-target.md`

## Boundary

`release.sh` orchestrates GitHub. It does not locally build all platform artifacts.

It may:

- validate the local version
- validate the tag does not already exist, unless explicitly allowed
- create and push a tag
- call `gh run list/view/watch`
- call `smoke.sh`

It must not:

- claim to produce official platform release archives locally
- bypass the GitHub matrix build
- upload partial local platform artifacts as an official release unless explicitly using `publish-assets.sh`

## Expected Commands

Dry run:

```bash
deploy/aws-cli-downloads/release.sh \
  --profile test \
  --version 0.2.0 \
  --dry-run
```

Create/push tag and watch:

```bash
deploy/aws-cli-downloads/release.sh \
  --profile test \
  --version 0.2.0 \
  --push-tag \
  --watch
```

Production later:

```bash
deploy/aws-cli-downloads/release.sh \
  --profile prod \
  --version 0.2.0 \
  --push-tag \
  --watch
```

## Documentation Requirements

README must explain:

- prerequisites
- version/tag validation
- dry-run mode
- what `--push-tag` does
- how to watch workflow logs
- how to recover if GitHub Actions fails
- how to rerun publish/promotion without rebuilding
- how test profile differs from production profile

## Testing Requirements

Run:

```bash
deploy/aws-cli-downloads/release.sh --profile test --version <current-version> --dry-run
```

Verify:

- version parsing works
- tag name is correct
- script refuses dirty worktree unless bypassed
- script prints exact `git tag`, `git push`, and `gh` commands in dry-run mode
- script uses testing profile base URL

If approved for a real test tag:

- run against the testing profile
- confirm GitHub Actions matrix starts
- confirm publish job targets the testing download bucket/domain
- confirm `smoke.sh` passes against the testing domain

## Execution plan

Status: Approved

Finish the orchestration script before it is trusted to create the new release
tag required by subtask 050.

Correct the current script behavior:

1. Keep version, clean-worktree, local-tag, and remote-tag validation.
2. Make `--dry-run` usable for an approved new version before its tag exists.
3. Before `--push-tag`, capture the release commit SHA and verify it is present
   on `origin/main`.
4. Validate that GitHub's non-secret CLI download variables match the selected
   `--profile`. The profile currently controls only local stack lookup and
   smoke output; without this guard a test-profile invocation can still publish
   to production through repository variables.
5. Verify the OIDC secret name exists in `gh secret list`.
6. After pushing the tag, poll `gh run list` using the workflow name, `push`
   event, release commit SHA, and tag until the corresponding run ID appears.
7. Call:

   ```bash
   gh run watch <run-id> --repo <repo> --exit-status
   ```

   The current script calls `gh run watch` without a run ID.
8. On success, query and print the GitHub Release URL with
   `gh release view <tag>`.
9. Print the exact smoke command for the selected profile and version. During
   the real validation campaign, execute that command immediately after the
   script returns.
10. Make failures report the tag, commit SHA, run ID when known, and safe
    recovery options. Do not automatically delete or move a published tag.

Add focused tests around the script's command/control behavior using a fake
`git`, `gh`, stack-output environment, or another isolated harness:

- valid dry-run prints the expected tag and does not mutate git
- dirty worktree is rejected
- requested version mismatch is rejected
- existing local and remote tags are rejected
- selected profile/GitHub variable mismatch is rejected
- missing OIDC secret is rejected
- run discovery selects the push run for the release SHA rather than an older
  workflow-dispatch run
- failed watched run propagates a non-zero exit
- successful watched run prints the release URL and smoke command

Run the corrected script in stages:

1. Run `--profile test --version <new-version> --dry-run` on a clean release
   commit while GitHub variables still point to production. Confirm the new
   profile mismatch guard refuses or clearly reports that state.
2. Switch GitHub configuration to testing as planned in subtask 050.
3. Repeat the dry run and require success.
4. Run the actual:

   ```bash
   deploy/aws-cli-downloads/release.sh \
     --profile test \
     --version <new-version> \
     --push-tag \
     --watch
   ```

5. Confirm the script watches the correct run, exits successfully, prints the
   GitHub Release URL, and prints the testing-domain smoke command.
6. Run the printed smoke command and record its result.

### Implementation decisions and open questions

- Requirement question: this script will create a public release tag. It shares
  the version and authoritative-main approval required by subtask 050.
- Implementation decision: refuse to push a tag when repository download
  variables do not match the selected profile. A warning is insufficient
  because the mismatch can publish a release to the wrong bucket/domain.
- Implementation decision: identify the workflow run by release commit SHA and
  `push` event, then pass the concrete run ID to `gh run watch`.
- Implementation decision: do not auto-delete tags or releases after failure;
  print recovery instructions and require explicit maintainer action.

### Documentation

- Update `deploy/aws-cli-downloads/README.md` to state that `--profile` must
  match the currently configured GitHub repository variables.
- Document run-ID discovery, release URL output, and failure recovery.
- Record dry-run and real-run evidence in this task.

### Task checklist

- [x] Add selected-profile versus GitHub-variable validation.
- [x] Add OIDC secret existence validation.
- [x] Fix release workflow run discovery and `gh run watch` invocation.
- [x] Print the GitHub Release URL after successful publication.
- [x] Add focused orchestration-script tests.
- [x] Run local syntax/lint/tests.
- [ ] Run a successful testing-profile dry run for the approved version.
- [ ] Create/push the approved release tag and watch the correct workflow run.
- [ ] Run the emitted testing-domain smoke command.
- [ ] Record evidence and mark this subtask complete.

### Requirement verification

- Version/tag validation: focused tests plus successful dry run.
- Clean-worktree and existing-tag safety: isolated failure-path tests.
- No-op mode: successful `--dry-run` with no git/GitHub mutation.
- Tag creation: tag and remote-ref inspection after the real run.
- Workflow watching: captured run ID, `gh run watch --exit-status`, and matching
  workflow run URL/SHA.
- GitHub Release reporting: `gh release view` URL output.
- Testing-profile validation: repository variable read-back and successful
  testing-domain smoke.

### Additional implementation verification

- Confirm the release tag and workflow run use the prevalidated release commit
  SHA.
- Confirm script failure leaves enough state to rerun failed publication jobs
  without rebuilding or moving the tag.

## Implementation Notes

- 2026-08-23: Execution approved with release version `0.1.1`; implementation
  started on synchronized `main`.
- 2026-08-23: `release.sh` now verifies profile-specific GitHub variables, the
  OIDC secret, clean synchronized `main`, discovers the tag run by SHA, watches
  the concrete run ID with `--exit-status`, and prints the GitHub Release URL.
- 2026-08-23: Nine focused release/promotion script tests passed.

## Completion Notes

Added during completion on 2026-06-18.

The release orchestration script exists and is documented. A real release/tag flow was intentionally not run after the live installer smoke found a macOS runtime portability issue.
