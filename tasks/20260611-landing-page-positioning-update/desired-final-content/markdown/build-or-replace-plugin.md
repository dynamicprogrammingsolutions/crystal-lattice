Your workflow does not need to be accepted upstream to exist. Ask an agent to inspect the plugin docs, choose the right plugin type, and draft a plan.

```text
I want to build a Crystal Lattice plugin.

Please inspect the plugin documentation in this repository, especially:
- plugins/docs/index.md
- plugins/docs/tool-plugins.md
- plugins/docs/application-plugins.md
- plugins/docs/provider-plugins.md
- plugins/docs/provider-extensions.md
- plugins/docs/ui-elements.md
- plugins/docs/plugin-packaging-and-loading.md

Goal:
Create a plugin that [describe what I want].

Please:
1. Identify whether this should be a provider, provider extension, feature, tool, or application plugin.
2. Find the closest existing plugin to copy from.
3. Explain what UI, if any, the plugin should expose.
4. Propose the file layout.
5. Draft an implementation plan.
6. Tell me what tests should be added before coding.
```

Then point config at the plugin:

```json
{
  "plugins": [
    "path:./plugins/my-custom-plugin"
  ]
}
```
