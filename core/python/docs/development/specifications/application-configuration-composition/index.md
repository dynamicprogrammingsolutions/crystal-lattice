# Application configuration composition

This specification defines the target configuration-composition behavior owned
by `core/python/agent_app`.

It covers:

- existing reusable configuration mixins;
- one shared shallow/deep merge contract;
- recursive parent-scoped `$merge` policies;
- model- and config-selected `$variants`;
- exact and regular-expression conditions;
- effective-config and override precedence;
- validation, protected topology, and compatibility;
- consumer documentation responsibilities.

It does not define provider wire protocols, provider model capabilities,
plugin-specific request options, or arbitrary configuration expressions.

Specification documents:

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)

Decision record:

- [Configuration-language and merge policy](decisions/001-configuration-language-and-merge-policy.md)

Current consumer documentation:

- [Application configuration](../../../../../../application/python/docs/configuration.md)

Active delivery work:

- `tasks/20260824-direct-claude-provider-and-plugin-login/021-application-config-variants-and-recursive-merge.md`