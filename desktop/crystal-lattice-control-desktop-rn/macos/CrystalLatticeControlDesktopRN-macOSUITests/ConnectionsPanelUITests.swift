import AppKit
import XCTest

final class ConnectionsPanelUITests: XCTestCase {
  private let stateURL = URL(
    fileURLWithPath: "/tmp/clc-connections-panel-harness-state.json"
  )

  override func setUpWithError() throws {
    continueAfterFailure = false
    for application in NSRunningApplication.runningApplications(
      withBundleIdentifier: "org.reactjs.native.CrystalLatticeControlDesktopRN"
    ) {
      application.forceTerminate()
    }
    RunLoop.current.run(until: Date().addingTimeInterval(0.3))
    try? FileManager.default.removeItem(at: stateURL)
  }

  private func launchHarness(
    count: Int,
    preset: String = "default"
  ) -> XCUIApplication {
    try? FileManager.default.removeItem(at: stateURL)
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_CONNECTIONS_PANEL_HARNESS"] = "1"
    app.launchEnvironment["CLC_CONNECTIONS_HARNESS_COUNT"] = String(count)
    app.launchEnvironment["CLC_CONNECTIONS_HARNESS_PRESET"] = preset
    app.launchArguments.append("--connections-panel-harness")
    app.launch()
    app.activate()
    return app
  }

  private func readState() -> [String: Any]? {
    guard let data = try? Data(contentsOf: stateURL) else {
      return nil
    }
    return (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
  }

  private func waitForState(
    count: Int,
    preset: String,
    timeout: TimeInterval = 20
  ) -> [String: Any] {
    let deadline = Date().addingTimeInterval(timeout)
    var latest: [String: Any]?
    while Date() < deadline {
      if let state = readState() {
        latest = state
        if (state["count"] as? NSNumber)?.intValue == count,
           state["preset"] as? String == preset,
           state["panelHeight"] is NSNumber,
           state["expectedListMaxHeight"] is NSNumber,
           state["expectedTitleLineHeight"] is NSNumber,
           state["expectedMetadataLineHeight"] is NSNumber {
          return state
        }
      }
      RunLoop.current.run(until: Date().addingTimeInterval(0.1))
    }
    XCTFail(
      "Timed out waiting for connections geometry \(count):\(preset). "
        + "Latest state: \(String(describing: latest))"
    )
    return latest ?? [:]
  }

  private func number(_ state: [String: Any], _ key: String) -> Double {
    guard let value = state[key] as? NSNumber else {
      XCTFail("Missing numeric \(key) in \(state)")
      return 0
    }
    return value.doubleValue
  }

  func testNaturalHeightAndBoundedScrollingFollowConnectionCount() throws {
    var app = launchHarness(count: 1)
    let oneState = waitForState(count: 1, preset: "default")
    XCTAssertEqual(app.scrollViews.count, 0, app.debugDescription)
    app.terminate()

    app = launchHarness(count: 3)
    let threeState = waitForState(count: 3, preset: "default")
    XCTAssertEqual(app.scrollViews.count, 0, app.debugDescription)
    XCTAssertGreaterThan(
      number(threeState, "panelHeight"),
      number(oneState, "panelHeight")
    )
    app.terminate()

    app = launchHarness(count: 5)
    let fiveState = waitForState(count: 5, preset: "default")
    let scroll = app.scrollViews.firstMatch
    XCTAssertTrue(scroll.waitForExistence(timeout: 20), app.debugDescription)

    let dynamicTolerance =
      number(fiveState, "expectedTitleLineHeight")
      + number(fiveState, "expectedMetadataLineHeight")
    XCTAssertLessThanOrEqual(
      abs(number(fiveState, "panelHeight") - number(threeState, "panelHeight")),
      dynamicTolerance
    )
    let fade = app.otherElements["More connections below"]
    XCTAssertTrue(fade.waitForExistence(timeout: 10), app.debugDescription)

    scroll.coordinate(withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5))
      .scroll(byDeltaX: 0, deltaY: -number(fiveState, "expectedListMaxHeight"))

    let fadeRemoved = NSPredicate(format: "exists == false")
    expectation(for: fadeRemoved, evaluatedWith: fade)
    waitForExpectations(timeout: 10)
    XCTAssertTrue(
      app.otherElements["Connection Harness connection 5"].isHittable,
      app.debugDescription
    )
  }

  func testDisclosureAndLargestPresetRemainUsable() throws {
    let app = launchHarness(count: 5, preset: "largest")
    let state = waitForState(count: 5, preset: "largest")
    let scroll = app.scrollViews.firstMatch
    XCTAssertTrue(scroll.waitForExistence(timeout: 20), app.debugDescription)

    let collapse = app.buttons["Collapse connections"]
    XCTAssertTrue(collapse.waitForExistence(timeout: 10), app.debugDescription)
    collapse.click()
    XCTAssertEqual(app.scrollViews.count, 0, app.debugDescription)

    let expand = app.buttons["Expand connections"]
    XCTAssertTrue(expand.waitForExistence(timeout: 10), app.debugDescription)
    expand.click()
    XCTAssertTrue(
      app.scrollViews.firstMatch.waitForExistence(timeout: 10),
      app.debugDescription
    )

    XCTAssertGreaterThan(
      number(state, "panelHeight"),
      number(state, "expectedListMaxHeight")
    )
  }
}