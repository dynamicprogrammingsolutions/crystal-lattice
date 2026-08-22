# Bridge E2EE key lifecycle

## Key classes

- Endpoint identity key: long-lived frontend or server key used to authenticate
  peer establishment.
- Session key material: short-lived keys derived for one connection/key epoch.
- Peer trust record: saved peer identity/fingerprint and related server/client
  scope.
- Recovery/reset state: explicit record that trust must be re-established.

The selected protocol may use additional internal keys, but public behavior
maps to these classes.

## Creation

- A frontend creates its identity key using platform cryptographic facilities.
- A server creates its identity key using an appropriate OS-protected store or
  protected credential file.
- Private key material never crosses the bridge or hosted control plane.

## Storage

Mobile:

- use Keychain/Keystore-backed storage;
- exclude keys from AsyncStorage, connection exports, logs, and debug timelines;
- apply platform accessibility/unlock policy selected during implementation.

Server:

- use OS credential storage where available;
- otherwise use a dedicated protected file with restrictive permissions;
- keep keys separate from ordinary project profile/config export.

## Pairing and trust

Pairing binds a server identity key to the frontend's saved server record and a
frontend key to the server's authorized peer state as required by the selected
protocol.

A pairing token is authorization state, not a key or peer trust record.

## Multiple devices

Each device has its own identity key unless an approved future design
explicitly supports secure key transfer. Adding a device requires an
authenticated enrollment/pairing flow.

## Rotation

- Session keys rotate on reconnect or key epoch according to protocol.
- Endpoint identity-key rotation requires authenticated transition or explicit
  re-pairing.
- A changed server key without approved transition is treated as a possible
  impersonation event.

## Removal

Keys and trust records are removed or invalidated on:

- explicit unpair/reset;
- deletion of the saved secure connection;
- server unclaim or credential reset as specified;
- account deletion for account-scoped hosted access;
- confirmed device wipe/logout behavior;
- administrative security revocation where supported.

Ordinary app backgrounding or bridge reconnect does not erase long-term trust.

## Recovery

Lost device:

- revoke account/device access where available;
- remove the device record;
- pair a replacement device independently.

Lost/reinstalled server:

- recover from an approved protected backup only if the final decision permits;
- otherwise generate a new key and require explicit re-pairing.

The final backup/recovery policy remains open and must balance usability against
silent impersonation risk.
