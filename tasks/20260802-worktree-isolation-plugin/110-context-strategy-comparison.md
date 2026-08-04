# Workspace Context Strategy Comparison

Compare the production baseline and approved opt-in workspace-context strategies across the required model/tool families, document reliability and tradeoffs, and recommend whether any strategy merits a future default change.

Parent Task: tasks/20260802-worktree-isolation-plugin/000-main.md

Depends On: tasks/20260802-worktree-isolation-plugin/060-explicit-workspace-system-context.md

Depends On: tasks/20260802-worktree-isolation-plugin/070-workspace-transition-reminders.md

Depends On: tasks/20260802-worktree-isolation-plugin/090-relative-path-mode-codex-and-claude.md

Depends On: tasks/20260802-worktree-isolation-plugin/100-relative-path-mode-kimi-and-gemini.md

## Requirements checklist

- [ ] The baseline, explicit system context, transition reminders, relative-path mode, and meaningful compatible combinations run through a common realistic scenario.
- [ ] GPT/Codex tools, Claude/Claude tools, GLM/Claude tools, Kimi/Kimi tools, and Gemini/Gemini tools are represented with exact provider/model/tool configuration recorded.
- [ ] Results measure workflow success, stale-path reuse, unnecessary cwd checks, absolute-path exposure, token/tool overhead, retries, and failure modes.
- [ ] Comparisons use public production paths and equivalent prompts/assertions rather than strategy-specific test shortcuts.
- [ ] A durable report recommends retaining the baseline or promoting, revising, combining, or abandoning each experimental strategy.
- [ ] No default changes are made without a separate approved requirement change after review.

## Supporting details

- Some combinations are intentionally incompatible, especially explicit absolute-path system context plus path-minimizing mode. The matrix should record them as invalid rather than force execution.
- Reminder plus explicit system context and reminder plus relative-path mode may be meaningful combinations if reminder wording follows the selected path representation.
- Hosted model behavior is nondeterministic. Exact attempts, bounded retries, and observed variance matter more than a single aggregate pass rate.
- Cost-conscious models are preferred, but suitability for the workflow is required.

## Execution plan

Status: Draft

Extend the baseline harness with a strategy dimension while keeping repository setup, user prompts, action flow, Git assertions, and tool-workdir capture equivalent. Run supported matrix slices explicitly and retain structured results suitable for comparison. Separate provider/transient failures from model/tool behavior and product defects.

Analyze results by family and strategy. Produce a concise recommendation with evidence, privacy/reliability tradeoffs, implementation maintenance cost, and unresolved risks. Stop before changing defaults and request a new scope decision if promotion is recommended.

### Implementation decisions and open questions

- Use repeated trials only where variance affects conclusions; document count and cost before running a broad matrix.
- Define absolute-path exposure as model-visible request/result content, not as an impossible claim that shell cannot discover host paths.
- A strategy that improves privacy but materially reduces task completion should not be promoted without an explicit product tradeoff decision.
- Recommendation categories: retain experimental, revise, combine, promote in a follow-up, or abandon/remove.

### Documentation

- Add a dated comparison report with configurations, methods, raw structured result location, summarized outcomes, limitations, and recommendation.
- Update experimental setting docs with observed compatibility and known model-specific behavior.
- Link any proposed default change to a new task rather than editing the stable main requirements.

### Task checklist

- [ ] Define supported strategy matrix and metrics.
- [ ] Extend baseline harness without weakening acceptance.
- [ ] Run required model/tool/strategy slices.
- [ ] Triage and rerun genuine product defects.
- [ ] Analyze reliability, stale paths, exposure, and overhead.
- [ ] Publish recommendation and request follow-up scope if needed.

### Requirement verification

- Review structured results and successful Git/file assertions for every required supported slice.
- Confirm prompts and public boundaries are equivalent across strategies.
- Confirm the report distinguishes invalid combinations, provider failures, product defects, and model behavior and makes no unauthorized default change.

### Additional implementation verification

- Validate result aggregation against fixture data before hosted runs, preserve exact model/provider metadata, and ensure incomplete/skipped rows cannot be summarized as passes.