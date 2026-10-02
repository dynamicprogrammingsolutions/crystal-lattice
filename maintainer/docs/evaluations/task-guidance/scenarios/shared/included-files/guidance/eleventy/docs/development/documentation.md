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
