# Manual installation

Manual installation is useful when you want to inspect the archive, retain an
immutable release file, launch without an installer, or control command
placement yourself.

## Choose the archive

| System | Architecture | Release target | Archive |
|---|---|---|---|
| macOS | Intel | `darwin-amd64` | `.tar.gz` |
| macOS | Apple silicon | `darwin-arm64` | `.tar.gz` |
| Linux | x64 | `linux-amd64` | `.tar.gz` |
| Linux | ARM64 | `linux-arm64` | `.tar.gz` |
| Windows | x64 | `windows-amd64` | `.zip` |
| Windows | ARM64 | `windows-arm64` | `.zip` |

Release filenames use:

```text
crystal-lattice-python-runtime-v<version>-<target>.<archive-extension>
```

Download the matching file from the
[latest GitHub Release](https://github.com/dynamicprogrammingsolutions/crystal-lattice/releases/latest).

## Check your architecture

macOS or Linux:

```bash
uname -m
```

Windows PowerShell:

```powershell
[System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture
```

`x86_64`, `AMD64`, and `X64` correspond to the `amd64` release targets.
`arm64`, `aarch64`, and `Arm64` correspond to the `arm64` targets.

## Extract and run on macOS or Linux

This Linux x64 example uses the current package version. Change `target` to
the value from the table for another supported system:

```bash
version=0.2.0
target=linux-amd64
archive="crystal-lattice-python-runtime-v${version}-${target}.tar.gz"

tar -xzf "$archive"
"./${archive%.tar.gz}/bin/crystal-lattice" --help
```

The archive launcher uses the Python runtime inside the extracted directory.

## Extract and run on Windows

This Windows x64 example can also use `windows-arm64`:

```powershell
$Version = "0.2.0"
$Target = "windows-amd64"
$Archive = "crystal-lattice-python-runtime-v$Version-$Target.zip"
$Runtime = $Archive -replace "\.zip$", ""

Expand-Archive -LiteralPath $Archive -DestinationPath .
& ".\$Runtime\Scripts\crystal-lattice.cmd" --help
```

## Inspect the runtime layout

macOS or Linux:

```bash
"./${archive%.tar.gz}/bin/crystal-lattice" --runtime-layout-json
```

Windows PowerShell:

```powershell
& ".\$Runtime\Scripts\crystal-lattice.cmd" --runtime-layout-json
```

The result identifies the bundled Python runtime, built-in plugin sources,
default configuration, and user-owned paths.

## Install an optional POSIX command

Choose a stable location for the extracted runtime. Then write a small
forwarding command into a directory already on `PATH`:

```bash
runtime="$(pwd)/crystal-lattice-python-runtime-v0.2.0-linux-amd64"
command_dir="$HOME/.local/bin"

mkdir -p "$command_dir"
printf '#!/usr/bin/env sh\nexec "%s/bin/crystal-lattice" "$@"\n' "$runtime" \
  > "$command_dir/crystal-lattice"
chmod +x "$command_dir/crystal-lattice"
"$command_dir/crystal-lattice" --help
```

If `~/.local/bin` is not already on `PATH`, choose another command directory
or update your shell configuration.

## Install an optional Windows command

Choose a stable location for the extracted runtime and a command directory
already on PATH:

```powershell
$Runtime = (
  Resolve-Path ".\crystal-lattice-python-runtime-v0.2.0-windows-amd64"
).Path
$CommandDirectory = "$HOME\bin"
$Command = Join-Path $CommandDirectory "crystal-lattice.cmd"

New-Item -ItemType Directory -Path $CommandDirectory -Force | Out-Null
$CommandText = "@echo off`r`ncall `"$Runtime\Scripts\crystal-lattice.cmd`" %*`r`n"
[IO.File]::WriteAllText($Command, $CommandText, [Text.Encoding]::ASCII)
& $Command --help
```

If that directory is not already on PATH, add it yourself or use the
[native PowerShell installer](installation-windows.md), which manages the user
PATH automatically.

## Remove a manual installation

Delete:

- the extracted runtime directory;
- an optional forwarding command you created.

Configuration, credentials, sessions, logs, and plugin caches remain under
their user-owned `.crystal` locations unless you explicitly remove them.

## Troubleshooting

### The archive contains an unexpected directory

The archive must contain one top-level directory whose name matches the
archive filename without `.tar.gz` or `.zip`.

### The launcher is missing

The expected launchers are:

```text
bin/crystal-lattice
Scripts\crystal-lattice.cmd
```

Download the correct archive again if the appropriate launcher is absent.