# Decision: use Git bundles and a stable remote-style sync

## Context

The current default transfers a committed archive and working patch. It is
useful for one delegated session but does not give a generic workspace full
repository history or a durable Git-native way to inspect cloud branches.

Copying raw `.git` internals is less portable, especially with linked
worktrees and host-specific paths.

## Decision

- Add a full-clone default profile based on Git bundles plus explicit metadata
  and current worktree state.
- Clone from the bundle in cloud and restore the original upstream as `origin`.
- Export cloud refs to a bundle during sync-down.
- Store the latest usable bundle under local Git state.
- Create or update a stable workspace-specific local remote and fetch cloud
  refs into its remote-tracking namespace.
- Never automatically checkout, merge, rebase, reset, or delete local branches.
- Retain current patch and branch-import profiles and the existing script phase
  contract.

## Consequences

Positive:

- The cloud workspace behaves like a normal repository clone.
- Users choose how to integrate cloud work.
- Transfer remains script-defined and replaceable.
- Existing project overrides remain valid.

Costs:

- Full history may increase initial transfer size.
- Bundle/refspec and interrupted-update handling require careful tests.
- Linked worktrees, ignored outputs, private submodules, and unreachable
  objects need separate future behavior.
