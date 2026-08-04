# Prepare iOS Branding Assets

Generate and wire the iOS app icon assets from the existing Crystal Lattice SVG icon used by the landing page and splash screen.

## Requirements checklist

- [x] Locate the source SVG icon used by the landing page and splash screen.
- [x] Generate the full iOS `AppIcon.appiconset` PNG set from the source SVG, including the `1024x1024` marketing icon.
- [x] Update `Contents.json` filenames if needed.
- [x] Verify the icon renders in the app icon/home screen/TestFlight context.
- [x] Confirm the splash screen and in-app logo continue to use the intended SVG path.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/010-preflight-audit.md

## Known Starting State

The app has SVG icon sources under:

- `mobile/crystal-lattice-control-rn/src/assets/icons/icon.svg`
- `mobile/crystal-lattice-control-rn/src/assets/icons/icon_dark.svg`
- `mobile/crystal-lattice-control-rn/src/assets/icons/SvgAssets.ts`

The splash/logo code uses:

- `mobile/crystal-lattice-control-rn/src/components/AnimatedSplashScreen.tsx`
- `mobile/crystal-lattice-control-rn/src/components/AppLogo.tsx`

The iOS app icon asset set currently has only:

- `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/Images.xcassets/AppIcon.appiconset/Contents.json`

No actual app icon PNG files were present in that asset set during the audit.

## Implementation Notes

Use a deterministic script/tooling approach if possible so icons can be regenerated from the SVG. Acceptable approaches include a small documented generation script, `sharp`, ImageMagick, or another existing/reasonable tool. Avoid manually editing binary assets in ways that future maintainers cannot reproduce.

Recommended icon sizes to include are the sizes required by the current Xcode `AppIcon.appiconset/Contents.json`, including iPhone notification/settings/spotlight/app sizes and the iOS marketing icon.

## Acceptance Criteria

- `AppIcon.appiconset` contains real PNG files referenced by `Contents.json`.
- Xcode build does not warn about missing app icon files.
- Generated assets are derived from the approved existing SVG icon.

## Completion Notes

Added during completion on 2026-07-05.

Completed iOS app icon asset generation.

- Confirmed `mobile/crystal-lattice-control-rn/src/assets/icons/icon.svg` and `landing_page/public/icon.svg` are byte-identical by SHA-256.
- Added reproducible icon generation script:
  - `mobile/crystal-lattice-control-rn/scripts/generate_ios_app_icons.sh`
- Added package script:

```bash
cd mobile/crystal-lattice-control-rn
npm run ios:icons
```

- Generated PNGs in `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/Images.xcassets/AppIcon.appiconset`:
  - `Icon-App-20x20@2x.png`
  - `Icon-App-20x20@3x.png`
  - `Icon-App-29x29@2x.png`
  - `Icon-App-29x29@3x.png`
  - `Icon-App-40x40@2x.png`
  - `Icon-App-40x40@3x.png`
  - `Icon-App-60x60@2x.png`
  - `Icon-App-60x60@3x.png`
  - `Icon-App-1024x1024@1x.png`
- Updated `Contents.json` to reference every generated PNG.
- The generated PNGs are square RGB files with a white background and padding, derived from the approved SVG source.
- Verified with a Debug iOS simulator build:

```bash
xcodebuild -workspace mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN.xcworkspace \
  -scheme CrystalLatticeControlRN \
  -configuration Debug \
  -destination 'generic/platform=iOS Simulator' \
  build
```

Result: build succeeded. Xcode did not report missing app icon files. Final visual confirmation on a physical device/TestFlight install remains part of `tasks/20260614-ios-testflight-github-fastlane/090-first-testflight-dry-run.md`.
