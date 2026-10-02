# Evaluation result packages product specification

## Purpose

Let evaluation maintainers preserve a completed evaluation in one durable,
compact package that is easy to inspect, compare, regenerate, and process
without rerunning models.

## Users

Evaluation authors need to retain the inputs, outputs, assessments, provenance,
and resource information relevant to their suite.

Human reviewers need a concise entry point that leads from aggregate findings
to the exact result material needed to understand them.

Tooling and later analyses need stable machine-readable records rather than
having to rediscover information in temporary run directories.

## Target experience

An evaluation author selects completed runs and supplies suite-specific
records. A collection step creates a committed result package containing the
normalized source material required for later review. A rendering step creates
human-readable and machine-readable views from that committed material.

A reviewer can start at the package index, understand the evaluation and its
limitations, compare runs, and open the relevant inputs, outputs,
assessments, and execution context without extracting values through custom
commands.

Changing the report layout or adding a view from already preserved data does
not invoke a model. When a requested field was not retained but still exists
in local raw records, collection can be repeated before those raw records are
discarded.

## Goals

- Preserve completed evaluations as compact, self-contained result packages.
- Serve both human review and machine processing from one maintained source.
- Regenerate review views deterministically without rerunning model work.
- Accommodate suite-defined stages, outputs, assessments, and relationships.
- Preserve source and generation provenance and identify incomplete records.
- Exclude secrets and unnecessary diagnostic volume.
- Make available usage and estimated cost comparable without treating missing
  data as zero.

## Non-goals

- Changing the `AgentEval.run()` contract or generic run lifecycle.
- Defining sessions, messages, prompts, tool calls, providers, or assessment
  semantics.
- Replacing environment-owned runtime projections or suite-owned result
  interpretation.
- Requiring every evaluation to use the result-package feature.
- Building a hosted result service, database, benchmark, or leaderboard.
- Committing complete temporary workspaces, caches, provider streams, or
  unrestricted raw tool output.
- Inferring missing provider usage or pricing without an approved source.

## Ownership relationships

The generic evaluation kernel persists opaque values and evidence. It does not
define result-package review content.

An environment integration may provide reusable runtime-specific review
projections. The Crystal Lattice integration, for example, may project
delivered instructions, effective configuration, visible session activity,
tool activity, failures, and provider usage.

A suite selects runs and owns the meaning of its stages, targets, outputs,
assessments, scores, and findings.

Result-package support owns only the durable package, regeneration, generic
navigation, provenance, and shared presentation mechanics across those inputs.
