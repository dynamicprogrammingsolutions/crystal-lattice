#!/usr/bin/env bash

create_cloud_orchestrator_source_bundle() {
  local output_path="$1"
  local repo_dir="$2"

  COPYFILE_DISABLE=1 tar \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude '.pytest_cache' \
    --exclude '.mypy_cache' \
    --exclude '.ruff_cache' \
    --exclude '.coverage' \
    --exclude '.DS_Store' \
    --exclude '_build' \
    --exclude 'deps' \
    --exclude '.elixir_ls' \
    --exclude '.data' \
    --exclude '.plugin_cache' \
    --exclude 'node_modules' \
    --exclude '.venv' \
    --exclude 'logs' \
    --exclude 'sessions' \
    -czf "$output_path" \
    -C "$repo_dir" \
    cloud-orchestrator \
    core/python \
    application/python \
    plugins \
    scripts/build_cloud_runtime_plugin_bundle.py
}