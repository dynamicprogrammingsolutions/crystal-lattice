import XCTest

final class TranscriptRangeNavigationUITests: XCTestCase {
  override func setUpWithError() throws {
    continueAfterFailure = false
  }

  private func launchHarness() -> XCUIApplication {
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_TRANSCRIPT_RANGE_NAVIGATION_HARNESS"] = "1"
    app.launchArguments.append("--transcript-range-navigation-harness")
    app.launch()
    app.activate()
    return app
  }

  private func element(_ app: XCUIApplication, label: String) -> XCUIElement {
    app.descendants(matching: .any)
      .matching(NSPredicate(format: "identifier == %@ OR label == %@", label, label))
      .firstMatch
  }

  private func assertClose(
    _ actual: CGFloat,
    _ expected: CGFloat,
    tolerance: CGFloat = 16,
    file: StaticString = #filePath,
    line: UInt = #line
  ) {
    XCTAssertLessThanOrEqual(
      abs(actual - expected),
      tolerance,
      "Expected \(actual) to be within \(tolerance) of \(expected)",
      file: file,
      line: line
    )
  }

  private func waitForVisibleFrame(
    _ target: XCUIElement,
    in viewport: XCUIElement,
    timeout: TimeInterval = 30
  ) -> CGRect? {
    let deadline = Date().addingTimeInterval(timeout)
    repeat {
      if target.exists && viewport.exists {
        let intersection = target.frame.intersection(viewport.frame)
        if !intersection.isNull && intersection.height > 1 {
          return target.frame
        }
      }
      RunLoop.current.run(until: Date().addingTimeInterval(0.1))
    } while Date() < deadline
    return nil
  }

  func testOlderAndNewerRangeNavigationPreserveVisibleOverlap() throws {
    let app = launchHarness()

    let viewport = app.windows["DesktopTranscriptRangeNavigationHarnessWindow"]
    XCTAssertTrue(viewport.waitForExistence(timeout: 20), app.debugDescription)

    let scrollTop = app.buttons["Scroll to top"]
    XCTAssertTrue(scrollTop.waitForExistence(timeout: 20), app.debugDescription)
    scrollTop.click()

    let message100 = element(app, label: "Transcript message 100")
    XCTAssertTrue(message100.waitForExistence(timeout: 30), app.debugDescription)
    let olderFrame = waitForVisibleFrame(message100, in: viewport)
    XCTAssertNotNil(olderFrame, app.debugDescription)
    let olderY = try XCTUnwrap(olderFrame).minY

    let showOlder = app.buttons["Show 50 older messages"]
    XCTAssertTrue(showOlder.waitForExistence(timeout: 20), app.debugDescription)
    showOlder.click()

    let message50 = element(app, label: "Transcript message 50")
    XCTAssertTrue(message50.waitForExistence(timeout: 20), app.debugDescription)
    let restoredOlderFrame = waitForVisibleFrame(message100, in: viewport)
    XCTAssertNotNil(restoredOlderFrame, app.debugDescription)
    assertClose(try XCTUnwrap(restoredOlderFrame).minY, olderY)

    let scrollBottom = app.buttons["Scroll to bottom"]
    XCTAssertTrue(scrollBottom.waitForExistence(timeout: 20), app.debugDescription)
    scrollBottom.click()

    let message149 = element(app, label: "Transcript message 149")
    XCTAssertTrue(message149.waitForExistence(timeout: 30), app.debugDescription)
    let newerFrame = waitForVisibleFrame(message149, in: viewport)
    XCTAssertNotNil(newerFrame, app.debugDescription)
    let newerY = try XCTUnwrap(newerFrame).minY

    let showNewer = app.buttons["Show 50 newer messages"]
    XCTAssertTrue(showNewer.waitForExistence(timeout: 20), app.debugDescription)
    showNewer.click()

    let message199 = element(app, label: "Transcript message 199")
    XCTAssertTrue(message199.waitForExistence(timeout: 20), app.debugDescription)
    let restoredNewerFrame = waitForVisibleFrame(message149, in: viewport)
    XCTAssertNotNil(restoredNewerFrame, app.debugDescription)
    assertClose(try XCTUnwrap(restoredNewerFrame).minY, newerY)
  }
}