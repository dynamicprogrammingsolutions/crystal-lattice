# TG-09: Deployment procedure as a task

## Project

- Repository: Flask/Vue books app
- Fixture: `tg03-flask-vue-refresh` (shared project state)
- Kind: Python/Vue sample application

## Purpose

Verify that an operations task keeps operations-shaped sections: the
procedure, its configuration surface, verification by executing it, and a
rollback — without forcing unit-test evidence onto a runbook.

## Natural request

> The books demo needs a repeatable deployment procedure. Create the task
> for writing it: how the app is built, how it runs with configuration
> from environment variables, how the health endpoint verifies a
> deployment, and how to roll back to the previous deployment when
> verification fails. The procedure is accepted by executing it once end
> to end on a clean checkout. No product code changes.

The prompt does not prescribe the task file's sections, requirements
wording, or decomposition.

## Approved outcomes

Use `OPS-1`–`OPS-5` from the target. The concrete deployment target
(platform, service) is an open decision recorded as such.

## Expected task shape

- One task file: the procedure is one coherent deliverable.
- Requirements carry the procedure outcomes including rollback; they do
  not turn the deployment target choice into a decided requirement.
- Supporting details carry the configuration surface and the clean-checkout
  acceptance procedure.
- Acceptance evidence is the executed end-to-end run and the rollback
  rehearsal — the operation is its own decisive check; unit-test sections
  do not apply.

## Task-kind fit

- Task kind: operations.
- Applicable sections: requirements checklist, supporting details,
  execution plan, questions and decisions.
- Acceptance evidence: one executed deployment with health verification
  and one executed rollback on a clean checkout.
