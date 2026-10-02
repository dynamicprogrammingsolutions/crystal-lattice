## Testing

Add or update evidence for changed behavior and regressions.

- Map each requirement or coherent group to the smallest reliable evidence at
  the boundary where its failure would be observable.
- Use unit or component tests for local behavior. Use integration tests when
  the requirement depends on real components, storage, transports, processes,
  or adapters interacting. Use end-to-end, hosted, or native tests only for
  important paths lower layers cannot represent faithfully.
- Separate component tests do not prove an interaction requirement. Name at
  least one check through the real connection between those components; when
  that check is unavailable, record the gap instead of substituting mocks.
- A mock that supplies or bypasses the claimed behavior is not decisive
  evidence. Cite existing coverage only when it actually proves the required
  behavior; otherwise add focused evidence or record the gap.
- For bounded inputs, include valid boundaries and representative invalid
  values. For behavior that must remain compatible, identify focused
  regression evidence.
- Do not test unresolved or unapproved behavior. Avoid exact internal values,
  structures, calls, ordering, markup, or source identity unless they are part
  of an approved contract.
- Prefer representative checks over duplicate layers or operation-by-state
  combinations without a distinct risk.
- Separate requirement acceptance from additional implementation robustness
  checks. Keep routine formatting, lint, compilation, and broad test counts as
  supporting evidence.
- Integration and end-to-end tests use realistic public or deployment paths;
  do not add test-only shortcuts that hide a product defect.
- Run requested or required gated tests with their gate enabled. Otherwise
  report them as not run.
- Describe coverage by the boundary it actually crosses. A run succeeds only
  when the intended tests collect and exit cleanly.
- Planning-only work leaves no generated files, caches, or other incidental
  repository changes behind.
- Treat shared test harnesses as maintained test infrastructure and verify
  them through a real consumer.