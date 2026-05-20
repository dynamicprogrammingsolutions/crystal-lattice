# claude-tools

Claude Code-compatible tool plugin bundle for Crystal Lattice.

This package is being built from behavior-driven investigations of Claude Code's Anthropic API traffic. Raw logs live under `investigation/raw/` and are ignored; normalized fixtures and implementation notes live under `investigation/fixtures/` and `investigation/notes/`.

## Implemented Tools

- `Read`: Claude Code-compatible file reader with Anthropic-native schemas and tool-result payloads.

`Read` currently supports text files, images, PDF status/page rendering through Poppler, simple Jupyter notebooks, and observed Claude Code error formatting. OpenAI Chat Completions-compatible providers consume the Anthropic-native result through a narrow temporary bridge until first-class tool-result interop lands.

## License

Unless otherwise noted in an individual file, original source code in this
package that was authored for this repository is licensed under the Apache
License, Version 2.0.

Files that carry an Apache license header are covered by the following notice:

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

Certain other files in this package contain materials derived from or adapted
from Claude Code or other Anthropic-authored materials. Those files are not
licensed by us under Apache-2.0 and are instead subject to Anthropic's terms:

© Anthropic PBC. All rights reserved. Use is subject to Anthropic's
[Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms).

Rights in this package should therefore be determined on a file-by-file basis
by checking the notices or headers in the individual files.
