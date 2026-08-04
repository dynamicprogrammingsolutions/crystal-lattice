# Clear Sensitive Data And Git History For Publication

Establish evidence that the repository can be exposed publicly without
publishing active credentials, private user content, or unintended runtime data.

## Requirements checklist

- [ ] The current tree, all branches, all tags, and reachable Git history are scanned with a dedicated secret scanner.
- [ ] Tracked conversations, sessions, logs, configuration examples, workflow artifacts, and generated fixtures are reviewed for private or identifying content.
- [ ] The AGI conversation export is confirmed suitable for intentional archival publication or is redacted before archival.
- [ ] The tracked `.crystal` runtime session is converted into an intentional sanitized fixture or removed.
- [ ] Any discovered active credential is rotated before publication.
- [ ] Any discovered private or secret material is removed from reachable history, not merely deleted in a new commit.
- [ ] A fresh clone of the publication candidate contains none of the prohibited material.

Parent Task: tasks/20260804-open-source-public-release/000-main.md

## Known findings

- `conversation_ai-agent-architecture_2025-11-16-1202.agi.json` is a tracked
  full conversation export. The owner intends to preserve it under
  `archive/conversations/`.
- `core/python/.crystal/sessions/18a6a2c7-7c00-4c1d-83fd-829ac223af11.json`
  is a tracked runtime session and has not yet been approved as intentional
  public content.
- `.env` and common private-key formats are ignored in the current tree.
- A preliminary pattern scan did not establish an active secret, but no
  dedicated full-history scanner was available during planning.
- Existing GitHub Actions logs and artifacts may become visible after the
  repository becomes public.

## Requirement question

- Should the tracked `.crystal` session be retained as a sanitized test fixture,
  or removed? Recommendation: remove it unless a current test or example
  demonstrably depends on its exact content.

## Execution plan
Status: Draft

Create a mirrored backup and record all branches/tags before any history
mutation. Run a dedicated scanner such as Gitleaks and a second independent
scanner or targeted validation over the entire repository history. Review the
two known conversation/session artifacts manually without copying their content
into task files or logs.

Move the approved AGI export through task `050` only after this task confirms it
contains no prohibited content. Resolve the `.crystal` session according to the
owner decision. If actual secrets or private data are found, rotate credentials,
remove the material with `git filter-repo`, force-push affected references, and
require collaborators to reclone. If no prohibited historical content is
found, avoid an unnecessary history rewrite.

Review existing Actions run logs and artifacts for infrastructure details,
tokens, or confidential output. Remove sensitive runs/artifacts before the
visibility change.

### Implementation decisions and open questions

- The AGI export is not removed solely because it is a conversation; it is
  intentional historical content after review.
- Archive relocation does not sanitize Git history.
- History rewriting is evidence-driven and conditional.
- The `.crystal` session disposition remains the only open content decision.

### Documentation

- Record scanner commands, versions, date, references scanned, findings, and
  remediation without recording secret values.
- Add any new local/runtime artifact patterns to `.gitignore`.

### Task checklist

- [ ] Create a mirror backup and reference inventory.
- [ ] Run two current-tree/history scanning approaches.
- [ ] Review the AGI export.
- [ ] Resolve and implement the `.crystal` session disposition.
- [ ] Review GitHub Actions logs and artifacts.
- [ ] Rotate and purge anything discovered.
- [ ] Verify the candidate with a fresh clone and repeat scans.

### Requirement verification

- Scanner reports cover all branches and tags and report no unresolved active
  secrets.
- Human confirmation records that the archived AGI content is intentionally
  public.
- The `.crystal` session is absent from the runtime-data path at publication.
- A fresh clone and path/history checks confirm all required remediation.
