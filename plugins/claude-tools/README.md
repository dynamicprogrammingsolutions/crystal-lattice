# claude-tools

Claude Code-compatible tool plugin bundle for Crystal Lattice.

This package is being built from behavior-driven investigations of Claude Code's Anthropic API traffic. Raw logs live under `investigation/raw/` and are ignored; normalized fixtures and implementation notes live under `investigation/fixtures/` and `investigation/notes/`.

## Implemented Tools

- `Read`: Claude Code-compatible file reader with Anthropic-native schemas and tool-result payloads.
- `Write`: Claude Code-compatible file writer with Anthropic-native schemas, parent-directory creation, and the observed read-before-write guard for existing files.
- `Edit`: Claude Code-compatible exact string editor with Anthropic-native schemas, read-before-edit guard behavior, and replace-all support.
- `Glob`: Claude Code-compatible file matcher with Anthropic-native schemas, relative-vs-absolute output parity, and truncation handling.
- `Grep`: Claude Code-compatible regex search tool with Anthropic-native schemas and mode-specific result formatting.
- `Bash`: Claude Code-compatible shell execution tool with Anthropic-native schemas, timeout handling, and background command support.

`Read` currently supports text files, images, PDF status/page rendering through Poppler, simple Jupyter notebooks, and observed Claude Code error formatting. OpenAI Chat Completions-compatible providers consume the Anthropic-native result through a narrow temporary bridge until first-class tool-result interop lands.

`Write` currently supports new-file creation, full overwrites after a prior `Read`, and the observed Claude error payload when attempting to overwrite an unread existing file.

`Edit` currently supports exact single replacements, `replace_all`, and the observed Claude error payloads for missing prior reads, missing match strings, and ambiguous multiple matches.

`Glob` currently supports default-directory relative results, scoped absolute-path results, the observed no-match string, and the Claude truncation suffix for large result sets.

`Grep` currently supports default `files_with_matches`, `content`, and `count` output modes, along with the observed no-match string and missing-path error wrapper.

`Bash` currently supports foreground execution, raw-success vs `Exit code N` failure formatting, the observed timeout behavior, and the Claude background-run message format.

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
