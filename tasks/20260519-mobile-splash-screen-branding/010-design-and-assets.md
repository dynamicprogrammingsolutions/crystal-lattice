# Design And Assets For Mobile Splash

Lock the visual spec and asset strategy for Crystal Lattice Control native launch screens.

## Requirements checklist

- [ ] Confirm layout: centered icon, title, optional subtitle; portrait only
- [ ] Confirm colors align with `src/theme.ts` light/dark backgrounds and text
- [ ] Confirm iOS uses `SplashIcon` imageset (launcher icon copied from Android mipmap)
- [ ] Confirm subtitle copy: `Connect to your agent` (muted secondary)
- [ ] Confirm no “Powered by React Native” or Bonjour-example strings on splash

Parent Task: `tasks/20260519-mobile-splash-screen-branding/000-main.md`

## Locked design (v1)

| Element | Light | Dark |
|---------|-------|------|
| Background | `#F2F2F7` / iOS `systemBackground` | `#000000` |
| Title | `Crystal Lattice Control`, bold, primary label color | same |
| Subtitle | `Connect to your agent`, `#8E8E93` / `secondaryLabel` | same |
| Icon | 96pt logical square (`SplashIcon` @3x from `mipmap-xxhdpi/ic_launcher.png`) | same |

**Layout:** Vertical stack centered in safe area — icon, 16pt gap, title, 8pt gap, subtitle.

**Assets:** `ios/.../Images.xcassets/SplashIcon.imageset` — single 144×144 PNG (`splash-icon.png`) copied from Android `ic_launcher.png`. `AppIcon.appiconset` has no PNGs in repo; do not block on App Store icon set.

**Out of scope:** New logo design, animation, `react-native-bootsplash`, renaming `BonjourExampleRN` internal package names.
