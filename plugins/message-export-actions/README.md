# message-export-actions

Application plugins that add two message actions to the chat UI:

- `Send to Kindle`
- `Share as PDF`

These actions export a single selected message, not the whole session.

## Features

- `Send to Kindle`
  - prompts for a title
  - generates an EPUB with `pandoc`
  - derives the attachment filename from the title
  - sends through iCloud SMTP using the same config-key contract as the existing Kindle tool

- `Share as PDF`
  - prompts for optional title and optional filename
  - generates a PDF from the selected message
  - stores the PDF as a session asset
  - returns a follow-up action so clients can share on mobile or save on desktop
  - includes its own download action, so it does not rely on a separate attachment-download plugin being loaded

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
- v1 export scope is intentionally limited to message text plus lightweight metadata.
- Multipart attachments are not rendered into the exported document in v1.