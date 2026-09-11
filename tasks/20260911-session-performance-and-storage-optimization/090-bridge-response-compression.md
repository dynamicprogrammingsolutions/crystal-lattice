# Bridge response compression

Reduce large message and schema transfer time by preserving negotiated compressed response bytes through direct HTTP and the HTTP bridge path without redundant decode/re-encode work.

## Requirements checklist

- [ ] **BCOMP-001** Large compressible JSON responses support negotiated compression above a measured threshold.
- [ ] **BCOMP-002** Small or poorly compressible responses are not compressed when compression would increase latency or size.
- [ ] **BCOMP-003** HTTP bridge v2 preserves compressed response bytes and the applicable `Content-Encoding`, content type, and cache validators end to end.
- [ ] **BCOMP-004** The Python bridge client does not unnecessarily decompress and recompress a v2 response.
- [ ] **BCOMP-005** Direct HTTP, HTTP bridge, and hybrid bridge clients decode to functionally identical response data.
- [ ] **BCOMP-006** Compression does not cause the bridge to buffer multiple complete compressed and uncompressed copies of large bodies.
- [ ] **BCOMP-007** Cancellation, timeout, body-size enforcement, streaming backpressure, and error responses remain correct for compressed bodies.
- [ ] **BCOMP-008** Compression of authenticated or user-controlled responses is reviewed for relevant security risks and constrained appropriately.
- [ ] **BCOMP-009** The measured 4.81 MB last-50 fixture transfers at approximately its demonstrated 658 KB gzip size or better when the negotiated algorithm is gzip-equivalent.
- [ ] **BCOMP-010** Integration tests cover direct, HTTP bridge, hybrid, binary/non-JSON, already-compressed, and legacy-client compatibility cases.
- [ ] **BCOMP-011** Shared benchmark output separates backend generation time, local-to-bridge upload time, bridge-to-client transfer time, and client decode/parse time where measurable.

## Scope

In scope:

- FastAPI/ASGI response compression or an equivalent owning layer.
- Python HTTP bridge v2 raw-body forwarding.
- Elixir bridge HTTP transfer and compression behavior.
- Frontend HTTP/hybrid transport header and body handling.
- Threshold, algorithm, streaming, cancellation, memory, compatibility, and security verification.

Out of scope:

- Changing the default bridge transport mode.
- Redesigning the message DTO.
- Compression of canonical on-disk session storage.

Parent Task: `tasks/20260911-session-performance-and-storage-optimization/000-main.md`

Depends On: `tasks/20260911-session-performance-and-storage-optimization/010-session-growth-and-benchmark-foundation.md`

## Requirement questions

- Should compression originate at the local ASGI server, the bridge edge, or both under non-overlapping conditions?
- Which algorithms are supported by all production clients, and is gzip the compatibility baseline?
- Does `httpx.aiter_raw()` plus preserved headers provide the required compressed pass-through for every response class?
- How should already-compressed assets and binary responses bypass compression?
- Does the legacy WebSocket path need explicit per-message compression, or is HTTP/hybrid the supported efficient path for large bodies?
- What threshold balances CPU against network savings on developer laptops and mobile devices?

## Research details and suggested direction

The sampled 4,805,958-byte message response compressed to 658,349 bytes, a ratio of about 13.7%. At 10 Mbps the uncompressed payload alone requires about 3.84 seconds of one-way payload time, while the compressed payload is approximately 0.53 seconds before protocol overhead.

HTTP bridge v2 streams `local_response.aiter_raw()` to the bridge response-body upload. This is a promising pass-through path if response headers remain coherent and no layer transparently decodes the body first.

The bridge HTTP listener already enables compression above a configured threshold, but the local-server-to-bridge upload may remain uncompressed. Research must distinguish where each leg compresses and avoid double compression or header/body mismatch.

Because this spans HTTP behavior across several independently owned components, the implementation direction remains open pending an end-to-end protocol review.