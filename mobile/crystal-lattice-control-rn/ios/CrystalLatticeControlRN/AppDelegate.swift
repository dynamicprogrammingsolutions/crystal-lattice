import UIKit
import React
import React_RCTAppDelegate
import ReactAppDependencyProvider

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
  var window: UIWindow?

  var reactNativeDelegate: ReactNativeDelegate?
  var reactNativeFactory: RCTReactNativeFactory?

  func application(
    _ application: UIApplication,
    didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
  ) -> Bool {
    let delegate = ReactNativeDelegate()
    let factory = RCTReactNativeFactory(delegate: delegate)
    delegate.dependencyProvider = RCTAppDependencyProvider()

    reactNativeDelegate = delegate
    reactNativeFactory = factory

    window = UIWindow(frame: UIScreen.main.bounds)

    let arguments = ProcessInfo.processInfo.arguments
    let displayPresetIndex = arguments.firstIndex(where: {
      $0 == "-clcDisplayPreset" || $0 == "clcDisplayPreset"
    })
    let useLargestDisplayPreset =
      displayPresetIndex.map { index in
        arguments.indices.contains(index + 1) &&
          arguments[index + 1] == "largest"
      } ?? false
    let moduleName: String
    var initialProperties: [String: Any] = [:]
    for name in [
      "clcChatOperationsBaseUrl",
      "clcChatOperationsSessions",
      "clcDisplayPreset",
      "clcTranscriptAnchorStrategy",
    ] {
      if let index = arguments.firstIndex(where: { $0 == "-\(name)" || $0 == name }),
         arguments.indices.contains(index + 1) {
        initialProperties[name] = arguments[index + 1]
      }
    }
    if initialProperties["clcChatOperationsBaseUrl"] != nil {
      moduleName = "MobileChatOperationsHarness"
    } else if arguments.contains(where: {
      $0 == "-clcSessionListHarness" || $0 == "clcSessionListHarness"
    }) {
      moduleName = useLargestDisplayPreset
        ? "MobileSessionListLargestPresetHarness"
        : "MobileSessionListHarness"
    } else if arguments.contains(where: {
      $0 == "-clcTranscriptScrollHarness" || $0 == "clcTranscriptScrollHarness"
    }) {
      moduleName = "MobileTranscriptScrollHarness"
    } else if arguments.contains(where: {
      $0 == "-clcTranscriptRangeNavigationHarness" ||
        $0 == "clcTranscriptRangeNavigationHarness"
    }) {
      moduleName = "MobileTranscriptRangeNavigationHarness"
    } else if arguments.contains(where: {
      $0 == "-clcNotificationBannerHarness" || $0 == "clcNotificationBannerHarness"
    }) {
      moduleName = "MobileNotificationBannerHarness"
    } else if arguments.contains(where: {
      $0 == "-clcSelectableCodeBlockHarness" || $0 == "clcSelectableCodeBlockHarness"
    }) {
      moduleName = "MobileSelectableCodeBlockHarness"
    } else if arguments.contains(where: {
      $0 == "-clcOrderedListMarkdownHarness" || $0 == "clcOrderedListMarkdownHarness"
    }) {
      moduleName = "MobileOrderedListMarkdownHarness"
    } else if arguments.contains(where: {
      $0 == "-clcNotificationUiEffectsHarness" || $0 == "clcNotificationUiEffectsHarness"
    }) {
      moduleName = "MobileNotificationUiEffectsHarness"
    } else if arguments.contains(where: {
      $0 == "-clcWebsiteVisualHarness" || $0 == "clcWebsiteVisualHarness"
    }) {
      moduleName = "MobileWebsiteVisualHarness"
    } else if arguments.contains(where: {
      $0 == "-clcConnectionsSettingsHarness" || $0 == "clcConnectionsSettingsHarness"
    }) {
      moduleName = "MobileConnectionsSettingsHarness"
    } else if arguments.contains(where: {
      $0 == "-clcActionFormsHarness" || $0 == "clcActionFormsHarness"
    }) {
      moduleName = "MobileActionFormsHarness"
    } else if arguments.contains(where: {
      $0 == "-clcHomeHarness" || $0 == "clcHomeHarness"
    }) {
      moduleName = "MobileHomeHarness"
    } else if arguments.contains(where: {
      $0 == "-clcRichSessionUiHarness" || $0 == "clcRichSessionUiHarness"
    }) {
      moduleName = "MobileRichSessionUiHarness"
    } else if arguments.contains(where: {
      $0 == "-clcEmbeddedProviderMatrixHarness" ||
        $0 == "clcEmbeddedProviderMatrixHarness"
    }) {
      moduleName = "EmbeddedProviderMatrixDiagnostics"
    } else if arguments.contains(where: {
      $0 == "-clcEmbeddedPythonWebFetchHarness" ||
        $0 == "clcEmbeddedPythonWebFetchHarness"
    }) {
      moduleName = "EmbeddedPythonWebFetchDiagnostics"
    } else if arguments.contains(where: {
      $0 == "-clcEmbeddedPythonRuntimeHarness" ||
        $0 == "clcEmbeddedPythonRuntimeHarness"
    }) {
      moduleName = "EmbeddedPythonRuntimeDiagnostics"
    } else {
      moduleName = "CrystalLatticeControlRN"
    }

    for key in ["clcEmbeddedMatrixAgent", "clcEmbeddedMatrixAuthMode"] {
      if let index = arguments.firstIndex(where: {
        $0 == "-\(key)" || $0 == key
      }), arguments.indices.contains(index + 1) {
        initialProperties[key] = arguments[index + 1]
      }
    }
    factory.startReactNative(
      withModuleName: moduleName,
      in: window,
      initialProperties: initialProperties,
      launchOptions: launchOptions
    )

    return true
  }

  func application(
    _ application: UIApplication,
    open url: URL,
    options: [UIApplication.OpenURLOptionsKey: Any] = [:]
  ) -> Bool {
    RCTLinkingManager.application(application, open: url, options: options)
  }
}

class ReactNativeDelegate: RCTDefaultReactNativeFactoryDelegate {
  override func sourceURL(for bridge: RCTBridge) -> URL? {
    self.bundleURL()
  }

  override func bundleURL() -> URL? {
#if DEBUG
    RCTBundleURLProvider.sharedSettings().jsBundleURL(forBundleRoot: "index")
#else
    Bundle.main.url(forResource: "main", withExtension: "jsbundle")
#endif
  }
}
