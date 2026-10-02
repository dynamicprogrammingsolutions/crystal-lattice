# Embedded workspace settings

This feature plugin contributes the per-session `working_directory` control
used by the embedded mobile runtime.

The configured `workspace_root` is the fixed boundary. The UI lists the root
and existing descendant directories with workspace-relative labels. It does
not provide arbitrary filesystem paths, directory creation, or iOS
Files/iCloud access.

Containment is also enforced by `AgentApplication` when session overrides are
patched and by the embedded tool packages when paths are resolved. The UI is
therefore not the security boundary.