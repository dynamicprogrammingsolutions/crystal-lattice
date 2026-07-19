# Sample Scripts

Reference samples showing how to use the same building blocks as the
`bash-send-kindle-icloud` plugin tools outside of the agent tool loop.

These scripts are not part of the plugin's runtime; they are standalone shell
and Python utilities that demonstrate the underlying patterns. The plugin
itself ships its own production versions (`send_icloud_email.py`,
`build_epub_from_markdown.bash`, `send_to_kindle.bash`,
`send_markdown_to_kindle.bash`) that are wired into the agent tool loop.

## Samples

### `build_auth_notifications_epub.sh`

Builds an EPUB from an ordered set of Markdown files using `pandoc`. This is
the same pattern as the plugin's `build_epub_from_markdown` tool, but run
directly from a shell. The example task directory
(`tasks/20260516-auth-notifications-staged-rollout`) is the one the script was
originally written for; adjust `TASK_DIR` for your own Markdown source set.

Requirements: `pandoc` on `PATH`.

### `send_kindle_email.py`

Sends an email with an attachment through SMTP using a password stored in
macOS Keychain. This is the same pattern as the plugin's `send_icloud_email.py`
helper, but as a standalone CLI script that reads the SMTP password from a
configurable Keychain service name (defaults to `kindle-smtp`).

Requirements: macOS with the `security` command-line tool and an app-specific
password stored in Keychain under the configured service name.

```bash
python plugins/bash-send-kindle-icloud/samples/send_kindle_email.py \
  --smtp-user <icloud-email> \
  --from <sender> \
  --to <kindle-email> \
  --subject "Auth And Notifications Staged Rollout" \
  --attachment /path/to/file.epub
```