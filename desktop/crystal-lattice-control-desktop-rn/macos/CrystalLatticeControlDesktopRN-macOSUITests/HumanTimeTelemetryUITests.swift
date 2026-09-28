import XCTest
import CoreGraphics

final class HumanTimeTelemetryUITests: XCTestCase {
  private let fixtureURL = URL(
    fileURLWithPath: "/tmp/clc-human-time-telemetry-native.json"
  )

  override func setUpWithError() throws {
    continueAfterFailure = false
  }

  private func loadFixture() throws -> [String: Any] {
    guard let data = try? Data(contentsOf: fixtureURL),
          let fixture = try? JSONSerialization.jsonObject(with: data)
            as? [String: Any] else {
      XCTFail("Missing host-runner fixture at \(fixtureURL.path)")
      throw NSError(
        domain: "HumanTimeTelemetryUITests",
        code: 1,
        userInfo: nil
      )
    }
    return fixture
  }

  private func element(
    _ app: XCUIApplication,
    identifier: String
  ) -> XCUIElement {
    app.descendants(matching: .any)
      .matching(identifier: identifier)
      .firstMatch
  }

  private func waitForElement(
    _ app: XCUIApplication,
    identifier: String,
    timeout: TimeInterval = 30
  ) -> XCUIElement {
    let candidate = element(app, identifier: identifier)
    XCTAssertTrue(
      candidate.waitForExistence(timeout: timeout),
      "Missing \(identifier)\n\(app.debugDescription)"
    )
    return candidate
  }

  private func openGlobalSettings(_ app: XCUIApplication) {
    let applicationMenu =
      app.menuBars.menuBarItems["CrystalLatticeControlDesktopRN"]
    XCTAssertTrue(
      applicationMenu.waitForExistence(timeout: 20),
      app.debugDescription
    )
    applicationMenu.click()
    let settings = app.menuItems["Settings…"]
    XCTAssertTrue(settings.waitForExistence(timeout: 5), app.debugDescription)
    settings.click()
    XCTAssertTrue(
      app.windows["globalSettingsWindow"].waitForExistence(timeout: 10),
      app.debugDescription
    )
  }

  func testProductionActivityStoresSessionSpan() throws {
    let fixture = try loadFixture()
    guard let connection = fixture["connection"] as? [String: Any],
          let connectionName = connection["name"] as? String,
          let fixtureData = try? JSONSerialization.data(
            withJSONObject: fixture
          ),
          let fixtureJson = String(data: fixtureData, encoding: .utf8) else {
      XCTFail("Invalid host-runner fixture: \(fixture)")
      return
    }

    let app = XCUIApplication()
    app.launchArguments.append("--human-time-native-test")
    app.launchEnvironment["CLC_HUMAN_TIME_NATIVE_FIXTURE_JSON"] = fixtureJson
    app.launch()
    app.activate()

    let closeConnection = app.descendants(matching: .any)
      .matching(
        NSPredicate(
          format: "label == %@",
          "Close \(connectionName)"
        )
      )
      .firstMatch
    XCTAssertTrue(
      closeConnection.waitForExistence(timeout: 30),
      app.debugDescription
    )

    let composer = waitForElement(
      app,
      identifier: "message-composer-input",
      timeout: 30
    )
    composer.click()
    composer.typeText("hello")
    Thread.sleep(forTimeInterval: 1.0)
    composer.typeText(" desktop human time")
    waitForElement(app, identifier: "composer-send").click()

    waitForElement(app, identifier: "desktop-home-tab").click()
    Thread.sleep(forTimeInterval: 1.0)

    openGlobalSettings(app)
    waitForElement(
      app,
      identifier: "global-settings-time-tracking-diagnostics"
    ).click()
    let collectionState = waitForElement(
      app,
      identifier: "time-tracking-collection-state"
    )
    XCTAssertEqual(collectionState.label, "Collection: Enabled")
    let connectedCount = waitForElement(
      app,
      identifier: "time-tracking-connected-count"
    )
    XCTAssertEqual(connectedCount.label, "Connected servers: 1")
    waitForElement(app, identifier: "time-tracking-upload-now").click()
    Thread.sleep(forTimeInterval: 5.0)
  }
}