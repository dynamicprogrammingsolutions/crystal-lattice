# bash-send-kindle-icloud

Bash tool plugin that exposes three small tools:

- `build_epub_from_markdown`
- `send_to_kindle`
- `send_markdown_to_kindle`

The tools are intentionally separate:

- `build_epub_from_markdown` creates an EPUB from local Markdown files
- `send_to_kindle` sends an already-existing local file through iCloud Mail SMTP
- `send_markdown_to_kindle` builds and sends in one step using a temporary EPUB

The transport is specifically implemented with **iCloud Mail SMTP** on macOS.

## What this plugin does

- Tool name: `build_epub_from_markdown`
  - builds an EPUB from an ordered list of local Markdown files using `pandoc`
  - defaults to a built-in Lua filter that converts local file links into plain text so EPUB readers do not show broken local links
- Tool name: `send_to_kindle`
  - sends a local file as an email attachment
  - defaults such as recipient email and Keychain service are read from agent config keys
  - uses macOS Keychain to retrieve the iCloud app-specific password at send time
- Tool name: `send_markdown_to_kindle`
  - builds an EPUB from an ordered list of Markdown files
  - sends that EPUB through the existing iCloud Mail SMTP path
  - removes the temporary EPUB afterward

This plugin is a good fit if you want a model-callable EPUB builder, a
separate model-callable sender, and a combined one-shot workflow while keeping
SMTP secrets out of plain text config.

## Platform and dependency requirements

This plugin is **specific to iCloud Mail on macOS** for the sending half.

Required dependencies:

- macOS
- `bash`
- `jq`
- `pandoc`
- `python3`
- the `security` command-line tool from macOS
- an iCloud Mail account
- an Apple app-specific password stored in macOS Keychain

## iCloud and Kindle setup guide

This plugin sends mail through iCloud SMTP. The safest setup is:

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

## Plugin installation

Add the plugin to your config and enable bash tools:

```json
{
  "plugin_policy": {
    "allow_bash_tools": true
  },
  "mixins": {
    "shared_agent_defaults": {
      "send_to_kindle_smtp_user": "${env:ICLOUD_KINDLE_SMTP_USER}",
      "send_to_kindle_from_addr": "${env:ICLOUD_KINDLE_FROM_ADDR}",
      "send_to_kindle_default_to": "${env:ICLOUD_KINDLE_DEFAULT_TO}",
      "send_to_kindle_keychain_service": "${env:ICLOUD_KINDLE_KEYCHAIN_SERVICE}"
    }
  },
  "plugins": [
    "bash:${env:BUILTIN_PLUGINS}/bash-send-kindle-icloud"
  ],
  "agents": {
    "default": {
      "provider": "your-provider-id",
      "mixin_refs": ["shared_agent_defaults"],
      "disabled_plugins": ["send_to_kindle"]
    }
  }
}
```

If your config already has a `plugins` list or `plugin_policy`, merge the new
entries into the existing objects instead of replacing them wholesale.

## Agent configuration keys

Only `send_to_kindle` reads resolved config keys from the agent config:

- `send_to_kindle_smtp_user`
- `send_to_kindle_from_addr`
- `send_to_kindle_default_to`
- `send_to_kindle_keychain_service`

Recommended pattern:

1. keep raw values in `CONFIG_DIR/.env`
2. reference them from config using `${env:...}`
3. let the bash tool host pass those resolved config values into the tool

Example `.env` values:

```dotenv
ICLOUD_KINDLE_SMTP_USER=your-icloud-address@icloud.com
ICLOUD_KINDLE_FROM_ADDR=your-icloud-address@icloud.com
ICLOUD_KINDLE_DEFAULT_TO=your-kindle-address@kindle.com
ICLOUD_KINDLE_KEYCHAIN_SERVICE=kindle-smtp
```

Notes:

- `send_to_kindle_from_addr` defaults to `send_to_kindle_smtp_user` if omitted.
- `send_to_kindle_keychain_service` defaults to `kindle-smtp` if omitted.
- The tool can override the recipient per call using the `to` argument.

## Tool arguments

### `build_epub_from_markdown`

- `markdown_files` required: ordered list of Markdown file paths
- `output_epub` required: output path for the generated EPUB
- `title` optional
- `author` optional
- `language` optional, defaults to `en-US`
- `toc_depth` optional, defaults to `2`
- `lua_filter` optional, defaults to the plugin's built-in local-link filter

The tool is intentionally simple. It only creates the EPUB.

### `send_to_kindle`

- `attachment` required: local path to the file to attach
- `subject` optional
- `body` optional
- `to` optional

The tool rejects missing files. It does not enforce the `.epub` suffix itself.
This keeps the helper simple and lets the downstream recipient system decide
whether the attachment is acceptable.

### `send_markdown_to_kindle`

- `markdown_files` required: ordered list of Markdown file paths
- `title` optional
- `author` optional
- `language` optional, defaults to `en-US`
- `toc_depth` optional, defaults to `2`
- `lua_filter` optional, defaults to the plugin's built-in local-link filter
- `output_filename` optional
- `to` optional
- `subject` optional, defaults to `title` when provided
- `body` optional

This tool builds a temporary EPUB, sends it, and removes it. It is the
combined convenience tool for the same workflow that the other two tools can
perform separately.

When `title` is omitted, the tool uses the first Markdown heading it finds
across `markdown_files` as the effective title. When `output_filename` is
omitted, the tool generates a Kindle-visible attachment filename from the
effective title by lowercasing it, replacing non-alphanumeric runs with `-`,
and appending a local timestamp in `YYYYMMDD-HHMMSS` format plus `.epub`.

Example autogenerated filename:

- `auth-and-notifications-staged-rollout-20260516-231500.epub`

## Example tool calls

### Build an EPUB from multiple Markdown files

```json
{
  "markdown_files": [
    "/absolute/path/000-main.md",
    "/absolute/path/010-local-notification-polling.md",
    "/absolute/path/020-bridge-push-delivery.md",
    "/absolute/path/030-authentik-auth-integration.md"
  ],
  "output_epub": "/absolute/path/rollout.epub",
  "title": "Auth And Notifications Staged Rollout",
  "author": "OpenAI Codex"
}
```

### Send an already-built EPUB

```json
{
  "attachment": "/absolute/path/rollout.epub"
}
```

### Override the recipient and subject when sending

```json
{
  "attachment": "/absolute/path/to/book.epub",
  "to": "someone@example.com",
  "subject": "EPUB delivery test",
  "body": "Sending this EPUB from the agent tool."
}
```

### Build and send Markdown in one step

```json
{
  "markdown_files": [
    "/absolute/path/000-main.md",
    "/absolute/path/010-local-notification-polling.md",
    "/absolute/path/020-bridge-push-delivery.md"
  ],
  "title": "Auth And Notifications Staged Rollout",
  "author": "OpenAI Codex",
  "subject": "Auth And Notifications Staged Rollout"
}
```

### Build and send Markdown with an explicit attachment filename

```json
{
  "markdown_files": [
    "/absolute/path/000-main.md",
    "/absolute/path/010-local-notification-polling.md"
  ],
  "output_filename": "rollout-for-kindle.epub"
}
```

## Direct shell testing

When invoking `send_to_kindle.bash` directly, there is no Python host to
inject agent config values. For direct shell tests, export the expected
`AGENT_TOOL_CONFIG_*` variables manually first.

Example:

```bash
export AGENT_TOOL_CONFIG_SEND_TO_KINDLE_SMTP_USER='your-icloud-address@icloud.com'
export AGENT_TOOL_CONFIG_SEND_TO_KINDLE_FROM_ADDR='your-icloud-address@icloud.com'
export AGENT_TOOL_CONFIG_SEND_TO_KINDLE_DEFAULT_TO='your-kindle-address@kindle.com'
export AGENT_TOOL_CONFIG_SEND_TO_KINDLE_KEYCHAIN_SERVICE='kindle-smtp'
```

Schema for the EPUB builder:

```bash
bash plugins/bash-send-kindle-icloud/build_epub_from_markdown.bash schema
```

Preview for the EPUB builder:

```bash
printf '%s' '{
  "markdown_files": [
    "/tmp/a.md",
    "/tmp/b.md"
  ],
  "output_epub": "/tmp/book.epub",
  "title": "Demo Book"
}' | bash plugins/bash-send-kindle-icloud/build_epub_from_markdown.bash preview --args-json
```

Build an EPUB directly:

```bash
printf '%s' '{
  "markdown_files": [
    "/tmp/a.md",
    "/tmp/b.md"
  ],
  "output_epub": "/tmp/book.epub",
  "title": "Demo Book"
}' | bash plugins/bash-send-kindle-icloud/build_epub_from_markdown.bash run --args-json
```

Schema for the combined tool:

```bash
bash plugins/bash-send-kindle-icloud/send_markdown_to_kindle.bash schema
```

Dry run for the combined tool:

```bash
export SEND_TO_KINDLE_DRY_RUN=1
printf '%s' '{
  "markdown_files": [
    "/tmp/a.md",
    "/tmp/b.md"
  ],
  "title": "Demo Book"
}' | bash plugins/bash-send-kindle-icloud/send_markdown_to_kindle.bash run --args-json
```

Schema for the sender:

```bash
bash plugins/bash-send-kindle-icloud/send_to_kindle.bash schema
```

Preview for the sender:

```bash
printf '%s' '{"attachment":"/tmp/test.epub"}' | \
  bash plugins/bash-send-kindle-icloud/send_to_kindle.bash preview --args-json
```

Dry run for the sender:

```bash
export SEND_TO_KINDLE_DRY_RUN=1
printf '%s' '{"attachment":"/tmp/test.epub"}' | \
  bash plugins/bash-send-kindle-icloud/send_to_kindle.bash run --args-json
```

## Why this is iCloud-specific

The sending tool always uses:

- SMTP host: `smtp.mail.me.com`
- SMTP port: `587`
- TLS/STARTTLS

It expects an Apple app-specific password stored in Keychain, not a generic
arbitrary SMTP configuration. If you later want a provider-neutral SMTP tool,
that should be a separate plugin.

## Optional interpreter override

If the host process uses an unexpected `python3`, you can override the helper
interpreter with:

```bash
export SEND_TO_KINDLE_PYTHON=/absolute/path/to/python3
```

The sender tool automatically prefers:

1. `SEND_TO_KINDLE_PYTHON`
2. `AGENT_TOOL_PYTHON` supplied by the bash tool host
3. `PYTHON`
4. `${VIRTUAL_ENV}/bin/python3`
5. `python3` from `PATH`