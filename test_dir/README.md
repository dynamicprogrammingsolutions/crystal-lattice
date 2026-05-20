# External LLM client test

What this is
- A tiny, tool-based prompt to check whether a model can carry its pre–tool-call private reasoning across a tool result into the next request.

Files
- prompt.txt — Based on repo root prompt_template.txt; paths point to local bank JSONs and a concrete SEED is embedded.
- bank0.json, bank1.json, bank2.json — The three banks, colocated with the prompt so a standard file-read capability can load them via relative paths like "bank1.json".

How to run
- Ensure your client provides a file-read capability. Resolve requested paths relative to this directory.
- Send the contents of prompt.txt as the user message with tools enabled.
- When the model requests a file read, return the raw JSON of the requested bank file from this folder.
- The model should output exactly one label string (no extra text).

What to expect
- If prior reasoning is preserved across the tool result (properly added): you should still see seed1’s label — "Clock".
- If prior reasoning is NOT preserved:
  - GPT-5 family: typically re-reasons after the tool call (loses the earlier reasoning), recomputes the index from seed2 but still uses the bank chosen in Step 1; with the seeds above, you may see "Cup" (id 9 in bank0).
  - Anthropic Claude (e.g., sonnet-4.5): often guesses a result without reasoning.

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
