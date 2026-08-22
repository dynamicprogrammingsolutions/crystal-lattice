# Hosted bridge client-experience decisions and open questions

## Approved decisions

### HBC-D001 — Hosted subscription does not gate self-hosted use

Status: Approved

Direct, local-network, and custom self-hosted bridge connections remain
available without the operated hosted-bridge subscription.

### HBC-D002 — Initial login providers

Status: Approved

Initial login uses Apple and Google. Email is deferred while the account model
supports adding another identity link later.

### HBC-D003 — Native mobile stores

Status: Approved

Initial purchasing occurs through StoreKit on iOS and Google Play Billing on
Android. There is no initial web checkout.

### HBC-D004 — Initial commercial shape

Status: Approved direction

The initial public offer is monthly, around USD 10, and includes an
introductory trial. Clients display localized store values rather than a
hardcoded price.

### HBC-D005 — No existing-user grandfathering

Status: Approved

There are no current users requiring grandfathered hosted entitlement.

## Open decisions

### HBC-D006 — Trial duration

Status: Open

Seven days is recommended. Decide before production store-product setup.

### HBC-D007 — Production pairing

Status: Open

The client supports both pairing-required and pairing-disabled hosted access.
Final production behavior follows BAC-Q001.

### HBC-D008 — Annual product

Status: Deferred

Initial release is monthly only unless separately approved. Revisit after
public launch and retention/cost evidence.
