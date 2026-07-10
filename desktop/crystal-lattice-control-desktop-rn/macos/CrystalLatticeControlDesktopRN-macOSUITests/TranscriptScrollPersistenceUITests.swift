import XCTest

final class TranscriptScrollPersistenceUITests: XCTestCase {
  private let stateURL = URL(fileURLWithPath: "/tmp/clc-progressive-scroll-harness-state.json")
  private let commandURL = URL(fileURLWithPath: "/tmp/clc-progressive-scroll-harness-command.json")
  private let progressiveOptInURL =
    URL(fileURLWithPath: "/tmp/clc-include-progressive-transcript-scroll-tests")
  private var runId = ""

  override func setUpWithError() throws {
    continueAfterFailure = false
    try? FileManager.default.removeItem(at: stateURL)
    try? FileManager.default.removeItem(at: commandURL)
  }

  private func readState() -> [String: Any]? {
    guard let data = try? Data(contentsOf: stateURL) else {
      return nil
    }
    return (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
  }

  private func waitForState(command: String, timeout: TimeInterval = 12) -> [String: Any] {
    let deadline = Date().addingTimeInterval(timeout)
    var latest: [String: Any]?
    while Date() < deadline {
      if let state = readState(), state["runId"] as? String == runId {
        latest = state
        if state["command"] as? String == command {
          return state
        }
      }
      RunLoop.current.run(until: Date().addingTimeInterval(0.1))
    }
    XCTFail("Timed out waiting for transcript scroll command \(command). Latest state: \(String(describing: latest))")
    return latest ?? [:]
  }

  private func launchHarness(
    implementation: String,
    progressiveBackingList: String = "scrollView",
    restoreReady: Bool = true
  ) -> XCUIApplication {
    runId = UUID().uuidString
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_TRANSCRIPT_SCROLL_PERSISTENCE_HARNESS"] = "1"
    app.launchEnvironment["CLC_SCROLL_HARNESS_RUN_ID"] = runId
    app.launchEnvironment["CLC_TRANSCRIPT_SCROLL_LIST_IMPLEMENTATION"] = implementation
    app.launchEnvironment["CLC_PROGRESSIVE_SCROLL_BACKING_LIST"] = progressiveBackingList
    if !restoreReady {
      app.launchEnvironment["CLC_TRANSCRIPT_SCROLL_RESTORE_READY_FALSE"] = "1"
    }
    app.launchArguments.append("--transcript-scroll-persistence-harness")
    app.launch()
    app.activate()
    return app
  }

  private func clickHarnessMenu(_ app: XCUIApplication, _ item: String) {
    let menu = app.menuBars.menuBarItems["Transcript Scroll Harness"]
    XCTAssertTrue(menu.waitForExistence(timeout: 10), app.debugDescription)
    menu.click()
    let menuItem = app.menuItems[item]
    XCTAssertTrue(menuItem.waitForExistence(timeout: 10), app.debugDescription)
    menuItem.click()
  }

  private func intValue(_ state: [String: Any], _ key: String) -> Int? {
    if let value = state[key] as? Int {
      return value
    }
    if let value = state[key] as? NSNumber {
      return value.intValue
    }
    return nil
  }

  private func stringValue(_ state: [String: Any], _ key: String) -> String? {
    state[key] as? String
  }

  private func dictionary(_ state: [String: Any], _ key: String) -> [String: Any]? {
    state[key] as? [String: Any]
  }

  private func intValue(_ dictionary: [String: Any]?, _ key: String) -> Int? {
    guard let dictionary else {
      return nil
    }
    if let value = dictionary[key] as? Int {
      return value
    }
    if let value = dictionary[key] as? NSNumber {
      return value.intValue
    }
    return nil
  }

  private func stringValue(_ dictionary: [String: Any]?, _ key: String) -> String? {
    dictionary?[key] as? String
  }

  private func assertApproxEqual(
    _ lhs: Int?,
    _ rhs: Int?,
    tolerance: Int = 8,
    file: StaticString = #filePath,
    line: UInt = #line
  ) {
    guard let lhs, let rhs else {
      XCTFail("Missing values for approximate comparison: \(String(describing: lhs)) vs \(String(describing: rhs))", file: file, line: line)
      return
    }
    XCTAssertLessThanOrEqual(abs(lhs - rhs), tolerance, file: file, line: line)
  }

  private var progressiveSmokeEnabled: Bool {
    ProcessInfo.processInfo.environment["CLC_INCLUDE_PROGRESSIVE_TRANSCRIPT_SCROLL_TESTS"] == "1" ||
      FileManager.default.fileExists(atPath: progressiveOptInURL.path)
  }

  func testScrollViewOffsetRoundTripRestoresOffset() throws {
    let app = launchHarness(implementation: "scrollView")

    clickHarnessMenu(app, "Transcript Harness Offset Round Trip")
    let state = waitForState(command: "offsetRoundTrip", timeout: 20)
    let savedAnchor = dictionary(state, "savedAnchor")

    XCTAssertEqual(stringValue(state, "implementation"), "scrollView")
    XCTAssertEqual(stringValue(savedAnchor, "kind"), "offset", "\(state)")
    XCTAssertNotNil(intValue(savedAnchor, "bottomGapPx"), "\(state)")
    assertApproxEqual(intValue(state, "offsetY"), intValue(state, "targetScrollOffsetY"), tolerance: 12)
  }

  func testScrollViewDelayedCacheAnchorRestoresWhenReady() throws {
    let app = launchHarness(implementation: "scrollView", restoreReady: false)

    clickHarnessMenu(app, "Transcript Harness Release Delayed Offset Anchor")
    let state = waitForState(command: "releaseDelayedOffsetAnchor", timeout: 20)
    let maxOffsetY = intValue(state, "maxOffsetY")
    let bottomGapPx = intValue(state, "requestedBottomGapPx")

    XCTAssertEqual(stringValue(state, "implementation"), "scrollView")
    XCTAssertEqual(state["restoreReady"] as? Bool, true, "\(state)")
    guard let maxOffsetY, let bottomGapPx else {
      XCTFail("Missing delayed offset diagnostics: \(state)")
      return
    }
    assertApproxEqual(intValue(state, "offsetY"), maxOffsetY - bottomGapPx, tolerance: 12)
  }

  func testFlatListSavesMeasuredMessageAnchor() throws {
    let app = launchHarness(implementation: "flatList")

    clickHarnessMenu(app, "Transcript Harness Message Anchor Save")
    let state = waitForState(command: "messageAnchorSave", timeout: 20)
    let savedAnchor = dictionary(state, "savedAnchor")
    let visibleAnchor = dictionary(state, "visibleAnchor")

    XCTAssertEqual(stringValue(state, "implementation"), "flatList")
    XCTAssertEqual(stringValue(savedAnchor, "kind"), "messageViewport", "\(state)")
    XCTAssertEqual(intValue(savedAnchor, "messageIndex"), intValue(visibleAnchor, "sourceIndex"), "\(state)")
    assertApproxEqual(
      intValue(savedAnchor, "offsetFromViewportTop"),
      intValue(visibleAnchor, "offsetFromViewportTop"),
      tolerance: 10
    )
    assertApproxEqual(
      intValue(state, "targetMessageActualOffsetFromViewportTop"),
      intValue(state, "targetMessageRequestedOffsetFromViewportTop"),
      tolerance: 10
    )
  }

  func testFlatListRestoresPresetMessageAnchor() throws {
    let app = launchHarness(implementation: "flatList")

    clickHarnessMenu(app, "Transcript Harness Message Anchor Restore")
    let state = waitForState(command: "messageAnchorRestore", timeout: 20)

    XCTAssertEqual(stringValue(state, "implementation"), "flatList")
    assertApproxEqual(
      intValue(state, "targetMessageActualOffsetFromViewportTop"),
      intValue(state, "targetMessageRequestedOffsetFromViewportTop"),
      tolerance: 10
    )
  }

  func testFlatListMessageAnchorRoundTripRestoresPosition() throws {
    let app = launchHarness(implementation: "flatList")

    clickHarnessMenu(app, "Transcript Harness Message Anchor Round Trip")
    let state = waitForState(command: "messageAnchorRoundTrip", timeout: 20)
    let savedAnchor = dictionary(state, "savedAnchor")

    XCTAssertEqual(stringValue(state, "implementation"), "flatList")
    XCTAssertEqual(stringValue(savedAnchor, "kind"), "messageViewport", "\(state)")
    assertApproxEqual(
      intValue(state, "targetMessageActualOffsetFromViewportTop"),
      intValue(state, "targetMessageRequestedOffsetFromViewportTop"),
      tolerance: 10
    )
  }

  func testFlatListDelayedCacheAnchorRestoresWhenReady() throws {
    let app = launchHarness(implementation: "flatList", restoreReady: false)

    clickHarnessMenu(app, "Transcript Harness Release Delayed Anchor")
    let state = waitForState(command: "releaseDelayedMessageAnchor", timeout: 20)

    XCTAssertEqual(stringValue(state, "implementation"), "flatList")
    XCTAssertEqual(state["restoreReady"] as? Bool, true, "\(state)")
    assertApproxEqual(
      intValue(state, "targetMessageActualOffsetFromViewportTop"),
      intValue(state, "targetMessageRequestedOffsetFromViewportTop"),
      tolerance: 10
    )
  }

  func testProgressiveScrollPresetMessageAnchorSmoke() throws {
    try XCTSkipUnless(
      progressiveSmokeEnabled,
      "Progressive transcript scroll persistence smoke is opt-in because progressive FlatList backing is a POC."
    )

    let app = launchHarness(implementation: "progressiveScroll", progressiveBackingList: "scrollView")

    clickHarnessMenu(app, "Transcript Harness Message Anchor Restore")
    let state = waitForState(command: "messageAnchorRestore", timeout: 20)

    XCTAssertEqual(stringValue(state, "implementation"), "progressiveScroll")
    XCTAssertEqual(stringValue(state, "backingList"), "scrollView")
    assertApproxEqual(
      intValue(state, "targetMessageActualOffsetFromViewportTop"),
      intValue(state, "targetMessageRequestedOffsetFromViewportTop"),
      tolerance: 12
    )
  }

  func testProgressiveFlatListBackingPresetMessageAnchorSmoke() throws {
    try XCTSkipUnless(
      progressiveSmokeEnabled,
      "Progressive FlatList backing is a POC and remains opt-in for transcript persistence smoke coverage."
    )

    let app = launchHarness(implementation: "progressiveScroll", progressiveBackingList: "flatList")

    clickHarnessMenu(app, "Transcript Harness Message Anchor Restore")
    let state = waitForState(command: "messageAnchorRestore", timeout: 20)

    XCTAssertEqual(stringValue(state, "implementation"), "progressiveScroll")
    XCTAssertEqual(stringValue(state, "backingList"), "flatList")
    assertApproxEqual(
      intValue(state, "targetMessageActualOffsetFromViewportTop"),
      intValue(state, "targetMessageRequestedOffsetFromViewportTop"),
      tolerance: 12
    )
  }
}