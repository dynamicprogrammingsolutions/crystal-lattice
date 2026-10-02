# Install on macOS or Linux

The Bash installer supports:

| System | Architecture | Release target |
|---|---|---|
| macOS | Intel | `darwin-amd64` |
| macOS | Apple silicon | `darwin-arm64` |
| Linux | x64 | `linux-amd64` |
| Linux | ARM64 | `linux-arm64` |

It downloads the matching bundled-Python archive, installs the versioned
runtime, places `crystal-lattice` in a suitable writable directory already on
`PATH`, and verifies the installed command.

## Install

```bash
curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | bash
```

Then verify:

```bash
crystal-lattice --help
```

## What the installer changes

The versioned runtime is installed under:

```text
~/.local/opt/crystal-lattice-cli/
```

The installer writes a small `crystal-lattice` forwarding command. Without an
override, it selects the first suitable writable location from:

1. the command directory of a previous bundled-Python installation;
2. `~/.local/bin`;
3. `~/bin`;
4. another directory already present on `PATH`.

If no suitable directory exists, installation stops before replacing runtime
state and asks you to provide `BIN_DIR`. It does not leave an installed command
that the shell cannot find.

Configuration, credentials, sessions, logs, and plugin caches stay outside the
versioned runtime.

## Review the installer first

```bash
curl -fsSLO https://download.crystallattice.dev/crystal-lattice-cli/install.sh
less install.sh
bash install.sh
```

## Install a specific version

```bash
curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh \
  | VERSION=0.1.5 bash
```

## Choose the command directory

Set `BIN_DIR` when you deliberately want another location:

```bash
curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh \
  | BIN_DIR="$HOME/.local/bin" bash
```

An explicit directory is created when needed, but the installer does not add
that override to `PATH`. Choose a directory already on `PATH` or update your
shell configuration yourself.

## Update

Run the normal installer again. It stages and verifies the new runtime before
replacing the matching versioned target and command.

User-owned configuration and session data are not replaced.

## Remove

Locate the installed forwarding command:

```bash
command -v crystal-lattice
```

The installer prints the command and runtime paths when it completes. Remove
that forwarding command and the corresponding directory under
`~/.local/opt/crystal-lattice-cli/`.

The CLI normally stores user-owned state under `.crystal/` in a workspace and
under `~/.crystal/`. Removing the runtime does not remove that state.

## Troubleshooting

### The installer cannot find a command directory

Choose a writable directory already on `PATH` and pass it as `BIN_DIR`.

### The command is not found in the current shell

Confirm that the command directory is on `PATH`, then start a new terminal or
refresh the shell's command cache:

```bash
hash -r
```

### The architecture is unsupported

Check the machine architecture:

```bash
uname -m
```

The supported values correspond to Intel/x64 and ARM64. Other architectures
must use a source build.

### Inspect the installed layout

```bash
crystal-lattice --runtime-layout-json
```

For direct extraction without an installer, see
[Manual installation](installation-manual.md).