# Android Splash Theme

Add a native splash theme and drawable so Android cold start matches iOS branding.

## Requirements checklist

- [ ] Add `res/values/colors.xml` and `res/values-night/colors.xml` with `splash_background`
- [ ] Add `res/drawable/splash_screen.xml` layer-list (background + centered launcher icon)
- [ ] Add `SplashTheme` with `windowBackground` and API 31+ `windowSplashScreen*` + `postSplashScreenTheme`
- [ ] Set `MainActivity` `android:theme="@style/SplashTheme"` in `AndroidManifest.xml`
- [ ] Keep `application` theme as `AppTheme` for post-splash UI

Parent Task: `tasks/20260519-mobile-splash-screen-branding/000-main.md`

Depends On: `tasks/20260519-mobile-splash-screen-branding/010-design-and-assets.md`

## Reference

- `minSdkVersion` is 24; SplashScreen API attributes apply on API 31+ via `values-v31/styles.xml`.
- Launcher icons: `res/mipmap-*/ic_launcher.png`
- `MainActivity.kt` enables edge-to-edge after splash — `postSplashScreenTheme` must be `AppTheme`.

## Files to touch

- `android/app/src/main/res/values/colors.xml` (new)
- `android/app/src/main/res/values-night/colors.xml` (new)
- `android/app/src/main/res/values/styles.xml`
- `android/app/src/main/res/values-v31/styles.xml` (new)
- `android/app/src/main/res/drawable/splash_screen.xml` (new)
- `android/app/src/main/AndroidManifest.xml`
