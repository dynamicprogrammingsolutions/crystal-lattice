# Prepare Android Branding And Google Play Media

Generate modern Android launcher/splash resources and the Google Play listing
media needed for a credible internal, closed, and eventual production release.

## Requirements checklist

- [ ] Android launcher resources are reproducibly generated from the approved
      Crystal Lattice SVG source.
- [ ] Legacy, round, adaptive, and themed/monochrome launcher behavior is
      complete for supported Android versions.
- [ ] Light and dark splash branding remains correct.
- [ ] A compliant 512×512 Google Play icon and 1024×500 feature graphic are
      prepared.
- [ ] Required phone screenshot scenarios and capture dimensions are defined;
      final screenshots accurately show current app behavior.
- [ ] Generated assets pass automated dimension/format checks and human visual
      review on representative launchers.

Parent Task: tasks/20260820-android-google-play-github-fastlane/000-main.md
Depends On: tasks/20260820-android-google-play-github-fastlane/020-android-release-build-audit.md

## Required reading

Read the parent task's `Shared required reading`, then:

- `mobile/crystal-lattice-control-rn/src/assets/icons/icon.svg`
- `mobile/crystal-lattice-control-rn/src/assets/icons/icon_dark.svg`
- `mobile/crystal-lattice-control-rn/scripts/generate_ios_app_icons.sh`
- `mobile/crystal-lattice-control-rn/android/app/src/main/res/`
- `tasks/20260614-ios-testflight-github-fastlane/030-ios-branding-assets.md`
- Adaptive icons:
  https://developer.android.com/develop/ui/views/launch/icon_design_adaptive
- Themed icons:
  https://developer.android.com/develop/ui/views/launch/icon_design_adaptive#themed
- Play graphic requirements:
  https://support.google.com/googleplay/android-developer/answer/9866151

## Known starting state

- Approved source icons exist as light/dark SVG files.
- Android has PNG launcher and round icons in mdpi through xxxhdpi.
- Android has 192×192 light/dark splash PNGs.
- No `mipmap-anydpi-v26` adaptive-icon XML, foreground/background layers, or
  Android 13 monochrome icon was found.
- No dedicated 512×512 Play icon or 1024×500 feature graphic was found.
- Existing iOS icon generation uses `rsvg-convert` and ImageMagick and can
  provide a reproducible pattern.
- Existing marketing screenshot source:
  `landing_page/public/cl-mobile-frame.png`; verify that it reflects the current
  app before reuse.

## Execution plan

Status: Draft

Build a deterministic Android asset generator from the approved SVG. Preserve
safe-zone padding and verify masking on round, squircle, and other adaptive
launcher shapes. Generate store media in source-controlled, reproducible form
where practical. Do not fabricate screenshots of behavior the app does not
currently provide.

### Implementation decisions and open questions

- Decision: use the existing approved SVG as the logo source.
- Recommendation: use a solid approved background with a foreground safe zone
  matching the current white/padded icon treatment.
- Recommendation: supply a monochrome vector/layer for themed icons.
- Open design decision: feature-graphic composition, tagline, and approved
  screenshot captions require owner visual approval.
- Open distribution question: phone-only screenshots initially, unless tablet
  optimization is intentionally claimed.

### Documentation

- Document the regeneration command in the mobile package.
- Keep store-copy/media source guidance in package development docs, not in
  generated resource directories.

### Task checklist

- [ ] Confirm light/dark SVG source and brand colors.
- [ ] Add a deterministic Android icon-generation script.
- [ ] Generate density, round, adaptive, and monochrome launcher resources.
- [ ] Verify Android 12+ splash integration in light/dark mode.
- [ ] Generate the 512×512 Play icon.
- [ ] Create the 1024×500 feature graphic source and export.
- [ ] Define and capture current phone screenshot scenarios.
- [ ] Run dimension/format checks and physical/emulator visual review.

### Requirement verification

- Generated assets: script output is deterministic and source-controlled.
- Launcher behavior: human verification on at least one pre-Android-13 and one
  Android-13+ launcher, including themed icon mode.
- Splash behavior: light/dark cold-launch verification.
- Store media: exact pixel dimensions and accepted formats.
- Screenshot truthfulness: compare each image with a current build and recorded
  scenario.

### Additional implementation verification

- Run Release resource processing and check for missing/duplicate icon warnings.
- Verify no unintended transparency or clipped foreground under common masks.