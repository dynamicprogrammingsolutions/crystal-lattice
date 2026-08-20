# Publish Clear Desktop Distribution Options

Add a desktop landing/download experience that clearly separates the app-only
DMG from the app-plus-CLI PKGs and directs users to the correct architecture
and installation instructions.

## Requirements checklist

- [ ] A public `/desktop` route presents two primary choices: `Desktop app only` and `Desktop app + CLI`.
- [ ] The app-only choice downloads the retained DMG and explains that a compatible `crystal-lattice` terminal command must be installed separately for workspace startup.
- [ ] The app-plus-CLI choice offers clearly labeled Apple Silicon and Intel PKGs and explains that the installer adds the terminal command.
- [ ] Version, supported macOS version, architecture, file type, file size where available, checksums, release notes, installation, Gatekeeper, upgrade, support, privacy, license, and source links are accurate.
- [ ] Download URLs come from maintained release metadata/configuration and do not require manual code edits for every version where practical.
- [ ] Navigation/footer discoverability, responsive layout, accessibility, production deployment, and download behavior are verified.
- [ ] Existing mobile, privacy, support, and home-page claims remain accurate and distinguish desktop from mobile behavior.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
Depends On: tasks/20260820-macos-desktop-distribution/100-automated-combined-installer-release.md

## Approved presentation

- `Desktop app only` → universal notarized DMG.
- `Desktop app + CLI` → notarized PKG, with separate Apple Silicon and Intel downloads.
- Workspace onboarding is available in both app builds.
- The DMG description must not imply that it installs the CLI; it assumes the user already has compatible CLI terminal commands.

## Execution plan
Status: Draft

Add an authored Astro desktop page using the existing section/content system
and design language. Integrate release metadata or stable download endpoints,
add navigation/footer routes, provide architecture guidance, and update
privacy/support wording for the desktop client. Verify local builds and the
production deployment/download path.

### Implementation decisions and open questions

- Prefer explicit architecture buttons over unreliable browser architecture detection.
- Keep the two choices visually equal and explain the difference in one sentence before detailed instructions.
- Do not expose internal workflow, task, signing, or approval terminology in public copy.
- If dynamic release metadata would require disproportionate infrastructure, use a maintained build-time data file with validation against published assets.

### Documentation

- `landing_page/` owns public download and marketing copy.
- Desktop package user documentation owns detailed installation/troubleshooting and should be linked where useful.
- Privacy and support pages must describe current desktop behavior and self-hosted runtime expectations.
- Update `landing_page/README.md` only when maintainers need new build variables, data files, or release integration instructions.

### Task checklist

- [ ] Add `/desktop` route and content/components.
- [ ] Add the two approved distribution choices and architecture-specific PKG links.
- [ ] Add version/support/checksum/release metadata integration.
- [ ] Update navigation and footer discoverability.
- [ ] Update privacy and support text for desktop.
- [ ] Add responsive/accessibility/content tests where supported.
- [ ] Build and preview the landing site.
- [ ] Deploy and verify production URLs and downloads.

### Requirement verification

- Verify every production button downloads the intended signed file and matches displayed version/checksum.
- Verify DMG and PKG descriptions accurately state CLI inclusion.
- Verify keyboard, screen-size, contrast, link, and semantic behavior.
- Verify mobile and existing site routes remain unchanged except for approved navigation/copy updates.

### Additional implementation verification

- Test missing or stale release metadata as a build failure rather than silently rendering broken links.
- Verify CDN cache headers and invalidation allow new releases to become visible predictably.