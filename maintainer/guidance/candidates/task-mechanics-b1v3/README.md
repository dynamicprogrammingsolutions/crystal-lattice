# Task mechanics B1v3

This candidate extends
[task-mechanics B1v2](../task-mechanics-b1v2/README.md) with one validity
correction selected after the B1v2 evaluation run (September 25, 2026).

Changed section:

- `tasks-v7`

Relative to B1v2 it changes exactly one rule. Step 1 of creating task files
previously read "Confirm which format the user wants: a single task file, or
a main task with subtasks", which one model family read as a mandatory
question: when a request delegates the structure choice ("create the
appropriate task structure"), it asked and stopped instead of creating files
— observed repeatedly across evaluations (B0, B1, and four of six B1v2
samples of one cell). The step now directs the agent to determine the
structure from the request and the decomposition rules (single task by
default, children only when justified) and to ask only when the user's
structure preference is material and cannot be inferred from the request.

Everything else — the B1v2 decisive-check rule, the design-visibility rule,
the decomposition rules, the conditional technical-layer rule, and every
other current section — is inherited from B1v2/current unchanged.

Evaluation selects this candidate explicitly and never promotes or writes it
into current guidance.
