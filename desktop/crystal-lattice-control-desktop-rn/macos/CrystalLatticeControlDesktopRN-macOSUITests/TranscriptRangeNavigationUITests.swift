import XCTest

final class TranscriptRangeNavigationUITests: XCTestCase {
  override func setUpWithError() throws {
    continueAfterFailure = false
  }

  private func launchHarness(textSurfaceScenario: String? = nil) -> XCUIApplication {
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_TRANSCRIPT_RANGE_NAVIGATION_HARNESS"] = "1"
    if let textSurfaceScenario {
      app.launchEnvironment["CLC_TRANSCRIPT_TEXT_SURFACE_SCENARIO"] = textSurfaceScenario
    }
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

  func testWheelOverRawAssistantTextScrollsTranscript() throws {
    let app = launchHarness(textSurfaceScenario: "raw")

    let scrollTop = app.buttons["Scroll to top"]
    XCTAssertTrue(scrollTop.waitForExistence(timeout: 20), app.debugDescription)
    scrollTop.click()

    let message = element(app, label: "Transcript message 101")
    XCTAssertNotNil(waitForVisibleFrame(message, in: app.windows.firstMatch), app.debugDescription)
    let plain = element(app, label: "Transcript message 100")
    let plainBefore = plain.frame.minY
    app.windows.firstMatch.coordinate(withNormalizedOffset: .zero)
      .withOffset(CGVector(dx: plain.frame.midX, dy: plain.frame.midY))
      .scroll(byDeltaX: 0, deltaY: -240)
    XCTAssertGreaterThan(abs(plain.frame.minY - plainBefore), 20, "Control wheel gesture failed")
    let returnToTop = app.buttons["Scroll to top"]
    XCTAssertTrue(returnToTop.waitForExistence(timeout: 10), app.debugDescription)
    returnToTop.click()

    let toggle = message.buttons["Toggle markdown"]
    XCTAssertTrue(toggle.waitForExistence(timeout: 20), app.debugDescription)
    toggle.click()

    let raw = element(app, label: "assistant-raw-message-101")
    XCTAssertTrue(raw.waitForExistence(timeout: 20), app.debugDescription)
    RunLoop.current.run(until: Date().addingTimeInterval(0.7))
    let window = app.windows.firstMatch
    let visibleRaw = raw.frame.intersection(window.frame)
    XCTAssertGreaterThan(visibleRaw.height, 40, app.debugDescription)
    XCTAssertGreaterThan(raw.frame.height, visibleRaw.height, app.debugDescription)
    XCTAssertGreaterThan(raw.frame.minY, message.frame.minY + 20, app.debugDescription)
    let before = message.frame.minY
    let point = window.coordinate(withNormalizedOffset: .zero)
      .withOffset(CGVector(
        dx: visibleRaw.midX,
        dy: visibleRaw.minY + min(35, visibleRaw.height / 2)
      ))
    point.scroll(byDeltaX: 0, deltaY: -240)
    RunLoop.current.run(until: Date().addingTimeInterval(0.5))

    XCTAssertGreaterThan(
      abs(message.frame.minY - before),
      20,
      "Expected transcript row to move under wheel; before \(before), after \(message.frame.minY), raw \(raw.frame), start \(visibleRaw). \(app.debugDescription)"
    )
  }

  func testWheelOverMarkdownCodeBlockScrollsTranscript() throws {
    let app = launchHarness(textSurfaceScenario: "code")

    let scrollTop = app.buttons["Scroll to top"]
    XCTAssertTrue(scrollTop.waitForExistence(timeout: 20), app.debugDescription)
    scrollTop.click()

    let message = element(app, label: "Transcript message 101")
    XCTAssertNotNil(waitForVisibleFrame(message, in: app.windows.firstMatch), app.debugDescription)
    let code = message.descendants(matching: .any)
      .matching(identifier: "desktop-markdown-code-block")
      .firstMatch
    XCTAssertTrue(code.waitForExistence(timeout: 20), app.debugDescription)
    let window = app.windows.firstMatch
    let visibleCode = code.frame.intersection(window.frame)
    XCTAssertGreaterThan(visibleCode.height, 40, app.debugDescription)
    XCTAssertGreaterThan(
      code.frame.height,
      visibleCode.height,
      "Expected markdown code to expand beyond the viewport without a bounded vertical scroller. \(app.debugDescription)"
    )
    let before = message.frame.minY
    window.coordinate(withNormalizedOffset: .zero)
      .withOffset(CGVector(dx: visibleCode.midX, dy: visibleCode.minY + 30))
      .scroll(byDeltaX: 0, deltaY: -240)
    RunLoop.current.run(until: Date().addingTimeInterval(0.5))

    XCTAssertGreaterThan(
      abs(message.frame.minY - before),
      20,
      "Expected transcript to move while the pointer is over markdown code. \(app.debugDescription)"
    )
  }

  private func assertBoundedReadOnlyBlockScrolls(
    app: XCUIApplication,
    disclosureId: String,
    textId: String,
    file: StaticString = #filePath,
    line: UInt = #line
  ) {
    let scrollTop = app.buttons["Scroll to top"]
    XCTAssertTrue(scrollTop.waitForExistence(timeout: 20), app.debugDescription, file: file, line: line)
    scrollTop.click()

    let message = element(app, label: "Transcript message 101")
    XCTAssertNotNil(
      waitForVisibleFrame(message, in: app.windows.firstMatch),
      app.debugDescription,
      file: file,
      line: line
    )
    let disclosure = element(app, label: disclosureId)
    XCTAssertTrue(disclosure.waitForExistence(timeout: 20), app.debugDescription, file: file, line: line)
    disclosure.click()

    let text = element(app, label: textId)
    XCTAssertTrue(text.waitForExistence(timeout: 20), app.debugDescription, file: file, line: line)
    RunLoop.current.run(until: Date().addingTimeInterval(0.5))
    let window = app.windows.firstMatch
    let visibleText = text.frame.intersection(window.frame)
    XCTAssertGreaterThan(visibleText.height, 40, app.debugDescription, file: file, line: line)
    XCTAssertGreaterThan(text.frame.height, visibleText.height, app.debugDescription, file: file, line: line)
    let textBefore = text.frame.minY
    let messageBefore = message.frame.minY
    window.coordinate(withNormalizedOffset: .zero)
      .withOffset(CGVector(dx: visibleText.midX, dy: visibleText.minY + 30))
      .scroll(byDeltaX: 0, deltaY: -180)
    RunLoop.current.run(until: Date().addingTimeInterval(0.5))

    XCTAssertGreaterThan(
      abs(text.frame.minY - textBefore),
      20,
      "Expected the bounded region to scroll its native text. \(app.debugDescription)",
      file: file,
      line: line
    )
    assertClose(message.frame.minY, messageBefore, tolerance: 12, file: file, line: line)
  }

  func testExpandedReasoningScrollsInsideBoundedRegion() throws {
    let app = launchHarness(textSurfaceScenario: "reasoning")
    assertBoundedReadOnlyBlockScrolls(
      app: app,
      disclosureId: "assistant-reasoning-disclosure-101",
      textId: "assistant-reasoning-101"
    )
  }

  func testExpandedToolResultScrollsInsideBoundedRegion() throws {
    let app = launchHarness(textSurfaceScenario: "tool")
    assertBoundedReadOnlyBlockScrolls(
      app: app,
      disclosureId: "tool-result-disclosure-101",
      textId: "tool-result-101"
    )
  }
}