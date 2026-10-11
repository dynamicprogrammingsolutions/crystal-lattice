import XCTest
import AppKit

final class SessionFiltersPopoverUITests: XCTestCase {
  func testWebsiteProofBatch() throws {
    let project = URL(fileURLWithPath: #filePath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let input = project.appendingPathComponent("artifacts/website-proof-batch/active-run.json")
    let run = try XCTUnwrap(JSONSerialization.jsonObject(with: Data(contentsOf: input)) as? [String: Any])
    let bundleId = try XCTUnwrap(run["captureBundleId"] as? String)
    XCTAssertEqual(bundleId, "com.dynamicprogrammingsolutions.crystallatticecontrol.website-capture")
    for scene in try XCTUnwrap(run["scenes"] as? [[String: Any]]) {
      for appearance in ["light", "dark"] {
        try captureWebsiteProof(scene: scene, appearance: appearance, bundleId: bundleId)
        if scene["reportAction"] != nil {
          var compact = scene
          compact["compact"] = true
          try captureWebsiteProof(scene: compact, appearance: appearance, bundleId: bundleId)
        }
      }
    }
  }

  private func captureWebsiteProof(scene: [String: Any], appearance: String, bundleId: String) throws {
    XCTAssertTrue(NSRunningApplication.runningApplications(withBundleIdentifier: bundleId).isEmpty,
                  "Existing capture instance is not owned by this run.")
    let app = XCUIApplication(bundleIdentifier: bundleId)
    app.launchEnvironment["CLC_ENABLE_WEBSITE_VISUAL_HARNESS"] = "1"
    app.launchEnvironment["CLC_WEBSITE_VISUAL_KIND"] = scene["kind"] as? String
    app.launchEnvironment["CLC_WEBSITE_VISUAL_THEME"] = appearance
    app.launchEnvironment["CLC_WEBSITE_VISUAL_BACKEND_URL"] = scene["baseUrl"] as? String
    app.launchEnvironment["CLC_WEBSITE_VISUAL_SESSION_ID"] = scene["sessionId"] as? String
    let compact = scene["compact"] as? Bool == true
    if compact { app.launchEnvironment["CLC_WEBSITE_VISUAL_REPORT_COMPACT"] = "1" }
    app.launchArguments = ["-clcWebsiteVisualTheme", appearance, "-AppleInterfaceStyle", appearance == "dark" ? "Dark" : "Light"]
    addTeardownBlock { if app.state != .notRunning { app.terminate() } }
    app.launch()
    let window = app.windows["DesktopWebsiteVisualHarnessWindow"]
    XCTAssertTrue(window.waitForExistence(timeout: 30), app.debugDescription)
    dismissDevelopmentWarningBanner(in: window)
    let name = try XCTUnwrap(scene["name"] as? String)
    let sessionId = try XCTUnwrap(scene["sessionId"] as? String)
    let prefix = "\(name)-\(appearance)"
    let suffix = compact ? "-compact" : ""
    var controls: [[String: Any]] = []
    let menu: XCUIElement
    if name == "session-list" {
      let row = element(window, "session-row-\(sessionId)")
      XCTAssertTrue(row.waitForExistence(timeout: 30), app.debugDescription)
      for (id, target) in [
        ("toggle_session_pinned", "session-rich-header-\(sessionId)-header_trailing-toggle_session_pinned"),
        ("toggle_session_archived", "session-rich-action-\(sessionId)-toggle_session_archived"),
        ("set_session_status", "session-rich-action-\(sessionId)-set_session_status")
      ] {
        let control = element(row, target)
        XCTAssertTrue(control.waitForExistence(timeout: 15), app.debugDescription)
        controls.append(["id": id, "frame": websiteFrame(control.frame), "label": control.label])
      }
      menu = element(row, "session-actions-menu-\(sessionId)")
    } else if name == "message-actions" {
      let message = element(window, "transcript-message-1")
      XCTAssertTrue(message.waitForExistence(timeout: 30), app.debugDescription)
      menu = element(message, "message-actions-menu")
    } else {
      menu = element(window, "session-actions-menu")
    }
    XCTAssertTrue(menu.waitForExistence(timeout: 30), app.debugDescription)
    if scene["reportAction"] != nil && !compact {
      websiteAttach(window.screenshot(), name: "\(prefix)-conversation")
    }
    menu.click()
    let popover = window.popovers.firstMatch
    XCTAssertTrue(popover.waitForExistence(timeout: 15), app.debugDescription)
    dismissDevelopmentWarningBanner(in: popover)
    let detail: XCUIElement
    var rows: [[String: Any]] = []
    var geometry: [String: Any] = ["window": websiteFrame(window.frame), "controls": controls]
    if let action = scene["reportAction"] as? [String: Any] {
      let id = try XCTUnwrap(action["id"] as? String)
      let trigger = element(popover, "actions-menu-action-\(id)")
      XCTAssertTrue(trigger.waitForExistence(timeout: 15), app.debugDescription)
      for _ in 0..<8 {
        if trigger.isHittable { break }
        popover.scrollViews.firstMatch.swipeUp()
      }
      XCTAssertTrue(trigger.isHittable, app.debugDescription)
      trigger.click()
      detail = app.windows["actionDisplayWindow"]
      XCTAssertTrue(detail.waitForExistence(timeout: 30), app.debugDescription)
      let response = try XCTUnwrap(scene["response"] as? [String: Any])
      let result = try XCTUnwrap(response["result"] as? [String: Any])
      let display = try XCTUnwrap(result["display"] as? [String: Any])
      let title = try XCTUnwrap(display["title"] as? String)
      XCTAssertTrue(detail.staticTexts.matching(NSPredicate(format: "value BEGINSWITH %@", String(title.prefix(16)))).firstMatch.waitForExistence(timeout: 15),
                    app.debugDescription)
      dismissDevelopmentWarningBanner(in: detail)
      geometry["report"] = websiteFrame(detail.frame)
      geometry["reportActionId"] = action["actionId"]
      websiteAttach(detail.screenshot(), name: "\(prefix)-report\(suffix)")
    } else {
      for mapping in try XCTUnwrap(scene["mappings"] as? [[String: Any]]) {
        let id = try XCTUnwrap(mapping["id"] as? String)
        let label = try XCTUnwrap(mapping["label"] as? String)
        let target = element(popover, "actions-menu-action-\(id)")
        XCTAssertTrue(target.waitForExistence(timeout: 15), app.debugDescription)
        waitForLabel(target, label)
        rows.append(["id": id, "label": label, "frame": websiteFrame(target.frame)])
      }
      detail = popover
      geometry["popover"] = websiteFrame(popover.frame)
      geometry["rows"] = rows
      if name == "session-list" {
        geometry["listRow"] = websiteFrame(element(window, "session-row-\(sessionId)").frame)
      }
      websiteAttach(popover.screenshot(), name: "\(prefix)-popover")
    }
    websiteAttach(window.screenshot(), name: "\(prefix)-window\(suffix)")
    let data = XCTAttachment(
      data: try JSONSerialization.data(withJSONObject: geometry, options: [.prettyPrinted, .sortedKeys]),
      uniformTypeIdentifier: "public.json")
    data.name = "\(prefix)-geometry\(suffix)"
    data.lifetime = .keepAlways
    add(data)
    app.terminate()
  }

  private func websiteAttach(_ screenshot: XCUIScreenshot, name: String) {
    let attachment = XCTAttachment(screenshot: screenshot)
    attachment.name = name
    attachment.lifetime = .keepAlways
    add(attachment)
  }

  func testWebsiteSessionActionsLight() throws {
    try captureWebsiteSessionActions(appearance: "light")
  }

  func testWebsiteSessionActionsDark() throws {
    try captureWebsiteSessionActions(appearance: "dark")
  }

  private func captureWebsiteSessionActions(appearance: String) throws {
    let project = URL(fileURLWithPath: #filePath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let input = project.appendingPathComponent("artifacts/website-session-actions/active-run.json")
    let run = try XCTUnwrap(JSONSerialization.jsonObject(with: Data(contentsOf: input)) as? [String: Any])
    let bundleId = try XCTUnwrap(run["captureBundleId"] as? String)
    XCTAssertEqual(bundleId, "com.dynamicprogrammingsolutions.crystallatticecontrol.website-capture")
    XCTAssertTrue(NSRunningApplication.runningApplications(withBundleIdentifier: bundleId).isEmpty,
                  "An existing capture app is running; leave it untouched and stop.")
    let app = XCUIApplication(bundleIdentifier: bundleId)
    app.launchEnvironment["CLC_ENABLE_WEBSITE_VISUAL_HARNESS"] = "1"
    app.launchEnvironment["CLC_WEBSITE_VISUAL_KIND"] = "session-actions"
    app.launchEnvironment["CLC_WEBSITE_VISUAL_THEME"] = appearance
    app.launchEnvironment["CLC_WEBSITE_VISUAL_BACKEND_URL"] = run["baseUrl"] as? String
    app.launchEnvironment["CLC_WEBSITE_VISUAL_SESSION_ID"] = run["sessionId"] as? String
    app.launchArguments = ["-clcWebsiteVisualTheme", appearance, "-AppleInterfaceStyle", appearance == "dark" ? "Dark" : "Light"]
    app.launch()
    addTeardownBlock { app.terminate() } // Only the isolated capture instance started above.
    let window = app.windows["DesktopWebsiteVisualHarnessWindow"]
    XCTAssertTrue(window.waitForExistence(timeout: 30), app.debugDescription)
    let menu = element(app, "session-actions-menu")
    XCTAssertTrue(menu.waitForExistence(timeout: 30), app.debugDescription)
    dismissDevelopmentWarningBanner(in: window)
    let response = element(app, "transcript-message-1")
    XCTAssertTrue(response.waitForExistence(timeout: 30), app.debugDescription)
    let request = app.textViews.matching(
      NSPredicate(format: "value CONTAINS %@", "Help me plan a welcoming, hands-on workshop")
    ).firstMatch
    XCTAssertTrue(request.waitForExistence(timeout: 10), app.debugDescription)
    menu.click()
    let popover = window.popovers.firstMatch
    XCTAssertTrue(popover.waitForExistence(timeout: 15), app.debugDescription)
    dismissDevelopmentWarningBanner(in: popover)
    let mappings = try XCTUnwrap(run["mappings"] as? [[String: Any]])
    var rows: [[String: Any]] = []
    for mapping in mappings {
      let id = try XCTUnwrap(mapping["id"] as? String)
      let label = try XCTUnwrap(mapping["label"] as? String)
      let action = element(popover, "actions-menu-action-\(id)")
      XCTAssertTrue(action.waitForExistence(timeout: 15), app.debugDescription)
      waitForLabel(action, label)
      XCTAssertGreaterThanOrEqual(action.frame.minY, popover.frame.minY)
      XCTAssertLessThanOrEqual(action.frame.maxY, popover.frame.maxY)
      rows.append(["id": id, "label": label, "frame": websiteFrame(action.frame)])
    }
    let windowAttachment = XCTAttachment(screenshot: window.screenshot())
    windowAttachment.name = "\(appearance)-window"
    windowAttachment.lifetime = .keepAlways
    add(windowAttachment)
    let popoverAttachment = XCTAttachment(screenshot: popover.screenshot())
    popoverAttachment.name = "\(appearance)-popover"
    popoverAttachment.lifetime = .keepAlways
    add(popoverAttachment)
    let geometry: [String: Any] = [
      "appearance": appearance,
      "window": websiteFrame(window.frame),
      "popover": websiteFrame(popover.frame),
      "rows": rows,
    ]
    let geometryAttachment = XCTAttachment(
      data: try JSONSerialization.data(withJSONObject: geometry, options: [.prettyPrinted, .sortedKeys]),
      uniformTypeIdentifier: "public.json")
    geometryAttachment.name = "\(appearance)-geometry"
    geometryAttachment.lifetime = .keepAlways
    add(geometryAttachment)
    element(popover, "actions-popover-close").click()
    waitForDisappearance(popover)
  }

  private func websiteFrame(_ frame: CGRect) -> [String: Double] {
    return ["x": Double(frame.minX), "y": Double(frame.minY),
            "width": Double(frame.width), "height": Double(frame.height)]
  }

  func testMessageActionNamesWrapAndKeepPinsIndependent() throws {
    let app = XCUIApplication()
    app.launchEnvironment["CLC_ENABLE_RICH_SESSION_UI_HARNESS"] = "1"
    app.launch()
    let harness = app.windows["DesktopRichSessionUiHarnessWindow"]
    XCTAssertTrue(harness.waitForExistence(timeout: 15))
    dismissDevelopmentWarningBanner(in: harness)
    let openMenu = element(app, "message-actions-menu")
    XCTAssertTrue(openMenu.waitForExistence(timeout: 10), app.debugDescription)
    openMenu.click()
    let popover = harness.popovers.firstMatch
    XCTAssertTrue(popover.waitForExistence(timeout: 10), app.debugDescription)
    dismissDevelopmentWarningBanner(in: popover)
    let compaction = element(popover, "actions-menu-action-compact_native_history_through_message")
    let longAction = element(popover, "actions-menu-action-long_plugin_action")
    let copy = element(popover, "actions-menu-action-copy")
    XCTAssertTrue(longAction.waitForExistence(timeout: 10), app.debugDescription)
    waitForLabel(compaction, "OpenAI compaction up to here")
    XCTAssertGreaterThan(popover.frame.width, 320)
    XCTAssertLessThan(popover.frame.width, harness.frame.width)
    XCTAssertGreaterThan(longAction.frame.height, copy.frame.height + 5)
    XCTAssertLessThanOrEqual(longAction.frame.maxY, popover.frame.maxY)
    let pin = element(popover, "actions-menu-pin-compact_native_history_through_message")
    pin.click()
    waitForLabel(pin, "Unpin OpenAI compaction up to here")
    XCTAssertTrue(popover.exists)
    waitForLabel(element(app, "desktop-rich-session-ui-action-marker"), "Desktop rich action none")
    let attachment = XCTAttachment(screenshot: popover.screenshot())
    attachment.name = "Two-line message actions"
    attachment.lifetime = .keepAlways
    add(attachment)
    element(popover, "actions-popover-close").click()
    waitForDisappearance(popover)

    element(app, "message-menu-long-list").click()
    openMenu.click()
    XCTAssertTrue(popover.waitForExistence(timeout: 10))
    dismissDevelopmentWarningBanner(in: popover)
    XCTAssertLessThan(popover.frame.height, harness.frame.height)
    let lastPin = element(popover, "actions-menu-pin-long-17")
    let scroll = popover.scrollViews.firstMatch
    for _ in 0..<6 {
      if lastPin.frame.maxY <= popover.frame.maxY && lastPin.isHittable { break }
      scroll.scroll(byDeltaX: 0, deltaY: -400)
    }
    XCTAssertTrue(lastPin.isHittable)
    XCTAssertLessThanOrEqual(lastPin.frame.maxY, popover.frame.maxY)
    lastPin.click()
    waitForLabel(lastPin, "Unpin Summarize this conversation and preserve every decision")
    element(popover, "actions-popover-close").click()
    waitForDisappearance(popover)
  }

  private func dismissDevelopmentWarningBanner(in root: XCUIElement) {
    // Dismiss the Debug-only LogBox overlay through its normal close control,
    // keeping the rendered menu unobscured in the review screenshot.
    let banner = root.descendants(matching: .other).matching(
      NSPredicate(format: "label CONTAINS %@", "Open debugger to view warnings.")
    ).firstMatch
    if banner.exists {
      let close = banner.children(matching: .other).firstMatch
      if close.exists { close.click() }
    }
  }

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