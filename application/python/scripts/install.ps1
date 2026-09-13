& {
    $ErrorActionPreference = "Stop"

    $PackageName = "crystal-lattice-cli"
    $ArchivePackageName = "crystal-lattice-python-runtime"
    $CommandName = if ($env:COMMAND_NAME) { $env:COMMAND_NAME } else { "crystal-lattice" }
    $DefaultDownloadBaseUrl = "https://download.crystallattice.dev/crystal-lattice-cli"
    $DownloadBaseUrl = if ($env:CRYSTAL_LATTICE_DOWNLOAD_BASE_URL) {
        $env:CRYSTAL_LATTICE_DOWNLOAD_BASE_URL
    } elseif ($env:DOWNLOAD_BASE_URL) {
        $env:DOWNLOAD_BASE_URL
    } else {
        $DefaultDownloadBaseUrl
    }
    $UserProfile = if ($env:USERPROFILE) { $env:USERPROFILE } else { $HOME }
    $InstallRoot = if ($env:INSTALL_ROOT) {
        $env:INSTALL_ROOT
    } else {
        Join-Path $UserProfile ".local\opt\$PackageName"
    }
    $LocalArchive = $env:CRYSTAL_LATTICE_PYTHON_RUNTIME_ARCHIVE
    $Script:TemporaryDirectory = $null
    $Script:LogStepIndex = 0
    $LogStepTotal = 5

    function Write-InstallStep {
        param([Parameter(Mandatory = $true)][string]$Message)
        $Script:LogStepIndex += 1
        Write-Host "[$($Script:LogStepIndex)/$LogStepTotal] $Message"
    }

    function Write-InstallDetail {
        param([Parameter(Mandatory = $true)][string]$Message)
        Write-Host "      $Message"
    }

    function Fail-Install {
        param([Parameter(Mandatory = $true)][string]$Message)
        throw "error: $Message"
    }

    function Normalize-ReleaseTag {
        param([Parameter(Mandatory = $true)][string]$Value)
        $trimmed = $Value.Trim()
        if (-not $trimmed) {
            Fail-Install "release version cannot be empty"
        }
        if ($trimmed.StartsWith("crystal-lattice-cli-v")) {
            return $trimmed
        }
        if ($trimmed.StartsWith("v")) {
            return "crystal-lattice-cli-$trimmed"
        }
        return "crystal-lattice-cli-v$trimmed"
    }

    function Get-NativeTarget {
        if ($env:OS -ne "Windows_NT") {
            Fail-Install "the PowerShell installer supports Windows only"
        }

        $architecture = $null
        try {
            $architecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
        } catch {
            if ($env:PROCESSOR_ARCHITEW6432) {
                $architecture = $env:PROCESSOR_ARCHITEW6432
            } else {
                $architecture = $env:PROCESSOR_ARCHITECTURE
            }
        }

        switch -Regex ($architecture) {
            "^(X64|AMD64|x86_64)$" { return "windows-amd64" }
            "^(Arm64|ARM64|aarch64)$" { return "windows-arm64" }
            default {
                Fail-Install "unsupported Windows architecture: $architecture"
            }
        }
    }

    function Get-LatestReleaseTag {
        $url = "$DownloadBaseUrl/latest.txt"
        $latest = (Invoke-RestMethod -Uri $url).ToString().Trim()
        if (-not $latest) {
            Fail-Install "latest version marker was empty: $url"
        }
        return Normalize-ReleaseTag $latest
    }

    function Get-NormalizedPath {
        param([Parameter(Mandatory = $true)][string]$Path)
        $expanded = [Environment]::ExpandEnvironmentVariables($Path.Trim().Trim('"'))
        $fullPath = [IO.Path]::GetFullPath($expanded)
        $root = [IO.Path]::GetPathRoot($fullPath)
        if ([StringComparer]::OrdinalIgnoreCase.Equals($fullPath, $root)) {
            return $root
        }
        return $fullPath.TrimEnd([char[]]@('\', '/'))
    }

    function Test-PathListContains {
        param(
            [AllowEmptyString()][string]$PathList,
            [Parameter(Mandatory = $true)][string]$Directory
        )
        $requested = Get-NormalizedPath $Directory
        foreach ($entry in ($PathList -split ";")) {
            if (-not $entry.Trim()) {
                continue
            }
            try {
                $candidate = Get-NormalizedPath $entry
            } catch {
                continue
            }
            if ([StringComparer]::OrdinalIgnoreCase.Equals($candidate, $requested)) {
                return $true
            }
        }
        return $false
    }

    function Assert-WritableDirectory {
        param([Parameter(Mandatory = $true)][string]$Directory)
        New-Item -ItemType Directory -Path $Directory -Force | Out-Null
        $probe = Join-Path $Directory ".crystal-lattice-write-$([Guid]::NewGuid().ToString('N'))"
        try {
            [IO.File]::WriteAllText($probe, "")
        } catch {
            Fail-Install "command directory is not writable: $Directory"
        } finally {
            Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue
        }
    }

    function Find-ExistingRuntimeCommandDirectory {
        $candidate = Get-Command "$CommandName.cmd" -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if (-not $candidate) {
            $candidate = Get-Command $CommandName -CommandType Application -ErrorAction SilentlyContinue |
                Select-Object -First 1
        }
        if (-not $candidate -or -not $candidate.Source) {
            return $null
        }

        try {
            $layoutText = (& $candidate.Source --runtime-layout-json 2>$null | Out-String)
            if ($LASTEXITCODE -ne 0) {
                return $null
            }
            $layout = $layoutText | ConvertFrom-Json
            if ($layout.layout -ne "python-runtime") {
                return $null
            }
            $directory = Split-Path -Parent $candidate.Source
            Assert-WritableDirectory $directory
            return Get-NormalizedPath $directory
        } catch {
            return $null
        }
    }

    function Add-UserPathDirectory {
        param([Parameter(Mandatory = $true)][string]$Directory)
        $normalized = Get-NormalizedPath $Directory
        $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if (-not (Test-PathListContains $userPath $normalized)) {
            $newUserPath = if ($userPath -and $userPath.Trim()) {
                "$($userPath.TrimEnd(';'));$normalized"
            } else {
                $normalized
            }
            try {
                [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
            } catch {
                Fail-Install "could not add the command directory to the user PATH: $normalized"
            }
        }
        if (-not (Test-PathListContains $env:Path $normalized)) {
            $env:Path = "$normalized;$env:Path"
        }
    }

    function Resolve-CommandDirectory {
        if ($env:BIN_DIR) {
            $explicit = Get-NormalizedPath $env:BIN_DIR
            Assert-WritableDirectory $explicit
            return @{
                Path = $explicit
                Persisted = $false
            }
        }

        $existing = Find-ExistingRuntimeCommandDirectory
        if ($existing) {
            return @{
                Path = $existing
                Persisted = $false
            }
        }

        $localAppData = if ($env:LOCALAPPDATA) {
            $env:LOCALAPPDATA
        } else {
            Join-Path $UserProfile "AppData\Local"
        }
        $fallback = Get-NormalizedPath (
            Join-Path $localAppData "Programs\Crystal Lattice\bin"
        )
        Assert-WritableDirectory $fallback
        Add-UserPathDirectory $fallback
        return @{
            Path = $fallback
            Persisted = $true
        }
    }

    function Download-Archive {
        param(
            [Parameter(Mandatory = $true)][string]$Url,
            [Parameter(Mandatory = $true)][string]$Destination
        )
        Invoke-WebRequest -Uri $Url -OutFile $Destination -UseBasicParsing
    }

    function Install-RuntimeBundle {
        param(
            [Parameter(Mandatory = $true)][string]$Archive,
            [Parameter(Mandatory = $true)][string]$ArchiveStem,
            [Parameter(Mandatory = $true)][string]$CommandDirectory
        )
        $extractDirectory = Join-Path $Script:TemporaryDirectory "extract"
        New-Item -ItemType Directory -Path $extractDirectory -Force | Out-Null
        Expand-Archive -LiteralPath $Archive -DestinationPath $extractDirectory -Force

        $extractedBundle = Join-Path $extractDirectory $ArchiveStem
        if (-not (Test-Path -LiteralPath $extractedBundle -PathType Container)) {
            Fail-Install "archive did not contain expected directory: $ArchiveStem"
        }
        $extractedLauncher = Join-Path $extractedBundle "Scripts\crystal-lattice.cmd"
        if (-not (Test-Path -LiteralPath $extractedLauncher -PathType Leaf)) {
            Fail-Install "archive did not contain launcher Scripts\crystal-lattice.cmd"
        }

        New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
        $targetBundle = Join-Path $InstallRoot $ArchiveStem
        $stagingBundle = Join-Path $InstallRoot ".$ArchiveStem.staging"
        Remove-Item -LiteralPath $stagingBundle -Recurse -Force -ErrorAction SilentlyContinue
        Move-Item -LiteralPath $extractedBundle -Destination $stagingBundle
        Remove-Item -LiteralPath $targetBundle -Recurse -Force -ErrorAction SilentlyContinue
        Move-Item -LiteralPath $stagingBundle -Destination $targetBundle

        $targetLauncher = Join-Path $targetBundle "Scripts\crystal-lattice.cmd"
        $installedCommand = Join-Path $CommandDirectory "$CommandName.cmd"
        $commandText = "@echo off`r`ncall `"$targetLauncher`" %*`r`n"
        [IO.File]::WriteAllText($installedCommand, $commandText, [Text.Encoding]::ASCII)

        return @{
            Bundle = $targetBundle
            Command = $installedCommand
        }
    }

    function Verify-InstalledCommand {
        param([Parameter(Mandatory = $true)][string]$CommandPath)
        & $CommandPath --help *> $null
        if ($LASTEXITCODE -ne 0) {
            Fail-Install "installed command failed its help check"
        }
        $layoutText = (& $CommandPath --runtime-layout-json | Out-String)
        if ($LASTEXITCODE -ne 0) {
            Fail-Install "installed command failed its runtime-layout check"
        }
        $layout = $layoutText | ConvertFrom-Json
        if ($layout.layout -ne "python-runtime") {
            Fail-Install "installed command did not report python-runtime layout"
        }
        if (-not ($layoutText -match "[/\\]plugins")) {
            Fail-Install "installed command did not report bundled plugin source path"
        }
    }

    if ($CommandName -notmatch "^[A-Za-z0-9._-]+$") {
        Fail-Install "invalid command name: $CommandName"
    }
    $InstallRoot = Get-NormalizedPath $InstallRoot

    try {
        Write-InstallStep "Checking installer prerequisites and command location"
        $commandSelection = Resolve-CommandDirectory
        $BinDirectory = $commandSelection.Path
        Write-InstallDetail "command directory: $BinDirectory"

        Write-InstallStep "Resolving the target platform and release"
        $target = Get-NativeTarget
        Write-InstallDetail "target: $target"

        $Script:TemporaryDirectory = Join-Path (
            [IO.Path]::GetTempPath()
        ) "crystal-lattice-install-$([Guid]::NewGuid().ToString('N'))"
        New-Item -ItemType Directory -Path $Script:TemporaryDirectory -Force | Out-Null

        if ($LocalArchive) {
            $archivePath = Get-NormalizedPath $LocalArchive
            if (-not (Test-Path -LiteralPath $archivePath -PathType Leaf)) {
                Fail-Install "local archive does not exist: $archivePath"
            }
            $archiveName = Split-Path -Leaf $archivePath
            $pattern = "^$([Regex]::Escape($ArchivePackageName))-v(?<version>.+)-$([Regex]::Escape($target))\.zip$"
            if ($archiveName -notmatch $pattern) {
                Fail-Install "local archive does not match current target ${target}: $archiveName"
            }
            $version = $Matches.version
            $tag = "crystal-lattice-cli-v$version"
            $archiveStem = [IO.Path]::GetFileNameWithoutExtension($archiveName)
        } else {
            $tag = if ($env:VERSION) {
                Normalize-ReleaseTag $env:VERSION
            } else {
                Get-LatestReleaseTag
            }
            $version = $tag.Substring("crystal-lattice-cli-v".Length)
            $archiveStem = "$ArchivePackageName-v$version-$target"
            $archiveName = "$archiveStem.zip"
            $archivePath = Join-Path $Script:TemporaryDirectory $archiveName
            $archiveUrl = "$DownloadBaseUrl/$archiveName"
        }
        Write-InstallDetail "release: $tag"

        Write-InstallStep "Acquiring the bundled-Python archive"
        if ($LocalArchive) {
            Write-InstallDetail "Installing $PackageName $tag for $target from $archivePath"
        } else {
            Write-InstallDetail "Downloading $archiveUrl"
            Download-Archive -Url $archiveUrl -Destination $archivePath
        }

        Write-InstallStep "Installing the runtime and command"
        $installed = Install-RuntimeBundle `
            -Archive $archivePath `
            -ArchiveStem $archiveStem `
            -CommandDirectory $BinDirectory

        Write-InstallStep "Verifying the installed command"
        Verify-InstalledCommand $installed.Command

        Write-InstallDetail "Installed bundle: $($installed.Bundle)"
        Write-InstallDetail "Installed command: $($installed.Command)"
        if ($commandSelection.Persisted) {
            Write-InstallDetail "Added command directory to user PATH: $BinDirectory"
        } elseif (-not (Test-PathListContains $env:Path $BinDirectory)) {
            Write-InstallDetail "Add this directory to PATH if needed: $BinDirectory"
        }
    } finally {
        if ($Script:TemporaryDirectory) {
            Remove-Item -LiteralPath $Script:TemporaryDirectory -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}