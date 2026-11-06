# Add a Post-Creation Guide to CONTRIBUTING.md

Write a contributor-facing section in `CONTRIBUTING.md` that explains how to
add and preview a post using this Eleventy site.

## Requirements checklist

- [ ] Explain where and how to create a post file.
- [ ] Show the required post front matter: `title`, `date`, `description`, and
  `tags`.
- [ ] Explain the supported draft workflow accurately.
- [ ] Explain how to preview the site locally.
- [ ] Make no product behavior changes; a maintainer review against this
  checklist is the acceptance criterion.

## Scope

Documentation only. Do not change site behavior, configuration, dependencies,
or post-processing to create or modify draft support.

## Supporting details

- The repository currently has no `CONTRIBUTING.md`.
- Existing example posts are Markdown files under `content/posts/`. They use
  `title`, `date`, and `tags`; they do not yet show `description`.
- `package.json` defines `npm run build` and `npm test`, but no preview script.
- No draft behavior was evident in the initial inspection of the Eleventy
  configuration or post examples. Confirm the actual behavior before describing
  it; do not infer a draft convention or imply that draft posts are excluded
  from production output without evidence.
- The production build generates the site in `_site/`.

## Execution plan

Status: Draft

Inspect the current Eleventy behavior and available commands before writing
instructions, especially whether any existing convention excludes draft posts
from production output. Keep the guide aligned with supported behavior; if the
repository has no draft workflow, say so clearly rather than introducing one.
Add a concise post-authoring section to the root `CONTRIBUTING.md`, using an
example consistent with the repository’s Markdown posts and all four required
front matter fields. Include the verified local preview invocation and what
contributors should expect from draft handling. No product code or
configuration changes are in scope.

### Implementation decisions and open questions

- Decision: Keep the change documentation-only and describe existing behavior,
  not a desired or proposed draft feature.
- Open investigation: Verify draft inclusion/exclusion behavior and the exact
  local preview command before documenting either.

### Documentation

- Add post creation, required front matter, draft handling, and local preview
  guidance to `CONTRIBUTING.md`.
- Keep instructions concise and actionable for new contributors.

### Task checklist

- [ ] Verify current draft behavior and local preview command.
- [ ] Write the post contribution section in `CONTRIBUTING.md`.
- [ ] Check that every requirement is covered and no product files changed.
- [ ] Request maintainer review against the requirements checklist.

### Requirement verification

- Requirements are accepted by maintainer review against the checklist at the
  top of this task, as requested.
- Confirm documentation facts about draft behavior and preview invocation
  against the repository’s actual behavior before review; do not rely on
  assumptions or examples alone.

### Additional implementation verification

- Review the final diff to confirm it contains documentation changes only.
