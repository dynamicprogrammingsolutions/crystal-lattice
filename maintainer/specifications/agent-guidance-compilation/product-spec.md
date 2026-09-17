# Agent guidance source and compilation product specification

## Purpose

Agent guidance currently exists partly as repository files and partly as
Python string replacements used by behavioral tests. Historical candidates
can be reproduced, but they are harder to inspect than ordinary source files,
and unrelated project fixtures receive Crystal Lattice-specific instructions.

The repository needs one understandable source and compilation model for
current guidance, candidate variations, project-specific bases, committed
repository outputs, and pinned evaluation inputs.

## Users

### Maintainers changing guidance

Maintainers need to:

- find the current source of every compiled guidance section;
- review a candidate by reading only the sections it changes;
- render a complete candidate file before running models;
- compare current and candidate files without reconstructing Python
  replacements;
- test uncommitted work by content hash or committed work by Git reference;
- promote an accepted candidate deliberately rather than letting a test write
  repository guidance.

### Evaluation authors

Evaluation authors need to:

- use the current checked-out guidance by default;
- select a candidate directory without changing test code;
- optionally select a Git reference and directory for historical
  reproduction;
- compile the same shared sections into bases appropriate to Eleventy,
  FastAPI, Flask/Vue, Crystal Lattice, or another project;
- preserve exact source and output provenance in cache keys and result
  records;
- distinguish old-context evidence from corrected project-specific evidence.

### Agents and contributors using compiled guidance

Ordinary users should continue reading normal files such as `AGENTS.md` and
`agents/TASKS-v7.md`. They should not need to understand the compiler,
candidate directories, or evaluation snapshots.

## Target experience

Current guidance is assembled from:

1. a current shared-section bundle;
2. a target-specific base file with named slots;
3. target-local sections for project-specific rules.

A candidate extends the current bundle and overrides only named shared
sections. A reviewer sees the candidate manifest and changed Markdown files
without reading test fixtures or generated model records.

The compiler accepts a bundle, target, and optional Git reference. It validates
every slot, produces deterministic Markdown, and records a lock containing
every source hash and compiled-file hash.

Tests default to the current bundle and current checkout. A test invocation may
select a candidate directory and optional Git reference, but no test module is
permanently tied to a candidate or commit.

Crystal Lattice and external project fixtures compile the same portable
requirements and testing sections into different project-specific bases.
Repository maps, package paths, and local commands therefore reach only the
projects to which they apply.

After successful testing and human approval, maintainers copy or merge the
accepted section changes into the current bundle and manually compile the
repository outputs. Compilation never promotes a candidate automatically.

## Goals

- Make current and candidate guidance directly inspectable as Markdown source.
- Separate portable sections from project-specific context.
- Compile root `AGENTS.md`, canonical task guidance, and later guidance files
  through one deterministic mechanism.
- Keep the normal compiled files at their existing repository paths.
- Use simple named slots with no general-purpose template language.
- Make current checkout/current bundle the default test selection.
- Permit explicit candidate-directory and optional Git-reference selection.
- Pin every evaluation to exact input and output hashes.
- Keep candidate source outside test-fixture directories.
- Compile external project fixtures from project-appropriate bases.
- Preserve the September 17 old-context matrix for comparison.
- Rerun the current baseline and latest candidate with corrected project bases.
- Interpret model behavior by model and effort, including the quality of
  passing outputs, rather than only aggregate failure counts.

## Non-goals

- Automatically publishing or promoting a candidate after tests pass.
- Replacing Git history with permanent copies of every candidate.
- Introducing conditionals, arbitrary code execution, or recursive template
  logic into base files.
- Requiring agents applying normal repository guidance to read maintainer
  source manifests.
- Treating a compilation lock as approval evidence.
- Treating the legacy old-context matrix as the corrected portable baseline.
- Assuming one full model matrix provides formal statistical inference across
  all software tasks.