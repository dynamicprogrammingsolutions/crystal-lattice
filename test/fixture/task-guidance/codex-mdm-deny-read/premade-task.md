# Fix Managed Requirements Home-Relative Deny-Read Paths

Make MDM-delivered base64 requirements resolve home-relative deny-read paths consistently with requirements loaded from the filesystem.

## Requirements checklist

- [ ] A `~/...` entry in `permissions.filesystem.deny_read` resolves to the current user's home directory when requirements are delivered through `requirements_toml_base64`.
- [ ] The same requirements content produces equivalent resolved deny-read paths through MDM base64 and filesystem delivery.
- [ ] Existing absolute-path, relative-path, glob, and malformed-input behavior remains supported.

## Context

The repository is pinned to a revision where filesystem requirements already resolve home-relative paths, while the macOS managed-preferences base64 path does not. Inspect the managed requirements loader, the shared path-resolution behavior, and existing regression tests before choosing the change boundary.
