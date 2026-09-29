import XCTest
import CoreGraphics

final class ConnectionsPanelUITests: XCTestCase {
  private let stateURL = URL(
    fileURLWithPath: "/tmp/clc-connections-panel-harness-state.json"
  )
  private let workspaceStateURL = URL(
    fileURLWithPath: "/tmp/clc-desktop-workspace-harness-state.json"
  )

  override func setUpWithError() throws {
    continueAfterFailure = false
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

  private func middleClickCenter(_ element: XCUIElement) {
    let point = CGPoint(x: element.frame.midX, y: element.frame.midY)
    let source = CGEventSource(stateID: .hidSystemState)
    CGEvent(
      mouseEventSource: source,
      mouseType: .mouseMoved,
      mouseCursorPosition: point,
      mouseButton: .center
    )?.post(tap: .cghidEventTap)
    CGEvent(
      mouseEventSource: source,
      mouseType: .otherMouseDown,
      mouseCursorPosition: point,
      mouseButton: .center
    )?.post(tap: .cghidEventTap)
    CGEvent(
      mouseEventSource: source,
      mouseType: .otherMouseUp,
      mouseCursorPosition: point,
      mouseButton: .center
    )?.post(tap: .cghidEventTap)
  }

  private func assertNoHorizontalOverlap(
    _ left: XCUIElement,
    _ right: XCUIElement,
    file: StaticString = #filePath,
    line: UInt = #line
  ) {
    XCTAssertLessThanOrEqual(
      left.frame.maxX,
      right.frame.minX + 2,
      "Expected \(left) to remain left of \(right)",
      file: file,
      line: line
    )
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

  private func sidebarMetrics(_ state: [String: Any]) -> [String: Any]? {
    return state["sidebarMetrics"] as? [String: Any]
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
        == [
          "two", "one", "three", "four",
          "session-with-a-deliberately-long-identifier-for-native-truncation",
        ]
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

  func testSidebarPointerAndKeyboardResizeStayWithinReportedPolicy() throws {
    let app = launchWorkspaceHarness()
    let initialState = waitForWorkspaceState { state in
      self.sidebarMetrics(state)?["width"] is NSNumber
    }
    guard let initialMetrics = sidebarMetrics(initialState) else {
      XCTFail("Missing initial sidebar metrics: \(initialState)")
      return
    }
    let initialWidth = number(initialMetrics, "width")
    let step = number(initialMetrics, "adjustmentStep")

    let handle = workspaceElement(app, "desktop-sidebar-resize-handle")
    XCTAssertTrue(handle.waitForExistence(timeout: 20), app.debugDescription)
    XCTAssertEqual(handle.label, "Resize sidebar")

    let source = handle.coordinate(
      withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)
    )
    source.press(
      forDuration: 0.2,
      thenDragTo: source.withOffset(CGVector(dx: step * 2, dy: 0))
    )
    let draggedState = waitForWorkspaceState { state in
      guard let metrics = self.sidebarMetrics(state),
            let width = metrics["width"] as? NSNumber else {
        return false
      }
      return width.doubleValue > initialWidth
    }
    guard let draggedMetrics = sidebarMetrics(draggedState) else {
      XCTFail("Missing dragged sidebar metrics: \(draggedState)")
      return
    }
    let draggedWidth = number(draggedMetrics, "width")

    clickCenter(handle)
    handle.typeKey(.leftArrow, modifierFlags: [])
    let keyboardState = waitForWorkspaceState { state in
      guard let metrics = self.sidebarMetrics(state),
            let width = metrics["width"] as? NSNumber else {
        return false
      }
      return abs(width.doubleValue - (draggedWidth - step)) < 0.5
    }
    guard let keyboardMetrics = sidebarMetrics(keyboardState) else {
      XCTFail("Missing keyboard sidebar metrics: \(keyboardState)")
      return
    }

    let resizedHandle = workspaceElement(app, "desktop-sidebar-resize-handle")
    let maximumWidth = number(keyboardMetrics, "maximumWidth")
    let currentWidth = number(keyboardMetrics, "width")
    let resizeSource = resizedHandle.coordinate(
      withNormalizedOffset: CGVector(dx: 0.5, dy: 0.5)
    )
    resizeSource.press(
      forDuration: 0.2,
      thenDragTo: resizeSource.withOffset(
        CGVector(dx: maximumWidth - currentWidth + step * 2, dy: 0)
      )
    )
    let maximumState = waitForWorkspaceState { state in
      guard let metrics = self.sidebarMetrics(state),
            let width = metrics["width"] as? NSNumber,
            let maximum = metrics["maximumWidth"] as? NSNumber,
            let mainWidth = metrics["mainWidth"] as? NSNumber,
            let minimumMain = metrics["minimumMainWidth"] as? NSNumber else {
        return false
      }
      return abs(width.doubleValue - maximum.doubleValue) < 0.5
        && mainWidth.doubleValue >= minimumMain.doubleValue
    }
    guard let maximumMetrics = sidebarMetrics(maximumState) else {
      XCTFail("Missing maximum sidebar metrics: \(maximumState)")
      return
    }
    XCTAssertGreaterThanOrEqual(
      number(maximumMetrics, "mainWidth"),
      number(maximumMetrics, "minimumMainWidth")
    )
  }

  func testMiddleClickClosesTabWithoutSelectingOrDragging() throws {
    let app = launchWorkspaceHarness()
    _ = waitForWorkspaceState { state in
      (state["permanentOrder"] as? [String]) == ["one", "two"]
        && (state["active"] as? String) == "harness-connection:preview"
    }
    let tab = workspaceElement(
      app,
      "desktop-session-tab-harness-connection:one"
    )
    XCTAssertTrue(tab.waitForExistence(timeout: 20), app.debugDescription)

    middleClickCenter(tab)

    _ = waitForWorkspaceState { state in
      (state["permanentOrder"] as? [String]) == ["two"]
        && (state["active"] as? String) == "harness-connection:preview"
    }
  }

  func testHomeAndHistoryPresentationKeepMetadataAndActionsVisible() throws {
    let app = launchWorkspaceHarness()
    _ = waitForWorkspaceState { state in
      (state["watchlistOrder"] as? [String])?.count == 5
    }
    clickCenter(workspaceElement(app, "desktop-home-tab"))

    let longID =
      "session-with-a-deliberately-long-identifier-for-native-truncation"
    let homeScroll = app.scrollViews.firstMatch
    XCTAssertTrue(homeScroll.waitForExistence(timeout: 20), app.debugDescription)

    let tileTitle = workspaceElement(
      app,
      "desktop-tile-title-harness-connection-\(longID)-native"
    )
    if !tileTitle.isHittable {
      homeScroll.coordinate(
        withNormalizedOffset: CGVector(dx: 0.5, dy: 0.7)
      ).scroll(byDeltaX: 0, deltaY: -homeScroll.frame.height)
    }
    XCTAssertTrue(tileTitle.waitForExistence(timeout: 10), app.debugDescription)
    XCTAssertEqual(tileTitle.label, "A complete native session title")
    XCTAssertTrue(
      workspaceElement(
        app,
        "desktop-tile-subtitle-harness-connection-\(longID)-native"
      ).waitForExistence(timeout: 10),
      app.debugDescription
    )
    XCTAssertTrue(
      workspaceElement(
        app,
        "desktop-tile-session-id-harness-connection-\(longID)-native"
      ).waitForExistence(timeout: 10),
      app.debugDescription
    )
    let tileConnection = workspaceElement(
      app,
      "desktop-tile-connection-harness-connection-\(longID)-native"
    )
    let tileTime = workspaceElement(
      app,
      "desktop-tile-time-harness-connection-\(longID)-native"
    )
    XCTAssertTrue(tileConnection.waitForExistence(timeout: 10))
    XCTAssertTrue(tileTime.waitForExistence(timeout: 10))
    assertNoHorizontalOverlap(tileConnection, tileTime)
    XCTAssertTrue(
      workspaceElement(
        app,
        "desktop-tile-note-action-harness-connection-\(longID)"
      ).waitForExistence(timeout: 10)
    )
    XCTAssertTrue(
      workspaceElement(
        app,
        "desktop-tile-watch-action-harness-connection-\(longID)"
      ).waitForExistence(timeout: 10)
    )

    homeScroll.coordinate(
      withNormalizedOffset: CGVector(dx: 0.5, dy: 0.7)
    ).scroll(byDeltaX: 0, deltaY: -homeScroll.frame.height * 2)
    let recentTitle = workspaceElement(
      app,
      "desktop-home-recent-title-harness-connection-\(longID)-native"
    )
    XCTAssertTrue(
      recentTitle.waitForExistence(timeout: 10),
      app.debugDescription
    )
    let recentConnection = workspaceElement(
      app,
      "desktop-home-recent-connection-harness-connection-\(longID)-native"
    )
    let recentTime = workspaceElement(
      app,
      "desktop-home-recent-time-harness-connection-\(longID)-native"
    )
    let recentActions = workspaceElement(
      app,
      "desktop-home-recent-note-action-harness-connection-\(longID)"
    )
    XCTAssertTrue(recentConnection.waitForExistence(timeout: 10))
    XCTAssertTrue(recentTime.waitForExistence(timeout: 10))
    XCTAssertTrue(recentActions.waitForExistence(timeout: 10))
    assertNoHorizontalOverlap(recentConnection, recentTime)
    assertNoHorizontalOverlap(recentTime, recentActions)
    XCTAssertTrue(
      workspaceElement(
        app,
        "desktop-home-recent-dot-harness-connection-\(longID)"
      ).waitForExistence(timeout: 10)
    )
    XCTAssertEqual(
      workspaceElement(
        app,
        "desktop-home-recent-title-harness-connection-preview-only-native"
      ).label,
      "Preview rendered exactly once"
    )
    XCTAssertFalse(
      workspaceElement(
        app,
        "desktop-home-recent-subtitle-harness-connection-preview-only-native"
      ).exists
    )

    clickCenter(workspaceElement(app, "desktop-activity-history"))
    _ = waitForWorkspaceState { state in
      (state["lowerPanel"] as? String) == "history"
    }
    let historyPanel = workspaceElement(app, "desktop-history-panel")
    let historyTitle = workspaceElement(
      app,
      "desktop-panel-history-title-harness-connection-\(longID)-native"
    )
    if !historyTitle.isHittable {
      historyPanel.coordinate(
        withNormalizedOffset: CGVector(dx: 0.5, dy: 0.7)
      ).scroll(byDeltaX: 0, deltaY: -historyPanel.frame.height)
    }
    XCTAssertTrue(
      historyTitle.waitForExistence(timeout: 10),
      app.debugDescription
    )
    XCTAssertTrue(
      workspaceElement(
        app,
        "desktop-panel-history-subtitle-harness-connection-\(longID)-native"
      ).waitForExistence(timeout: 10)
    )
    XCTAssertTrue(
      workspaceElement(
        app,
        "desktop-panel-history-session-id-harness-connection-\(longID)-native"
      ).waitForExistence(timeout: 10)
    )
    let historyConnection = workspaceElement(
      app,
      "desktop-panel-history-connection-harness-connection-\(longID)-native"
    )
    let historyTime = workspaceElement(
      app,
      "desktop-panel-history-time-harness-connection-\(longID)-native"
    )
    XCTAssertTrue(historyConnection.waitForExistence(timeout: 10))
    XCTAssertTrue(historyTime.waitForExistence(timeout: 10))
    assertNoHorizontalOverlap(historyConnection, historyTime)
    XCTAssertTrue(
      workspaceElement(
        app,
        "desktop-panel-history-note-action-harness-connection-\(longID)"
      ).waitForExistence(timeout: 10)
    )
  }

  func testWatchlistVerticalDragFollowsPointerDirection() throws {
    let app = launchWorkspaceHarness()
    _ = waitForWorkspaceState { state in
      (state["watchlistOrder"] as? [String])
        == [
          "one", "two", "three", "four",
          "session-with-a-deliberately-long-identifier-for-native-truncation",
        ]
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
        == [
          "two", "three", "one", "four",
          "session-with-a-deliberately-long-identifier-for-native-truncation",
        ]
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
        == [
          "one", "two", "three", "four",
          "session-with-a-deliberately-long-identifier-for-native-truncation",
        ]
    }
  }
}