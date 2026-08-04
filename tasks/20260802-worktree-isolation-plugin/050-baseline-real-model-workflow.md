# Baseline Real-Model Worktree Workflow

Prove the production baseline with realistic hosted model/tool-family flows before deciding whether optional workspace-context strategies are necessary.

Parent Task: tasks/20260802-worktree-isolation-plugin/000-main.md

Depends On: tasks/20260802-worktree-isolation-plugin/040-baseline-worktree-ux-and-documentation.md

## Requirements checklist

- [ ] A reusable public-application workflow runs with GPT plus Codex tools, Claude plus Claude tools, GLM plus Claude tools, Kimi plus Kimi tools, and Gemini plus Gemini tools.
- [ ] In each case, one session edits and commits in a created worktree, closes it, returns to the original checkout, merges the branch using AI tools, and performs a follow-up modification.
- [ ] Acceptance asserts repository graph and file state, not merely model text or logs.
- [ ] Post-close tool-call evidence proves commands and file operations do not incorrectly execute against the stale closed worktree path.
- [ ] Model IDs are environment-overridable and default to suitable low-cost models documented at execution time.
- [ ] Tests use explicit credential/marker gates and do not count skips, collection failures, or infrastructure errors as success.
- [ ] Product defects exposed by the realistic workflow are fixed without adding test-only product paths or weakening the scenario.

## Supporting details

- The matrix is intended to test model behavior plus production providers, tool adapters, application actions, persistence, and Git—not just direct tool invocation.
- Pricing and model availability change. Stable environment variables are preferable to hard-coding a permanent "cheapest" claim.
- GLM with Claude tools may require a purpose-built test agent because the current default GLM agent uses Gemini tools.
- The baseline intentionally uses corrected dynamic system context without optional explicit-path or reminder injections.

## Execution plan

Status: Draft

Build one parameterized scenario around temporary real Git repositories and the public application request/action flow. Give each model bounded, explicit user instructions to edit a sentinel, commit, close through the user-driven action boundary, merge from the original checkout, and make a final edit. Capture production events/tool calls for workdir assertions and inspect Git directly for acceptance.

Keep deterministic setup and assertions shared while allowing provider/model-specific configuration. Mark the suite `integration`, `api`, and `slow_integration` as appropriate. Run each matrix row explicitly, record exact models and results, and correct baseline code where failures reveal real workspace confusion.

### Implementation decisions and open questions

- Use a unified hosted provider where it faithfully supports each model/tool protocol; otherwise use the repository's production provider for that family. Do not distort tool shapes merely to force one provider.
- Prompts should state the requested Git outcome but should not reveal test internals or tell the model which stale path assertion is being measured.
- A model retry policy may handle transient provider errors, but behavioral retries must be bounded and reported rather than hiding unreliable behavior.
- If a low-cost model cannot reliably perform the workflow, record evidence and choose the cheapest suitable model rather than weakening acceptance.

### Documentation

- Document environment variables, credentials, markers, per-row commands, expected cost-conscious defaults, and how to interpret failures.
- Add a baseline result record with date, provider, exact model, tool family, attempts, and observed stale-path behavior.
- Update the manual guide with any model-facing wording proven necessary for the baseline.

### Task checklist

- [ ] Build shared public-flow harness.
- [ ] Add five required model/tool rows.
- [ ] Add Git and tool-workdir acceptance assertions.
- [ ] Run every row with gates explicitly enabled.
- [ ] Fix and rerun product defects.
- [ ] Record results and baseline review recommendation.

### Requirement verification

- For every matrix row, collect a successful test run and inspect the resulting original branch, merged worktree commit, final follow-up content, absence/removal or retained status of the linked worktree, and post-close tool workdirs.
- Confirm the tests crossed application action, request/tool loop, provider, real model, filesystem, and Git boundaries.
- Conduct the baseline product review using deterministic, manual, and hosted evidence before approving optional subtasks.

### Additional implementation verification

- Verify the harness type-checks/imports before hosted calls and that one existing integration consumer still passes if shared fixtures change.
- Keep provider outages, rate limits, credentials, model refusals, and product behavior distinguishable in reports.