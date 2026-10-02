# Agent guidance compiler product specification

## Purpose

Compile inspectable Markdown section bundles into project-owned target files
with deterministic provenance, without embedding candidate generation or
project-specific policy in evaluation code.

## Users

Guidance maintainers need readable current and candidate source. Project
maintainers need to own their templates and local sections. Evaluation authors
need exact source and output hashes and the ability to select current,
candidate, or historical source by path.

## Target experience

A bundle maps stable section names to Markdown files. A target maps output files
to templates and resolves each named slot from the bundle or target-local
source. Compilation validates the mapping, renders deterministic bytes, and
returns a lock describing every input and output.

`check` compares compiled output with an existing destination. `compile` writes
a preview. `write` updates approved destination files. None of these operations
promotes a candidate into the current bundle.

## Goals

- Keep source and candidates directly inspectable.
- Keep project templates and local sections with their owning project.
- Use simple named slots without a general template language.
- Support bundle and target paths in different repositories.
- Produce location-independent compilation identity from content.
- Preserve optional independent Git provenance for bundle and target.
- Make historical source selectable through a checkout or worktree.
- Keep promotion explicit and human-approved.

## Non-goals

- Defining Documentation, Requirements, Testing, or task-guidance semantics.
- Assigning instruction priority to compiled files.
- Storing real consuming-project templates in the compiler repository.
- Automatically promoting candidates after tests pass.
- Providing conditionals, recursive includes, or arbitrary template code.
