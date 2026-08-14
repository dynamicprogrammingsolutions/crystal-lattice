# Create the chat transcript navigation baseline specification

Record the shared intended behavior, technical boundaries, existing
requirements, and validation gaps for chat transcript navigation after the
baseline investigation was completed.

## Requirements checklist

- [x] The specification has an honest cross-package owner and preserves
  separate mobile and desktop native implementations.
- [x] Product behavior distinguishes loaded-range navigation from viewport
  navigation.
- [x] Portable frontend behavior defines existing range controls, loaded-edge
  controls, bottom affinity, and overlap preservation.
- [x] The technical contract records server slice semantics, shared
  responsibilities, native responsibilities, and snapshot-relative index
  limitations.
- [x] Stable TNAV requirement IDs distinguish implementation, verification,
  documentation, and evidence state.
- [x] Intended but unreliable viewport preservation is marked in progress and
  unverified rather than presented as validated behavior.
- [x] Future message-index and previous/next user-message navigation remains
  outside the baseline implementation claims.

Parent Task: `tasks/20260813-chat-transcript-navigation/000-main.md`

## Implementation Notes

This tracking file was created after the specification work and commit at the
user's request. The specification was based on implementation, test, prior
task, and repository-policy inspection performed before this task directory
existed.

## Completion Notes

Completed on 2026-08-13.

- Added
  `docs/development/specifications/chat-transcript-navigation/index.md`,
  `product-spec.md`, `frontend-behavior.md`, `technical-spec.md`, and
  `requirements.md`.
- Added the specification to `docs/development/index.md`.
- Recorded TNAV-013 as `In progress` and `Unverified; known nonconforming
  behavior`.
- Validated the authored documentation with local-link inspection and
  `git diff --check`.
- Committed the specification as `ddba399c`:
  `Add chat transcript navigation baseline specification`.
- No implementation or automated test suites were changed or run by this
  completed subtask.