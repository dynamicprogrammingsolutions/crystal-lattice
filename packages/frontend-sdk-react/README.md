# Frontend Sdk React

Frontend Sdk React package for Crystal Lattice.

## Testing

Run the package tests from the repository root:

```bash
npm --workspace @crystal-lattice/frontend-sdk-react test
```

Or from this package directory:

```bash
npm test
```

This package currently has fast Vitest coverage only; it does not define
integration or e2e scripts.

## Session request-status polling

`useSessionRequestStatuses` is a host-neutral explicit-ID polling hook. The
host supplies active/foreground policy, saved connections, grouped session
IDs, and a `ConnectionSessionStatusReader`. The hook deduplicates IDs, splits
large connection groups into bounded requests, polls per connection, cancels
stale work, and applies bounded backoff. Successful batches replace only the
IDs they queried, so changing one visible consumer does not erase unrelated
status.

A transient unavailable read retains a recently observed Running value through
retry. Successful non-running or missing-session data replaces it
authoritatively, while a bounded staleness window prevents unavailable
authority from leaving Running visible indefinitely.

## License

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
