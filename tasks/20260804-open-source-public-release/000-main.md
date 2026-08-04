# Publish Crystal Lattice As An Open Source Repository

Prepare the existing private Crystal Lattice repository for a lean, controlled
public release, then improve the public project incrementally with feedback from
known developers and early adopters.

## Requirements checklist

- [ ] The repository is not made public until every mandatory pre-publication subtask passes its release gate.
- [ ] The current tree and reachable Git history contain no known active secrets, private user data, or unintentionally published runtime sessions.
- [ ] Claude Tools and its normalized fixtures are consistently licensed under Apache-2.0 with accurate public-behavior provenance and no claim that Anthropic's license applies merely because Claude Code was observed.
- [ ] A new contributor can understand the project, report a security issue privately, request support, and open a useful issue without internal guidance.
- [ ] Public pull requests cannot access deployment credentials, and repository automation uses least-privilege permissions suitable for untrusted contributors.
- [ ] The historical AGI conversation export is preserved under the repository archive, obvious temporary root files are removed, and `agents/` and `test_dir/` remain intact.
- [ ] The repository can be changed to public visibility with protected `main`, safe Actions settings, security reporting, and dependency/secret alerts.
- [ ] An anonymous user can clone the repository, find the license and support path, open an issue, and run the documented primary validation path.
- [ ] Non-blocking cleanup and governance improvements remain tracked as post-publication work rather than expanding the initial release gate.

## Scope and release stages

### Do now: mandatory before or immediately around publication

- Sensitive-data and full-history release gate.
- Claude Tools Apache-2.0 restoration and provenance cleanup.
- Minimum public documentation, support, security reporting, and issue intake.
- Minimum pull-request CI and GitHub Actions permission hardening.
- Lean root cleanup, including archival of the AGI export and deletion of obvious temporary files.
- Formal publication readiness review.
- Manual GitHub visibility/security settings.
- Immediate post-publication validation.

### Do later: explicitly non-blocking for the first public release

- Expanded governance, code of conduct, DCO/CLA automation, and maintainer policy.
- Repository-wide package metadata and license classifier normalization.
- Broader CI matrices, CodeQL, Dependabot version updates, and additional supply-chain automation.
- Deeper reorganization of historical plans and root documentation.

The initial audience is expected to be friends, known developers, and early
adopters. The release gate therefore stays intentionally lean while retaining
all controls needed to prevent security incidents, legal confusion, unexpected
cloud cost, or a major obstacle to understanding the repository.

## Decisions

- Decision: Original Crystal Lattice implementation and AI-generated normalized
  Claude behavior fixtures are intended to be Apache-2.0 licensed.
- Decision: Observing publicly visible Claude Code behavior does not by itself
  make Anthropic's license apply to the resulting normalized fixtures or
  independently authored implementation.
- Decision: The AGI conversation export is intentional historical material and
  should be moved to `archive/conversations/`, subject to the mandatory
  sensitive-data review.
- Decision: `agents/` and `test_dir/` stay intact.
- Decision: Clearly temporary files such as `poem.txt` may be deleted.
- Decision: Dynamic Programming Solutions Kft. has confirmed that the existing
  contributions are approved for publication.
- Decision: Large governance and repository-organization changes should follow
  early-adopter feedback instead of blocking the initial public release.

## Requirement question

- What is the intended disposition of
  `core/python/.crystal/sessions/18a6a2c7-7c00-4c1d-83fd-829ac223af11.json`?
  It must be reviewed before publication. If it is an intentional reusable test
  fixture, it should be sanitized, renamed, and moved to a fixture directory.
  Otherwise it should be removed, with history rewriting only if private or
  secret material is discovered.

## Supporting findings

- The GitHub repository is currently private, with `main` as the default branch
  and Issues enabled.
- No branch protection or repository ruleset is currently active.
- GitHub Actions currently defaults to write permission and may approve pull
  requests.
- Dependabot alerts, secret scanning, and code scanning are currently disabled.
- Existing workflows can deploy static sites and publish CLI releases.
- The root `LICENSE`, `LICENSING.md`, and `NOTICE` establish an Apache-2.0
  foundation, but Claude Tools currently contains mixed and ambiguous licensing
  statements.
- The repository lacks root contribution, support, and security-reporting
  guidance.
- The tracked AGI export and Crystal runtime session contain full message/session
  structures and therefore require intentional publication review.

## Subtasks

### Mandatory release path

- [ ] `tasks/20260804-open-source-public-release/010-sensitive-data-and-history-release-gate.md`
- [ ] `tasks/20260804-open-source-public-release/020-claude-tools-license-and-provenance-restoration.md`
- [ ] `tasks/20260804-open-source-public-release/030-minimum-public-documentation-and-support.md`
- [ ] `tasks/20260804-open-source-public-release/040-minimum-ci-and-automation-hardening.md`
- [ ] `tasks/20260804-open-source-public-release/050-lean-root-cleanup-and-archive.md`
- [ ] `tasks/20260804-open-source-public-release/060-publication-readiness-gate.md`
- [ ] `tasks/20260804-open-source-public-release/070-github-visibility-and-security-settings.md`
- [ ] `tasks/20260804-open-source-public-release/080-post-publication-validation-and-early-adopter-intake.md`

### Post-publication improvement path

- [ ] `tasks/20260804-open-source-public-release/110-expanded-community-governance.md`
- [ ] `tasks/20260804-open-source-public-release/120-package-metadata-and-license-consistency.md`
- [ ] `tasks/20260804-open-source-public-release/130-expanded-ci-and-dependency-security.md`
- [ ] `tasks/20260804-open-source-public-release/140-follow-up-repository-information-architecture.md`

## Execution plan
Status: Draft

Execute the mandatory path in numerical order. Tasks `010` through `050` can
progress independently where they do not overlap, but `060` is the single
pre-publication go/no-go review. Task `070` is the manual GitHub visibility
transition and its immediately adjacent settings. Task `080` must be completed
before the initial publication is considered successful.

Do not begin post-publication tasks merely because the repository has become
public. Reassess them after the first round of early-adopter feedback and
prioritize actual confusion, contribution friction, security alerts, or
operational cost over speculative polish.

### Implementation decisions and open questions

- Use `archive/conversations/` for the AGI export.
- Use an `archive/README.md` index if the archive is created.
- Do not move `agents/` or `test_dir/`.
- History rewriting is conditional on finding actual secrets, private data, or
  material that the company does not intend to publish.
- Resolve the tracked `.crystal` session disposition during task `010`.

### Documentation

- Mandatory documentation is limited to README clarity, contribution guidance,
  support guidance, security reporting, and issue intake.
- Expanded governance and repository-wide documentation restructuring are
  deferred.

### Task checklist

- [ ] Complete mandatory subtasks `010` through `050`.
- [ ] Perform the `060` publication readiness review and receive owner approval.
- [ ] Complete the manual visibility/settings procedure in `070`.
- [ ] Complete immediate anonymous/public validation in `080`.
- [ ] Reprioritize `110` through `140` after early-adopter feedback.

### Requirement verification

- Mandatory requirements are mapped to the acceptance evidence in subtasks
  `010` through `080`.
- The main task can be marked complete only when the public repository has
  passed the anonymous-user checks in task `080`.
