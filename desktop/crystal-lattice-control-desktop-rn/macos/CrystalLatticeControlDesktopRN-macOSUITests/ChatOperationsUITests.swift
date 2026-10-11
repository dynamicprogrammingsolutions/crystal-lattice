import XCTest

final class ChatOperationsUITests: XCTestCase {
  override func setUpWithError() throws {
    continueAfterFailure = false
  }

  private func element(_ app: XCUIApplication, _ identifier: String) -> XCUIElement {
    app.descendants(matching: .any).matching(identifier: identifier).firstMatch
  }

  private func wait(_ app: XCUIApplication, _ identifier: String) -> XCUIElement {
    let target = element(app, identifier)
    if !target.exists {
      XCTAssertTrue(target.waitForExistence(timeout: 30), "Missing \(identifier)\n\(app.debugDescription)")
    }
    return target
  }

  private func waitGone(_ app: XCUIApplication, _ identifier: String) {
    let target = element(app, identifier)
    XCTAssertTrue(
      NSPredicate(format: "exists == false")
        .evaluate(with: target) ||
        XCTWaiter.wait(
          for: [XCTNSPredicateExpectation(predicate: NSPredicate(format: "exists == false"), object: target)],
          timeout: 30
        ) == .completed,
      "Still visible: \(identifier)\n\(app.debugDescription)"
    )
  }

  private func waitForSendProgress(_ app: XCUIApplication, active: Bool) {
    let send = wait(app, "composer-send")
    let expected = active ? "In progress" : "Ready"
    let predicate = NSPredicate(format: active
      ? "label ENDSWITH ', in progress'"
      : "NOT (label ENDSWITH ', in progress')")
    XCTAssertEqual(
      XCTWaiter.wait(for: [XCTNSPredicateExpectation(predicate: predicate, object: send)], timeout: 30),
      .completed,
      "Expected Send \(expected): \(app.debugDescription)"
    )
  }

  private func waitForRecovery(_ app: XCUIApplication, active: Bool) {
    let row = element(app, "chat-activity-row")
    let predicate = NSPredicate { _, _ in
      let showingRecovery = row.exists && row.label == "Send recovery"
      return showingRecovery == active
    }
    XCTAssertEqual(
      XCTWaiter.wait(for: [XCTNSPredicateExpectation(predicate: predicate, object: nil)], timeout: 30),
      .completed,
      "Expected recovery \(active)\n\(app.debugDescription)"
    )
  }

  private func replaceText(_ app: XCUIApplication, _ text: String) {
    let composer = wait(app, "message-composer-input")
    composer.click()
    composer.typeKey("a", modifierFlags: .command)
    composer.typeText(text)
  }

  private func selectTab(_ app: XCUIApplication, connectionId: String, sessionId: String) {
    let tab = wait(app, "desktop-session-tab-\(connectionId):\(sessionId)")
    let home = wait(app, "desktop-home-tab")
    guard let strip = app.scrollViews.allElementsBoundByIndex.first(where: {
      abs($0.frame.minY - home.frame.minY) < 4 && $0.frame.minX > home.frame.maxX
    }) else {
      XCTFail("Missing native session tab scroll view")
      return
    }
    for _ in 0..<8 {
      let visible = tab.frame.intersection(strip.frame)
      if visible.width >= 80 {
        app.windows.firstMatch.coordinate(withNormalizedOffset: .zero)
          .withOffset(CGVector(
            dx: visible.minX + 24 - app.windows.firstMatch.frame.minX,
            dy: visible.midY - app.windows.firstMatch.frame.minY
          )).click()
        return
      }
      strip.scroll(byDeltaX: tab.frame.midX > strip.frame.midX ? -200 : 200, deltaY: 0)
    }
    XCTFail("Could not scroll to session tab \(sessionId)")
  }

  private func checkGeometry(_ app: XCUIApplication, status: Bool) {
    let viewport = wait(app, "chat-transcript-viewport")
    let scrollView = viewport.scrollViews.firstMatch
    let transcript = scrollView.exists ? scrollView.frame : viewport.frame
    let composer = wait(app, "chat-composer").frame
    let title = wait(app, "chat-header").frame
    let usableHeight = composer.maxY - title.minY
    XCTAssertLessThanOrEqual(composer.maxY, app.windows.firstMatch.frame.maxY + 2)
    XCTAssertGreaterThanOrEqual(
      transcript.height, usableHeight * 0.30,
      "Transcript \(transcript), composer \(composer), header \(title)\n\(app.debugDescription)"
    )
    XCTAssertLessThanOrEqual(transcript.maxY, composer.minY + 2)
    if status {
      let row = wait(app, "chat-activity-row").frame
      XCTAssertLessThanOrEqual(row.maxY, transcript.minY + 2)
      XCTAssertLessThanOrEqual(row.height, 56)
    }
  }

  private func action(_ app: XCUIApplication, id: String, label: String) -> XCUIElement {
    let pinned = element(app, "session-rich-action-\(id)-session-header")
    if pinned.exists { return pinned }
    wait(app, "session-actions-menu").click()
    let menuItem = app.buttons.matching(NSPredicate(format: "label == %@", label)).firstMatch
    XCTAssertTrue(menuItem.waitForExistence(timeout: 15), "Missing action \(label)\n\(app.debugDescription)")
    return menuItem
  }

  private func checkWheel(_ app: XCUIApplication, status: Bool) {
    let window = app.windows.firstMatch
    let viewport = wait(app, "chat-transcript-viewport").frame.intersection(window.frame)
    let rows = app.descendants(matching: .any)
      .matching(NSPredicate(format: "identifier BEGINSWITH 'transcript-message-'"))
      .allElementsBoundByIndex
    guard let message = rows.first(where: {
      $0.frame.intersection(viewport).height > 20
    }) else {
      XCTFail("No visible production transcript row")
      return
    }
    let frame = message.frame.intersection(viewport)
    XCTAssertGreaterThan(frame.height, 1)
    let before = message.frame.minY
    let point = window.coordinate(withNormalizedOffset: .zero)
      .withOffset(CGVector(dx: frame.midX - window.frame.minX, dy: frame.midY - window.frame.minY))
    let direction: CGFloat = app.buttons["Scroll to top"].exists ? 160 : -160
    point.scroll(byDeltaX: 0, deltaY: direction)
    let moved = XCTNSPredicateExpectation(
      predicate: NSPredicate { _, _ in abs(message.frame.minY - before) > 10 },
      object: nil
    )
    if XCTWaiter.wait(for: [moved], timeout: 3) != .completed {
      point.scroll(byDeltaX: 0, deltaY: -direction)
      let reversed = XCTNSPredicateExpectation(
        predicate: NSPredicate { _, _ in abs(message.frame.minY - before) > 10 },
        object: nil
      )
      XCTAssertEqual(
        XCTWaiter.wait(for: [reversed], timeout: 5), .completed,
        "Wheel did not move \(message.identifier) within \(viewport)\n\(app.debugDescription)"
      )
    }
    checkGeometry(app, status: status)
  }

  func testChatOperationsThroughProductionUIAndHTTP() throws {
    let fixtureURL = URL(fileURLWithPath: #filePath)
      .deletingLastPathComponent()
      .deletingLastPathComponent()
      .deletingLastPathComponent()
      .appendingPathComponent("build/chat-operations-fixture.json")
    guard let data = try? Data(contentsOf: fixtureURL),
          let text = String(data: data, encoding: .utf8),
          let fixture = try JSONSerialization.jsonObject(with: data) as? [String: Any],
          let connection = fixture["connection"] as? [String: Any],
          let connectionId = connection["id"] as? String,
          let sessionIds = fixture["openSessionIds"] as? [String],
          let sessionId = fixture["sessionId"] as? String,
          let bundleIdentifier = fixture["bundleIdentifier"] as? String else {
      XCTFail("Missing native fixture")
      return
    }
    let app = XCUIApplication(bundleIdentifier: bundleIdentifier)
    app.launchArguments.append("--chat-operations-native-test")
    app.launchEnvironment["CLC_HUMAN_TIME_NATIVE_FIXTURE_JSON"] = text
    app.launch()
    app.activate()

    replaceText(app, "native desktop request")
    wait(app, "composer-send").click()
    waitForSendProgress(app, active: true)
    checkWheel(app, status: true)
    for otherId in sessionIds where otherId != sessionId {
      selectTab(app, connectionId: connectionId, sessionId: otherId)
    }
    let backgroundStatus = wait(app, "desktop-tab-request-status-\(connectionId):\(sessionId)")
    let finished = XCTNSPredicateExpectation(
      predicate: NSPredicate { _, _ in
        guard let value = backgroundStatus.value as? String else { return false }
        return value != "In progress"
      },
      object: nil
    )
    XCTAssertEqual(XCTWaiter.wait(for: [finished], timeout: 80), .completed)
    selectTab(app, connectionId: connectionId, sessionId: sessionId)
    waitForSendProgress(app, active: false)

    replaceText(app, "native ordinary desktop draft")
    let bottom = app.buttons["Scroll to bottom"]
    if bottom.exists { bottom.click() }
    let original = wait(app, "transcript-message-23")
    let modify = original.descendants(matching: .any).matching(identifier: "message-action-modify").firstMatch
    XCTAssertTrue(modify.waitForExistence(timeout: 10))
    modify.click()
    XCTAssertEqual(wait(app, "composer-edit-context").label, "Editing message [23]")
    wait(app, "composer-cancel-edit").click()
    waitGone(app, "composer-edit-context")
    XCTAssertEqual(wait(app, "message-composer-input").value as? String, "native ordinary desktop draft")
    modify.click()
    let save = wait(app, "composer-send")
    XCTAssertEqual(save.label, "Save edit")
    replaceText(app, "native desktop edited message " + String(repeating: "long content ", count: 30))
    checkWheel(app, status: false)
    for otherId in sessionIds where otherId != sessionId {
      selectTab(app, connectionId: connectionId, sessionId: otherId)
    }
    selectTab(app, connectionId: connectionId, sessionId: sessionId)
    XCTAssertEqual(wait(app, "composer-edit-context").label, "Editing message [23]")
    XCTAssertTrue((wait(app, "message-composer-input").value as? String)?.hasPrefix("native desktop edited message ") == true)
    wait(app, "composer-send").click()
    waitForSendProgress(app, active: true)
    checkWheel(app, status: true)
    waitGone(app, "composer-edit-context")
    XCTAssertEqual(wait(app, "message-composer-input").value as? String, "native ordinary desktop draft")

    let slow = action(app, id: "slow", label: "Slow action")
    slow.click()
    _ = wait(app, "chat-activity-progress")
    let second = action(app, id: "second", label: "Second action")
    XCTAssertTrue(second.isEnabled)
    second.click()
    checkGeometry(app, status: true)
    waitGone(app, "chat-activity-progress")

    replaceText(app, "native uncertain desktop send")
    wait(app, "composer-send").click()
    waitForRecovery(app, active: true)
    checkWheel(app, status: true)
    wait(app, "chat-send-recovery-resend").click()
    waitForRecovery(app, active: false)
    wait(app, "composer-action-cancel").click()
    waitForSendProgress(app, active: false)

    replaceText(app, "native cancelled desktop draft")
    wait(app, "composer-send").click()
    waitForRecovery(app, active: true)
    checkGeometry(app, status: true)
    wait(app, "chat-send-recovery-cancel").click()
    waitForRecovery(app, active: false)
    XCTAssertEqual(wait(app, "message-composer-input").value as? String, "native cancelled desktop draft")
    XCTAssertTrue(wait(app, "composer-send").isEnabled)
    let screenshot = XCTAttachment(screenshot: app.screenshot())
    screenshot.name = "Chat operations after recovery cancellation"
    screenshot.lifetime = .keepAlways
    add(screenshot)
  }
}