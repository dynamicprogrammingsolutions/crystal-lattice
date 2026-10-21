# Install on Windows

Use the native PowerShell installer on Windows x64 or ARM64. It does not
require Git Bash, WSL, Python, administrator rights, or a PowerShell profile
edit.

## Install from PowerShell

```powershell
irm https://download.crystallattice.dev/crystal-lattice-cli/install.ps1 | iex
```

The command is immediately available in the PowerShell process that runs the
installer:

```powershell
Get-Command crystal-lattice
crystal-lattice --help
```

## What the installer changes

The versioned runtime is installed under:

```text
%USERPROFILE%\.local\opt\crystal-lattice-cli
```

For the `crystal-lattice.cmd` forwarding command, the installer first reuses
the suitable writable command directory of a previous bundled-Python
installation.

When none exists, it creates:

```text
%LOCALAPPDATA%\Programs\Crystal Lattice\bin
```

It adds that directory once to your user PATH and to the current PowerShell
process. It does not change the machine PATH.

Configuration, credentials, sessions, logs, and plugin caches stay outside the
versioned runtime.

## Use the command from Command Prompt

A newly opened PowerShell or Command Prompt sees the persisted user PATH:

```batch
where crystal-lattice
crystal-lattice --help
```

If an already-open Command Prompt launches the installer in a child
PowerShell, open a new terminal afterward. A child process cannot change its
parent process environment.

## Review the installer first

```powershell
Invoke-WebRequest `
  https://download.crystallattice.dev/crystal-lattice-cli/install.ps1 `
  -OutFile install.ps1
Get-Content .\install.ps1
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

## Install a specific version

```powershell
$env:VERSION = "0.2.2"
try {
  irm https://download.crystallattice.dev/crystal-lattice-cli/install.ps1 | iex
} finally {
  Remove-Item Env:VERSION -ErrorAction SilentlyContinue
}
```

## Choose the command directory

Set `BIN_DIR` when you deliberately want another location:

```powershell
$env:BIN_DIR = "$HOME\bin"
try {
  irm https://download.crystallattice.dev/crystal-lattice-cli/install.ps1 | iex
} finally {
  Remove-Item Env:BIN_DIR -ErrorAction SilentlyContinue
}
```

An explicit directory is created when needed, but the installer does not add
that override to the user PATH. Choose a directory already on PATH or update
PATH yourself.

## Git Bash

Git Bash, MSYS2, and Cygwin provide an additional Windows x64 path:

```bash
curl -fsSL https://download.crystallattice.dev/crystal-lattice-cli/install.sh | bash
```

That installer writes both a POSIX forwarding command and
`crystal-lattice.cmd`. Use native PowerShell on Windows ARM64.

## Update

Run the normal PowerShell installer again. It stages and verifies the new
runtime before replacing the matching versioned target and command. Repeated
installation does not duplicate the user PATH entry.

## Remove

Locate the forwarding command:

```powershell
(Get-Command crystal-lattice.cmd).Source
```

Remove that command and the corresponding versioned runtime under:

```text
%USERPROFILE%\.local\opt\crystal-lattice-cli
```

If the installer created its default command directory, you may remove the
unused `%LOCALAPPDATA%\Programs\Crystal Lattice\bin` entry from your user PATH.
Removing the runtime does not remove `.crystal` user data.

## Troubleshooting

### The command is unavailable in an older terminal

Open a new PowerShell or Command Prompt so it receives the persisted user PATH.

### A downloaded script is blocked

Run the review-first form with
`powershell -ExecutionPolicy Bypass -File .\install.ps1`. The installer does
not change your system execution policy.

### Inspect the installed layout

```powershell
crystal-lattice --runtime-layout-json
```

For direct ZIP extraction, see
[Manual installation](installation-manual.md).