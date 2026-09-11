# Settings and UI schema synchronization

Avoid duplicate first-load work and avoid recomputing or retransferring settings and UI schemas during reloads when their dependencies have not changed.

## Requirements checklist

- [ ] **UISYNC-001** Initial chat activation does not issue duplicate requests for the same session UI schema or application UI schema.
- [ ] **UISYNC-002** The complete settings controller is not eagerly loaded solely because a chat tab is active when its data is not needed by the visible UI.
- [ ] **UISYNC-003** Static config schema, base config, session setting values, session UI schema, and application UI schema have separately defined dependency and invalidation boundaries.
- [ ] **UISYNC-004** The backend exposes stable revision or validator identities for each independently cacheable settings/schema category.
- [ ] **UISYNC-005** The frontend shares cached results and in-flight requests across controllers and component remounts for the same connection and validator identity.
- [ ] **UISYNC-006** An ordinary message reload transfers no settings or schema payload when all applicable validators are unchanged.
- [ ] **UISYNC-007** A session override change reloads affected setting values without automatically recomputing unrelated static schemas.
- [ ] **UISYNC-008** Plugin registry, plugin version, server configuration, model/tool catalog, and application-plugin changes invalidate every schema category that depends on them.
- [ ] **UISYNC-009** Dynamic application UI state is separated from static schema, or its broader invalidation behavior is explicitly justified and tested.
- [ ] **UISYNC-010** Connected clients receive a lightweight invalidation/revision signal when backend state changes in a way that requires a refresh.
- [ ] **UISYNC-011** Reconnect, missed-event, and stale-cache scenarios recover through conditional validation such as ETag/`If-None-Match` or an equivalent mechanism.
- [ ] **UISYNC-012** An unchanged conditional request does not recompute the complete schema merely to rediscover its validator.
- [ ] **UISYNC-013** Production frontend integration tests verify first load, ordinary reload, override mutation, backend/plugin invalidation, and reconnect behavior.
- [ ] **UISYNC-014** The shared benchmark reports endpoint count, schema-hook executions, transferred bytes, and total chat activation/reload time before and after the change.

## Scope

In scope:

- Session settings controllers and UI/application-schema controllers in shared frontend code and production mobile/desktop consumers.
- Server/application/core endpoints and caches that produce config schema, base config, overrides, UI schema, and application UI schema.
- Revision identities, invalidation events, conditional requests, cache scope, in-flight request sharing, and optional bootstrap aggregation.
- Tool/provider/application-plugin schema generation costs.

Out of scope:

- Message-history delta transport.
- Canonical session persistence.
- General event transport replacement.

Parent Task: `tasks/20260911-session-performance-and-storage-optimization/000-main.md`

Depends On: `tasks/20260911-session-performance-and-storage-optimization/010-session-growth-and-benchmark-foundation.md`

## Requirement questions

- Which inputs affect each schema category, including hidden dependencies in plugin hooks?
- Can application UI be split into a static schema and a small dynamic state/action response?
- Which validator identities can be global per server build, per agent, per effective config, or per session?
- How are model-list and tool-catalog changes observed and incorporated into validator changes?
- Which event or lightweight status response should carry schema revision changes?
- Is a compound bootstrap endpoint still valuable after shared caches and lazy settings loading remove duplication?
- How should older backends/frontends behave when revision validators are unavailable?

## Research details and suggested direction

Candidate validator categories include:

| Category | Candidate dependencies |
|---|---|
| Config schema | Server build, plugin registry, plugin versions |
| Base config | Agent definition and server configuration |
| Session setting values | Session config/override publication identity |
| Session UI schema | Effective config, enabled plugins, capability tags, models, tool catalog |
| Application UI schema | Application plugins plus declared session/application dependencies |

A revision signal avoids even the bridge round trip when the frontend already knows nothing changed. ETag/conditional GET remains useful as a reconnect and missed-event fallback.

The backend should cache both the schema and its validator. Hashing a freshly recomputed expensive schema on every lightweight check would preserve the same CPU bottleneck.

Current core UI-schema generation retrieves available tools and then obtains prepared tools through a path that can retrieve tool schemas again. The research should determine whether the second retrieval can be eliminated and which plugin hooks are safe to cache.

This task changes frontend/backend invalidation contracts and should have an approved owning or cross-package specification before implementation.