# Documentation and specification guidance product specification

## Purpose

Provide concise, project-independent guidance that helps people and agents
choose, write, place, and maintain documentation, specifications,
requirements, and testing strategies without forcing unnecessary files or
project-specific terminology.

## Users

Package users need readable first-use and reference material. Contributors and
agents need practical guidance for current developer documentation,
specification targets, requirement restraint, and proportionate verification.
Maintainers need portable source that can be compiled or adopted by several
repositories without carrying one repository's paths or workflow.

## Target experience

A reader begins with the smallest useful structure: a README, one focused page,
an index plus focused pages, or a larger specification set only when the work
benefits from that separation.

The guidance introduces each document role before placement and workflow rules
use it. User and developer documentation describes current supported behavior.
Specifications describe intended targets. Requirements track necessary
approved outcomes and their implementation, verification, and documentation
state. Tasks track approval and execution.

Requirements remain minimal and traceable. They do not absorb implementation
steps, test cases, documentation work, possible improvements, or unapproved
public choices. Testing guidance selects the least expensive reliable boundary,
retains important real crossings, and avoids duplicated, combinatorial, or
implementation-coupled checks.

Portable repository-guidance sections reinforce only the concise rules that
benefit ordinary work. Their source format does not claim an instruction
priority; the consuming runtime documents how the compiled file is delivered.

## Goals

- Define optional documentation structures adaptable to task and package size.
- Explain practical content for README, AGENTS, indexes, quickstarts, user and
  developer pages, specifications, requirements, testing strategies, reference,
  and decision records.
- Place documentation according to behavioral ownership and reader need.
- Keep current documentation distinct from target specifications and work
  tracking.
- Keep requirements necessary, approved, traceable, and proportionately
  grouped.
- Make testing decisive and proportionate at the cheapest reliable boundary.
- Preserve audience, source-of-truth, validation, and generated-output
  boundaries when normal workflows are blocked.
- Provide concise portable Documentation, Requirements, and Testing sections
  without project names or paths.

## Non-goals

- Requiring every illustrated file or directory.
- Requiring a specification for every small change.
- Treating specifications as evidence of implementation.
- Defining one repository's package map, publication system, or runtime
  instruction delivery.
- Maximizing requirement count, test count, or guidance length.
- Publishing maintainer evaluation records as user documentation.

## Acceptance examples

A small package improves one README rather than adding placeholders. A frontend
package may define a substantial package-owned UX specification that refines a
broader contract. A planner records telemetry and hardening ideas as optional
follow-up rather than completion requirements. A test plan uses a real
client/server crossing where mocks would supply the behavior under test, while
keeping local calculations at unit or component level.
