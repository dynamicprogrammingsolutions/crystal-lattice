# ChatGPT Auth App

Minimal application plugin implementing a device-code login flow for ChatGPT-style auth.

## Actions

The plugin exposes session actions for OpenAI Responses sessions with
`auth_mode` set to `auto` or `chatgpt`:

- **Sign in with ChatGPT**: starts the device-code login flow.
- **Show ChatGPT login status**: returns the current login state.
- **Show ChatGPT account status**: returns the account and current
  usage-limit status, plus estimated usage accumulated since the last usage
  tracking reset.
- **Show ChatGPT usage report**: shows estimated usage totals (requests,
  tokens, cost) since the last reset marker, current left percentage and
  next reset time per limit window, and usage-percent history. The report
  embeds `from`/`to` text inputs; the **Apply date range** follow-up action
  narrows the report to an inclusive date or date+time range interpreted in
  the server's own timezone.
- **Reset ChatGPT usage tracking**: appends a reset marker to the ChatGPT
  usage journal after confirmation, so subsequent reports count usage from
  that point. Journal history is preserved.
- **Cancel ChatGPT login** / **Log out of ChatGPT**: login lifecycle
  controls.

## ChatGPT usage journal

Usage reports and reset markers operate on the append-only
`auth/chatgpt-usage-journal.ndjson` file written by the `openai_responses`
provider and usage extension. It records every captured rate-limit snapshot
and every ChatGPT-backed request's estimated usage with the plan-limit state
observed on the same response, so usage contributors, usage-percent history,
and reset-time changes can be reconstructed by date. See the
`openai_responses` package's
[usage journal documentation](../openai_responses/docs/development/usage-journal.md)
for the record format and the CLI inspection script.

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
