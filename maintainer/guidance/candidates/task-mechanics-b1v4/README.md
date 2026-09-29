# Task mechanics B1v4

This candidate extends the promoted v3 baseline (current) with wording for the
six observed gaps (kind baseline, quality-coverage and file-quality packages,
September 26–27, 2026) plus the plan-content findings from the Layer 1
calibration and the September 27 amendment directions.

Changed section:

- `tasks-v7`

Relative to v3 it changes exactly these rules:

1. **Rename `## Execution plan` → `## Implementation plan`** everywhere
   (term, handoff rules, section title, presenting, executor steps). "Execution
   plan" reads as a step list; the section carries a decided design. Gap 1.
2. **Conditional plan inclusion, decided by the author.** The v3 handoff rule
   ended with "If the user does not say whether to retain the plan, ask",
   which produced two producer failures (ask-and-stop on a content task, a
   filled plan despite an explicit deferral). The author now decides from the
   request and the recorded planning; explicit retain/omit instructions are
   followed; requirements-only files are valid when no approach exists; a plan
   is never invented to fill the section. Gaps 5 and 6.
3. **First-class risks/order content and a restatement duty.** The plan
   carries risks and the way back, and order logic, as named content; when the
   file follows planning, the decided design is restated completely (risks and
   order rationale included) without invented detail. Layer 1 findings:
   risks/way-back conveyed in 18% of judged plans, order logic 23%,
   retained-plan files 0/6 on both; tg04 fabricated events. Gap 1 and 5.
4. **Per-section readability.** Each section is written to be readable on its
   own; formatting elements are named as examples, never mandated. Theme C
   findings: 27 partial sections, list items packing several facts and long
   paragraphs dominate. Gap 2.
5. **Self-containedness.** Facts that matter for continuation are stated in
   the file (and in a presented plan summary) rather than living only behind a
   link or in the planning conversation. Layer 1 GENERIC-9.
6. **Placement taxonomy.** A compact table maps each kind of content to its
   one owning section, including the notes-family sections (Implementation
   Notes, Completion Notes, Post-completion follow-up). Gap 4.
7. **Verification wording.** Requirement verification names what it
   deliberately does not cover, and evidence fits the task kind (decision
   recorded, page published) instead of forcing test-based evidence.
   Layer 1 GENERIC-5 at 55%; gap 6.
8. **Depth follows decisions.** Plan depth includes what would change a
   reader's decision and summarizes the rest (contract change without field
   validation detail; testing strategy without exhaustive edge cases).
   Layer 1 GENERIC-10.
9. **Follow-up immutability.** Completion Notes are immutable once written;
   corrections go under Post-completion follow-up.

Everything else — the structure and decomposition rules, the decisive-check
rule, status semantics, subtask naming, and every other current section — is
inherited from current unchanged.

Compatibility: the suite's draft-plan assertion accepts both `## Execution
plan` and `## Implementation plan` headings, and the scenario targets name the
new heading. Historical packages keep the old heading as record.
