# Bridge E2EE decisions and open questions

## Approved decisions

### BEE-D001 — Hosted production requires E2EE

Status: Approved

The production hosted bridge cannot launch without implemented and reviewed
E2EE. Community deployments may require, allow, or disable E2EE.

### BEE-D002 — Pairing code is not encryption key material

Status: Approved

The six-digit pairing code may authenticate or confirm a stronger exchange but
cannot directly provide the encryption key or sufficient offline key entropy.

### BEE-D003 — Protect complete HTTP-shaped application content

Status: Approved

Protection includes method, path/query, application headers, request/response
bodies, response status, attachments, and content-bearing errors. The bridge
retains only minimal routing metadata.

## Open design decisions

### BEE-D004 — Protocol construction and cryptographic libraries

Status: Open

Select an established authenticated key-agreement and streaming-capable
authenticated-encryption construction with maintained React Native/native and
Python libraries.

Decision trigger: interoperability and security spike in Task 060.

### BEE-D005 — Peer-key recovery and backup

Status: Open

Decide whether server endpoint identity keys may be backed up and restored or
whether reinstall/replacement always requires re-pairing.

Required constraints:

- no silent trust of a new key;
- clear lost-device/server recovery;
- secure backup if allowed;
- explicit user-visible reset.

### BEE-D006 — Multiple-device enrollment

Status: Open

Initial recommendation: independent device identity keys and explicit
enrollment/pairing for each device. Do not add shared-key synchronization
without a separately reviewed design.
