# Mobile Splash Screen Branding

Replace stale Bonjour-example launch branding on the React Native mobile app with a native Crystal Lattice Control splash on iOS and Android.

## Task checklist

- [x] `tasks/20260519-mobile-splash-screen-branding/010-design-and-assets.md`
- [x] `tasks/20260519-mobile-splash-screen-branding/020-ios-launch-screen.md`
- [x] `tasks/20260519-mobile-splash-screen-branding/030-android-splash-theme.md`
- [ ] `tasks/20260519-mobile-splash-screen-branding/040-verification.md`

## Context summary

- Wrong splash title comes from `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/LaunchScreen.storyboard` (`text="BonjourExampleRN"` and `text="Powered by React Native"`).
- Home-screen display name is already correct (`Crystal Lattice Control`) in `app.json`, `Info.plist`, and `strings.xml`.
- Android has no dedicated splash theme today; only `AppTheme` on `MainActivity`.
- Approach: **native-only** (no `react-native-bootsplash`).
- Brand colors from `mobile/crystal-lattice-control-rn/src/theme.ts`: light background `#F2F2F7`, dark `#000000`, primary `#007AFF` / `#0A84FF`, muted text `#8E8E93`.
- Related but separate: distribution iOS readiness in `tasks/20260421-distribution-release-workstreams/080-ios-release-distribution-and-review-readiness.md`.

## Recommended sequencing

1. Lock design in 010 (icon reuse, subtitle, colors).
2. iOS storyboard (020) — fixes the reported bug on iOS.
3. Android splash theme (030).
4. Manual QA (040).
