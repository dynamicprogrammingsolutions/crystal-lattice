import XCTest

final class ProgressiveScrollListUITests: XCTestCase {
  private let stateURL = URL(fileURLWithPath: "/tmp/clc-progressive-scroll-harness-state.json")
  private let commandURL = URL(fileURLWithPath: "/tmp/clc-progressive-scroll-harness-command.json")
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

  private func waitForState(command: String, timeout: TimeInterval = 10) -> [String: Any] {
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
    XCTFail("Timed out waiting for harness command \(command). Latest state: \(String(describing: latest))")
    return latest ?? [:]
  }

  private func clickHarnessMenu(_ app: XCUIApplication, _ item: String) {
    let menu = app.menuBars.menuBarItems["Scroll Harness"]
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

  private func assertWindowSize(_ state: [String: Any], max: Int = 100) {
    guard let start = intValue(state, "windowStart"),
          let end = intValue(state, "windowEnd") else {
      XCTFail("Missing window range in state \(state)")
      return
    }
    XCTAssertLessThanOrEqual(end - start, max)
  }

  private func assertApproxEqual(_ lhs: Int?, _ rhs: Int?, tolerance: Int = 4, file: StaticString = #filePath, line: UInt = #line) {
    guard let lhs, let rhs else {
      XCTFail("Missing values for approximate comparison: \(String(describing: lhs)) vs \(String(describing: rhs))", file: file, line: line)
      return
    }
    XCTAssertLessThanOrEqual(abs(lhs - rhs), tolerance, file: file, line: line)
  }

  private func launchHarness(backingList: String = "scrollView", growOnly: Bool = false) -> XCUIApplication {
    runId = UUID().uuidString
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_SCROLL_TEST_HARNESS"] = "1"
    app.launchEnvironment["CLC_SCROLL_HARNESS_RUN_ID"] = runId
    app.launchEnvironment["CLC_PROGRESSIVE_SCROLL_BACKING_LIST"] = backingList
    app.launchEnvironment["CLC_PROGRESSIVE_SCROLL_GROW_ONLY"] = growOnly ? "1" : "0"
    app.launchArguments.append("--scroll-test-harness")
    app.launch()
    app.activate()
    return app
  }

  func testProgressiveScrollHarnessEdgesAndAnchors() throws {
    let app = launchHarness()

    clickHarnessMenu(app, "Scroll Harness Top")
    let top = waitForState(command: "top", timeout: 30)
    XCTAssertEqual(intValue(top, "windowStart"), 0)
    XCTAssertEqual(intValue(top, "dataLength"), 220)
    assertWindowSize(top)

    clickHarnessMenu(app, "Scroll Harness Bottom")
    let bottom = waitForState(command: "bottom")
    XCTAssertEqual(intValue(bottom, "windowEnd"), 220)
    XCTAssertEqual(intValue(bottom, "dataLength"), 220)
    assertWindowSize(bottom)

    clickHarnessMenu(app, "Scroll Harness Message 120")
    let anchored = waitForState(command: "message120")
    XCTAssertEqual(intValue(anchored, "windowStart"), 80)
    XCTAssertEqual(intValue(anchored, "windowEnd"), 180)
    XCTAssertLessThanOrEqual(intValue(anchored, "windowStart") ?? 999, 120)
    XCTAssertGreaterThan(intValue(anchored, "windowEnd") ?? -1, 120)
    XCTAssertEqual(intValue(anchored, "message120OffsetFromViewportTop"), 40)
    assertWindowSize(anchored)

    clickHarnessMenu(app, "Scroll Harness Window Top")
    let windowTop = waitForState(command: "windowTop")
    XCTAssertEqual(intValue(windowTop, "anchorSourceIndex"), intValue(windowTop, "windowStart"))
    assertWindowSize(windowTop)

    clickHarnessMenu(app, "Scroll Harness Load Above")
    let loadAbove = waitForState(command: "loadAbove")
    XCTAssertLessThanOrEqual(intValue(loadAbove, "windowStart") ?? 999, intValue(windowTop, "windowStart") ?? 999)
    XCTAssertEqual(intValue(loadAbove, "trackedAnchorSourceIndex"), intValue(windowTop, "anchorSourceIndex"))
    assertApproxEqual(
      intValue(loadAbove, "trackedAnchorActualOffsetFromViewportTop"),
      intValue(loadAbove, "trackedAnchorOffsetFromViewportTop")
    )
    assertWindowSize(loadAbove)

    clickHarnessMenu(app, "Scroll Harness Window Bottom")
    let windowBottom = waitForState(command: "windowBottom")
    XCTAssertGreaterThanOrEqual(intValue(windowBottom, "anchorSourceIndex") ?? -1, 110)
    assertWindowSize(windowBottom)

    clickHarnessMenu(app, "Scroll Harness Load Below")
    let loadBelow = waitForState(command: "loadBelow")
    XCTAssertGreaterThanOrEqual(intValue(loadBelow, "windowEnd") ?? -1, intValue(windowBottom, "windowEnd") ?? -1)
    XCTAssertEqual(intValue(loadBelow, "trackedAnchorSourceIndex"), intValue(windowBottom, "anchorSourceIndex"))
    assertApproxEqual(
      intValue(loadBelow, "trackedAnchorActualOffsetFromViewportTop"),
      intValue(loadBelow, "trackedAnchorOffsetFromViewportTop")
    )
    assertWindowSize(loadBelow)
  }

  func testProgressiveScrollHarnessFlatListGrowOnly() throws {
    let app = launchHarness(backingList: "flatList", growOnly: true)

    clickHarnessMenu(app, "Scroll Harness Top")
    let top = waitForState(command: "top", timeout: 30)
    XCTAssertEqual(top["backingList"] as? String, "flatList")
    XCTAssertEqual(intValue(top, "windowStart"), 0)
    XCTAssertEqual(intValue(top, "windowEnd"), 100)
    assertWindowSize(top)

    clickHarnessMenu(app, "Scroll Harness Bottom")
    let bottom = waitForState(command: "bottom")
    XCTAssertEqual(intValue(bottom, "windowStart"), 120)
    XCTAssertEqual(intValue(bottom, "windowEnd"), 220)
    assertWindowSize(bottom)

    clickHarnessMenu(app, "Scroll Harness Message 120")
    let anchored = waitForState(command: "message120")
    XCTAssertEqual(intValue(anchored, "windowStart"), 80)
    XCTAssertEqual(intValue(anchored, "windowEnd"), 180)
    XCTAssertEqual(intValue(anchored, "message120OffsetFromViewportTop"), 40)
    assertWindowSize(anchored)

    clickHarnessMenu(app, "Scroll Harness Window Top")
    let windowTop = waitForState(command: "windowTop")
    XCTAssertEqual(intValue(windowTop, "anchorSourceIndex"), 80)

    clickHarnessMenu(app, "Scroll Harness Load Above")
    let loadAbove = waitForState(command: "loadAbove")
    XCTAssertEqual(intValue(loadAbove, "windowStart"), 30)
    XCTAssertEqual(intValue(loadAbove, "windowEnd"), 180)
    XCTAssertGreaterThan((intValue(loadAbove, "windowEnd") ?? 0) - (intValue(loadAbove, "windowStart") ?? 0), 100)
    XCTAssertEqual(intValue(loadAbove, "trackedAnchorSourceIndex"), intValue(windowTop, "anchorSourceIndex"))
    assertApproxEqual(
      intValue(loadAbove, "trackedAnchorActualOffsetFromViewportTop"),
      intValue(loadAbove, "trackedAnchorOffsetFromViewportTop")
    )

    clickHarnessMenu(app, "Scroll Harness Window Bottom")
    let windowBottom = waitForState(command: "windowBottom")
    let windowBottomStart = intValue(windowBottom, "windowStart")
    let windowBottomEnd = intValue(windowBottom, "windowEnd")
    let windowBottomSize = (windowBottomEnd ?? 0) - (windowBottomStart ?? 0)

    clickHarnessMenu(app, "Scroll Harness Load Below")
    let loadBelow = waitForState(command: "loadBelow")
    XCTAssertEqual(intValue(loadBelow, "windowStart"), windowBottomStart)
    XCTAssertEqual(intValue(loadBelow, "windowEnd"), 220)
    XCTAssertGreaterThan((intValue(loadBelow, "windowEnd") ?? 0) - (intValue(loadBelow, "windowStart") ?? 0), windowBottomSize)
    XCTAssertEqual(intValue(loadBelow, "trackedAnchorSourceIndex"), intValue(windowBottom, "anchorSourceIndex"))
    assertApproxEqual(
      intValue(loadBelow, "trackedAnchorActualOffsetFromViewportTop"),
      intValue(loadBelow, "trackedAnchorOffsetFromViewportTop")
    )

    clickHarnessMenu(app, "Scroll Harness Bottom")
    let resetBottom = waitForState(command: "bottom")
    XCTAssertEqual(intValue(resetBottom, "windowStart"), 120)
    XCTAssertEqual(intValue(resetBottom, "windowEnd"), 220)
    assertWindowSize(resetBottom)
  }

  func testProgressiveScrollHarnessFlatListBoundedLoadBelowDoesNotCascade() throws {
    let app = launchHarness(backingList: "flatList", growOnly: false)

    clickHarnessMenu(app, "Scroll Harness Message 60")
    let anchored = waitForState(command: "message60", timeout: 30)
    XCTAssertEqual(intValue(anchored, "windowStart"), 20)
    XCTAssertEqual(intValue(anchored, "windowEnd"), 120)
    XCTAssertGreaterThanOrEqual(intValue(anchored, "anchorSourceIndex") ?? -1, 54)
    XCTAssertLessThanOrEqual(intValue(anchored, "anchorSourceIndex") ?? 999, 60)
    assertWindowSize(anchored)

    clickHarnessMenu(app, "Scroll Harness Window Bottom")
    let windowBottom = waitForState(command: "windowBottom")
    XCTAssertEqual(intValue(windowBottom, "windowStart"), 20)
    XCTAssertEqual(intValue(windowBottom, "windowEnd"), 120)

    clickHarnessMenu(app, "Scroll Harness Load Below")
    let loadBelow = waitForState(command: "loadBelow")
    XCTAssertEqual(intValue(loadBelow, "windowStart"), 70)
    XCTAssertEqual(intValue(loadBelow, "windowEnd"), 170)
    XCTAssertNotEqual(intValue(loadBelow, "windowEnd"), 220)
    XCTAssertEqual(intValue(loadBelow, "trackedAnchorSourceIndex"), intValue(windowBottom, "anchorSourceIndex"))
    assertApproxEqual(intValue(loadBelow, "anchorSourceIndex"), intValue(windowBottom, "anchorSourceIndex"), tolerance: 3)
    assertWindowSize(loadBelow)
  }

  func testProgressiveScrollHarnessFlatListGrowOnlyLoadBelowDoesNotCascade() throws {
    let app = launchHarness(backingList: "flatList", growOnly: true)

    clickHarnessMenu(app, "Scroll Harness Message 60")
    let anchored = waitForState(command: "message60", timeout: 30)
    XCTAssertEqual(intValue(anchored, "windowStart"), 20)
    XCTAssertEqual(intValue(anchored, "windowEnd"), 120)
    XCTAssertGreaterThanOrEqual(intValue(anchored, "anchorSourceIndex") ?? -1, 54)
    XCTAssertLessThanOrEqual(intValue(anchored, "anchorSourceIndex") ?? 999, 60)
    assertWindowSize(anchored)

    clickHarnessMenu(app, "Scroll Harness Window Bottom")
    let windowBottom = waitForState(command: "windowBottom")
    XCTAssertEqual(intValue(windowBottom, "windowStart"), 20)
    XCTAssertEqual(intValue(windowBottom, "windowEnd"), 120)

    clickHarnessMenu(app, "Scroll Harness Load Below")
    let loadBelow = waitForState(command: "loadBelow")
    XCTAssertEqual(intValue(loadBelow, "windowStart"), 20)
    XCTAssertEqual(intValue(loadBelow, "windowEnd"), 170)
    XCTAssertNotEqual(intValue(loadBelow, "windowEnd"), 220)
    XCTAssertGreaterThan((intValue(loadBelow, "windowEnd") ?? 0) - (intValue(loadBelow, "windowStart") ?? 0), 100)
    XCTAssertEqual(intValue(loadBelow, "trackedAnchorSourceIndex"), intValue(windowBottom, "anchorSourceIndex"))
    assertApproxEqual(intValue(loadBelow, "anchorSourceIndex"), intValue(windowBottom, "anchorSourceIndex"), tolerance: 3)
  }
}