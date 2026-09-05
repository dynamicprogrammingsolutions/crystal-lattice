# Inspect agent instructions

Crystal Lattice compiles project guidance into the effective
developer/system message used by an agent session. Inspect that message before
relying on short task prompts, especially when a task depends on repository
`AGENTS.md` or task-file guidance.

## Include task guidance

Task guidance is disabled by default and configured per session:

1. Open the active conversation in **Messages**.
2. Select the Settings gear.
3. In **Session settings**, enable **Include TASKS Guidance**.

The setting affects the compiled message for subsequent requests in that
session.

## Show the compiled message

Open the conversation's session actions and select **Show compiled system
message**. The app displays the current effective message in a dialog without
sending a model request or adding to the conversation.

Check that the dialog contains the expected project instructions and, when
enabled, task guidance. Close the dialog when inspection is complete.