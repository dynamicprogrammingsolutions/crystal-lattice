# Reviewed target — tg01-eleventy-archive-handoff

**Eleventy archive pagination handoff** — Preserve a reviewed cohesive archive-pagination plan in a durable task handoff.

Category: handoff · Project: `Eleventy Base Blog` · Acceptable partition sizes: 1

**Approved outcomes**

- ARCHIVE-1: `/blog/` remains the first page and later pages have stable approved URLs.
- ARCHIVE-2: Every archive page contains no more than twenty posts.
- ARCHIVE-3: Posts remain newest-first and appear exactly once across archive pages.
- ARCHIVE-4: Accessible previous and next navigation appears only when its destination exists.
- ARCHIVE-5: Home, tags, feed, sitemap, and individual-post navigation retain current behavior.
- ARCHIVE-6: Archive output remains statically generated without client-side JavaScript.

**Coherent deliverables**

- **ARCHIVE-DELIVERY** — Deliver archive pagination
  All outcomes form one accepted archive capability; no implementation layer is useful as a separate delivery.
  - Outcomes: ARCHIVE-1, ARCHIVE-2, ARCHIVE-3, ARCHIVE-4, ARCHIVE-5, ARCHIVE-6

**Important crossings**

- Production Eleventy configuration and templates generate and expose the expected public archive output.

**Acceptable alternatives**

- The task may group protected generated surfaces into one compatibility requirement.
- The task may leave the exact later-page URL pattern as an approval question.

**Fragmentation examples**

- Archive configuration, templates, generated-output tests, and documentation are phases of one delivery.

**Open questions**

- The later-page URL pattern and exact navigation presentation require approval if not already decided.

**Handoff expectations**

- fresh agent plan: A fresh agent can reconstruct the complete generated-output plan without broad site rediscovery.
- omit plan: Preserve outcomes, project facts, source pointers, protected surfaces, and unresolved public decisions without plan steps.
- retain plan: Preserve the reviewed implementation and verification approach as a Draft plan.

**Plan content requirements**

- PLAN-1: The pagination URL design: `/blog/` as page one and the stable later-page URL pattern, with the approval status of that pattern stated — recommended versus decided — rather than silently chosen. (from ARCHIVE-1)
- PLAN-2: The mechanism keeping every archive page at or under twenty posts while each post appears exactly once across pages. (from ARCHIVE-2, ARCHIVE-3)
- PLAN-3: How pagination preserves the newest-first ordering of posts. (from ARCHIVE-3)
- PLAN-4: Conditional previous/next navigation: what 'its destination exists' means and how the navigation stays accessible. (from ARCHIVE-4)
- PLAN-5: Why home, tags, feed, sitemap, and individual-post surfaces keep their current behavior — the change stays scoped to the archive. (from ARCHIVE-5)
- PLAN-6: That the archive output stays statically generated without client-side JavaScript, and how the approach preserves it. (from ARCHIVE-6)
- PLAN-7: The verification approach names the production Eleventy build over a multi-page fixture as the decisive check of pagination correctness.
