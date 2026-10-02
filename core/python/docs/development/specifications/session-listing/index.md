# Application session listing

This specification defines the application-layer session-list contract owned
by `core/python/agent_app`.

It covers:

- opaque live-session discovery and exact summary lookup;
- shared summary, presentation, ordering, filtering, and diagnostic behavior;
- application-plugin contributions to session summaries;
- summary validity and invalidation;
- complete membership when some session contents are slow or unavailable;
- cross-runtime reuse of derived summaries;
- bounded foreground full resolution after file-attribute enumeration;
- private background resolution, persistence, concurrency, and lifecycle
  behavior;
- implementation independence behind `SessionListService`.

It does not define frontend list rendering, frontend refresh behavior, the
Sessions action menu, session snapshot listing, or generic application
configuration composition.

Specification documents:

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)

Decision record:

- [Service boundary and implementation independence](decisions/001-service-boundary-and-implementation-independence.md)

Related specifications:

- [Application configuration composition](../application-configuration-composition/index.md)
- [Session and message data query](../../../../../../application/python/docs/development/specifications/session-data-query/index.md)
- [Application runtime reload](../../../../../../docs/development/specifications/application-runtime-reload/index.md)
- [Sessions actions](../../../../../../docs/development/specifications/sessions-actions/index.md)

Current consumer documentation:

- [Application plugins](../../../../../../plugins/docs/application-plugins.md)
- [Plugin actions](../../../../../../plugins/docs/actions.md)
- [Plugin UI elements](../../../../../../plugins/docs/ui-elements.md)