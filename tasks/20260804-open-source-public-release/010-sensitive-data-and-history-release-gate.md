# Clear Sensitive Data And Git History For Publication

Establish evidence that the repository can be exposed publicly without
publishing active credentials, private user content, or unintended runtime data.

## Requirements checklist

- [x] The current tree, all branches, all tags, and reachable Git history are scanned with a dedicated secret scanner.
- [x] Tracked conversations, sessions, logs, configuration examples, workflow artifacts, and generated fixtures are reviewed for private or identifying content.
- [x] The AGI conversation export is confirmed suitable for intentional archival publication or is redacted before archival.
- [x] The tracked `.crystal` runtime session is removed from the current tree without rewriting history.
- [x] Any discovered active or historically exposed credential is reported and revoked or rotated before publication.
- [x] Git history is not rewritten, and historical findings are documented for explicit owner acceptance.
- [x] A fresh clone of the publication candidate has no unintended runtime session or active credential in its checked-out tree.

Parent Task: tasks/20260804-open-source-public-release/000-main.md

## Known findings

- `conversation_ai-agent-architecture_2025-11-16-1202.agi.json` is a tracked
  full conversation export. The owner intends to preserve it under
  `archive/conversations/`.
- `core/python/.crystal/sessions/18a6a2c7-7c00-4c1d-83fd-829ac223af11.json`
  is an unreferenced 47-message runtime session containing native provider
  history. It is not used by a test, example, or document and has not yet been
  approved as intentional public content.
- `.env` and common private-key formats are ignored in the current tree.
- A preliminary pattern scan did not establish an active secret, but no
  dedicated full-history scanner was available during planning.
- Existing GitHub Actions logs and artifacts may become visible after the
  repository becomes public.
- The current checkout contains 78 local branches, 28 remote-tracking branches,
  one release tag, and 12 GitHub pull requests. The GitHub repository contains
  25 workflow runs and 34 workflow artifacts.
- The runtime-session introduction is reachable from nine current remote
  branches, including `origin/main` and `origin/develop`. The owner has decided
  to remove it from the current tree without rewriting those historical refs.
- The historical AGI export is reachable from the release tag and most current
  branch histories. It is intentional public material after review and should
  not trigger history rewriting merely because it is a conversation export.
- Gitleaks and TruffleHog are not currently installed in the development
  environment.

## Resolved requirement decisions

- Decision: Remove the tracked `.crystal` session from the current tree only.
- Decision: Never rewrite Git history for this release.
- Decision: Report historical credential findings and revoke or rotate the
  credentials rather than purging commits.
- Decision: Review GitHub-hosted runs and artifacts for accessible credentials
  and report findings; do not delete hosted records without a separate owner
  decision.
- Decision: Create a backup only immediately before branch cleanup, to protect
  against accidental branch deletion.

## Execution plan
Status: Approved

### Phase 1: Define the publication ref set

1. Pause merges, direct pushes, releases, and deployment-triggering changes for
   the duration of the final scan and any approved branch cleanup.
2. Fetch and prune all origin branches and tags.
3. Record:
   - local branches;
   - remote branches;
   - tags;
   - open, merged, and closed pull requests;
   - pull-request head refs;
   - workflow runs, artifacts, and releases.
4. Fetch GitHub pull-request head refs into a temporary local namespace so
   abandoned or closed pull-request content is included in the scan.
5. Do not create a backup as a general scan prerequisite.

The publication ref set is every remote branch, tag, and GitHub pull-request
head that will remain accessible after the repository becomes public. Local-only
branches are scanned as an additional precaution but do not need to be pushed
unless the owner intends to preserve them remotely.

If stale remote branches will be deleted before publication, create and verify a
Git bundle immediately before branch cleanup. The bundle exists only to recover
from accidental branch deletion.

### Phase 2: Install pinned temporary audit tools

1. Use official releases or official container images for Gitleaks and
   TruffleHog.
2. Pin the selected tool versions and record checksums or container digests.
3. Install tools outside the repository or run them through temporary
   containers.
4. Do not install or use `git-filter-repo`.
5. Record tool versions and commands in Implementation Notes, but keep reports
   in an ignored temporary audit directory.

### Phase 3: Scan current files and complete Git history

Run two independent scanning layers against the fetched local repository:

1. Gitleaks over all refs and complete Git history.
2. TruffleHog over the fetched local Git repository, retaining verified and
   unverified findings for triage.

Add targeted checks for:

- private keys, certificates, mobile provisioning files, cloud credentials, API
  keys, access/refresh tokens, passwords, and authorization headers;
- `.env` files and historical configuration files;
- absolute user home paths, personal email addresses, hostnames, IP addresses,
  and account identifiers;
- runtime sessions, exported conversations, logs, profiles, database files,
  generated cloud state, and archived workflow output;
- release assets and GitHub Actions artifacts.

Scanner output must identify file, commit/ref, rule, and remediation status
without copying secret values into task files, commits, or chat.

### Phase 4: Triage findings and review intentional content

Classify every finding as one of:

- active credential or secret;
- expired/revoked credential that is still unsuitable for publication;
- private or identifying content;
- intentional public example/fixture;
- synthetic placeholder;
- scanner false positive.

For the AGI export:

1. Run both scanners against its current and historical blobs.
2. Review its full content manually for credentials, private customer data,
   private infrastructure, personal correspondence, or material not approved
   for publication.
3. Redact it before archival if necessary.
4. Record owner confirmation that the reviewed form is intentional public
   historical content.
5. Leave the actual move to `archive/conversations/` to task `050`.

For the `.crystal` runtime session:

1. Review the current and historical blob.
2. Confirm that no test, example, or document depends on it.
3. Delete it from the current tree with a normal commit.
4. Leave the historical commits unchanged.

### Phase 5: Remediate without rewriting history

For any current or historical credential:

1. Report its provider/type, affected path and refs, and whether it appears
   active, without copying the credential value into task files or chat.
2. Revoke or rotate it before publication.
3. Review provider access logs and scope for possible misuse.
4. Replace repository/workflow configuration with a safe secret reference.

Do not rewrite, filter, replace, or force-push Git history. Historical findings
remain visible in history and are handled through revocation, documentation,
and explicit owner acceptance.

If non-credential private data is discovered in retained history, report it as a
publication blocker or risk for owner decision. This task does not rewrite the
history to remove it.

For branch cleanup:

1. Prepare a proposed stale remote-branch deletion list.
2. Obtain explicit owner approval for that list.
3. Immediately before deletion, create a Git bundle containing all branches and
   tags and verify the bundle.
4. Delete only the approved remote branches.
5. Confirm retained branches and tags still resolve to their original commit
   IDs.

Task `050` will move the approved AGI export with a normal commit.

### Phase 6: Review GitHub-hosted output

1. Inspect metadata and, where necessary, downloadable content for all 25
   workflow runs and 34 current artifacts.
2. Review release assets and release notes.
3. Report any accessible credential or unapproved sensitive output without
   automatically deleting a run or artifact.
4. Revoke or rotate any credential found in accessible hosted output.
5. Confirm deployment logs do not reveal reusable AWS, provider, signing, or
   application credentials.
6. Record any infrastructure identifiers that are intentionally public.
7. Leave deletion of a hosted run, artifact, or release asset to a separate
   explicit owner decision.

### Phase 7: Verify the publication candidate

1. Clone the final GitHub candidate into a clean temporary directory.
2. Fetch all publication branches, tags, and pull-request refs.
3. Repeat Gitleaks, TruffleHog, and targeted path/content checks.
4. Verify the `.crystal` runtime session is absent from the checked-out current
   tree while acknowledging that its historical blob remains reachable.
5. Verify the approved AGI export remains available for task `050`.
6. Confirm `.gitignore` covers runtime sessions, logs, local profiles, scanner
   output, backup bundles, and temporary audit directories.
7. Produce a concise evidence summary and request owner signoff.

### Implementation decisions and open questions

- The AGI export is not removed solely because it is a conversation; it is
  intentional historical content after review.
- Archive relocation does not sanitize Git history.
- Git history is never rewritten as part of this task.
- The `.crystal` session is removed only from the current tree.
- Historical credentials are reported and revoked or rotated.
- Scanner output remains local, ignored, and outside committed repository
  content.
- A backup is created only immediately before approved branch cleanup.
- GitHub-hosted findings are reported; hosted deletion requires separate owner
  approval.

### Documentation

- Record scanner commands, pinned versions/digests, date, references scanned,
  finding classifications, and remediation without recording secret values.
- Add any new local/runtime artifact patterns to `.gitignore`.
- Record revoked credential identifiers by provider and purpose, never by
  secret value.
- Record the AGI publication approval and current-tree `.crystal` removal.
- Record the branch backup path, checksum, and approved deletion list if branch
  cleanup occurs.

### Task checklist

- [x] Freeze publication refs and record the publication ref inventory.
- [x] Inventory branches, tags, pull-request refs, runs, artifacts, and releases.
- [x] Install pinned temporary Gitleaks and TruffleHog tooling.
- [x] Run both scanners over the complete publication history.
- [x] Complete targeted credential, PII, runtime-data, and artifact checks.
- [x] Review and approve/redact the AGI export.
- [x] Remove the `.crystal` session from the current tree.
- [x] Report and revoke or rotate any discovered credentials.
- [x] Review and report GitHub Actions run/artifact and release-asset findings.
- [x] If branch cleanup is approved, create a verified backup immediately before it.
- [x] If branch cleanup is approved, delete only owner-approved stale remote branches.
- [x] Repeat scans against a clean clone of the final candidate.
- [x] Record owner signoff and unblock task `020`.

### Requirement verification

- Scanner reports cover all publication branches, tags, and pull-request refs
  and report no unresolved active credentials.
- Human confirmation records that the archived AGI content is intentionally
  public.
- The `.crystal` session is absent from the runtime-data path at publication.
- Historical findings, including the retained `.crystal` blob, are documented
  and explicitly accepted.
- GitHub Actions artifacts and release assets have no unresolved active
  credential; any finding is reported and revoked.
- A fresh clone and repeated scans confirm all required remediation.

### Additional implementation verification

- Verify the release tag and intended release assets remain usable.
- If branch cleanup occurs, verify retained ref commit IDs are unchanged and the
  backup bundle can list and restore deleted branch tips.
- Verify origin branch count matches the approved post-cleanup inventory.
- Verify no scanner output, branch-backup bundle, or credential value is staged.

## Implementation Notes

### Audit execution on August 4, 2026

- The ref inventory covered 78 local branches, 29 remote-tracking branches
  after refresh, one release tag, and all 12 GitHub pull-request head refs.
- GitHub-hosted inventory covered 25 workflow runs, 34 workflow artifacts, and
  one release.
- Temporary audit data was stored under a permission-restricted `/tmp`
  directory and was not staged.
- Scanner binaries were downloaded from official releases and verified against
  published SHA-256 checksums:
  - Gitleaks `8.30.1`
  - TruffleHog `3.96.0`
- Temporary pull-request refs were deleted after scanning.
- Raw TruffleHog output and extracted conversation/session string reports were
  deleted after redacted triage because they could repeat historical token
  material.

### Scanner results

- Gitleaks reported three historical findings:
  - one generic API-key rule match in
    `packages/frontend-sdk/src/notifications/notificationDismissalCache.ts`;
  - two JWT findings in the historical
    `application/python/agent_terminal_app/default_config/auth/chatgpt-auth.json`.
- The notification cache finding is a false positive for the literal storage
  key `clc_notification_dismissals_v1`.
- TruffleHog independently reported the two historical JWTs as unverified and
  reported no verified credentials.
- The historical auth file also contains a refresh token, account/session
  identifiers, and a local credentials path. The access token expired on
  April 22, 2026, and the ID token expired on April 12, 2026. Refresh-token
  revocation remains a manual blocker.
- The final working-tree snapshot reported only the documented cache-key false
  positive in Gitleaks and zero TruffleHog findings.

### Known artifact review

- The AGI export reported no scanner finding, email address, absolute user home
  path, access/refresh token, password, secret, or private key.
- Its `api_key`, `Authorization`, and `Bearer` strings are architectural example
  text using public API hosts, localhost, and `0.0.0.0`.
- The owner had already decided to preserve the AGI export, and the reviewed
  content is approved for normal archival movement in task `050`.
- The `.crystal` file is an unrelated 47-message runtime conversation. It
  reported no credential finding but has been removed from the current working
  tree without rewriting its historical commit.
- `.gitignore` now excludes `**/.crystal/sessions/*.json`.

### Current-tree privacy and portability cleanup

- Removed the tracked mobile `.xcode.env.local` containing a personal NVM path
  and added an ignore rule preventing it from being recommitted.
- Replaced the desktop Xcode hardcoded personal Node path with portable `node`
  lookup.
- Removed hardcoded personal Apple Development signing identities and the old
  team identifier from the desktop Xcode project.
- Made the active evaluation launcher derive the repository root dynamically.
- Sixty-five tracked files still contain the development username in historical
  task prose, compatibility fixtures, and stored evaluation snapshots/reports.
  These are not credentials; they remain for explicit owner acceptance and
  possible later cleanup.
- Git commit metadata contains two real contributor email addresses. These
  remain in history under the no-rewrite decision and require owner acceptance.

### GitHub-hosted output review

- Twenty-three workflow-log archives were accessible and two were expired.
- Both scanners reported zero findings across all 118 extracted accessible log
  files.
- Thirty artifacts remain accessible and four are expired. All accessible
  artifacts are CLI build archives from nine source commits whose checked-out
  trees exclude the historical auth file.
- The release tag and its four release archives are also based on a tree that
  excludes the auth file.
- No branch cleanup was approved or performed, so no branch-deletion backup was
  created.

### Resolved manual gates

- On August 4, 2026, the owner confirmed that all ChatGPT sessions had been
  logged out, revoking the historically exposed refresh-token session.
- The owner explicitly accepted publication of:
  - the expired and revoked auth material and account/session identifiers
    retained in Git history;
  - two contributor email addresses in Git commit metadata;
  - the remaining development-username paths in tasks, fixtures, and evaluation
    snapshots.
- A clean clone was created from temporary candidate
  `896070443e56ab69f57ff04555c971a21b313956`, including all 12 GitHub
  pull-request refs.
- Final clean-clone history results matched the accepted baseline:
  - three Gitleaks findings: the documented cache-key false positive and two
    expired historical JWTs;
  - two unverified TruffleHog JWT findings;
  - zero verified credentials.
- Final checked-out-tree results contained only the documented Gitleaks
  cache-key false positive and zero TruffleHog findings.

## Completion Notes

Task `010` completed on August 4, 2026.

The repository's current publication candidate contains no known active
credential or unintended runtime session. The tracked `.crystal` session,
machine-local mobile Xcode environment file, desktop personal signing identity,
desktop hardcoded Node path, and active evaluation launcher path were cleaned
from the current tree. Preventive ignore rules were added for runtime session
JSON and mobile `.xcode.env.local`.

Complete-history scanning intentionally retains the previously committed
ChatGPT auth file under the approved no-rewrite policy. Its access and ID tokens
are expired, the associated ChatGPT sessions were revoked, TruffleHog verified
no active credential, and the owner accepted the historical account/session
identifiers, contributor emails, and development-path metadata.

The AGI conversation export passed scanner and manual review and remains
approved for normal movement to `archive/conversations/` in task `050`.

GitHub-hosted workflow logs produced zero findings. Accessible CLI artifacts and
the release were traced to source trees that exclude the auth file. No GitHub
run, artifact, release, branch, or tag was deleted.

Plan deviations:

- No branch cleanup was requested, so no branch-deletion backup was created.
- Accessible CLI artifacts were not bulk-downloaded because their source
  commits excluded the credential file and all corresponding accessible
  workflow logs were scanner-clean.
- Git history was not rewritten, as explicitly required by the owner.

Deferred findings:

- Historical and current task/fixture/evaluation files still contain accepted
  development-username paths and may be normalized during later repository
  information-architecture work.
- The harmless notification dismissal storage key remains a documented
  Gitleaks false positive.
