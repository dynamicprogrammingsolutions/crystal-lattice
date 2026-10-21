# Frontend App-Link Routing And Action Resume
If the Codex redirect POC works, add frontend deep-link handling so the app can capture the redirect and resume the login flow by calling the right action on the right connection and session.

SUPERSEDED BY:

- `tasks/20261016-provider-login-experience/010-codex-browser-login-and-method-selection.md`
- `tasks/20261016-provider-login-experience/020-provider-login-notifications-and-anthropic-adoption.md`

## Requirements checklist

- [ ] Define the deep-link or app-link format that the mobile app will receive.
- [ ] Define how the link identifies connection, session, provider, and login attempt without overloading the URL with sensitive data.
- [ ] Add frontend routing and callback handling for the redirect.
- [ ] Define the action contract the frontend should call after receiving the redirect payload.

Parent Task: `tasks/20260605-mobile-oauth-login-flows/000-main.md`
Depends On: `tasks/20260605-mobile-oauth-login-flows/010-codex-mobile-redirect-poc.md`

## Important constraint

This task only makes sense if the POC confirms that a mobile redirect URI is accepted by Codex.

## Product direction from the request

The intended flow is:

1. Browser redirects to an app link.
2. The link carries enough context to identify the target connection and session.
3. The frontend extracts the redirect details and calls an application action.
4. The backend/plugin completes the token exchange and persists credentials.

## Current repo starting points

Likely frontend entry points:

- `mobile/crystal-lattice-control-rn/App.tsx`
- `mobile/crystal-lattice-control-rn/src/ConnectedRoot.tsx`
- `mobile/crystal-lattice-control-rn/src/ConnectionScreen.tsx`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

Backend/action starting points:

- `plugins/chatgpt-auth-app/src/chatgpt_auth_app/__init__.py`
- `application/python/agent_terminal_app/server.py`

## Questions to answer

- Should the app link contain:
  - connection id
  - session id
  - plugin/action id
  - opaque login attempt id
  - the full provider redirect URL
- Which parts should instead live server-side in plugin state keyed by a login attempt id?
- How should the frontend behave if the app is opened while disconnected from the target backend?
- Should the app link resume immediately, or land the user on a confirmation screen that then calls the action?

## Expected output

- Implementation-ready deep-link payload design.
- Frontend routing plan.
- Backend action-resume contract for the post-redirect completion step.