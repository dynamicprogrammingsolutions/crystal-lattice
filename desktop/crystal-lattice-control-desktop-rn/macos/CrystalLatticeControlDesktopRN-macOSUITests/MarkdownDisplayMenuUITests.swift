import XCTest

final class MarkdownDisplayMenuUITests: XCTestCase {
  private let stateURL = URL(
    fileURLWithPath: "/tmp/clc-markdown-geometry-harness-state.json"
  )

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

  private func waitForState(
    baseFontSize: Int,
    headerSize: String,
    timeout: TimeInterval = 20
  ) -> [String: Any] {
    let deadline = Date().addingTimeInterval(timeout)
    var latest: [String: Any]?
    while Date() < deadline {
      if let state = readState() {
        latest = state
        if (state["baseFontSize"] as? NSNumber)?.intValue == baseFontSize,
           state["headerSize"] as? String == headerSize,
           state["h1Height"] is NSNumber,
           state["h6Height"] is NSNumber,
           state["bodyHeight"] is NSNumber,
           state["footerHeight"] is NSNumber {
          return state
        }
      }
      RunLoop.current.run(until: Date().addingTimeInterval(0.1))
    }
    XCTFail(
      "Timed out waiting for markdown geometry \(baseFontSize):\(headerSize). "
        + "Latest state: \(String(describing: latest))"
    )
    return latest ?? [:]
  }

  private func height(_ state: [String: Any], _ key: String) -> Double {
    guard let value = state[key] as? NSNumber else {
      XCTFail("Missing numeric \(key) in \(state)")
      return 0
    }
    return value.doubleValue
  }

  private func chooseViewSubmenuItem(
    _ app: XCUIApplication,
    submenu: String,
    item: String
  ) {
    let view = app.menuBars.menuBarItems["View"]
    XCTAssertTrue(view.waitForExistence(timeout: 10), app.debugDescription)
    view.click()
    let submenuItem = app.menuItems[submenu]
    XCTAssertTrue(submenuItem.waitForExistence(timeout: 5), app.debugDescription)
    submenuItem.hover()
    let choice = app.menuItems[item]
    XCTAssertTrue(choice.waitForExistence(timeout: 5), app.debugDescription)
    choice.click()
  }

  func testMarkdownDisplayMenusPersistSelections() throws {
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_MARKDOWN_GEOMETRY_HARNESS"] = "1"
    app.launchArguments.append("--markdown-geometry-harness")
    app.launch()
    app.activate()

    chooseViewSubmenuItem(app, submenu: "Font Size", item: "17")
    chooseViewSubmenuItem(app, submenu: "Markdown Headers", item: "Small")
    _ = waitForState(baseFontSize: 17, headerSize: "small")

    app.terminate()
    try? FileManager.default.removeItem(at: stateURL)
    app.launch()
    app.activate()
    _ = waitForState(baseFontSize: 17, headerSize: "small")
  }

  func testMarkdownDisplayMenusUpdateRenderedGeometry() throws {
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_MARKDOWN_GEOMETRY_HARNESS"] = "1"
    app.launchArguments.append("--markdown-geometry-harness")
    app.launch()
    app.activate()

    let harnessWindow = app.windows["DesktopMarkdownGeometryHarnessWindow"]
    XCTAssertTrue(harnessWindow.waitForExistence(timeout: 20), app.debugDescription)

    chooseViewSubmenuItem(app, submenu: "Font Size", item: "15 (Default)")
    chooseViewSubmenuItem(app, submenu: "Markdown Headers", item: "Normal")

    let normalState = waitForState(baseFontSize: 15, headerSize: "normal")
    let normalHeadingOneHeight = height(normalState, "h1Height")
    let normalHeadingSixHeight = height(normalState, "h6Height")
    XCTAssertGreaterThan(normalHeadingOneHeight, normalHeadingSixHeight * 1.5)

    chooseViewSubmenuItem(app, submenu: "Markdown Headers", item: "Small")
    let smallState = waitForState(baseFontSize: 15, headerSize: "small")
    XCTAssertLessThanOrEqual(
      abs(height(smallState, "h1Height") - height(smallState, "h6Height")),
      6
    )

    chooseViewSubmenuItem(app, submenu: "Font Size", item: "14")
    let stateAt14 = waitForState(baseFontSize: 14, headerSize: "small")
    let bodyAt14 = height(
      stateAt14,
      "bodyHeight"
    )
    chooseViewSubmenuItem(app, submenu: "Font Size", item: "17")
    let stateAt17 = waitForState(baseFontSize: 17, headerSize: "small")
    let bodyAt17 = height(
      stateAt17,
      "bodyHeight"
    )
    XCTAssertGreaterThan(bodyAt17, bodyAt14)

    chooseViewSubmenuItem(app, submenu: "Font Size", item: "15 (Default)")
    let footerAt15 = height(
      waitForState(baseFontSize: 15, headerSize: "small"),
      "footerHeight"
    )
    chooseViewSubmenuItem(app, submenu: "Font Size", item: "16")
    let footerAt16 = height(
      waitForState(baseFontSize: 16, headerSize: "small"),
      "footerHeight"
    )
    XCTAssertGreaterThan(footerAt16, footerAt15)
  }
}