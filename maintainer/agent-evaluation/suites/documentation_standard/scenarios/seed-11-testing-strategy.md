# Seed 11: testing-strategy investigation

## Purpose

Establish the current option-visibility contract and the available local and
cross-layer implementation paths before documentation guidance is added.

## Exact seed prompt

> Please inspect `plugins/ui-options/README.md`,
> `plugins/ui-options/src/options.py`,
> `plugins/ui-options/tests/test_options.py`,
> `plugins/ui-options/docs/development/specifications/option-visibility/index.md`,
> `application/python/example_api/options.py`,
> `packages/frontend-sdk/src/options.ts`, and
> `docs/development/specifications/option-delivery/index.md`. Report the
> contracted behavior, implementation details outside that contract, existing
> test coverage, and the boundaries crossed by option delivery. Do not modify
> files or propose a test plan yet.

## Expected seed result

The response distinguishes observable option visibility and identity from
private metadata, complete mapping shape, key order, and helper calls. It also
identifies the plugin, public endpoint, and production frontend adapter as
separate boundaries. The seed makes no file changes.

## Fixture

Use fixture `testing-strategy`, revision `v1`, branch variant `base`.

## Seed checks

- The named files are inspected.
- Contracted behavior and implementation details are separated.
- Current unit coverage and cross-layer paths are reported.
- No testing strategy is chosen.
- No files change.