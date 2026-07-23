# Revise Task Guidance for Continuation and Flexible Execution Plans

Refine `TASKS-v7.md` so human-facing task sections stay clean while supporting details and execution plans retain enough information for another agent to continue. Keep execution-plan details free-form, collect important implementation decisions and open implementation questions near the bottom immediately before documentation, and place verification after the planned work.

## Requirements checklist

- [x] **R1. Continuation-first handoffs:** The guidance prioritizes continuation without material rediscovery over minimum task-file length and gives section-specific rules for retaining or dropping information.
- [x] **R2. Clean human-facing sections:** Requirements, scope, requirement questions, and user-facing material decisions remain concise and scannable without imposing a general brevity requirement on supporting details or execution plans.
- [x] **R3. Explicit status syntax:** Requirements and execution tasks explicitly use Markdown checkbox items.
- [x] **R4. Flexible plan body:** After plan status, an execution plan has a substantive free-form body that agents may structure and detail as needed; no fixed implementation-direction heading is required.
- [x] **R5. Collected implementation decisions:** Important implementation decisions and open implementation questions are collected near the bottom of a retained execution plan immediately before documentation work.
- [x] **R6. Verification follows planned work:** Documentation and the execution task checklist follow the implementation decision collection, and requirement verification plus optional additional implementation verification appear at the end.
- [x] **R7. Clear omit-plan boundary:** Omit-plan handoffs exclude the free-form execution plan, implementation decisions/questions, planned documentation, tasks, and verification in substance rather than relabeling them.
- [x] **R8. Compact guidance:** The revised guide encodes these rules mainly by replacing overlapping text and remains approximately at or below its current 1,275-word size.
- [x] **R9. Verifiable model understanding:** Mechanical and empirical evaluation distinguish continuation value from raw brevity, enforce the plan tail where applicable, and validate retain-plan and omit-plan behavior with reusable guidance-neutral investigations.

## Scope

This revision changes task-file guidance and its evaluation suite. The task-guidance README receives only generic workflow or evaluator behavior needed by future users; comparison-specific refs and run instructions remain in this task and generated artifacts.

## Requirement questions and user-facing decisions

No unresolved requirement questions remain. The user selected a flexible execution-plan body and fixed placement only for its closing implementation decisions/questions, documentation, tasks, and verification.

## Supporting facts

- Current `TASKS-v7.md` is 1,275 words.
- The prior GLM comparison showed that compact guidance reduced retain-plan length but made checkbox syntax too implicit and allowed an empty plan body before verification.
- The corrected reviewer showed that both GLM and ChatGPT placed implementation direction outside the execution plan and that omit-plan outputs relabeled implementation or verification planning.
- Guidance-neutral GLM and ChatGPT investigation sessions already exist and remain reusable because this task does not change the investigation prompt or non-guidance request profile.

## Execution plan

Status: Approved

Replace the global brevity instruction with a compact continuation rule. Human-facing requirements, scope, requirement questions, and user-facing decisions stay concise; supporting details retain durable facts, constraints, references, accepted facts, and failed approaches needed to avoid rediscovery. Chronology, raw output, duplication, replaceable inventories, and unselected speculation are condensed or omitted.

Revise execution-plan structure without prescribing the body’s internal headings. Require substantive content after plan status, then reserve a closing sequence for important implementation decisions and open implementation questions, documentation, checkbox execution tasks, requirement verification, and optional additional implementation verification.

Clarify that requirement questions and material user-facing decisions remain near the top. Implementation decisions and implementation questions belong in the execution plan’s near-bottom collection. Local reversible choices may be resolved by the agent and recorded there only when useful for continuation.

Align mechanical assertions with objectively parseable contracts: checkbox syntax, non-empty free-form plan body, required closing sections and order, requirement-ID traceability, and omission of the plan structure in omit-plan cases. Keep completeness, fact/decision labeling, and proportional detail as empirical judgments.

Reuse the saved GLM and ChatGPT guidance-neutral sessions. First generate tasks with the new guidance and the current evaluator, then update the evaluator and replay those exact task artifacts so guidance effects remain separate from evaluator effects.

### Important implementation decisions and open questions

- **Decision:** The plan body has no required internal heading or length; it may contain any agent-oriented implementation detail needed for execution.
- **Decision:** The required retained-plan tail is ordered: implementation decisions/questions, documentation, task checklist, requirement verification, then optional additional implementation verification.
- **Decision:** Requirement questions and material user-facing decisions stay near the top; implementation decisions and questions move to the retained plan tail.
- **Decision:** Omit-plan means the implementation decision/question collection is omitted with the rest of the plan unless the user explicitly asks to preserve a particular decision separately.
- **Decision:** Guidance length is controlled by replacement and deduplication, not by weakening continuation requirements.
- No open implementation questions remain before execution.

### Documentation

Update the generic evaluation README only if commands, reusable source behavior, structural assertions, or scenario-aware reviewer behavior changed. Do not document this one-off comparison or its refs there.

### Task checklist

- [x] Replace generic brevity wording with compact continuation-first, section-specific retention guidance.
- [x] Restore explicit Markdown checkbox requirements.
- [x] Define the free-form execution-plan body and ordered closing sections.
- [x] Clarify top-level requirement/user decisions versus near-bottom implementation decisions/questions.
- [x] Clarify omit-plan substantive exclusions.
- [x] Keep `TASKS-v7.md` approximately at or below 1,275 words.
- [x] Update mechanical assertions and deterministic tests.
- [x] Update the empirical reviewer and human review template for continuation value and flexible plan structure.
- [x] Update only generic README content.
- [x] Run deterministic tests and lint.
- [x] Reuse the neutral GLM seed for revised-guidance retain-plan and omit-plan generation.
- [x] Replay the GLM artifacts under the aligned evaluator and generate a review bundle.
- [x] Reuse the neutral ChatGPT seed for supplementary retain-plan and omit-plan confirmation.
- [x] Record findings, evidence, deviations, and unresolved scope in this task.

### Requirement verification

- **R1–R2:** Empirical review confirms human-facing sections are scannable while supporting details retain enough durable context for continuation without penalizing justified length.
- **R3:** Mechanical fixtures and real-model outputs use checkbox requirements and checkbox execution tasks.
- **R4–R6:** Retain-plan fixtures and real-model outputs contain substantive free-form content after status, followed in order by the implementation decision/question collection, documentation, task checklist, and verification tail.
- **R7:** Omit-plan mechanical and empirical review confirm the plan body and closing plan content are absent in substance rather than relabeled.
- **R8:** Word-count comparison confirms the revised guidance remains approximately at or below 1,275 words.
- **R9:** Deterministic tests pass, saved investigation hashes prove reuse without reinvestigation, and corrected review bundles assess the new contracts.

### Additional implementation verification

- Ensure requirement verification extraction includes nested H4 groups but stops before additional implementation verification.
- Do not introduce maximum task-file word counts, heading counts, or supporting-detail length limits.
- Confirm experiment-specific provenance remains outside the generic README.

## Implementation Notes

- Committed the guidance-only revision as `c1939b7c`; it is exactly 1,275 words, matching the prior guide.
- Committed evaluator alignment separately as `bc3ad982`. Mechanical checks now require a substantive free-form plan body, exact closing headings/order, checkbox tasks, verification at the end, and optional additional verification last.
- Deterministic verification passed: `pytest test/task_guidance -q` reported 31 tests passing, and `ruff check test/task_guidance` passed.
- Reused the existing neutral GLM investigation (`ceed4937645681d1e256c7e646ed4eca1f840c7a91ffdfad0d3bf64b409999cb`) and ChatGPT investigation (`abafeaf17e9c54d26de7525727897c7dc7dd35ce84dfcf6f5e62d4129be801d9`); no repository investigation was repeated.
- ChatGPT followed the retain-plan tail exactly and passed all mechanical checks. Its omit-plan handoff also passed and avoided implementation planning.
- GLM omit-plan passed mechanically but retained one prescriptive implementation-direction sentence in supporting details, which the aligned empirical reviewer flagged.
- The first GLM retain-plan attempt exceeded the unchanged three-mutation safety budget and produced no task. A preserved rerun produced a complete task with strong continuation context but used `### Implementation tasks`, put tasks and verification before the decision collection, and placed risks after it. The aligned mechanical and empirical checks reported these deviations; no assertion was weakened.
- The ChatGPT retain-plan empirical review found one execution-task item added to the requirements checklist, showing that outcome-versus-task judgment remains semantic even when checkbox structure is correct.
- Generic README changes cover only reusable evaluator behavior. Run refs and comparison provenance remain in generated bundles.
- Post-completion adjustment requested on 2026-07-23: strengthened the requirement definition and checklist rule so plan work is not promoted into requirements unless its resulting artifact or coverage is independently required, and then must be stated as an outcome rather than an action. The approved wording was added verbatim while unrelated redundancy was removed, reducing `TASKS-v7.md` from 1,275 to 1,273 words. GLM, ChatGPT, and Ollama `kimi-k2.7-code:cloud` evaluations are being rerun from guidance-neutral investigations.
- The first Kimi task-creation run exposed a source-reuse harness defect rather than a guidance result: the imported session still advertised the neutral seed's absolute workspace, so Kimi followed the system's absolute-path instruction and its writes were denied outside the isolated fork. Runtime parent sessions now rebase only source-workspace references to the fork workspace while preserving the original session artifact/hash for provenance. A regression test raises deterministic coverage to 32 passing tests; the generic README documents the rebasing behavior.
- The first rebased Kimi attempt then triggered native-history integrity protection because the runtime system-message path changed while cached provider-native messages remained. Rebased runtime sessions now discard only the derived `native_messages` and integrity cache so native history is rebuilt from the rebased generic messages; the original source session remains unchanged.
- Final reruns with guidance ref `a6aa565d` passed all mechanical checks for GLM, ChatGPT, and Kimi retain-plan and omit-plan cases. The GLM reviewer rated retain-plan compliance high; ChatGPT retain-plan and both ChatGPT/GLM omit-plan reviews were compliant. No model promoted regression coverage or other plan work into the requirements checklist.
- Kimi's final retain-plan review was largely compliant and its omit-plan review compliant. Its requirements remained R1–R5 outcomes. The retained task mildly duplicated the selected implementation approach near the top and in the required near-bottom decision collection, but did not add a work-step requirement.
- Final review bundles are `tmp/task-guidance-eval/review-bundles/20260723-task-guidance-outcome-glm`, `tmp/task-guidance-eval/review-bundles/20260723-task-guidance-outcome-chatgpt`, and `tmp/task-guidance-eval/review-bundles/20260723-task-guidance-outcome-kimi-rebased-2`. Failed pre-fix Kimi runs remain preserved separately as harness evidence.

## Completion Notes

- Replaced global brevity with continuation-first, section-specific selection; restored explicit checkbox syntax; retained a free-form agent-oriented plan body; and fixed the plan tail as implementation decisions/questions, documentation, task checklist, requirement verification, and optional additional verification.
- Requirements R1–R9 are supported by guide inspection, exact word count, deterministic tests, source-session provenance, real GLM and ChatGPT task creation, and aligned empirical review.
- The revision improved cross-model behavior without adding guide length. ChatGPT complied structurally; GLM demonstrated that exact heading/order adherence and omit-plan filtering remain model-dependent, with the evaluator providing clear evidence rather than hiding the failures.
- Review bundles:
  - `tmp/task-guidance-eval/review-bundles/20260723-task-guidance-continuation-glm-aligned-evaluator`
  - `tmp/task-guidance-eval/review-bundles/20260723-task-guidance-continuation-chatgpt-aligned-evaluator`
  - Guidance-only baseline bundles remain under `tmp/task-guidance-continuation-guidance-only/tmp/task-guidance-eval/review-bundles/`.
- No further scope is required for this revision. Future changes may add a dedicated information-selection fixture if broader cross-task evidence is desired.

## Post-completion follow-up

### Final quality assessment

- The task succeeded from task-file quality and handoff-usability perspectives. No material regression was observed against the pre-task guidance in the evaluated scenario.
- Final GLM, ChatGPT, and Kimi retain-plan and omit-plan runs all passed mechanical assertions. Their requirements remained completed-state outcomes/constraints, retained plans were continuation-capable, omit-plan files excluded plan content, and human-facing sections stayed scannable.
- The guidance retained the useful context of the pre-task state while improving requirement/task separation, plan ownership, decision placement, verification separation, and omit-plan behavior. Its final size is 1,273 words versus 1,275 before the last adjustment.
- This evidence establishes guidance usability, not the technical correctness of each generated implementation plan. Model generation is stochastic and the empirical comparison currently uses one repository scenario.

### Non-blocking follow-up areas

1. **Top-level versus implementation decisions:** Kimi mildly duplicated its selected approach near the top and in the required near-bottom implementation-decision collection. If this recurs, clarify that the top contains only requirement questions and decisions changing required scope/outcomes; implementation choices belong only in the retained plan.
2. **Semantic requirement classification:** Outcome-versus-task classification remains an empirical judgment. Do not add a verb-based mechanical rule; valid outcome requirements commonly contain verbs.
3. **Scenario diversity:** Add focused cases where tests or documentation are genuinely required deliverables, where no user-visible behavior changes, where human verification is required, and where requirement questions remain unresolved.
4. **Reuse-path smoke coverage:** Kimi exercised workspace rebasing and native-history rebuilding end to end. A future GLM and ChatGPT reuse run under the corrected harness would provide additional provider coverage.
5. **Omit-plan tradeoff:** Omit-plan intentionally removes implementation decisions/questions unless the user explicitly requests preservation. Monitor whether this causes avoidable rediscovery in real handoffs.

### Where to continue

- Start with the final review bundles listed in `## Implementation Notes` and the reusable harness under `test/task_guidance/`.
- Prefer adding a targeted evaluation fixture before changing guidance again. Strengthen wording only for a repeated cross-model failure, not a one-off formatting preference.
- If decision duplication recurs, the smallest candidate guidance addition is: “The top section contains only requirement questions and decisions changing required scope or outcomes. Collect implementation choices only in the retained execution plan.”
