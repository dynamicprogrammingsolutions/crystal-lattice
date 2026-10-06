# Tool Host Node

Tool Host Node package for Crystal Lattice.

## Protocol

The Python proxy and this Node host jointly implement the
[cross-package tool-host protocol](../../docs/reference/tool-host-protocol.md).
Coordinate wire-version, method, state, event, and error changes across both
implementations.

## Testing

This package does not currently define a package-local automated test script.
When changing the host or SDK entrypoints, verify through the tool-plugin flow
that consumes `agent-tool-host-node`.

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
