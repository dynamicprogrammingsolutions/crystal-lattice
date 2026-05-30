# skill-shared

Shared discovery and parsing helpers for vendor-owned skill integrations.

This package is a library package, not a plugin package. It is responsible for
mechanical skill discovery, filesystem safety, frontmatter parsing, and optional
sidecar YAML loading. Vendor packages own prompt wording, activation rules, and
tool behavior.