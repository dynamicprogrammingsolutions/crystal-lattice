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
