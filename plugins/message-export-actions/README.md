# message-export-actions

Application plugins that add two message actions to the chat UI:

- `Send to Kindle`
- `Share as PDF`

These plugins now expose both:

- message actions for exporting a single selected message
- session actions for exporting a filtered session transcript

## Features

- `Send to Kindle`
  - prompts for an optional title
  - supports an optional recipient email override
  - generates an EPUB with `pandoc`
  - derives the attachment filename from the effective title
  - sends through iCloud SMTP using the same config-key contract as the existing Kindle tool

- `Share as PDF`
  - prompts for optional title and optional filename
  - generates a PDF from the selected message
  - stores the PDF as a session asset
  - returns a follow-up action so clients can share on mobile or save on desktop
  - includes its own download action, so it does not rely on a separate attachment-download plugin being loaded

Session export behavior:

- includes all `user` messages
- includes `assistant` messages that have non-empty text content
- excludes `system` and `tool` messages
- adds an `H1` header at the top with the session id and session title when available
- adds an `H2` header for each exported user or assistant message
- demotes headings inside message content so message-local headings start at `H3`

## Configuration keys

This plugin reads resolved agent/session config keys at runtime:

- `send_to_kindle_smtp_user`
- `send_to_kindle_from_addr`
- `send_to_kindle_default_to`
- `send_to_kindle_keychain_service`
- `message_export_pdf_engine`

Recommended `message_export_pdf_engine` values:

- `auto`
- `pandoc`
- `xhtml2pdf`

Behavior:

- `auto`: prefer `pandoc` when available, otherwise use `xhtml2pdf`
- `pandoc`: require `pandoc`
- `xhtml2pdf`: always use the Python fallback engine

Kindle title behavior:

- message export default title: `Session <short-session-id> Message <index>`
- session export default title:
  - session metadata title when present
  - otherwise `Session <short-session-id>`
- both Kindle actions also accept an optional `to` email override
  - when omitted, `send_to_kindle_default_to` is used

## Runtime dependencies

Python dependencies installed with the plugin:

- `markdown`
- `xhtml2pdf`

Optional preferred system dependency:

- `pandoc`

Optional `pandoc` PDF engine dependencies:

- `xelatex` or `pdflatex`

Kindle sending is specifically implemented for macOS + iCloud Mail and expects:

- the `security` CLI
- an iCloud Mail app-specific password stored in Keychain

## iCloud and Kindle setup guide

This plugin’s `Send to Kindle` action uses iCloud SMTP on macOS. The safest setup is:

- keep non-secret defaults in config or `.env`
- keep the iCloud app-specific password only in macOS Keychain

### 1. Confirm iCloud Mail is enabled

Make sure the Apple account you want to use has iCloud Mail enabled and that you can send mail from it normally.

Useful Apple docs:

- iCloud Mail overview: <https://www.icloud.com/mail/>
- iCloud Mail server settings: <https://support.apple.com/en-us/102525>

### 2. Turn on two-factor authentication for the Apple account

Apple requires two-factor authentication before you can create app-specific passwords.

Apple docs:

- Two-factor authentication: <https://support.apple.com/en-us/102660>
- App-specific passwords: <https://support.apple.com/en-us/102654>

### 3. Generate an Apple app-specific password

1. Open the Apple account portal: <https://account.apple.com/>
2. Sign in with the Apple account used for iCloud Mail.
3. Go to `Sign-In and Security`.
4. Open `App-Specific Passwords`.
5. Create a new password with a label such as `kindle-smtp` or `crystal-lattice-kindle`.
6. Copy the generated password immediately.

Important:

- this is not your normal Apple account password
- the generated password is shown once
- if you later rotate or revoke it, update the Keychain entry described below

### 4. Find your Kindle email address and approve the sender

If you are sending to Kindle, you also need Amazon-side setup.

Amazon docs:

- Send to Kindle overview and supported formats: <https://www.amazon.com/sendtokindle>
- Kindle personal document email help: <https://www.amazon.com/sendtokindle/email>

Typical steps:

1. Find the Kindle `Send to Kindle` email address for the device or account.
2. Add your iCloud sender address to Amazon’s approved sender list.
3. Confirm Amazon accepts `EPUB` for your target workflow.

### 5. Store the app-specific password in macOS Keychain

Store the generated password once using the macOS `security` CLI.

Example:

```bash
security add-generic-password \
  -U \
  -a 'your-icloud-address@icloud.com' \
  -s 'kindle-smtp' \
  -w 'PASTE_THE_APP_SPECIFIC_PASSWORD_HERE'
```

Meaning of the fields:

- `-a`: Keychain account name, usually your iCloud SMTP username
- `-s`: Keychain service name, which should match your config
- `-w`: the app-specific password value

After that, the plugin reads the password from Keychain at send time. The raw password does not need to be stored in repo config, `.env`, or shell history again.

### 6. SMTP settings used by this plugin

The plugin uses the standard iCloud SMTP settings documented by Apple:

- host: `smtp.mail.me.com`
- port: `587`
- transport security: `STARTTLS`
- username: your full iCloud email address
- password: the app-specific password retrieved from Keychain

## Installation

Add the plugin repo to your config:

```json
{
  "mixins": {
    "shared_agent_defaults": {
      "send_to_kindle_smtp_user": "${env:ICLOUD_KINDLE_SMTP_USER}",
      "send_to_kindle_from_addr": "${env:ICLOUD_KINDLE_FROM_ADDR}",
      "send_to_kindle_default_to": "${env:ICLOUD_KINDLE_DEFAULT_TO}",
      "send_to_kindle_keychain_service": "${env:ICLOUD_KINDLE_KEYCHAIN_SERVICE}",
      "message_export_pdf_engine": "${env:MESSAGE_EXPORT_PDF_ENGINE}"
    }
  },
  "plugins": [
    {"path": "/absolute/path/to/plugins/message-export-actions"}
  ],
  "agents": {
    "default": {
      "provider": "your-provider-id",
      "mixin_refs": ["shared_agent_defaults"]
    }
  }
}
```

Example `.env` values:

```dotenv
ICLOUD_KINDLE_SMTP_USER=your-icloud-address@icloud.com
ICLOUD_KINDLE_FROM_ADDR=your-icloud-address@icloud.com
ICLOUD_KINDLE_DEFAULT_TO=your-kindle-address@kindle.com
ICLOUD_KINDLE_KEYCHAIN_SERVICE=kindle-smtp
MESSAGE_EXPORT_PDF_ENGINE=auto
```

If you prefer a fully inline config instead of `.env` placeholders:

```json
{
  "mixins": {
    "shared_agent_defaults": {
      "send_to_kindle_smtp_user": "your-icloud-address@icloud.com",
      "send_to_kindle_from_addr": "your-icloud-address@icloud.com",
      "send_to_kindle_default_to": "your-kindle-address@kindle.com",
      "send_to_kindle_keychain_service": "kindle-smtp",
      "message_export_pdf_engine": "auto"
    }
  },
  "plugins": [
    {"path": "/absolute/path/to/plugins/message-export-actions"}
  ],
  "agents": {
    "default": {
      "provider": "your-provider-id",
      "mixin_refs": ["shared_agent_defaults"]
    }
  }
}
```

You can also load it from the built-in plugins directory if your install layout exposes it there.

## Notes

- `Send to Kindle` does not currently fall back when `pandoc` is unavailable. It returns a clear error instead.
- Export scope is intentionally limited to message text plus lightweight metadata.
- Multipart attachments are not rendered into the exported document in this version.
- EPUB generation uses the same general metadata defaults as the bash Kindle tools:
  - language defaults to `en-US`
  - TOC is enabled
  - TOC depth defaults to `2`
  - the built-in local-link Lua filter is applied by default

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
