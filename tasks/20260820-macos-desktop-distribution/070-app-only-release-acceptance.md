# Accept The Automated App-Only DMG Release

Validate the published app-only DMG as an independent release product before
bundled-CLI and PKG work begins.

## Requirements checklist

- [x] A release candidate DMG is produced by GitHub Actions, published through the intended release/download path, and downloaded as an end user would obtain it.
- [x] Gatekeeper, signature, notarization, stapling, checksum, version, bundle identity, architecture, and privacy resources are independently verified.
- [ ] Installation and first launch succeed on a clean Apple Silicon Mac.
- [ ] Installation and first launch succeed on a clean Intel Mac or an approved equivalent real-architecture environment.
- [ ] Core desktop connection/session behavior works without Metro, source checkout, development credentials, or bundled CLI assumptions.
- [ ] Human observations, defects, waivers, and acceptance are recorded; unresolved release blockers keep this subtask incomplete.

Parent Task: tasks/20260820-macos-desktop-distribution/000-main.md
Historical dependency (retired):
tasks/20260820-macos-desktop-distribution/060-automated-app-only-release.md

## Supersession — October 7, 2026

Disposition: done by user-approved supersession on October 7, 2026.

SUPERSEDED BY: tasks/20260928-universal-macos-desktop-fastlane-release.md

This closes the task as historical work; it does not mark its unmet original
requirements fulfilled. Its former execution dependency is retired.

Its public-candidate and technical security/metadata checks have September 30
evidence. The replacement explicitly defers real Intel hardware feedback to
initial testers and requires automated universal validation. This differs from
the original mandatory clean Intel gate, which remains unchecked as retired
scope rather than being falsely marked passed.

Explicit Apple Silicon public-artifact human acceptance remains open in the
replacement record. No clean-machine or subjective observations are inferred
from workflow success. That replacement record is the active prerequisite for
bundled-CLI work; the original Draft plan is retained as history.

## Manual verification boundary

This is an acceptance gate. Automated checks provide evidence but do not
replace human confirmation of download, Finder installation, Gatekeeper
presentation, application menus, icon, first-launch behavior, and basic
interaction on clean systems.

## Execution plan
Status: Draft

Create or select a release candidate from the protected DMG workflow. Download
it through the public-intended path on clean Apple Silicon and Intel systems,
verify integrity and security metadata, install it through Finder, and execute
a concise user workflow against a separately running self-hosted Crystal
Lattice runtime. Record exact versions, systems, URLs, workflow run, checksum,
results, and any corrective reruns.

### Implementation decisions and open questions

- Do not accept a workflow artifact alone when the intended product is a GitHub/download-domain release.
- A GitHub-hosted runner can supplement architecture checks but does not replace human Gatekeeper/Finder acceptance.
- If Intel hardware is unavailable, propose a concrete equivalent and obtain approval before marking the Intel requirement complete.

### Documentation

- Correct current public installation/troubleshooting text when acceptance exposes a user-visible issue.
- Keep detailed acceptance evidence in this task, not in consumer documentation.

### Task checklist

- [ ] Select and record the release candidate workflow run and source commit.
- [ ] Download and checksum the published DMG.
- [ ] Verify signature, notarization, stapling, Gatekeeper, metadata, and architectures.
- [ ] Install and launch on clean Apple Silicon.
- [ ] Install and launch on clean Intel.
- [ ] Exercise local connection, sessions, messages, settings/actions as appropriate, and quit/relaunch.
- [ ] Review icon, display name, menus, privacy/support links, and diagnostics.
- [ ] Record human acceptance or blocking defects.

### Requirement verification

- Map every requirement to a command result, workflow/release reference, screenshot/observation, or named human confirmation.
- Leave architecture or human-verification requirements unchecked when evidence is unavailable.
- Confirm the candidate remains app-only and does not create a `crystal-lattice` terminal command.

### Additional implementation verification

- Test offline launch after ticket stapling and prior successful installation.
- Verify moving the app from the mounted DMG to Applications does not alter signatures.