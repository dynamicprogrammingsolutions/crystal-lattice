# Subtask: Write `plugins/docs/provider-plugins.md` (canonical provider plugin doc)

Parent Task: tasks/20260303-provider-plugin-docs/000-main.md

## Description

Create a new canonical documentation page for developing provider plugins:

- Location: `plugins/docs/provider-plugins.md`
- Link from: `plugins/docs/index.md`

This doc replaces the existing provider guidance in `docs/plugins/development.md` and other scattered references. It should be runtime-accurate and reference current code/docstrings by file path (URLs can be added later).

## Goals

- Provide a single, complete, current guide for authoring provider plugins.
- Include two quickstarts (non-streaming + streaming), each including:
  - a step for creating a plugin package (using the new provider template)
  - a step for running tests (tests live inside the template/package)
- Include a verbose “Complete guide” for building a full provider, with cross-links to deep dives.
- Include deep-dive sections for special cases (native history retention, streaming patterns, tools/reasoning/multipart, etc.).

## Planned doc structure

1. Title + scope
2. Audience/prereqs
3. Concepts/vocabulary
4. Quickstart A: Non-streaming provider (package + tests)
5. Quickstart B: Streaming provider (package + tests)
6. Complete guide: build a full provider step-by-step (includes package creation + tests)
7. Runtime request flows (non-streaming and streaming)
8. ProviderPlugin method reference (method-by-method)
9. Deep dives:
   - state patterns
   - native history retention
   - streaming recipes
   - interop: extensions/features/tools (incl reasoning and multipart)
   - testing
   - packaging/loading
   - troubleshooting
10. Reference implementations (code pointers)

## Success criteria

- `plugins/docs/provider-plugins.md` exists.
- `plugins/docs/index.md` exists and links to `provider-plugins.md`.
- Doc references the new template `plugins/template-python-provider` for package creation.
- Quickstarts and Complete Guide both instruct how to run tests from the package.

---

## Completion notes (added 2026-03-03)

Created a new docs directory and provider plugin guide:

- `plugins/docs/index.md`
- `plugins/docs/provider-plugins.md`

Also added shared docs under `plugins/docs/` for long sections that are common across plugin kinds:

- `plugins/docs/plugin-packaging-and-loading.md`
- `plugins/docs/plugin-execution-order.md`
- `plugins/docs/ui-elements.md`
- `plugins/docs/testing-and-validation.md`

### Key doc properties

- Provider guide is written as a natural, first-time-reader document (no internal review/process wording).
- Includes code examples throughout (message shapes, provider skeletons, streaming patterns, tests, logging).
- Recommends automated tests as the primary development loop, and includes a section showing how to try a provider in the terminal app via real JSON config.
- Explains both streaming implementation paths:
  - accumulator pattern (`extract_delta`/`process_delta` + shared `process_chunk`/`finalize`)
  - custom `process_chunk`/`finalize` for cases where the accumulator pattern isn't a fit

### Where to look

- Provider guide: `plugins/docs/provider-plugins.md`
- Packaging/loading: `plugins/docs/plugin-packaging-and-loading.md`
- Execution order: `plugins/docs/plugin-execution-order.md`
