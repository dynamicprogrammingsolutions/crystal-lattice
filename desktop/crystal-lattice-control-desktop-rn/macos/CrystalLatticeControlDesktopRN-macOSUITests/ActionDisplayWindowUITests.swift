import XCTest

final class ActionDisplayWindowUITests: XCTestCase {
  override func setUpWithError() throws {
    continueAfterFailure = false
    for application in NSRunningApplication.runningApplications(
      withBundleIdentifier: "org.reactjs.native.CrystalLatticeControlDesktopRN"
    ) {
      application.forceTerminate()
    }
    RunLoop.current.run(until: Date().addingTimeInterval(0.3))
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
    let body = actionWindow.staticTexts.containing(
      NSPredicate(format: "label CONTAINS %@", "Instruction line 0:")
    ).firstMatch
    XCTAssertTrue(body.waitForExistence(timeout: 10), app.debugDescription)
    let beforeY = body.frame.minY

    bodyScroll.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5))
      .scroll(byDeltaX: 0, deltaY: -500)

    let moved = NSPredicate { _, _ in body.frame.minY < beforeY - 20 }
    expectation(for: moved, evaluatedWith: body)
    waitForExpectations(timeout: 10)

    let close = actionWindow.buttons["Close"]
    XCTAssertTrue(close.waitForExistence(timeout: 10), app.debugDescription)
    close.click()
    let closed = NSPredicate(format: "exists == false")
    expectation(for: closed, evaluatedWith: actionWindow)
    waitForExpectations(timeout: 10)
  }
}