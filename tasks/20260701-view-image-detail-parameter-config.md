# Add configurable view_image detail parameter

Expose the `view_image.detail` input parameter by default so users can request original-resolution image processing, while allowing it to be disabled with a config key for older or incompatible models.

## Requirements checklist

- [ ] Make the `detail` input parameter available by default in the `view_image` schema.
- [ ] Add or reuse a config key that disables the `detail` parameter when set.
- [ ] Preserve support for only the documented `detail` value: `"original"`.
- [ ] Treat omitted or `null` detail as default resized/high behavior.
- [ ] Ensure disabled detail support rejects or hides `"original"` consistently.
- [ ] Add/update unit tests for default-enabled, disabled, invalid value, omitted, and null behavior.
- [ ] Update documentation to describe the default and the disable key.

## Context

Upstream Codex exposes `view_image.detail` based on model capability. The current project has a config-driven implementation:

- `plugins/codex-tools/src/codex_tools/view_image_tool.py:215` currently does:

```python
include_detail = bool(config.get("enable_view_image_detail_original"))
```

That means `detail` is hidden unless explicitly enabled. The desired behavior is the inverse: assume users use newest models and expose `detail` by default, but allow users to disable it.

## Codex CLI research

In upstream Codex:

- `ViewImageToolOptions.can_request_original_image_detail` controls whether the schema includes `detail`: `../codex/codex-rs/tools/src/view_image.rs:14`.
- The `detail` parameter is optional and only supports `"original"`: `../codex/codex-rs/core/src/tools/handlers/view_image.rs:75`.
- If original detail is requested and supported, Codex uses `ImageDetail::Original`; otherwise it uses the default image detail: `../codex/codex-rs/core/src/tools/handlers/view_image.rs:129`.

The requested local behavior does not need full upstream capability detection. It should be config driven with a default of enabled.

## Local code references

- `plugins/codex-tools/src/codex_tools/view_image_tool.py:64` defines `DETAIL_DESCRIPTION`.
- `plugins/codex-tools/src/codex_tools/view_image_tool.py:75` builds the parameter schema and includes `detail` only when `include_detail=True`.
- `plugins/codex-tools/src/codex_tools/view_image_tool.py:215` reads the current opt-in config.
- `plugins/codex-tools/src/codex_tools/view_image_tool.py:260` rejects invalid detail values.
- `plugins/codex-tools/src/codex_tools/view_image_tool.py:269` currently rejects `"original"` when `enable_view_image_detail_original` is not set.
- `plugins/codex-tools/tests/test_view_image_tool.py` already has schema/detail tests to update.

## Expected implementation direction

Use a config key with default enabled. A backward-compatible option is:

```python
enable_detail = config.get("enable_view_image_detail_original", True)
```

However, because the old key name sounds like an opt-in, consider adding a clearer disabling key such as:

```python
disable_view_image_detail_original
```

Recommended behavior:

- If `disable_view_image_detail_original` is true, hide `detail` from the schema and reject `detail="original"`.
- Otherwise, include `detail` in the schema by default and allow `detail="original"`.
- If the old `enable_view_image_detail_original` key exists, decide whether to preserve compatibility:
  - `False` should disable detail.
  - `True` should enable detail.
  - If absent, detail is enabled.

One possible resolver:

```python
def _detail_original_enabled(config: Dict[str, Any]) -> bool:
    if config.get("disable_view_image_detail_original") is True:
        return False
    if "enable_view_image_detail_original" in config:
        return bool(config.get("enable_view_image_detail_original"))
    return True
```

Use this resolver in both schema generation and execution validation so exposed schema and runtime behavior stay aligned.

## Testing expectations

Update or add unit tests in `plugins/codex-tools/tests/test_view_image_tool.py`:

- Default schema includes `detail`.
- `disable_view_image_detail_original=True` hides `detail`.
- Legacy `enable_view_image_detail_original=False` hides `detail`, if compatibility is implemented.
- `detail="original"` works by default.
- `detail="original"` is rejected when disabled.
- `detail="low"` is rejected.
- Omitted detail succeeds with default detail.
- `detail=None` is treated like omitted, if the current call payload path can pass null through.

Run:

```bash
pytest plugins/codex-tools/tests/test_view_image_tool.py -q
```

If schema behavior affects default app config, also run the existing view-image integration tests selectively after task `tasks/20260701-correct-view-image-output-schema.md` is complete.

## Documentation

Update `plugins/codex-tools/README.md` to explain:

- `detail` is available by default.
- The only supported value is `"original"`.
- Omit `detail` for default resized behavior.
- The config key to disable original-detail support.