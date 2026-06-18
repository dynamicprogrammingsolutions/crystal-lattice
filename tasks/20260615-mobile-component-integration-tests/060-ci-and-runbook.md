# CI And Runbook

Document and wire the new mobile component testing tiers so future tasks know when and how to use them.

## Requirements checklist

- [x] Add or document package scripts for fast component tests and real-backend component integration tests.
- [x] Decide whether the real-backend component integration tier should run in CI by default, nightly, or manually.
- [x] Document how to write a generic component test.
- [x] Document how to write a real-backend component integration test.
- [x] Document common pitfalls around React Native native-module mocks, backend startup, temporary config, and cleanup.
- [x] Update relevant mobile/development docs.

Parent Task: tasks/20260615-mobile-component-integration-tests/000-main.md
Depends On: tasks/20260615-mobile-component-integration-tests/030-generic-component-behavior-tests.md
Depends On: tasks/20260615-mobile-component-integration-tests/050-session-settings-real-backend-example.md

## Suggested Commands

Final command names should be chosen during implementation, but likely examples are:

```bash
cd mobile/crystal-lattice-control-rn
npm test
npm run test:components
npm run test:components:integration
```

If the real-backend tests need a separate Jest config or test path pattern, document it explicitly.

## CI Guidance

Recommended default:

- Fast generic component tests run with normal mobile Jest.
- Real-backend component integration tests run in an explicit CI job or manual workflow until runtime is known to be stable.

The real-backend tier should not require real provider API keys for its default examples. Use deterministic local providers or plugin/application actions that do not call hosted LLM APIs.

## Runbook Content

The docs should explain:

- when to use mocked component tests;
- when to use real-backend component integration tests;
- how to start a real backend in a test;
- how to create a session and pass `RestAgentBackend` into a component;
- how to wait for async UI loading;
- how to assert backend state after UI interaction;
- how to clean up backend processes and temp directories.

## Acceptance Criteria

- Maintainers can run each tier from documented commands.
- Future feature tasks can copy a small template for both test types.
- CI behavior is explicit and does not accidentally make the default mobile test suite slow or flaky.

## Completion Notes

Added during completion on 2026-06-15.

- Added scripts:

```bash
npm test
npm run test:components
npm run test:components:integration
```

- Documented the fast and real-backend test tiers in `mobile/crystal-lattice-control-rn/README.md`.
- Recommended CI behavior remains:
  - Run fast component tests with normal mobile Jest.
  - Run real-backend component integration as an explicit CI job/manual workflow until runtime/cache behavior is stable.
- Noted that first-run real-backend tests can be slower because path plugin dependencies may be installed into a temporary plugin cache.
