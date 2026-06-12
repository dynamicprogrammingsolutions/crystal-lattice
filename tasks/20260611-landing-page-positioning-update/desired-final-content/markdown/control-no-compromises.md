Serious users eventually disagree with the defaults. In Crystal Lattice, a setting can exist because a plugin exposes it, and that plugin can be replaced.

For many workflows, high-level control is enough: expose the request options you care about, let the UI render them in settings, and keep working. Power users can still replace the lower-level plugin that defines how those options map into the request.

Example shape:

```json
{
  "request_options": {
    "temperature": 0.6,
    "top_p": 0.95,
    "think": true,
    "stream_options": {
      "include_usage": true
    }
  },
  "request_options_ui": {
    "temperature": "number",
    "top_p": "number",
    "seed": "number"
  }
}
```

The important part is the pattern: high-level settings can become real UI controls, while the low-level behavior remains plugin-defined and replaceable. The app does not need to hardcode every possible request option ahead of time.
