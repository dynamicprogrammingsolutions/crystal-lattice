# Evaluation result packages technical specification

## Architecture

Result-package support is an optional consumer of completed evaluations:

```text
completed runs and saved suite records
             │
             ├── environment-owned review projections
             └── suite-owned selection and stage mapping
                              │
                              ▼
                       collection step
                              │
                              ▼
                   committed result package
                              │
                              ▼
                       rendering and checks
```

It does not participate in `AgentEval.run()` and does not extend
`RunEnvironment`.

## Responsibility boundaries

The reusable result-package component owns:

- package identity and source provenance;
- references among included runs and records;
- deterministic collection and rendering;
- generic human and machine navigation;
- safe file generation and redaction hooks;
- availability and reconstruction metadata supplied by an owner;
- configured usage/cost presentation from supplied normalized usage.

It treats environment and suite records as opaque named values. It does not
define a session, message, request, tool, provider, task, assessment, or score
schema.

An environment integration owns runtime-specific extraction and
normalization. A suite owns record selection, stage relationships, primary
outputs, assessment meaning, and report interpretation.

## Package source and generated views

Collection produces committed source records sufficient for later rendering.
These records identify:

- the evaluation and generator version;
- selected and related run identities;
- source hashes and availability;
- suite-defined stages and relationships;
- environment and suite records included by their owners;
- generated-file identities and hashes;
- the report configuration used.

Human-readable pages, tables, and machine comparison views are generated from
those committed records. Generated views are not independent sources of truth.

Collected source records may themselves be human-readable — for example a
concise full-session transcript or a readable rendering of assessment
results. Such records are sources of truth for later rendering, not
generated views: the deterministic-regeneration guarantee applies to the
generated views, while collected records are preserved as committed
history.

The exact directory and file names are repository decisions. The structure
must keep the package understandable without temporary run directories and
must make generated files distinguishable from collected source records.

## Collection and rendering

Collection may read:

- completed generic run directories;
- environment-owned review projections;
- suite records and generated files;
- assessor records;
- a report configuration;
- an explicitly selected price table.

Collection does not invoke producer or assessment models.

Rendering reads only committed package records and report configuration. It
may be repeated after changing layout, navigation, or included views. A check
mode compares expected generated content with the maintained package.

If later presentation needs information not present in the package, collection
may be repeated from still-available raw records. The package records the
source and generator revisions used for that update.

## Runtime-specific review data

Result-package support does not normalize sessions or provider data itself.
It accepts review data supplied by an environment integration and preserves
the owner's declared availability and provenance.

For Crystal Lattice evaluations, the
[Crystal Lattice environment specification](../crystal-lattice-environment/index.md)
owns the reusable representation of delivered instructions, effective
configuration, visible conversation, tool activity, failures, and provider
usage.

## Suite adapters

A suite adapter supplies:

- the runs and records included in one evaluation;
- stable suite identities and labels;
- stage or phase relationships;
- primary generated outputs;
- assessments and their subjects;
- aggregate findings and navigation;
- any suite-specific validation required before publication.

The adapter may preserve task files, plans, code changes, screenshots,
benchmark measurements, or other suite-defined outputs. None become required
concepts in the reusable package component.

## Usage and estimated cost

Environment or suite records supply aggregate usage for one run. The report
configuration supplies one price table and provenance. Result-package support
may calculate and present one estimated cost for each run and known totals
across the evaluation.

Provider-reported or provider-estimated cached input is retained as supplied.
Unavailable token categories or prices remain unavailable. Historical reports
do not silently change when a different repository price table is introduced.

The initial Crystal Lattice integration uses run-level summaries. It does not
publish request-level cost tables or separate model/provider rollups.

## Safety and proportionality

Collection and rendering must:

- redact credentials, authorization values, and secret environment data;
- avoid committing encrypted reasoning or unrestricted tool results;
- avoid duplicate native and normalized copies when one review form is enough;
- retain concise errors and execution context needed for diagnosis;
- record omitted or unavailable information honestly;
- keep detailed local diagnostics outside the committed package unless a
  reviewed evaluation needs them.

Machine-specific paths may be normalized when the package preserves enough
provenance to distinguish normalized content from an exact original.

## Historical migration

Historical data may be collected from saved runs without model calls.
Directly captured values remain distinguished from deterministic
reconstructions. A reconstruction is verified only when it matches an
independently recorded hash or equivalent identity.

Migration must prove that selected runs, primary outputs, and assessment
results agree with the previously maintained records before old copies are
removed.
