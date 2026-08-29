# Shared markdown display contract

Define the cross-platform preference values and React state boundary consumed
by desktop and mobile without coupling either platform's persistence or
markdown renderer to the other.

## Requirements checklist

### Functional requirements

- [x] One shared contract defines the supported markdown base sizes, the
  15-point default, and `Normal`/`Small` header profiles.
- [x] One pure derivation produces the body and H1–H6 sizes used by both
  applications for every supported preference combination.
- [x] Missing or malformed stored/native values resolve to the documented
  defaults.

### Non-functional requirements

- [x] Types, option metadata, parsing, equality, and size derivation are
  renderer-neutral and covered by deterministic unit tests.
- [x] A focused provider/hook exposes immutable resolved preferences without
  global mutable state.
- [x] The shared package does not own AsyncStorage, `NSUserDefaults`, native
  menu wiring, or application startup timing.

Parent Task: `tasks/20260827-cross-platform-markdown-and-mobile-connections/000-main.md`

## Scope

This subtask owns only the reusable contract and state boundary. Desktop and
mobile persistence, controls, and renderer mapping are owned by their
respective subtasks.

## Execution plan
Status: Approved

Add a small markdown-display preference module to the shared React Native
component package. Export the preference type, supported option arrays,
defaults, normalization helpers, heading-size derivation, provider, and hook
from the package entry point.

Model base sizes as a closed numeric union and headers as
`'normal' | 'small'`. Normalize `unknown` input instead of trusting native or
stored values. Keep heading derivation pure and return a stable value shape
that each renderer can translate to its own style keys.

Add package tests for every accepted value, malformed input, defaults, normal
scaling, small scaling, and provider updates. Run the shared package suite and
affected consumer type checks, and document the exported preference API in
this subtask before marking it complete.

### Implementation decisions and open questions

- The approved sizes are 13/15/17/19 and the Normal 15-point baseline is
  32/24/18/15/15/15.
- Recommended module ownership is
  `@crystal-lattice/frontend-rn-components` because it already owns shared
  theme/context primitives used by both applications.
- The provider receives already-hydrated values and a change callback; it does
  not persist autonomously.
- Fenced-code size is not part of this contract unless requirement question 3
  is answered differently.

### Documentation

- Add a focused shared-package development page for the maintained exported
  provider/derivation API and link it from the shared development index.
- Keep platform persistence and renderer implementation details in the owning
  application development docs.

### Task checklist

- [x] Confirm the approved preference values and heading baseline.
- [x] Add shared types, constants, option metadata, and normalizers.
- [x] Add pure body/heading size derivation.
- [x] Add provider and hook.
- [x] Export the public shared surface.
- [x] Add focused shared-package tests.
- [x] Run shared-package tests and affected consumer type checks.
- [x] Document and index the exported shared preference API.
- [x] Record evidence in implementation/completion notes.

### Requirement verification

- Unit tests enumerate every supported base/header value and malformed input.
- Unit tests assert exact H1–H6 output for both profiles at every base size.
- Provider tests assert initial value, updates, and default fallback.

### Additional implementation verification

- Run `npm --workspace @crystal-lattice/frontend-rn-components test`.
- Run the repository TypeScript checks that consume the new shared exports.

## Implementation Notes

- Added a controlled shared provider rather than platform persistence so
  desktop and mobile remain authoritative for their own lifecycle and storage.
- The first generic `npx tsc` check resolved to npm's placeholder `tsc`
  package. Verification used the installed TypeScript 5.9.3 compiler from the
  mobile workspace against the shared package configuration.

## Completion Notes

- Implemented and exported the approved 13/15/17/19 base sizes,
  Normal/Small header profiles, field-wise normalization, semantic typography
  derivation, and controlled provider/hook.
- Added 28 focused tests covering supported and malformed values plus every
  size/profile derivation. The complete shared suite passed with 35 tests.
- Type checking passed with
  `mobile/crystal-lattice-control-rn/node_modules/.bin/tsc --noEmit -p packages/frontend-rn-components/tsconfig.json`.
- Added and indexed current shared-package development documentation.