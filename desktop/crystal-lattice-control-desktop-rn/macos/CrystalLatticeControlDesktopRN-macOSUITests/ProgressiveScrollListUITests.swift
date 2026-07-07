import XCTest

final class ProgressiveScrollListUITests: XCTestCase {
  private let stateURL = URL(fileURLWithPath: "/tmp/clc-progressive-scroll-harness-state.json")

  override func setUpWithError() throws {
    continueAfterFailure = false
    try? FileManager.default.removeItem(at: stateURL)
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
      if let state = readState() {
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

  func testProgressiveScrollHarnessEdgesAndAnchors() throws {
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_SCROLL_TEST_HARNESS"] = "1"
    app.launchArguments.append("--scroll-test-harness")
    app.launch()
    app.activate()

    let mounted = waitForState(command: "mounted", timeout: 30)
    XCTAssertEqual(intValue(mounted, "windowEnd"), 220)
    XCTAssertEqual(intValue(mounted, "dataLength"), 220)

    clickHarnessMenu(app, "Scroll Harness Bottom")
    let bottom = waitForState(command: "bottom")
    XCTAssertEqual(intValue(bottom, "windowEnd"), 220)
    XCTAssertEqual(intValue(bottom, "dataLength"), 220)

    clickHarnessMenu(app, "Scroll Harness Top")
    let top = waitForState(command: "top")
    XCTAssertEqual(intValue(top, "windowStart"), 0)

    clickHarnessMenu(app, "Scroll Harness Message 120")
    let anchored = waitForState(command: "message120")
    XCTAssertLessThanOrEqual(intValue(anchored, "windowStart") ?? 999, 120)
    XCTAssertGreaterThan(intValue(anchored, "windowEnd") ?? -1, 120)
    XCTAssertEqual(intValue(anchored, "anchorSourceIndex"), 120)

    clickHarnessMenu(app, "Scroll Harness Load Above")
    let loadAbove = waitForState(command: "loadAbove")
    XCTAssertLessThanOrEqual(intValue(loadAbove, "windowStart") ?? 999, intValue(anchored, "windowStart") ?? 999)
    XCTAssertEqual(intValue(loadAbove, "anchorSourceIndex"), 120)

    clickHarnessMenu(app, "Scroll Harness Load Below")
    let loadBelow = waitForState(command: "loadBelow")
    XCTAssertGreaterThanOrEqual(intValue(loadBelow, "windowEnd") ?? -1, intValue(loadAbove, "windowEnd") ?? -1)
    XCTAssertEqual(intValue(loadBelow, "anchorSourceIndex"), 120)
  }
}