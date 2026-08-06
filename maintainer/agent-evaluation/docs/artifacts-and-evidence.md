# Artifacts and Evidence

## What evidence means

Evidence is a named observation recorded while an evaluation runs. It is the
structured material from which assertions, summaries, assessments, and review
artifacts can be produced.

Examples include:

- the exact user prompt;
- an instruction-file hash;
- a final assistant response;
- one application or tool event;
- changed file paths;
- a request summary;
- an error;
- a deterministic assertion result;
- a score returned by another model.

Evidence is not automatically proof that behavior is correct. It records what
happened or what one evaluator concluded. Pytest assertions and human
confirmation decide whether that evidence satisfies a requirement.

## How evidence fits into a run

```text
environment and program activity
            │
            ▼
      EvidenceJournal
       ├── canonical items ──▶ result.md / result.json
       ├── raw items ────────▶ raw/evidence.json
       └── explicit selection
                    │
                    ▼
                projection
             ├── deterministic assertion input
             ├── AI assessment input
             └── manual-review presentation
```

The evidence journal is run-local and append-only. The kernel records generic
lifecycle facts. Environments record runtime-specific observations. Programs
can add domain-specific facts through `context.services.record(...)`.

An artifact is a file saved for later inspection. Evidence may appear inside an
artifact, but the terms are not interchangeable: evidence is structured
run-time information; an artifact is a persisted representation such as
Markdown, JSON, a diff, or a serialized session.

## Artifact layout

Every invocation writes:

```text
<artifact-root>/runs/<run-id>/
├── result.md
├── result.json
├── records/
└── raw/
    ├── environment/
    ├── errors/
    ├── evidence.json
    └── workspace/
```

`result.md` and `result.json` are the routine review surface. They contain:

- run, parent, cache, environment, and workspace identity;
- program return value;
- normalized environment observation;
- changed paths;
- error phase and message;
- canonical evidence.

Large JSON values are truncated in Markdown but remain available in JSON or
raw artifacts.

## Evidence journal

Each evidence item has:

- a `kind`, which is its stable name;
- a `value`;
- a `source`;
- optional metadata;
- a timestamp;
- a visibility classification.

```python
context.services.record(
    "instruction.hash",
    instruction_hash,
)

selected = context.evidence.project(
    "ai-input",
    using=lambda evidence: {
        "response": evidence.require("response.final"),
        "changed_files": evidence.values("workspace.changed_file"),
    },
)
```

Evidence visibility can be:

- `canonical`: useful enough for routine review, so it is included in the
  compact result;
- `raw`: useful for diagnosis or later projection, but too detailed for the
  routine result, so it is retained in `raw/evidence.json`;
- `internal`: useful only while the program is running and omitted from the
  default persisted evidence views.

Crystal Lattice application events are raw by default. Request summaries are
canonical. This keeps the normal result readable without discarding event-level
diagnostics.

## Projections

A projection selects or transforms evidence for one specific consumer. It
prevents every assertion, model, and reviewer from receiving the entire
journal.

For example, a documentation assessment may need the instruction hash, user
prompt, final response, and changed Markdown, but not streaming chunks,
session-lock events, or provider-internal metadata.

## AI assessment input

Do not send the complete event journal or raw artifact directory to an
assessment model by default.

Create an explicit projection containing only:

- exact candidate instructions or their verified hash;
- relevant user request;
- final response;
- changed paths and primary changed content;
- concise tool/error summary;
- requirement identifiers being assessed.

Record the projection separately from the assessment output.

An assessment output is new evidence. It should identify which projection was
assessed and should not be confused with the underlying agent response.

## Manual review

Presentation is the final formatting step for an audience. It may combine
selected evidence, deterministic results, and assessment findings into a small
Markdown or JSON file.

Manual review usually needs a different presentation:

- visible prompt and response;
- primary changed files;
- deterministic assertion results;
- score or findings summary;
- focused review questions;
- links to raw diagnostics when needed.

Use `context.present()` or `Run.record()` to write a compact review artifact.

## Failures

Runtime failures preserve:

- failure phase;
- exception type and message;
- traceback under `raw/errors/`;
- safe snapshot/finalization evidence collected after the failure;
- workspace changes made before failure.

`run.raise_for_error()` raises `RunFailedError` carrying the complete `Run`.

Pytest assertion failures happen after `run()` returns, so the run artifacts
already exist.

## Sensitive data

JSON rendering redacts mapping keys that look like:

- authentication values;
- credentials;
- passwords;
- secrets;
- tokens;
- API keys.

Environment fingerprints hash configuration-environment values rather than
rendering them.

Raw artifact writers cannot infer whether arbitrary bytes contain credentials.
Programs and environment integrations must not copy authentication state or
credential files into artifacts. Use ignored local artifact roots and apply
additional retention controls for sensitive evaluations.