# Install Crystal Lattice

The bundled Crystal Lattice CLI includes Python and the application runtime.
You do not need a system Python installation or provider credentials to
install it, start the terminal, or inspect the configured agents.

## Choose an installation method

| Your system | Recommended method | Guide |
|---|---|---|
| macOS Intel or Apple silicon | Bash installer | [Install on macOS or Linux](installation-macos-linux.md) |
| Linux x64 or ARM64 | Bash installer | [Install on macOS or Linux](installation-macos-linux.md) |
| Windows x64 or ARM64 | Native PowerShell installer | [Install on Windows](installation-windows.md) |
| Any supported system | Download and inspect an immutable release archive | [Manual installation](installation-manual.md) |

Git Bash, MSYS2, and Cygwin provide an additional installer path on Windows
x64. Native PowerShell is the recommended Windows method and the supported
installer path on Windows ARM64.

## Verify the command

After any installation method:

```console
crystal-lattice --help
```

Start the terminal:

```console
crystal-lattice --console
```

The default configuration can start without provider API keys. Missing
optional credentials may produce configuration warnings, but they do not
prevent normal startup.

## Add API credentials when needed

Provider APIs require their real credentials when you send a request. Put
those values in the `.env` file beside the active configuration instead of
exporting them for normal use:

```dotenv
OPENAI_API_KEY=...
OPENROUTER_API_KEY=...
ANTHROPIC_API_KEY=...
```

For the complete lookup order, see
[Environment placeholders](configuration-placeholders.md#env-files).

## Source checkout

The bundled installers are intended for normal end-user installation.
Contributors working from a checkout should use the
[source installation instructions](../README.md#source-install).