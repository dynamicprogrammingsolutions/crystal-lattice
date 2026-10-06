# Select an agent

Creating a session and switching an existing session use the same agent
selection window.

The left pane lists configured agents in their display order. Each row can
show:

- a user-facing title;
- a short description;
- the stable configuration ID.

The right pane previews the selected agent's defaults before the operation is
submitted. Provider, extension, feature, and tool groups are always listed;
the Tools group starts expanded. Entries distinguish enabled defaults,
disabled catalog entries, and enabled plugins that are inactive for the
agent's current base configuration.

The preview is read-only. Session-specific plugin choices are still managed
from the Session plugins window after a session exists.

Choosing **Create** or **Switch** always submits the stable agent ID, not its
display title. If the connected server predates the preview API or the preview
cannot be loaded, agent selection remains available and the window explains
that only the optional defaults preview is unavailable.