# Add contributor guidance for publishing posts

Create a focused contributor guide section in the repository root
`CONTRIBUTING.md` so a new contributor can create, draft, and preview a blog
post without changing the Eleventy site behavior.

## Requirements checklist

- [ ] Add a contributor-facing section in `CONTRIBUTING.md` for adding a post.
- [ ] Tell contributors to create a Markdown post file under
      `content/posts/`, including the expected filename/slug convention and a
      short example they can copy.
- [ ] Show the required front matter for every post and explain each required
      field: `title`, `date`, `description`, and `tags`.
- [ ] Explain the repository-supported draft workflow, including how a draft
      is kept out of the published post collections/output and how a
      contributor can still inspect it locally. The guidance must match the
      maintainer-approved behavior and must not imply that an unsupported
      front-matter flag works.
- [ ] Give the exact local preview command, identify the local URL or output
      to inspect, and mention how to stop the preview process.
- [ ] Keep the change documentation-only: do not alter Eleventy templates,
      configuration, package scripts, post processing, or generated output.
- [ ] Obtain maintainer review against every checklist item above; that review
      is the acceptance criterion.

## Unresolved requirement questions

- What draft workflow should `CONTRIBUTING.md` describe? The current
  repository has no `draft` or `eleventyExcludeFromCollections` handling in
  its configuration, templates, or post data. Because the request explicitly
  excludes product behavior changes, a maintainer must approve either the
  current limitation and its contributor workflow (for example, keeping
  unfinished work out of the published source until ready) or an existing
  repository convention not visible in this fixture.

## Research and supporting facts

- The Eleventy input directory is `content`; post files are currently stored
  in `content/posts/`.
- `content/posts/posts.json` supplies the post layout and the `posts` tag.
- Existing sample posts use `title`, `date`, and `tags`; they do not currently
  include `description`.
- The current templates render post titles and bodies and do not implement
  draft filtering or description rendering.
- `package.json` defines `npm run build` but no preview script. The guide
  should use the local Eleventy CLI's serve mode and have the maintainer
  verify the exact command in the working dependency installation.
- No root `CONTRIBUTING.md` or `docs/index.md` exists yet. The requested
  contributor-facing guidance belongs in the root `CONTRIBUTING.md`, rather
  than in the development-only documentation.

## Execution plan

Status: Draft

The change will add or extend only the root contributor guide. The section
will use a copyable Markdown/front-matter example, then explain the required
metadata, the approved draft workflow, and the local Eleventy preview path.
It will describe current repository behavior rather than introduce validation,
draft filtering, a new npm script, or template changes.

The draft behavior is the only material documentation decision still open:
the implementation must wait for maintainer confirmation because the current
site has no draft mechanism. The preview command also needs a maintainer
verification run so the guide contains a command that works with the
repository's installed Eleventy version.

### Implementation decisions and open questions

- Keep the guidance in a single root `CONTRIBUTING.md` section; do not create
  a separate contributor-docs hierarchy for this small workflow.
- Treat `title`, `date`, `description`, and `tags` as the documented
  contributor contract even though `description` is not currently rendered.
- Do not document `draft: true` or any other draft flag as functional until a
  maintainer confirms that behavior exists outside the inspected files.
- Resolve the draft question before marking the draft-related requirement
  complete.

### Documentation

- Add the requested post-writing section to `CONTRIBUTING.md`.
- Include a concise front-matter example, file location, draft instructions,
  preview command, local inspection target, and stop command.
- Keep claims limited to behavior verified by the repository or explicitly
  approved by a maintainer.

### Task checklist

- [ ] Resolve the draft-workflow question with a maintainer.
- [ ] Draft the `CONTRIBUTING.md` post workflow and copyable example.
- [ ] Verify the preview command against the local Eleventy installation.
- [ ] Review the guide against the requirements checklist.
- [ ] Confirm the final diff contains documentation only.

### Requirement verification

- Post location and file creation: maintainer review confirms the guide names
  `content/posts/` and gives a usable filename example.
- Front matter: maintainer review confirms all four required fields are shown
  and explained without omitting their expected values or purpose.
- Drafts: maintainer review confirms the text matches the approved workflow
  and does not claim unsupported build behavior.
- Local preview: maintainer runs the documented command and confirms the site
  can be inspected at the documented local target.
- No product behavior changes: review of the final diff confirms only
  `CONTRIBUTING.md` is changed.
- Acceptance: a maintainer reviews every item in the Requirements checklist
  and approves the guide.