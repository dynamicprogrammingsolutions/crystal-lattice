import XCTest

final class ProgressiveScrollListUITests: XCTestCase {
  override func setUpWithError() throws {
    continueAfterFailure = false
  }

  func testProgressiveScrollHarnessEdgesAndAnchors() throws {
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_SCROLL_TEST_HARNESS"] = "1"
    app.launch()

    XCTAssertTrue(app.descendants(matching: .any)["scroll-harness-root"].waitForExistence(timeout: 30))

    let bottomButton = app.buttons["scroll-harness-bottom"]
    XCTAssertTrue(bottomButton.waitForExistence(timeout: 10))
    bottomButton.click()
    XCTAssertTrue(app.descendants(matching: .any)["scroll-harness-message-219"].waitForExistence(timeout: 10))

    let topButton = app.buttons["scroll-harness-top"]
    XCTAssertTrue(topButton.waitForExistence(timeout: 10))
    topButton.click()
    XCTAssertTrue(app.descendants(matching: .any)["scroll-harness-message-0"].waitForExistence(timeout: 10))

    let anchorButton = app.buttons["scroll-harness-anchor-120"]
    XCTAssertTrue(anchorButton.waitForExistence(timeout: 10))
    anchorButton.click()
    XCTAssertTrue(app.descendants(matching: .any)["scroll-harness-message-120"].waitForExistence(timeout: 10))

    let readAnchorButton = app.buttons["scroll-harness-read-anchor"]
    XCTAssertTrue(readAnchorButton.waitForExistence(timeout: 10))
    readAnchorButton.click()
    let status = app.staticTexts["scroll-harness-status"]
    XCTAssertTrue(status.waitForExistence(timeout: 10))
    XCTAssertTrue(status.label.contains("anchor msg-"))

    let loadTop = app.buttons["progressive-scroll-load-top"]
    XCTAssertTrue(loadTop.waitForExistence(timeout: 10))
    loadTop.click()
    XCTAssertTrue(app.descendants(matching: .any)["scroll-harness-message-120"].waitForExistence(timeout: 10))

    let loadBottom = app.buttons["progressive-scroll-load-bottom"]
    XCTAssertTrue(loadBottom.waitForExistence(timeout: 10))
    loadBottom.click()
    XCTAssertTrue(app.descendants(matching: .any)["scroll-harness-message-120"].waitForExistence(timeout: 10))
  }
}