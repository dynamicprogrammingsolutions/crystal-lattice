# Bridge end-to-end encryption

This specification defines the target that protects Crystal Lattice
application requests and responses between a frontend and the user's registered
server even when traffic crosses an operated bridge.

## Specification documents

- [Product behavior](product-spec.md)
- [Threat model](threat-model.md)
- [Protocol target](protocol.md)
- [Key lifecycle](key-lifecycle.md)
- [Requirements and live state](requirements.md)
- [Decisions and open questions](decisions.md)

## Ownership

| Responsibility | Owner |
| --- | --- |
| E2EE product and protocol contract | This specification |
| Mobile/desktop key handling and encrypted frontend envelopes | Mobile/desktop hosts and shared frontend SDK |
| Server key handling and encrypted local forwarding envelope | `application/python/agent_terminal_app` |
| Opaque routing and ciphertext transport | [Bridge connectivity](../bridge-connectivity/index.md) and `bridge-elixir` |
| Authentication, pairing policy, subjects, and access grants | [Bridge access control](../bridge-access-control/index.md) |
| Hosted user presentation | [Hosted bridge client experience](../hosted-bridge-client-experience/index.md) |

## Scope

- authenticated frontend/server key establishment;
- pairing-code role in authenticating the exchange;
- encryption of HTTP-shaped request and response metadata and bodies;
- minimal visible routing envelope;
- replay and downgrade protection;
- streaming, chunking, attachments, reconnect, and resume;
- secure key storage, rotation, reset, and deletion;
- multiple frontend devices;
- cross-language interoperability and test vectors;
- independent protocol and implementation review;
- precise public claim boundaries.

## Exclusions

- Protecting content from a compromised frontend or user server.
- Hiding unavoidable connection timing and ciphertext-size metadata.
- Defining account, entitlement, or quota policy.
- Replacing TLS between clients, edges, and bridge nodes.
- Inventing custom cryptographic primitives.

## Relationship to tasks

- `tasks/20260821-modular-bridge-access-platform/060-e2ee-protocol-and-threat-model.md`
- `tasks/20260821-modular-bridge-access-platform/070-e2ee-implementation.md`
- `tasks/20260821-modular-bridge-access-platform/170-mixed-transport-access-e2ee-and-metering-alignment.md`
- `tasks/20260821-modular-bridge-access-platform/210-public-privacy-terms-store-and-e2ee-documentation.md`
