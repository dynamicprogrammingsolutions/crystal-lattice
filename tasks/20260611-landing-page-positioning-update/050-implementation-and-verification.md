# Implementation And Verification

Implement the approved landing page copy and minimal component changes, then verify the site builds and reads accurately.

## Requirements checklist

- [ ] Apply the approved copy changes from the parent task and subtasks.
- [ ] Compare implemented content against `tasks/20260611-landing-page-positioning-update/desired-final-content/`.
- [ ] Add new section definitions/components where the desired YAML section types require them.
- [ ] Keep long structured content in Markdown sources where the desired content draft does so.
- [ ] Keep changes minimal and avoid redesigning the page.
- [ ] Preserve the current Astro content-driven structure where possible.
- [ ] Avoid broad unverified claims about store availability, licensing, provider switching, and feature completeness.
- [ ] Run `yarn build` from `landing_page`.
- [ ] Do a quick visual review in desktop and mobile viewport sizes.
- [ ] Report any remaining placeholders, missing screenshots, or claims needing maintainer confirmation.

Parent Task: `tasks/20260611-landing-page-positioning-update/000-main.md`
Depends On: `tasks/20260611-landing-page-positioning-update/010-claim-safety-and-current-state-audit.md`, `tasks/20260611-landing-page-positioning-update/020-homepage-structure-and-copy.md`, `tasks/20260611-landing-page-positioning-update/030-mobile-connectivity-and-store-links.md`, `tasks/20260611-landing-page-positioning-update/040-plugin-control-and-sdk-action-blocks.md`

## Verification Commands

From:

```text
/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/pr-10-cl-291/landing_page
```

Run:

```bash
yarn build
```

For manual visual review:

```bash
yarn dev
```

Then open the local Astro URL and check:

- Homepage desktop width.
- Homepage mobile width.
- Mobile page desktop width.
- Mobile page mobile width.
- Store buttons do not look like live downloads if links are coming soon.
- Long code snippets do not overflow awkwardly.
- Bridge section does not use localhost as the public bridge example.
- Desktop app wording does not imply a different device.
- HTTP/API wording does not call HTTP a client.

## Suggested Completion Notes Template

When completing the task, append:

```md
## Completion Notes

Added during completion.

- Updated hero and feature copy to lead with start-on-computer/continue-on-phone positioning.
- Adjusted mobile availability and connectivity claims.
- Added plugin/control and Python automation action blocks.
- Verified with `yarn build`.
- Remaining follow-up: [screenshots, store links, docs URL, SDK snippet confirmation, etc.]
```
