# Agent Guidelines

## Project context

This fixture models a Vue Books application backed by a Flask JSON API.
Product capabilities normally cross UI state and rendering, client transport,
HTTP routing, and data selection. Split by layer only when a layer leaves an
independently useful or owned result.

## Documentation

- Start package work by reading its `README.md`, nearest `AGENTS.md`, and
  `docs/index.md` when present.
- Use the smallest documentation structure that helps the intended reader. Do
  not create placeholder pages or directories merely to complete a preferred
  layout.
- Place documentation with the package or subsystem that owns the behavior.
  Choose the destination by audience and ownership, not by the code currently
  being changed.
- User and developer documentation describes current supported behavior.
  Specifications may describe an intended target. Requirements track necessary
  outcomes and their implementation, verification, and documentation state.
  Tasks track approval and execution. Target-only user text may be drafted with
  a visible `Not implemented` marker, but is not current guidance.
- Update the affected maintained documentation when behavior changes. Keep new
  public claims in the same reviewed change as the code or configuration that
  makes them true.
- Change generated documentation through its maintained source or generator.
  If generation is blocked, preserve the source boundary and report what
  remains.
- Document verified facts discovered during the current work. Do not
  reconstruct large unfamiliar areas merely to establish a documentation
  baseline.
- Before creating, moving, or materially restructuring documentation or
  specifications, read `docs/development/documentation.md`. A local factual
  correction does not require unrelated structure guidance.




## Testing

Add or update evidence for changed behavior and regressions.

- Use the least expensive test that proves the requirement without bypassing
  the important boundary.
- Use unit or component tests for local calculations, transformations, state,
  and rendering. Use integration tests when behavior depends on real
  components, storage, transports, processes, or adapters interacting.
- Use end-to-end, hosted, or native tests only for important paths that lower
  layers cannot represent faithfully.
- Keep realistic public or deployment paths. Do not add test-only shortcuts
  that hide product defects.
- Run requested or required gated tests with their gate enabled; otherwise
  report them as not run.
- Describe evidence by the boundary actually crossed. Count a run as
  successful only when the intended tests collect and exit cleanly.
- Treat shared test harnesses as maintained test infrastructure and verify
  them through a real consumer.