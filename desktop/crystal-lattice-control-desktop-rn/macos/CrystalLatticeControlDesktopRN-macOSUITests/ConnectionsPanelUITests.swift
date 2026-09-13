import AppKit
import XCTest

final class ConnectionsPanelUITests: XCTestCase {
  private let stateURL = URL(
    fileURLWithPath: "/tmp/clc-connections-panel-harness-state.json"
  )
  private let workspaceStateURL = URL(
    fileURLWithPath: "/tmp/clc-desktop-workspace-harness-state.json"
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
    try? FileManager.default.removeItem(at: workspaceStateURL)
  }

  private func launchWorkspaceHarness() -> XCUIApplication {
    try? FileManager.default.removeItem(at: workspaceStateURL)
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_DESKTOP_WORKSPACE_HARNESS"] = "1"
    app.launchArguments.append("--desktop-workspace-harness")
    app.launch()
    app.activate()
    return app
  }

  private func readWorkspaceState() -> [String: Any]? {
    guard let data = try? Data(contentsOf: workspaceStateURL) else {
      return nil
    }
    return (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
  }

  private func waitForWorkspaceState(
    timeout: TimeInterval = 20,
    where predicate: ([String: Any]) -> Bool
  ) -> [String: Any] {
    let deadline = Date().addingTimeInterval(timeout)
    var latest: [String: Any]?
    while Date() < deadline {
      if let state = readWorkspaceState() {
        latest = state
        if predicate(state) {
          return state
        }
      }
      RunLoop.current.run(until: Date().addingTimeInterval(0.1))
    }
    XCTFail(
      "Timed out waiting for desktop workspace state. "
        + "Latest state: \(String(describing: latest))"
    )
    return latest ?? [:]
  }

  private func workspaceElement(
    _ app: XCUIApplication,
    _ identifier: String
  ) -> XCUIElement {
    app.descendants(matching: .any)
      .matching(identifier: identifier)
      .firstMatch
  }

  private func clickCenter(_ element: XCUIElement) {
    element.coordinate(
      withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)
    ).click()
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

  func testWorkspaceActivityHomeAndPreviewPromotion() throws {
    let app = launchWorkspaceHarness()
    _ = waitForWorkspaceState { state in
      (state["previewSessionId"] as? String) == "preview"
        && (state["permanentOrder"] as? [String]) == ["one", "two"]
    }

    let preview = workspaceElement(
      app,
      "desktop-session-tab-harness-connection:preview"
    )
    XCTAssertTrue(preview.waitForExistence(timeout: 20), app.debugDescription)
    XCTAssertTrue(
      workspaceElement(
        app,
        "desktop-tab-request-status-harness-connection:preview"
      )
        .waitForExistence(timeout: 10),
      app.debugDescription
    )
    XCTAssertTrue(
      workspaceElement(
        app,
        "desktop-tab-request-status-harness-connection:one"
      )
        .waitForExistence(timeout: 10),
      app.debugDescription
    )
    preview.coordinate(
      withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)
    ).doubleClick()
    _ = waitForWorkspaceState { state in
      state["previewSessionId"] is NSNull
        && (state["permanentOrder"] as? [String])
          == ["one", "two", "preview"]
    }

    let home = workspaceElement(app, "desktop-home-tab")
    XCTAssertTrue(home.waitForExistence(timeout: 10), app.debugDescription)
    clickCenter(home)
    _ = waitForWorkspaceState { state in
      (state["active"] as? String) == "home"
    }
    XCTAssertTrue(
      workspaceElement(
        app,
        "desktop-tile-session-harness-connection-one"
      ).waitForExistence(timeout: 10),
      app.debugDescription
    )
    XCTAssertTrue(
      workspaceElement(
        app,
        "desktop-session-status-harness-connection-one"
      ).waitForExistence(timeout: 10),
      app.debugDescription
    )

    let firstWatched = workspaceElement(
      app,
      "desktop-tile-session-harness-connection-one"
    )
    let secondWatched = workspaceElement(
      app,
      "desktop-tile-session-harness-connection-two"
    )
    firstWatched.coordinate(
      withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)
    ).press(
      forDuration: 0.2,
      thenDragTo: secondWatched.coordinate(
        withNormalizedOffset: CGVector(dx: 0.8, dy: 0.5)
      )
    )
    _ = waitForWorkspaceState { state in
      (state["watchlistOrder"] as? [String])
        == ["two", "one", "three", "four"]
    }

    clickCenter(workspaceElement(app, "desktop-activity-history"))
    _ = waitForWorkspaceState { state in
      (state["lowerPanel"] as? String) == "history"
    }
    clickCenter(workspaceElement(app, "desktop-activity-connections"))
    _ = waitForWorkspaceState { state in
      (state["connectionsVisible"] as? NSNumber)?.boolValue == false
    }
  }

  func testPermanentTabsDragToLiveFinalOrder() throws {
    let app = launchWorkspaceHarness()
    _ = waitForWorkspaceState { state in
      (state["permanentOrder"] as? [String]) == ["one", "two"]
    }
    let first = workspaceElement(
      app,
      "desktop-session-tab-harness-connection:one"
    )
    let second = workspaceElement(
      app,
      "desktop-session-tab-harness-connection:two"
    )
    XCTAssertTrue(first.waitForExistence(timeout: 20), app.debugDescription)
    XCTAssertTrue(second.waitForExistence(timeout: 10), app.debugDescription)

    let source = first.coordinate(
      withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)
    )
    let destination = second.coordinate(
      withNormalizedOffset: CGVector(dx: 0.8, dy: 0.5)
    )
    source.press(forDuration: 0.2, thenDragTo: destination)

    _ = waitForWorkspaceState { state in
      (state["permanentOrder"] as? [String]) == ["two", "one"]
    }
  }

  func testWatchlistVerticalDragFollowsPointerDirection() throws {
    let app = launchWorkspaceHarness()
    _ = waitForWorkspaceState { state in
      (state["watchlistOrder"] as? [String])
        == ["one", "two", "three", "four"]
    }
    clickCenter(workspaceElement(app, "desktop-home-tab"))

    let first = workspaceElement(
      app,
      "desktop-tile-session-harness-connection-one"
    )
    let third = workspaceElement(
      app,
      "desktop-tile-session-harness-connection-three"
    )
    XCTAssertTrue(first.waitForExistence(timeout: 20), app.debugDescription)
    XCTAssertTrue(third.waitForExistence(timeout: 10), app.debugDescription)

    first.coordinate(
      withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)
    ).press(
      forDuration: 0.2,
      thenDragTo: third.coordinate(
        withNormalizedOffset: CGVector(dx: 0.5, dy: 0.7)
      )
    )
    _ = waitForWorkspaceState { state in
      (state["watchlistOrder"] as? [String])
        == ["two", "three", "one", "four"]
    }

    let movedFirst = workspaceElement(
      app,
      "desktop-tile-session-harness-connection-one"
    )
    let topLeft = workspaceElement(
      app,
      "desktop-tile-session-harness-connection-two"
    )
    movedFirst.coordinate(
      withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)
    ).press(
      forDuration: 0.2,
      thenDragTo: topLeft.coordinate(
        withNormalizedOffset: CGVector(dx: 0.5, dy: 0.3)
      )
    )
    _ = waitForWorkspaceState { state in
      (state["watchlistOrder"] as? [String])
        == ["one", "two", "three", "four"]
    }
  }
}