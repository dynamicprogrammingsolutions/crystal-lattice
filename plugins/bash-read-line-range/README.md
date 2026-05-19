# `read_line_range` (bash tool)

A minimal bash tool plugin that reads a line range from a file using `sed`,
with optional line numbers via `nl`.

This is intended as a simple template for writing new bash tools.

## Load the plugin

In your app config, add the plugin and enable bash tools:

```json
{
  "plugins": [{"bash_tool": {"path": "plugins/bash-read-line-range"}}],
  "plugin_policy": {"allow_bash_tools": true}
}
```

## Tool

- Tool name: `read_line_range`
- Arguments:
  - `path` (string, required)
  - `start_line` (int, required; 1-based, inclusive)
  - `end_line` (int, required; 1-based, inclusive)
  - `show_line_numbers` (bool, optional; default `false`)

## Implementation notes

- Uses `args_mode=positional`.
- When `show_line_numbers=true`, runs `nl -ba <path> | sed -n '<start>,<end>p'`.
- Otherwise runs `sed -n '<start>,<end>p' <path>`.

To create a new tool, copy `read_line_range.bash`, change the `schema` output
(`id`, `tools[0].function.name`, and parameters), then update `run`.

## License

This directory is available under the [Apache License 2.0](../../LICENSE).
