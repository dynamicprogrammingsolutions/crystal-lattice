# Terminal/Server Login And Ownership

Let a user authenticate a local Crystal Lattice server, claim its stable server
ID, and maintain revocable account-bound credentials for hosted-style bridge
registration.

## Requirements checklist

### Functional requirements

- [ ] **P1** — The terminal supports browser/device-code login suitable for
  interactive and headless environments.
- [ ] **P1** — A stable server ID can be claimed by one product account under
  explicit conflict and transfer rules.
- [ ] **P1** — Claimed servers use securely stored, revocable, role-scoped
  credentials to obtain short-lived bridge registration and reconnect grants.
- [ ] **P1** — Logout, unclaim, account deletion, credential revocation, server
  replacement, and ownership transfer have explicit behavior.
- [ ] **P2** — CLI errors distinguish authentication, ownership, entitlement,
  provider, and bridge failures.

### Non-functional requirements

- [ ] **P1** — Server credentials and grants are excluded from ordinary logs,
  diagnostics, and non-secret profile data.

Parent Task: `tasks/20260821-modular-bridge-access-platform/000-main.md`

Depends On:

- `tasks/20260821-modular-bridge-access-platform/080-authentik-client-identity-and-account-linking-contracts.md`
- `tasks/20260821-modular-bridge-access-platform/140-hosted-access-grant-enforcement.md`

## Required reading

- `application/python/agent_terminal_app/bridge_client.py`
- Project profile and CLI configuration code
- Authentik client contracts from Task 080
- Server ownership/access-grant contracts

## Execution plan

Status: Draft

Add terminal login and server-claim commands, persist only revocable
server-scoped credentials, refresh short-lived registration grants, and update
the Python bridge client for authenticated registration over the active
transport/control protocol.

Static-token and local bridge modes continue to work without account login and
remain part of regression verification.

### Implementation decisions and open questions

- Device authorization is the default headless flow.
- A server never stores the user's mobile refresh token.
- Ownership transfer requires explicit authenticated confirmation; silent
  takeover by server ID is prohibited.

### Documentation

- Document login, claim, status, logout/unclaim, headless use, secure storage,
  recovery, and local/static-token alternatives.

### Task checklist

- [ ] Add login/status/logout and claim/unclaim CLI operations.
- [ ] Add server credential storage and refresh.
- [ ] Authenticate bridge registration and reconnect.
- [ ] Add ownership conflict/transfer handling.
- [ ] Add revocation/deletion behavior.
- [ ] Add tests and user/development documentation.

### Requirement verification

- Claim and reconnect one server under one account.
- Reject wrong-account takeover.
- Revoke credentials and verify reconnect fails.
- Exercise headless device flow and browser cancellation.
- Verify local/static-token modes remain account-independent.
