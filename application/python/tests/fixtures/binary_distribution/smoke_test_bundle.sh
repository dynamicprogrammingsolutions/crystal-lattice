#!/usr/bin/env bash
set -euo pipefail

archive_path="${1:?usage: smoke_test_bundle.sh <archive.tar.gz>}"
workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT

tar -xzf "$archive_path" -C "$workdir"
bundle_dir="$(find "$workdir" -mindepth 1 -maxdepth 1 -type d | head -n 1)"

test -n "$bundle_dir"
test -x "$bundle_dir/crystal-lattice"
test -f "$bundle_dir/_internal/agent_terminal_app/runtime_layout.json"
test -f "$bundle_dir/_internal/agent_terminal_app/default_config/config.json"
test -f "$bundle_dir/_internal/bundled_plugins/openrouter/agent_plugin.json"
test -f "$bundle_dir/_internal/bundled_plugins/codex-tools/agent_plugin.json"
test -f "$bundle_dir/_internal/bundled_plugins/feature-system-message/agent_plugin.json"
test -f "$bundle_dir/_internal/bundled_plugins/cloud-agent-app/docs/cloud-script-authoring.md"
test -f "$bundle_dir/_internal/cloud_runtime/Dockerfile"
test -f "$bundle_dir/_internal/cloud_runtime/runtime.py"
test -d "$bundle_dir/_internal/cloud_runtime/python_lib/agent_core"
test -d "$bundle_dir/_internal/cloud_runtime/python_lib/agent_app"
test -d "$bundle_dir/_internal/cloud_runtime/python_lib/agent_terminal_app"
test -d "$bundle_dir/_internal/cloud_runtime/plugins/cloud-agent-app"
test ! -e "$bundle_dir/_internal/agent_terminal_app/default_config/auth"
test ! -e "$bundle_dir/_internal/agent_terminal_app/default_config/.plugin_cache"

"$bundle_dir/crystal-lattice" --help >/tmp/crystal-lattice-help.txt
"$bundle_dir/crystal-lattice" --runtime-layout-json >/tmp/crystal-lattice-layout.json

grep -q '"layout": "bundled"' /tmp/crystal-lattice-layout.json
grep -q '"BUILTIN_PLUGINS":' /tmp/crystal-lattice-layout.json
grep -q '/_internal/bundled_plugins' /tmp/crystal-lattice-layout.json
grep -q '/_internal/cloud_runtime' /tmp/crystal-lattice-layout.json

echo "bundle smoke test passed: $bundle_dir"