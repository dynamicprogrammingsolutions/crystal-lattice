# Fix Managed Requirements Home-Relative Deny-Read Paths

Make MDM-delivered base64 requirements resolve home-relative deny-read paths consistently with requirements loaded from the filesystem.

## Requirements checklist

- [ ] R1: A `~/...` entry in `permissions.filesystem.deny_read` resolves to the current user's home directory when requirements are delivered through `requirements_toml_base64`.
- [ ] R2: Equivalent home-relative requirements produce equivalent resolved deny-read paths through MDM base64 and filesystem delivery.
- [ ] R3: Existing absolute-path behavior remains unchanged.
- [ ] R4: Existing ordinary relative-path behavior remains unchanged for each delivery path.
- [ ] R5: Existing glob and malformed-input behavior remains unchanged.

## Context

The repository is pinned to a revision where filesystem requirements already resolve home-relative paths, while the macOS managed-preferences base64 path does not. Inspect the managed requirements loader, the shared path-resolution behavior, and existing regression tests before choosing the change boundary.

For R4, preserve the current distinction between delivery paths: filesystem-delivered relative paths continue to resolve against the requirements file's parent, while MDM-delivered ordinary relative paths remain rejected.
