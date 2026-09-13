import XCTest

final class SessionFiltersPopoverUITests: XCTestCase {
  func testRichSessionUiModelAndPlacedActions() throws {
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_RICH_SESSION_UI_HARNESS"] = "1"
    app.launch()

    let harness = app.windows["DesktopRichSessionUiHarnessWindow"]
    XCTAssertTrue(harness.waitForExistence(timeout: 15))

    let model = element(app, "composer-rich-config-model")
    XCTAssertTrue(model.waitForExistence(timeout: 10))
    waitForLabel(model, "Model: Claude A")
    model.click()

    var nativePopover = harness.popovers.firstMatch
    XCTAssertTrue(nativePopover.waitForExistence(timeout: 10), app.debugDescription)
    let option = element(
      nativePopover,
      "rich-config-dropdown-model-declared-claude-b"
    )
    XCTAssertTrue(option.waitForExistence(timeout: 10))
    option.click()
    waitForLabel(model, "Model: Claude B", timeout: 10)

    model.click()
    nativePopover = harness.popovers.firstMatch
    XCTAssertTrue(nativePopover.waitForExistence(timeout: 10), app.debugDescription)
    let customInput = element(
      nativePopover,
      "rich-config-dropdown-model-input"
    )
    XCTAssertTrue(customInput.waitForExistence(timeout: 10), app.debugDescription)
    customInput.click()
    customInput.typeText("vendor/custom-model")
    element(
      nativePopover,
      "rich-config-dropdown-model-custom-vendor/custom-model"
    ).click()
    waitForLabel(model, "Model: vendor/custom-model", timeout: 10)

    model.click()
    nativePopover = harness.popovers.firstMatch
    XCTAssertTrue(nativePopover.waitForExistence(timeout: 10), app.debugDescription)
    element(nativePopover, "rich-config-dropdown-model-reset").click()
    waitForLabel(model, "Model: Claude A", timeout: 10)

    let toggle = element(
      app,
      "session-rich-action-toggle_feature-session-header"
    )
    XCTAssertTrue(toggle.waitForExistence(timeout: 10))
    waitForLabel(toggle, "Toggle feature: Off")
    toggle.click()
    waitForLabel(toggle, "Toggle feature: On", timeout: 10)

    let status = element(app, "session-rich-action-set_status-composer")
    XCTAssertTrue(status.waitForExistence(timeout: 10))
    waitForLabel(status, "Set status: To do")
    status.click()
    nativePopover = harness.popovers.firstMatch
    XCTAssertTrue(nativePopover.waitForExistence(timeout: 10), app.debugDescription)
    let done = element(
      nativePopover,
      "session-rich-list-set_status-option-done"
    )
    XCTAssertTrue(done.waitForExistence(timeout: 10))
    done.click()
    waitForLabel(status, "Set status: Done", timeout: 10)
  }

  func testFullSessionSettingsUsesNativeComboBox() throws {
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_RICH_SESSION_UI_HARNESS"] = "1"
    app.launch()

    let harness = app.windows["DesktopRichSessionUiHarnessWindow"]
    XCTAssertTrue(harness.waitForExistence(timeout: 15))

    let model = element(app, "composer-rich-config-model")
    XCTAssertTrue(model.waitForExistence(timeout: 10))
    waitForLabel(model, "Model: Claude A")
    let backendModel = element(app, "desktop-rich-session-ui-model-marker")
    XCTAssertTrue(backendModel.waitForExistence(timeout: 10))
    waitForLabel(backendModel, "Desktop rich model claude-a")

    let sessionActions = element(app, "session-actions-menu")
    XCTAssertTrue(sessionActions.waitForExistence(timeout: 10))
    sessionActions.click()

    let actionsPopover = harness.popovers.firstMatch
    XCTAssertTrue(actionsPopover.waitForExistence(timeout: 10), app.debugDescription)
    let settingsAction = element(actionsPopover, "actions-menu-action-settings")
    XCTAssertTrue(settingsAction.waitForExistence(timeout: 10))
    settingsAction.click()

    let comboBox = app.comboBoxes["session-setting-dropdown-model"]
    XCTAssertTrue(comboBox.waitForExistence(timeout: 15), app.debugDescription)

    replaceComboBoxText(comboBox, with: "claude-b")
    selectComboBoxOption(app, comboBox, label: "Claude B")
    waitForLabel(backendModel, "Desktop rich model claude-b", timeout: 10)
    XCTAssertTrue(
      element(app, "session-setting-reset-model").waitForExistence(timeout: 10)
    )

    replaceComboBoxText(comboBox, with: "vendor/full-settings-model")
    selectComboBoxOption(
      app,
      comboBox,
      label: "Use 'vendor/full-settings-model' as a custom model ID"
    )
    waitForLabel(
      backendModel,
      "Desktop rich model vendor/full-settings-model",
      timeout: 10
    )

    replaceComboBoxText(comboBox, with: "not valid")
    comboBox.buttons.firstMatch.click()
    let invalidOption = app.descendants(matching: .any).matching(
      NSPredicate(
        format: "label == %@ OR value == %@",
        "Use 'not valid' as a custom model ID",
        "Use 'not valid' as a custom model ID"
      )
    ).firstMatch
    XCTAssertFalse(invalidOption.waitForExistence(timeout: 1))
    comboBox.typeKey(.escape, modifierFlags: [])
    waitForLabel(
      backendModel,
      "Desktop rich model vendor/full-settings-model",
      timeout: 2
    )

    let reset = element(app, "session-setting-reset-model")
    XCTAssertTrue(reset.waitForExistence(timeout: 10), app.debugDescription)
    reset.click()
    waitForLabel(backendModel, "Desktop rich model claude-a", timeout: 10)
  }

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

  private func replaceComboBoxText(
    _ comboBox: XCUIElement,
    with value: String
  ) {
    comboBox.click()
    comboBox.typeKey("a", modifierFlags: .command)
    comboBox.typeKey(.delete, modifierFlags: [])
    comboBox.typeText(value)
  }

  private func selectComboBoxOption(
    _ app: XCUIApplication,
    _ comboBox: XCUIElement,
    label: String
  ) {
    let disclosure = comboBox.buttons.firstMatch
    XCTAssertTrue(disclosure.exists)
    disclosure.click()
    let option = app.descendants(matching: .any).matching(
      NSPredicate(format: "label == %@ OR value == %@", label, label)
    ).firstMatch
    XCTAssertTrue(option.waitForExistence(timeout: 10), app.debugDescription)
    option.click()
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

  func testLocalWatchlistAndNoteActionsAppearInSessionsAndChat() throws {
    var app = launchHarness()
    var harnessWindow = app.windows["SessionFiltersPopoverHarnessWindow"]
    XCTAssertTrue(
      harnessWindow.waitForExistence(timeout: 20),
      app.debugDescription
    )

    var actionsButton = element(app, "session-actions-menu-pinned-done")
    XCTAssertTrue(actionsButton.waitForExistence(timeout: 10))
    actionsButton.click()
    var actionsPopover = harnessWindow.popovers.firstMatch
    XCTAssertTrue(actionsPopover.waitForExistence(timeout: 10))
    var watchlistAction = element(
      actionsPopover,
      "actions-menu-action-localWatchlist"
    )
    XCTAssertTrue(watchlistAction.waitForExistence(timeout: 10))
    waitForLabel(watchlistAction, "Add to Watchlist")
    watchlistAction.click()
    waitForLabel(
      element(app, "session-filters-watchlist-marker"),
      "Sessions Watchlist watched",
      timeout: 10
    )

    actionsButton.click()
    actionsPopover = harnessWindow.popovers.firstMatch
    XCTAssertTrue(actionsPopover.waitForExistence(timeout: 10))
    watchlistAction = element(
      actionsPopover,
      "actions-menu-action-localWatchlist"
    )
    waitForLabel(watchlistAction, "Remove from Watchlist")
    let noteAction = element(actionsPopover, "actions-menu-action-localNote")
    XCTAssertTrue(noteAction.waitForExistence(timeout: 10))
    waitForLabel(noteAction, "Add local note")
    noteAction.click()
    waitForLabel(
      element(app, "session-filters-note-marker"),
      "Sessions local note edits 1",
      timeout: 10
    )
    XCTAssertFalse(
      element(app, "desktop-session-note-action-pinned-done").exists
    )

    app.terminate()
    app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_RICH_SESSION_UI_HARNESS"] = "1"
    app.launch()
    harnessWindow = app.windows["DesktopRichSessionUiHarnessWindow"]
    XCTAssertTrue(
      harnessWindow.waitForExistence(timeout: 20),
      app.debugDescription
    )

    actionsButton = element(app, "session-actions-menu")
    XCTAssertTrue(actionsButton.waitForExistence(timeout: 10))
    actionsButton.click()
    actionsPopover = harnessWindow.popovers.firstMatch
    XCTAssertTrue(actionsPopover.waitForExistence(timeout: 10))
    watchlistAction = element(
      actionsPopover,
      "actions-menu-action-localWatchlist"
    )
    waitForLabel(watchlistAction, "Add to Watchlist")
    watchlistAction.click()
    waitForLabel(
      element(app, "desktop-rich-session-ui-watchlist-marker"),
      "Desktop Watchlist watched",
      timeout: 10
    )

    actionsButton.click()
    actionsPopover = harnessWindow.popovers.firstMatch
    XCTAssertTrue(actionsPopover.waitForExistence(timeout: 10))
    let chatNoteAction = element(
      actionsPopover,
      "actions-menu-action-localNote"
    )
    XCTAssertTrue(chatNoteAction.waitForExistence(timeout: 10))
    chatNoteAction.click()
    waitForLabel(
      element(app, "desktop-rich-session-ui-note-marker"),
      "Desktop local note edits 1",
      timeout: 10
    )
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