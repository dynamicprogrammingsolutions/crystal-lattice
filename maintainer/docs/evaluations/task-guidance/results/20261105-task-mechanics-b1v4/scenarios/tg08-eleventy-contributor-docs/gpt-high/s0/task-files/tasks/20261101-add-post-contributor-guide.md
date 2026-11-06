# Add a post-writing guide to `CONTRIBUTING.md`

Write a contributor guide section that helps new contributors add and preview a post.

## Requirements checklist

- [ ] Add a section to `CONTRIBUTING.md` explaining how to create a post file.
- [ ] Document the required post front matter fields: `title`, `date`, `description`, and `tags`.
- [ ] Explain how drafts work, based on verified current site behavior.
- [ ] Explain how to preview the site locally, using commands that work in this repository.
- [ ] A maintainer reviews the section against this checklist and accepts it.
- [ ] Make no product behavior changes.

## Supporting details

- Post source files are under `content/posts/`; the existing examples are `content/posts/first.md` and `content/posts/second.md`.
- The examples currently show `title`, `date`, and `tags`, but not `description`.
- `package.json` defines `build` and `test` scripts; it does not define a local preview script.
- The inspected post examples and configuration do not establish draft behavior. Verify the current behavior before documenting it; do not imply unsupported functionality.