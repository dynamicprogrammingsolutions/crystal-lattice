# File fidelity and readability rework results — 2026-09-27

The Theme C assessment rework: the six-dimension task-quality assessment
is replaced by two focused identity-blind judges — file fidelity
(does the file carry the conversation's decided design and durable
context) and file readability (can a human work with each section) —
re-judging the same B1v3 subjects with no producer runs.

- Package: [`results/20260927-file-fidelity-readability/`](results/20260927-file-fidelity-readability/)
  (28 judgments over 26 subject cells; labels `b1v3-r1` + `b1v3-k1`;
  judge `glm-5.3-flash:cloud` max; frozen dataset
  `task-guidance-file-quality-c1-20260927`).
- Contract: every grade carries `{where, quote, why}` findings (required
  for non-top grades) and every response harvests mistakes. Judged
  material is embedded as rendered text; fidelity judges files against
  the conversation plus a quality-specific target excerpt, readability
  judges files alone with measured per-section structure facts and
  `<file path> — <section title>` keys.

## Baseline

| Dimension | Old task-quality (same subjects) | New |
|---|---|---|
| findability | 28/28 complete (ceiling, zero variance) | **readability: 222/249 sections readable (89%), 27 partial with findings, 159 presentation mistakes** |
| section_appropriateness | 28/28 complete (ceiling) | 27 complete / 1 partial |
| plan_design_completeness | 22 complete / 5 partial / 1 poor | 25 complete / 3 partial |
| durable_context_preservation | 23 complete / 5 partial | 24 complete / 4 partial |
| plan_justification | 21 justified / 2 fabricated / 5 n/a | 23 justified / 5 n/a |
| task_kind_fit | 26 fits / 2 missing | 28 fits |

By model: readability GLM 55/70 (79%) vs GPT 167/179 (93%) sections;
fidelity mistakes harvested 45 (13 GLM + 32 GPT).

## Findings

1. **The readability ceiling broke.** The old whole-file `findability`
   graded every B1v3 file complete; per-section grading now yields 27
   partial sections, each with a concrete `{where, quote, why}` finding,
   plus 159 harvested presentation mistakes — the measurable signal the
   six-gap calibration needs.
2. **The tg04 fabrication events did not reproduce** under the new
   judge (2 `fabricated` → `justified`; 2 `missing` → `fits`).
   Open calibration question: GLM judge variance, or signal lost in the
   reworked prompt (target excerpt instead of the full target). The
   mistake harvest still flags tg04 content, but the grades moved —
   verify with the b0-style contrast before relying on
   `plan_justification` in the next calibration.
3. **b0 leniency verdict** (scratch, `tmp/b0_leniency_check.json`):
   fidelity discriminates pre-guidance files
   (`plan_design_completeness` 16/18, `durable_context` 15/18 top);
   readability has a UNIT CONFOUND — multi-file b0 sets with many small
   sections grade 89% readable, so per-section readability measures
   section size as much as guidance quality across different
   decompositions. Cross-corpus comparisons are caveated; candidate
   follow-up: a whole-file reading-effort grade or word-weighted
   aggregation.
4. Validation gates passed for both assessments before any baseline
   (natural + good + deliberately bad probes; the bad probes graded
   down with exact expected findings).

The old `task-quality-assessment` stage is retired from the
configuration; its records and packages remain as history.
