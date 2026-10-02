# Packaging & loading plugins

This page documents the recommended way to package plugin repos (providers, extensions, features, tools) and how applications load them.

It is shared across plugin kinds.

Substantial provider bundles should also follow the
[provider package and documentation standard](provider-implementation-standard/package-and-documentation.md).

## Recommended repo layout (Python)

Minimal layout:

```text
my-provider/
  pyproject.toml
  agent_plugin.json
  src/
    my_provider/
      __init__.py
      provider.py
  tests/
    test_provider_smoke.py
  README.md
```

Use `src/` layout and make your project pip-installable.

## `agent_plugin.json` (descriptor)

When loading a plugin repo via `path:...` or `git+...`, the application layer reads `agent_plugin.json` from the installed plugin directory.

Minimal schema:

```json
{
  "entries": [
    "my_provider.provider.MyProvider",
    "my_provider.extension.MyExtension",
    "my_provider.feature.MyFeature"
  ],
  "subdirectory": "."
}
```

Notes:

- `entries` is required.
- `subdirectory` is optional (useful for monorepos).
- A `kinds` map is optional; the application can also classify plugins by duck-typing.
- `local_workspace_dependencies` is optional; use it for sibling local Python
  packages in the same workspace.

Runtime reference: `core/python/agent_app/plugin_sources/descriptor.py`.

### Local workspace dependencies

Some local path plugin repos depend on sibling local packages in the same
workspace, for example a tool plugin depending on `../tool-compat-shared`.
Declare those packages explicitly in `agent_plugin.json`:

```json
{
  "entries": [
    "my_tools.my_tool.MyTool"
  ],
  "local_workspace_dependencies": [
    {
      "name": "tool-compat-shared",
      "path": "../tool-compat-shared"
    }
  ]
}
```

Rules:

- `name` is the distribution/project name.
- `path` is resolved relative to the plugin descriptor directory.
- The dependency target must be pip-installable (`pyproject.toml` or `setup.py`).
- Declared local workspace dependencies are fingerprinted with the parent
  plugin, so a sibling dependency change invalidates the parent plugin cache
  entry.
- The loader installs declared local workspace dependencies explicitly and keeps
  normal pip cache behavior enabled.

If a plugin package declares sibling `file://` dependencies in packaging
metadata, it must also declare them in `local_workspace_dependencies`. This
keeps local plugin cache invalidation explicit and avoids core hardcoding
workspace package names.

Release and cloud-runtime bundles also use this metadata. In the full
bundled-Python package, the default-config plugin closure is installed into the
packaged Python runtime and recorded in the package-owned
`preinstalled-plugins.json` manifest. The visible copied plugin source
descriptors remain unchanged, so copied/forked plugins behave like normal local
path plugins outside the installed package. Optimized PyInstaller and cloud
runtime images still use selected preinstalled descriptor/resource metadata
with `"preinstalled": true`. The cloud runtime Docker build uses declared local
workspace dependencies to copy the selected source closure into the build
stage, create Linux-compatible wheels, and install them into the final image.
At runtime, `path:${env:BUILTIN_PLUGINS}/<plugin>` should not trigger a plugin
cache install for those bundled/default plugins.

## Installing `agent_plugin.json` as a data file

If using setuptools via `pyproject.toml`:

```toml
[tool.setuptools.data-files]
"" = ["agent_plugin.json"]
```

Or with `setup.py`:

```python
from setuptools import setup

setup(
    name="my-provider",
    packages=["my_provider"],
    data_files=[("", ["agent_plugin.json"])],
)
```

## Application config: plugin spec forms

Applications support multiple ways to reference plugins:

### 1) Dotted class path (no install)

```json
{
  "plugins": ["plugins.openai_provider.OpenAICompatibleProvider"]
}
```

### 2) Local repo (descriptor-driven; recommended)

```json
{
  "plugin_cache_dir": "~/.crystal/cache/plugins",
  "plugins": ["path:/abs/or/rel/to/my-provider-repo"]
}
```

### 3) Git repo (descriptor-driven; recommended)

```json
{
  "plugin_cache_dir": "~/.crystal/cache/plugins",
  "plugin_policy": {"allow_remote": true},
  "plugins": ["git+https://github.com/acme/my-provider.git#v1.0.0"]
}
```

### 4) Verbose object spec (single explicit entry)

```json
{
  "plugin_cache_dir": "~/.crystal/cache/plugins",
  "plugins": [
    {
      "path": "/abs/or/rel/to/repo",
      "entry": "my_provider.provider.MyProvider",
      "subdirectory": "."
    }
  ]
}
```

## Placeholders

- `${env:VAR}` can be embedded anywhere within strings.
- `${file:...}` is supported as a whole-string placeholder only.

## Policy & security notes

- Git installs run arbitrary code via `pip install`.
- Prefer pinned refs (tag/commit) and host allowlists.
- Remote git URLs are typically disabled by default; enable explicitly with `plugin_policy.allow_remote`.
- Python dependency installs reuse completed plugin installations in `plugin_cache_dir`. By default pip's separate download cache is disabled, and any old default `pip` cache is cleared at application startup. If you explicitly set `plugin_policy.pip_cache_dir` or pass pip cache options through `pip_args`, that cache stays under your control and is not cleared.
- Each application startup removes unused cached plugin revisions and old abandoned temporary clones/installs. Running applications retain the installations they use through refreshed process leases; on close, those entries become eligible for cleanup at the next startup. The lease records and cache lock live beside `plugin_cache_dir`.
- **When upgrading to the version with startup cleanup:** stop or restart every older agent runtime that uses the same `plugin_cache_dir` *before the first startup of the new version against that cache*. Older runtimes do not publish leases and their files may be reclaimed. A current session needs a restart only if its runtime uses that same cache; projects using separate cache directories do not need a coordinated restart. A previously created pip download cache is also removed at that first startup.
- The bundled-Python runtime package is the supported distribution for
  plugin-rich installs. It uses a normal packaged Python interpreter for
  dynamic plugin installation. PyInstaller/frozen artifacts are
  config-specific optimized outputs and do not support arbitrary dynamic plugin
  installation by default.
- In runtimes that support dynamic plugin installation, set
  `CRYSTAL_PLUGIN_PYTHON` or `plugin_policy.python_executable` to choose the
  interpreter used for `python -m pip install --target ...`.

## Reference configs

See application examples:

- `application/python/agent_terminal_app/config_echo_app.json`
- `application/python/agent_terminal_app/default_config/config.json`
