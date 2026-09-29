# Add Tavily Web Search To The Embedded Runtime

Extend the working embedded runtime with one fixed web-search tool using Tavily
for ordinary credentials and an equivalent authenticated proxy for the
reviewer path.

## Requirements checklist

- [ ] The embedded agent exposes one stable `web_search` tool contract.
- [ ] A user can configure a Tavily credential without placing it in agent
  prompts, tool results, or logs.
- [ ] The reviewer path reaches equivalent search behavior through an
  authenticated proxy so the reviewer does not receive the service secret.
- [ ] Search results retain titles, URLs, excerpts, and errors in a provider-
  neutral result shape.
- [ ] A real mobile request combines search with the existing workspace file
  tools and remains testable in foreground/background lifecycle handling.

Parent Task: tasks/20260910-ios-embedded-runtime-poc/000-main.md

Depends On:
tasks/20260910-ios-embedded-runtime-poc/017-openai-responses-reviewer-and-chatgpt-settings.md

## Scope notes

This task should enhance the already working vertical slice rather than
redesign provider or tool architecture. It has no approved execution plan.

The first implementation should use Tavily directly when the user supplies a
key. The reviewer service may expose a small authenticated search proxy with
the same response shape and keep its Tavily key server-side. Detailed
retention, rate-limit, domain-filter, citation, and privacy decisions should
be made when this task is selected.

Email, crawling, arbitrary URL fetching, browser automation, and a general
research workflow are not implied by this task.