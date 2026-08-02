import XCTest

final class SessionFiltersPopoverUITests: XCTestCase {
  override func setUpWithError() throws {
    continueAfterFailure = false
  }

  private func element(_ root: XCUIElement, _ identifier: String) -> XCUIElement {
    root.descendants(matching: .any)[identifier]
  }

  private func waitForDisappearance(
    _ element: XCUIElement,
    timeout: TimeInterval = 5,
    file: StaticString = #filePath,
    line: UInt = #line
  ) {
    let predicate = NSPredicate(format: "exists == false")
    let expectation = XCTNSPredicateExpectation(predicate: predicate, object: element)
    let result = XCTWaiter.wait(for: [expectation], timeout: timeout)
    XCTAssertEqual(result, .completed, file: file, line: line)
  }

  private func waitForLabel(
    _ element: XCUIElement,
    _ label: String,
    timeout: TimeInterval = 5,
    file: StaticString = #filePath,
    line: UInt = #line
  ) {
    let predicate = NSPredicate(format: "label == %@", label)
    let expectation = XCTNSPredicateExpectation(predicate: predicate, object: element)
    let result = XCTWaiter.wait(for: [expectation], timeout: timeout)
    XCTAssertEqual(result, .completed, file: file, line: line)
  }

  private func waitForLabelContaining(
    _ element: XCUIElement,
    _ text: String,
    timeout: TimeInterval = 5,
    file: StaticString = #filePath,
    line: UInt = #line
  ) {
    let predicate = NSPredicate(format: "label CONTAINS %@", text)
    let expectation = XCTNSPredicateExpectation(predicate: predicate, object: element)
    let result = XCTWaiter.wait(for: [expectation], timeout: timeout)
    XCTAssertEqual(result, .completed, file: file, line: line)
  }

  private func launchHarness() -> XCUIApplication {
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_SESSION_FILTERS_POPOVER_HARNESS"] = "1"
    app.launchArguments.append("--session-filters-popover-harness")
    app.launch()
    app.activate()
    return app
  }

  func testSessionFiltersUseNativePopoverAndStaySynchronized() throws {
    let app = launchHarness()
    let harnessWindow = app.windows["SessionFiltersPopoverHarnessWindow"]
    XCTAssertTrue(
      harnessWindow.waitForExistence(timeout: 20),
      app.debugDescription
    )

    let filterButton = element(app, "session-filters-open")
    XCTAssertTrue(filterButton.waitForExistence(timeout: 10), app.debugDescription)
    filterButton.click()

    let nativePopover = harnessWindow.popovers.firstMatch
    XCTAssertTrue(nativePopover.waitForExistence(timeout: 10), app.debugDescription)
    XCTAssertEqual(app.sheets.count, 0)

    let horizontalDistance = abs(
      nativePopover.frame.midX - filterButton.frame.midX
    )
    XCTAssertLessThan(
      horizontalDistance,
      max(nativePopover.frame.width, 480),
      "Expected the native popover to remain anchored near the filter button."
    )

    let pinnedOption = element(
      nativePopover,
      "session-filter-pinned_state-option-true"
    )
    XCTAssertTrue(pinnedOption.waitForExistence(timeout: 5), app.debugDescription)
    pinnedOption.click()

    XCTAssertTrue(
      element(app, "session-row-pinned-done").waitForExistence(timeout: 5)
    )
    waitForDisappearance(element(app, "session-row-todo-session"))
    waitForDisappearance(element(app, "session-row-blocked-session"))
    waitForLabel(filterButton, "Open session filters, 1 active")

    let doneOption = element(
      nativePopover,
      "session-filter-session_status-option-3"
    )
    XCTAssertTrue(doneOption.waitForExistence(timeout: 5), app.debugDescription)
    doneOption.click()
    waitForLabel(filterButton, "Open session filters, 2 active")
    element(nativePopover, "session-filter-session_status-option-2").click()
    XCTAssertTrue(
      element(app, "session-row-pinned-done").waitForExistence(timeout: 5),
      "Selecting a second status while the popover is open must preserve the first selection."
    )

    element(nativePopover, "session-filters-close").click()
    waitForDisappearance(nativePopover)
    XCTAssertTrue(element(app, "session-row-pinned-done").exists)
    XCTAssertFalse(element(app, "session-row-todo-session").exists)

    filterButton.click()
    let reopenedPopover = harnessWindow.popovers.firstMatch
    XCTAssertTrue(reopenedPopover.waitForExistence(timeout: 10), app.debugDescription)
    waitForLabel(
      element(reopenedPopover, "session-filter-pinned_state-option-true"),
      "Pinned: Pinned, selected"
    )
    waitForLabel(
      element(reopenedPopover, "session-filter-session_status-option-3"),
      "Status: Done, selected"
    )
    waitForLabel(
      element(reopenedPopover, "session-filter-session_status-option-2"),
      "Status: Blocked, selected"
    )

    element(reopenedPopover, "session-filters-show-all").click()
    XCTAssertTrue(
      element(app, "session-row-todo-session").waitForExistence(timeout: 5)
    )
    XCTAssertTrue(
      element(app, "session-row-blocked-session").waitForExistence(timeout: 5)
    )
    waitForLabel(filterButton, "Open session filters")

    element(reopenedPopover, "session-filter-session_status-option-2").click()
    waitForDisappearance(element(app, "session-row-pinned-done"))
    XCTAssertTrue(
      element(app, "session-row-blocked-session").waitForExistence(timeout: 5)
    )
    element(reopenedPopover, "session-filters-reset").click()
    XCTAssertTrue(
      element(app, "session-row-pinned-done").waitForExistence(timeout: 5)
    )
    XCTAssertTrue(
      element(app, "session-row-todo-session").waitForExistence(timeout: 5)
    )

    app.typeKey(XCUIKeyboardKey.escape, modifierFlags: [])
    waitForDisappearance(reopenedPopover)
    XCTAssertEqual(app.sheets.count, 0)
  }

  func testNotificationRailAggregatesConnectionsAndPushesMessagesDown() throws {
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_NOTIFICATION_RAIL_HARNESS"] = "1"
    app.launchArguments.append("--notification-rail-harness")
    app.launch()
    app.activate()

    let harnessWindow = app.windows["DesktopNotificationRailHarnessWindow"]
    XCTAssertTrue(
      harnessWindow.waitForExistence(timeout: 20),
      app.debugDescription
    )
    let rail = element(app, "desktop-notification-combined-rail")
    let messages = element(app, "desktop-notification-message-content")
    XCTAssertTrue(rail.waitForExistence(timeout: 10), app.debugDescription)
    XCTAssertTrue(messages.waitForExistence(timeout: 10), app.debugDescription)
    XCTAssertTrue(rail.label.contains("First connection"))
    XCTAssertTrue(rail.label.contains("Second connection"))
    XCTAssertTrue(rail.label.contains("Active session notification"))
    XCTAssertLessThanOrEqual(
      rail.frame.maxY,
      messages.frame.minY,
      "The shared notification rail must push message content down."
    )

    let attachment = XCTAttachment(screenshot: app.screenshot())
    attachment.name = "desktop-notification-message-area-rail"
    attachment.lifetime = .keepAlways
    add(attachment)
  }

  func testRichSessionActionsUseNativePopoversAndImmediateStatusSelection() throws {
    let app = launchHarness()
    let harnessWindow = app.windows["SessionFiltersPopoverHarnessWindow"]
    XCTAssertTrue(
      harnessWindow.waitForExistence(timeout: 20),
      app.debugDescription
    )

    XCTAssertTrue(
      element(
        app,
        "session-rich-header-pinned-done-header_trailing-toggle_session_pinned"
      ).waitForExistence(timeout: 10),
      app.debugDescription
    )
    XCTAssertTrue(
      element(
        app,
        "session-rich-action-pinned-done-toggle_session_pinned"
      ).waitForExistence(timeout: 10),
      app.debugDescription
    )
    XCTAssertTrue(
      element(
        app,
        "session-rich-action-pinned-done-toggle_session_archived"
      ).waitForExistence(timeout: 10),
      app.debugDescription
    )

    let actionMenu = element(app, "session-actions-menu-pinned-done")
    XCTAssertTrue(actionMenu.waitForExistence(timeout: 10), app.debugDescription)
    actionMenu.click()

    let statusAction = element(app, "actions-menu-action-set_session_status")
    XCTAssertTrue(statusAction.waitForExistence(timeout: 10), app.debugDescription)
    statusAction.click()

    let statusList = element(
      app,
      "session-rich-list-pinned-done-set_session_status-close"
    )
    XCTAssertTrue(statusList.waitForExistence(timeout: 10), app.debugDescription)
    XCTAssertEqual(app.sheets.count, 0)

    let blocked = element(
      app,
      "session-rich-list-pinned-done-set_session_status-option-blocked"
    )
    XCTAssertTrue(blocked.waitForExistence(timeout: 5), app.debugDescription)
    blocked.click()
    waitForDisappearance(statusList)

    waitForLabelContaining(element(app, "session-row-pinned-done"), "Status: blocked")
    XCTAssertEqual(app.sheets.count, 0)
  }

  func testSessionsHeaderActionsUseNativePopoverAndSettingsWindow() throws {
    let app = launchHarness()
    let harnessWindow = app.windows["SessionFiltersPopoverHarnessWindow"]
    XCTAssertTrue(
      harnessWindow.waitForExistence(timeout: 20),
      app.debugDescription
    )

    let actionsButton = element(app, "sessions-actions-menu")
    XCTAssertTrue(actionsButton.waitForExistence(timeout: 10), app.debugDescription)
    actionsButton.click()

    let actionsPopover = harnessWindow.popovers.firstMatch
    XCTAssertTrue(actionsPopover.waitForExistence(timeout: 10), app.debugDescription)
    XCTAssertEqual(app.sheets.count, 0)
    XCTAssertTrue(
      element(actionsPopover, "actions-menu-action-serverSettings")
        .waitForExistence(timeout: 5)
    )
    XCTAssertTrue(
      element(actionsPopover, "actions-menu-action-refreshSessions")
        .waitForExistence(timeout: 5)
    )
    XCTAssertTrue(
      element(actionsPopover, "actions-menu-action-newSession")
        .waitForExistence(timeout: 5)
    )

    element(actionsPopover, "actions-menu-action-serverSettings").click()
    waitForDisappearance(actionsPopover)

    let settingsWindow = app.windows["serverSettingsWindow"]
    XCTAssertTrue(settingsWindow.waitForExistence(timeout: 10), app.debugDescription)
    XCTAssertTrue(
      element(app, "Close server settings")
        .waitForExistence(timeout: 5),
      app.debugDescription
    )
  }
}