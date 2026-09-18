# Guidance maintenance workflow

Use this workflow when changing reusable documentation guidance, compiled
repository guidance, task guidance, or their evaluation.

1. Identify the maintained source, intended readers, delivery channels, and
   projects affected by the change.
2. Update the target specification when the intended contract changes, and
   update live requirements without placing result narratives in the
   specification.
3. Compile or assemble each affected target and record exact source, target,
   output, and instruction-delivery provenance.
4. Run deterministic validation before model evaluation.
5. Run the smallest model comparison that exposes the behavior being changed.
   Test instruction layers in isolation when useful, then test their combined
   interaction.
6. Interpret semantic and pairwise results, including useful passing outputs,
   effort-level patterns, missing evidence, and execution failures.
7. Publish a dated human-readable result under
   `maintainer/docs/evaluations/` and retain frozen machine-readable records
   with the owning suite.
8. Obtain human approval before promoting a candidate.
9. Merge accepted source into the current bundle or maintained guide, compile
   repository outputs, and verify consuming projects separately.
10. Update the current-guidance status page and requirement evidence.

Do not infer discovery from direct injection, do not infer instruction
authority from a filename, and do not count a process exit as a valid semantic
or pairwise result without its expected record.
