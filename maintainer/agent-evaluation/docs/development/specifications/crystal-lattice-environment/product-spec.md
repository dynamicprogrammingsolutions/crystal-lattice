# Crystal Lattice evaluation environment product specification

## Purpose

Provide a complete adapter that lets evaluation authors run real Crystal
Lattice applications, providers, plugins, sessions, requests, tool loops, and
continuations through the reusable `agent_eval` kernel.

## Target experience

An author selects ordinary Crystal Lattice configuration, opens a context,
sends messages or custom requests, observes events and workspace changes,
creates compatible snapshots, and records evidence without making Crystal
Lattice behavior mandatory for alternate environments.

## Goals

- Use production `AgentApplication` and `AgentCore` paths.
- Support caller-owned configuration, providers, plugins, skills, and tools.
- Expose replaceable request, observation, snapshot, evaluation, and
  presentation strategies at their point of use.
- Preserve exact runtime and instruction provenance needed by consumers.
- Clean up application and runtime resources deterministically.

## Non-goals

- Defining the generic kernel lifecycle.
- Requiring alternate environments to expose messages, sessions, or tool loops.
- Embedding documentation-guidance scenarios in the adapter contract.
