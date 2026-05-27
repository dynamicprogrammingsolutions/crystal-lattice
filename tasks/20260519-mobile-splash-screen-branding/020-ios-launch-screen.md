# iOS Launch Screen

Redesign `LaunchScreen.storyboard` so cold launch shows Crystal Lattice Control branding instead of Bonjour-example defaults.

## Requirements checklist

- [x] Replace `BonjourExampleRN` title with `Crystal Lattice Control`
- [x] Remove “Powered by React Native” label and constraints
- [x] Add centered `UIImageView` using `SplashIcon` asset above title
- [x] Add subtitle `Connect to your agent` with secondary label styling
- [x] Use semantic system colors for light/dark (`systemBackground`, `label`, `secondaryLabel`)
- [x] Center icon + text group vertically with safe area constraints

Parent Task: `tasks/20260519-mobile-splash-screen-branding/000-main.md`

Depends On: `tasks/20260519-mobile-splash-screen-branding/010-design-and-assets.md`

## Current bug (reference)

```19:27:mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/LaunchScreen.storyboard
<label ... text="BonjourExampleRN" ...>
<label ... text="Powered by React Native" ...>
```

`Info.plist` already sets `UILaunchStoryboardName` to `LaunchScreen` — no plist change required.

## Files to touch

- `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/LaunchScreen.storyboard`
- `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/Images.xcassets/SplashIcon.imageset/` (new)

`Images.xcassets` is already in the Xcode target resources (`project.pbxproj`); new imageset is picked up automatically.
