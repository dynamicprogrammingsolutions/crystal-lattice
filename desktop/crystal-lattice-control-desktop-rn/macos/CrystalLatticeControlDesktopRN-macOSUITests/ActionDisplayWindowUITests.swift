import XCTest

final class ActionDisplayWindowUITests: XCTestCase {
  private func numericValue(_ element: XCUIElement) -> Double {
    if let number = element.value as? NSNumber {
      return number.doubleValue
    }
    if let text = element.value as? String,
       let number = Double(text) {
      return number
    }
    XCTFail("Expected numeric accessibility value for \(element)")
    return 0
  }

  override func setUpWithError() throws {
    continueAfterFailure = false
  }

  func testLongDirectActionDisplayOpensScrollableWindow() throws {
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_ACTION_DISPLAY_HARNESS"] = "1"
    app.launchArguments.append("--action-display-harness")
    app.launch()
    app.activate()

    let harnessWindow = app.windows["DesktopActionDisplayHarnessWindow"]
    XCTAssertTrue(harnessWindow.waitForExistence(timeout: 20), app.debugDescription)

    let actionWindow = app.windows["actionDisplayWindow"]
    XCTAssertTrue(actionWindow.waitForExistence(timeout: 20), app.debugDescription)
    XCTAssertTrue(
      actionWindow.staticTexts["Compiled system message"].waitForExistence(timeout: 10),
      app.debugDescription
    )

    let bodyScroll = actionWindow.scrollViews.firstMatch
    XCTAssertTrue(bodyScroll.waitForExistence(timeout: 10), app.debugDescription)
    let scrollBar = bodyScroll.scrollBars.firstMatch
    XCTAssertTrue(scrollBar.waitForExistence(timeout: 10), app.debugDescription)
    let beforeValue = numericValue(scrollBar)

    bodyScroll.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5))
      .scroll(byDeltaX: 0, deltaY: -500)

    let moved = NSPredicate { _, _ in
      self.numericValue(scrollBar) > beforeValue + 0.01
    }
    expectation(for: moved, evaluatedWith: scrollBar)
    waitForExpectations(timeout: 10)

    let close = actionWindow.descendants(matching: .any).matching(
      NSPredicate(format: "label == %@", "Close")
    ).firstMatch
    XCTAssertTrue(close.waitForExistence(timeout: 10), app.debugDescription)
    close.click()
    let closed = NSPredicate(format: "exists == false")
    expectation(for: closed, evaluatedWith: actionWindow)
    waitForExpectations(timeout: 10)
  }

  func testMultilineActionFieldKeepsFocusWhenTypingSpaces() throws {
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_ACTION_DISPLAY_HARNESS"] = "1"
    app.launchArguments.append("--action-display-harness")
    app.launch()
    app.activate()

    let actionWindow = app.windows["actionDisplayWindow"]
    XCTAssertTrue(actionWindow.waitForExistence(timeout: 20), app.debugDescription)

    let input = actionWindow.descendants(matching: .any)
      .matching(identifier: "action-form-input-prompt")
      .firstMatch
    XCTAssertTrue(input.waitForExistence(timeout: 20), app.debugDescription)

    input.click()
    input.typeKey("a", modifierFlags: .command)
    input.typeKey(.delete, modifierFlags: [])
    input.typeText("alpha beta")

    let value = input.value as? String
    XCTAssertEqual(value, "alpha beta", app.debugDescription)
  }
}