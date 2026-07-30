const iosDevice = process.env.DETOX_IOS_DEVICE || "iPhone 17 Pro";
const androidAvd = process.env.DETOX_ANDROID_AVD || "Medium_Phone_API_36.1";

/** @type {Detox.DetoxConfig} */
module.exports = {
  testRunner: {
    args: {
      $0: "jest",
      config: "e2e/jest.config.js",
    },
    jest: {
      setupTimeout: 180000,
    },
  },
  artifacts: {
    rootDir: "artifacts/detox",
    plugins: {
      log: "failing",
      screenshot: "failing",
      video: "failing",
      uiHierarchy: "enabled",
    },
  },
  apps: {
    "ios.release": {
      type: "ios.app",
      binaryPath:
        "ios/build/Build/Products/Release-iphonesimulator/CrystalLattice.app",
      build:
        "xcodebuild -workspace ios/CrystalLatticeControlRN.xcworkspace -scheme CrystalLatticeControlRN -configuration Release -sdk iphonesimulator -derivedDataPath ios/build",
    },
    "android.e2e": {
      type: "android.apk",
      binaryPath: "android/app/build/outputs/apk/e2e/app-e2e.apk",
      testBinaryPath:
        "android/app/build/outputs/apk/androidTest/e2e/app-e2e-androidTest.apk",
      build:
        "scripts/ensure_android_debug_keystore.sh && cd android && ./gradlew :app:assembleE2e :app:assembleE2eAndroidTest -DtestBuildType=e2e",
    },
  },
  devices: {
    iosSimulator: {
      type: "ios.simulator",
      device: {
        type: iosDevice,
      },
    },
    androidEmulator: {
      type: "android.emulator",
      device: {
        avdName: androidAvd,
      },
      readonly: true,
    },
  },
  configurations: {
    "ios.sim.release": {
      device: "iosSimulator",
      app: "ios.release",
    },
    "android.emu.e2e": {
      device: "androidEmulator",
      app: "android.e2e",
      artifacts: {
        plugins: {
          video: "none",
        },
      },
    },
  },
};
