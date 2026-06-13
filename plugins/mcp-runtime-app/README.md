# MCP Runtime App Plugin

Application-level observability plugin for MCP runtimes.

This plugin exposes session actions for:

- showing MCP runtime status
- clearing stored MCP runtimes
- forcing reconnect on the next request by clearing runtimes

It is intentionally application-scoped rather than tool-scoped so that the UI
can inspect runtime state independent of any one wrapper plugin.

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
