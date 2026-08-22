# Bridge quota and usage contract

## Limit dimensions

The public contract supports:

- registered servers per account;
- concurrent app-to-server sessions;
- concurrent transfers/requests;
- request size;
- response size;
- transferred bytes within a provider-defined window;
- rate/burst policy where supplied.

Exact commercial values are outside the public specification.

## Leases

Server, session, and transfer capacity use explicit leases:

- each lease has a unique ID, scope, issue time, and expiration;
- acquisition is atomic at the provider boundary;
- renewal is explicit;
- release is idempotent;
- failure to release is repaired by expiry;
- retries do not allocate duplicate capacity;
- node loss does not permanently consume quota.

## Usage windows

Windows are provider-defined and can be short or long. The contract does not
assume a calendar month or store billing period.

The provider reports enough public state for clients to understand:

- current tier/policy;
- whether work is allowed;
- warning or hard-limit state;
- reset/window end when appropriate;
- a public error reason.

## Usage batches

Usage is accumulated locally within strict bounds and submitted in idempotent
batches. Batch retry never double-counts.

The bridge meters:

- WebSocket request/response bytes;
- HTTP request-body download bytes;
- HTTP response-body upload bytes;
- hybrid WebSocket event traffic and HTTP-routed traffic;
- E2EE ciphertext bytes at the relay boundary.

## Limit behavior

- A server-count limit rejects a new registration.
- A concurrent-session limit rejects a new session.
- A transfer limit rejects or briefly queues new work according to public
  policy.
- A request/response-size limit terminates the violating transfer safely.
- A usage-window hard ceiling blocks new work without unnecessarily
  terminating a valid in-progress request.
- Abuse or administrative suspension denies new hosted-style access.

## Provider outage

- New hosted-style leases fail closed when the provider cannot make a current
  decision.
- Existing work lasts no longer than verified leases and grants.
- Locally buffered usage is bounded and never silently discarded as success.
- Recovery reconciles lease and usage state.
