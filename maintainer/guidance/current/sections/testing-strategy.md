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