# Define the structured author contract and transition policy

Choose and document the structured author metadata contract, its public
rendering shape, and the bounded compatibility policy that later subtasks must
implement.

Parent Task: tasks/20260919-author-metadata-migration/000-main.md

## Requirements checklist

- [ ] The structured multi-author shape and required fields are approved.
- [ ] Single-author and multiple-author ordering semantics are explicit.
- [ ] HTML post/archive rendering and XML feed representation are explicit.
- [ ] The transition behavior for legacy `author` input is explicit,
      including the final rejection condition.
- [ ] The authoring-tool input contract is explicit enough for implementation
      without inventing a public API.

## Research and supporting facts

The current repository has scalar `author` values in both post files,
direct scalar rendering in the post layout and feed, and scalar serialization
in `scripts/new-post.js`. The archive include does not currently render an
author, so its required public behavior must be decided rather than inferred
from existing output.

## Execution plan

Status: Draft

1. Compare the current scalar contract with the proposed structured
   representation and define the lossless mapping for existing posts.
2. Decide the author ordering, HTML separators/markup, feed shape, escaping
   expectations, and authoring-tool arguments.
3. Define the compatibility window: what reads legacy input, what writes only
   the new field, and what repository/build evidence permits rejection.
4. Record the accepted contract in this task and hand it to the content,
   rendering, verification, and documentation subtasks.

### Implementation decisions and open questions

- Recommended schema: ordered `authors` entries with required `name`; confirm
  before execution.
- Confirm whether archive rows should gain a byline or remain intentionally
  author-independent while still avoiding legacy-field access.
- Confirm whether the feed uses repeated author elements or an approved nested
  structure.

### Documentation

Record the accepted schema and transition policy in the implementation's
owning developer guidance during the documentation handoff; this subtask
should not create a speculative public guide.

### Task checklist

- [ ] Resolve and record the schema decision.
- [ ] Resolve and record HTML/feed output decisions.
- [ ] Resolve and record the compatibility and rejection gate.
- [ ] Pass the contract to dependent subtasks.

### Requirement verification

Review the recorded contract against every consumer identified in the parent
task and confirm that it supplies enough information to test source metadata,
HTML output, XML output, and tool serialization.

### Additional implementation verification

Check that the proposed contract does not require changing URLs, titles,
content, tags, collection ordering, or unrelated sitemap behavior.