# Splash Screen Verification

Manual QA for branded native splash on iOS and Android.

## Requirements checklist

- [ ] iOS cold launch: title is Crystal Lattice Control, not BonjourExampleRN
- [ ] iOS: no “Powered by React Native”
- [ ] iOS light and dark mode: readable background and text
- [x] Android cold launch: branded background + icon, smooth handoff to RN
- [x] Android light and dark mode
- [x] No obvious double-flash between splash and first app frame

Parent Task: `tasks/20260519-mobile-splash-screen-branding/000-main.md`

Depends On:
- `tasks/20260519-mobile-splash-screen-branding/020-ios-launch-screen.md`
- `tasks/20260519-mobile-splash-screen-branding/030-android-splash-theme.md`

## Commands

```bash
cd mobile/crystal-lattice-control-rn && npm run ios
cd mobile/crystal-lattice-control-rn && npm run android
```

Test cold start: force-quit app, relaunch. Toggle system appearance for dark mode checks.
