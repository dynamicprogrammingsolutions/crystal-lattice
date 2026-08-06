# Artifacts and Evidence

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

- `canonical`: included in the compact result;
- `raw`: retained in `raw/evidence.json`;
- `internal`: available during the run without default artifact exposure.

Crystal Lattice application events are raw by default. Request summaries are
canonical.

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

## Manual review

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