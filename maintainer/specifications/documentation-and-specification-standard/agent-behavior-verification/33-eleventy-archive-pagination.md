# Test 33: Eleventy archive-pagination requirement quality

Requirement coverage: `DOCGUIDE-005`–`DOCGUIDE-006`, `DOCVAL-010`,
`DOCVAL-011`

## Source project

- Project: Eleventy Base Blog, a static zero-JavaScript blog starter.
- Upstream: `https://github.com/11ty/eleventy-base-blog`
- Pinned revision: `26b26106d7fbb30b7b40d9ef52589d10ddbcb462`
- License: MIT

## Project context

The project generates a public blog with a home page, complete archive, tag
pages, feed, sitemap, and previous/next links between individual posts.
`content/blog.njk` currently renders every post through the shared
`_includes/postslist.njk` component. The home page independently shows the
latest three posts, and tag pages already use Eleventy pagination.

## Exact user prompt

> Please inspect this Eleventy blog project. Blogs with several thousand posts
> produce an unmanageably large archive page. Prepare a specification and
> requirements for paginating the public archive into 20 posts per page. The
> first archive page must keep the existing `/blog/` address, later pages need
> stable addresses, and readers need accessible previous and next navigation.
> Preserve newest-first ordering and ensure every post appears exactly once.
> The home page, tag pages, feed, sitemap, and individual-post navigation must
> keep their current behavior. Preserve static zero-JavaScript output. Do not
> implement the change or update current user documentation.

## Exact task-file user prompt

> Please inspect this Eleventy blog project. Blogs with several thousand posts
> produce an unmanageably large archive page. Paginate the public archive into
> 20 posts per page. The first archive page must keep the existing `/blog/`
> address, later pages need stable addresses, and readers need accessible
> previous and next navigation. Preserve newest-first ordering and ensure every
> post appears exactly once. The home page, tag pages, feed, sitemap, and
> individual-post navigation must keep their current behavior. Preserve static
> zero-JavaScript output. Create one task file with a Draft execution plan for
> this change. Do not implement the change.

## Fixture facts

- The archive passes `collections.posts` to the shared post-list template.
- The post-list template reverses the collection to display newest first.
- The home page selects the latest three posts separately.
- Tag pages generate one page per tag using Eleventy pagination.
- Feed, sitemap, and individual-post previous/next navigation are separate.
- No archive-pagination specification exists.
- `TASKS-v7` is not injected for the initial specification baseline.

## Desired target

The evaluator-only target is
[`targets/33-eleventy-archive-pagination.json`](targets/33-eleventy-archive-pagination.json).
Producing models do not receive it.

## Producer controls

- Start from a fresh fixture with no model-generated seed.
- Inject the requirement-minimal guidance variant.
- Permit changes only under `docs/development/`.
- Do not assert exact requirement wording, count, heading, or file shape.

## Task-file producer controls

- Reuse the same fixture, product outcomes, producers, and efforts.
- Inject the maintained general documentation guidance and effective current
  `TASKS-v7`.
- Request one task file with a Draft plan without separately requesting a
  testing strategy.
- Permit creation of one Markdown task file under `tasks/` only.
- Assess requirement and testing-plan quality from the same output.

## Semantic assessment

Compare the generated requirements with the target for archive URLs, page
size, post coverage/order, navigation, unaffected generated surfaces, and
static output. Identify missing outcomes and additional product, SEO,
JavaScript, search, styling, or build-system scope.

## Human review

The interpreted baseline summarizes material omissions and additions by model
and effort. Complete generated specification and requirement files remain
optional detail.