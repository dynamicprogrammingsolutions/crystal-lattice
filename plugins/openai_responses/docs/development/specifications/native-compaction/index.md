# Native conversation compaction

This specification defines native conversation compaction owned by the
`openai_responses` plugin package.

It covers:

- selection of the API or ChatGPT compaction protocol;
- the legacy API compact endpoint, retained as the API-key protocol;
- ChatGPT remote compaction v2 over the normal Responses endpoint;
- full and prefix compaction;
- compacted native-history construction and visible transcript projection;
- background execution, cancellation, conflict handling, and failure behavior;
- compatibility with existing configuration and compacted sessions.

It does not redefine general OpenAI Responses request handling, ChatGPT login,
session persistence, or application notification contracts. It applies those
package and framework capabilities to native compaction.

Artifacts:

- [Product specification](product-spec.md)
- [Technical specification](technical-spec.md)
- [Requirements and evidence](requirements.md)

Current package-user configuration and operation are documented in the
[OpenAI Responses README](../../../../README.md#native-compaction).