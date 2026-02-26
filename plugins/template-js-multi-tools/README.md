# template-js-multi-tools

Template plugin repo for **Node.js / TypeScript tool plugins**.

This is intentionally small and mirrors `plugins/js-multi-tools`:

- `package.json` with an `agent.tools` descriptor
- `src/` TypeScript sources
- No `dist/` checked in (build happens at install/load time)

## Build

```bash
npm install
npm run build
```

## Load

```json
{
  "plugins": [
    { "node_tool": { "path": "plugins/template-js-multi-tools" } }
  ]
}
```
