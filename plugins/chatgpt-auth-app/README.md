# ChatGPT Auth App

Application plugin implementing Codex browser and device-code login for
ChatGPT-style authentication.

## Terminal commands

The plugin contributes one complete foreground login operation:

```bash
crystal-lattice auth login codex
```

In an applicable OpenAI Responses terminal session, the same action is
available as:

```text
/login codex
```

Choose a method explicitly when needed:

```bash
crystal-lattice auth login codex --method browser
crystal-lattice auth login codex --method device-code
crystal-lattice auth login codex --method browser --no-open
```

```text
/login codex method=browser
/login codex method=device-code
```

Command flows default to browser. Browser login is supported only when the
browser runs on the same host as the backend/plugin listener. The plugin binds
`127.0.0.1` on provider-accepted port `1455` or `1457`, advertises the matching
`http://localhost:<port>/auth/callback`, performs PKCE and state validation,
exchanges the code, and closes the listener on every terminal outcome. The URL
is always printed; a local interactive terminal may open it best-effort unless
`--no-open` is supplied. No pasted callback/code flow is supported.

Device code remains the production method for mobile, remote, and headless
arrangements. It prints the verification URL and code while the plugin-owned
worker polls. No public bridge callback relay or embedded WebView is used.

Both methods return only at authentication, failure, cancellation, or expiry.
Ctrl-C requests cancellation for that exact attempt; a stale worker or
callback cannot replace a newer attempt or credentials.

Logout remains a separate action intent and is not contributed as a command
by this package. Mobile, desktop, and other frontends can continue invoking
the independent `login_start`, `check_status`, `cancel_login`, and `logout`
actions.

## Actions

The plugin exposes session actions for OpenAI Responses sessions with
`auth_mode` set to `auto` or `chatgpt`:

- **Sign in with ChatGPT**: selects browser (same-host only) or device-code
  login. The visible session action defaults to device code for cross-device
  safety.
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
  that point. Journal history is preserved; the reset also appends a
  zeroed-total row to the simplified usage summary CSV.
- **Cancel ChatGPT login** / **Log out of ChatGPT**: login lifecycle
  controls.

## HTTPS and fixed runtimes

Device-code start, polling, browser token exchange, and credential refresh keep
TLS verification enabled and use Certifi's bundled public roots. OpenAI's
device-auth endpoint may return a Cloudflare route error to Python `urllib`;
the plugin retries that specific response with the in-process `requests`
client. The plugin does not require a `curl` subprocess, so device-code actions
work in fixed runtimes such as the embedded iOS application.

## ChatGPT usage journal

Usage reports and reset markers operate on the append-only
`auth/chatgpt-usage-journal.ndjson` file written by the `openai_responses`
provider and usage extension (default root: the Crystal data directory,
`CRYSTAL_DATA_DIR`, default `~/.crystal`). It records every captured
rate-limit snapshot and every ChatGPT-backed request's estimated usage with
the plan-limit state observed on the same response, so usage contributors,
usage-percent history, and reset-time changes can be reconstructed by date.
Records carry the request's session id and absolute working directory, and a
simplified `auth/chatgpt-usage-summary.csv`
(`time, working_directory, session_id, estimated_cost, total_cost,
used_percent`) is appended alongside the journal. Detailed, cross-provider
cost reporting lives in the generic cost tracking plugin
(`plugins/cost-tracking`); this app keeps the simple ChatGPT usage report.
See the `openai_responses` package's
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
