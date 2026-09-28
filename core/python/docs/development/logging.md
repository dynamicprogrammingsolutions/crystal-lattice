# Core Python logging

The Core SDK uses
[structlog](https://www.structlog.org/) for structured diagnostic output.
Applications can call `agent_core.utils.configure_logging` directly, while
Core loggers configure themselves on first use when the application has not
already done so.

## Enable and filter logs

Set environment variables before starting an application or test:

```bash
LOG_LEVEL=DEBUG pytest core/python/tests/test_core.py
LOG_LEVEL=DEBUG LOG_SCOPE=provider pytest core/python/tests/test_core.py
LOG_LEVEL=DEBUG LOG_DATA="chunk,partials" python your_app.py
LOG_LEVEL=DEBUG LOG_FILTER="messages[0].role:equals:system" python your_app.py
LOG_LEVEL=DEBUG LOG_POS=true python your_app.py
```

The first positional argument to `logger.debug`, `logger.info`, and related
structlog methods is already the `event` field. Do not also pass an `event=`
keyword:

```python
# Correct
logger.debug("message received", event_type="partial")

# Raises TypeError because event is supplied twice
logger.debug("message received", event="partial")
```

## Environment variables

| Variable | Meaning | Default |
|---|---|---|
| `LOG_LEVEL` | Minimum level such as `DEBUG`, `INFO`, `WARNING`, or `ERROR` | `INFO` |
| `LOG_SCOPE` | Case-insensitive substring filter for the bound logger name | all scopes |
| `LOG_DATA` | Comma-separated whitelist of extra fields | all fields |
| `LOG_FILTER` | Comma-separated field conditions; every condition must match | no conditions |
| `LOG_POS` | Add a repository-relative `file:line` position when truthy | disabled |
| `LOG_COLORS` | Explicitly enable or disable ANSI colors | enabled |
| `LOG_FILE` | Append output to this file instead of standard output | standard output |

`configure_logging(colors=..., log_file_path=...)` can override color and file
settings. An explicit `log_file_path` takes precedence over `LOG_FILE`.

## Select output fields

`LOG_DATA` controls extra structured fields while retaining `event`,
`timestamp`, `level`, and `logger`:

```bash
# Variable absent: retain every field
LOG_LEVEL=DEBUG python your_app.py

# Empty value: retain only the standard fields
LOG_LEVEL=DEBUG LOG_DATA="" python your_app.py

# Retain selected extra fields
LOG_LEVEL=DEBUG LOG_DATA="chunk,partials" python your_app.py
```

Common fields include `chunk`, `partials`, `finals`, `core_partials`,
`messages`, `native_messages`, `final_native`, and `final_core`. A log call may
attach other fields; the whitelist is not a fixed event schema.

## Filter by field values

Each `LOG_FILTER` condition uses a field path followed by a condition:

| Condition | Meaning |
|---|---|
| `field:exists` | The resolved value is not `None` |
| `field:nonempty` | The value is a non-empty string, list, or dictionary |
| `field:equals:value` | The string representation equals `value` |
| `field:contains:text` | The string representation contains `text` |

Paths support dotted lookup and JSONPath-style array indices:

```bash
LOG_FILTER="chunk.reasoning:nonempty" LOG_LEVEL=DEBUG python your_app.py
LOG_FILTER="messages[0].role:equals:system" LOG_LEVEL=DEBUG python your_app.py
LOG_FILTER="chunk:exists,partials:nonempty" LOG_LEVEL=DEBUG python your_app.py
```

Comma-separated conditions use AND semantics.

## Logger scopes

Core commonly binds these logger names:

- `core` for request and session orchestration;
- `provider` for provider-wrapper processing;
- `extension` for provider-extension processing;
- `feature` for feature processing.

`LOG_SCOPE` performs a case-insensitive substring match, so applications and
plugins may use more specific bound names while retaining useful filtering.

## Source positions and files

Enable repository-relative source positions with:

```bash
LOG_POS=true LOG_LEVEL=DEBUG python your_app.py
```

Write logs to a file with:

```bash
LOG_FILE=tmp/core-debug.log LOG_LEVEL=DEBUG python your_app.py
```

If Core cannot open the requested file, it falls back to standard output.