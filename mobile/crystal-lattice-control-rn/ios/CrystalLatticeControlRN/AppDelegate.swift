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
    let moduleName: String
    if arguments.contains(where: {
      $0 == "-clcSessionListHarness" || $0 == "clcSessionListHarness"
    }) {
      moduleName = "MobileSessionListHarness"
    } else if arguments.contains(where: {
      $0 == "-clcTranscriptScrollHarness" || $0 == "clcTranscriptScrollHarness"
    }) {
      moduleName = "MobileTranscriptScrollHarness"
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
    } else {
      moduleName = "CrystalLatticeControlRN"
    }

    factory.startReactNative(
      withModuleName: moduleName,
      in: window,
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
