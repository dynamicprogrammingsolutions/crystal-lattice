# Linked Readonly Session UX
Add metadata-driven linking between a local readonly session and its cloud counterpart, so the UI can resolve and open the cloud session without storing long-lived credentials directly in session metadata.

## Requirements checklist

- [ ] Define a session metadata convention for cloud-linked sessions.
- [ ] Mark transferred local sessions readonly when they are represented by a cloud session.
- [ ] Store remote-link metadata with instance/session identifiers and a resolver action reference.
- [ ] Add an action convention, likely `cloud.resolve_connection`, that returns fresh connection details and token.
- [ ] Let mobile/frontend open the linked cloud session by calling the resolver action.
- [ ] Keep plugin-provided badges/tags possible, while native UI owns the metadata-driven link behavior.

Parent Task: `tasks/20260429-cloud-agent-orchestrator/000-main.md`
Depends On: `tasks/20260429-cloud-agent-orchestrator/0100-remote-docker-orchestrator-mvp.md`

## Metadata Direction

Example metadata shape:

```json
{
  "readonly": true,
  "remote_link": {
    "kind": "cloud_session",
    "label": "Cloud agent",
    "orchestrator_url": "https://cloud.example.com",
    "instance_id": "cloud-inst-123",
    "remote_session_id": "session-cloud-456",
    "resolve_action": {
      "plugin": "cloud",
      "action_id": "cloud.resolve_connection"
    }
  }
}
```

Session metadata should not contain long-lived connection secrets. The UI should call the resolver action to obtain current connection details, including a token.

## High-Level Behaviors To Test Before Acceptance

- A transferred local session is readonly and includes valid cloud-link metadata.
- The linked cloud session can be opened after resolving fresh connection details.
- Expired/missing tokens are handled by re-running the resolver action.
- The UI still renders ordinary readonly sessions correctly when no cloud link exists.
- Plugin-provided session tags/badges can coexist with native linked-session handling.