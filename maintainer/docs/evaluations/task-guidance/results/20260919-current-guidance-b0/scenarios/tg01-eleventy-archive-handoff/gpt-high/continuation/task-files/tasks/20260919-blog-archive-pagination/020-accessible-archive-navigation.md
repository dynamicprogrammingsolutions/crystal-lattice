# Accessible archive navigation

Add static, semantic previous/next controls to each paginated archive page.

Parent Task: tasks/20260919-blog-archive-pagination/000-main.md

Depends On: tasks/20260919-blog-archive-pagination/010-archive-pagination-generation.md

## Requirements checklist

- [ ] Provide accessible previous/next navigation on paginated archive
  pages.
- [ ] Render only valid directional links at the first and final page
  boundaries.
- [ ] Keep navigation server-rendered and usable without JavaScript.
- [ ] Avoid adding archive controls to unrelated outputs.

## Supporting facts

- The current archive has no navigation controls.
- The site is generated as static HTML and currently claims no client-side
  JavaScript requirement.
- The archive list is shared with home and tag pages, so navigation must be
  scoped to archive pagination context rather than added to the shared list
  include unconditionally.

## Execution plan

Status: Draft

- Add a semantic navigation region with an accessible label and explicit
  previous/next link text.
- Use the approved archive page URLs for link targets.
- Suppress the previous link on page one and the next link on the final page;
  render both on an interior page.
- Keep the controls as ordinary HTML anchors with no script, client-side
  state, or test-only fallback.

### Implementation decisions and open questions

- Choose the smallest markup location that receives archive pagination data
  without changing home or tag page output.
- Verify link names and landmarks with the focused HTML test; visual or
  browser-specific accessibility review remains separate if required by the
  project.

### Documentation

Record the existence of static previous/next archive navigation only if it is
useful to the developer-facing pagination guidance; the parent documentation
subtask owns that decision.

### Task checklist

- [ ] Add scoped semantic archive navigation.
- [ ] Verify first, interior, and final page link states.
- [ ] Verify generated navigation contains no JavaScript dependency.

### Requirement verification

- Inspect first, interior, and final archive page HTML from a build with at
  least three pages.
- Assert an accessible navigation label, valid link targets, correct
  previous/next link presence, and no script-driven navigation.