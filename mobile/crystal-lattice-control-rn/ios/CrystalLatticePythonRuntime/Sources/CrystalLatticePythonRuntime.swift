import Foundation
import React
import UIKit

@objc(CrystalLatticePythonRuntime)
final class CrystalLatticePythonRuntime: NSObject {
  private static let queue = DispatchQueue(
    label: "com.dynamicprogrammingsolutions.crystallattice.python-runtime"
  )
  private static var initialized = false
  private static var runtimeInformation: [String: Any]?
  private static var lifecycleInitialized = false
  private static var activeRequestId: String?
  private static var activeSessionId: String?
  private static var backgroundTaskIdentifier: UIBackgroundTaskIdentifier =
    .invalid
  private static let lifecycleDefaultsKey =
    "clcEmbeddedRuntimeLifecycleStatus"

  @objc
  static func requiresMainQueueSetup() -> Bool {
    false
  }

  @objc(start:rejecter:)
  func start(
    _ resolve: @escaping RCTPromiseResolveBlock,
    rejecter reject: @escaping RCTPromiseRejectBlock
  ) {
    Self.queue.async {
      do {
        let result = try Self.startIfNeeded()
        resolve(result)
      } catch {
        reject("python_start_failed", error.localizedDescription, error)
      }
    }
  }

  @objc(runSmoke:rejecter:)
  func runSmoke(
    _ resolve: @escaping RCTPromiseResolveBlock,
    rejecter reject: @escaping RCTPromiseRejectBlock
  ) {
    Self.queue.async {
      do {
        _ = try Self.startIfNeeded()
        guard
          let info = try CLPythonHostSupport.runSmoke() as? [String: Any]
        else {
          throw RuntimeError.executionFailed
        }
        resolve(info)
      } catch {
        reject("python_smoke_failed", error.localizedDescription, error)
      }
    }
  }

  @objc(runApplicationSmoke:rejecter:)
  func runApplicationSmoke(
    _ resolve: @escaping RCTPromiseResolveBlock,
    rejecter reject: @escaping RCTPromiseRejectBlock
  ) {
    Self.queue.async {
      do {
        _ = try Self.startIfNeeded()
        let runtimeRoot = try Self.runtimeRoot()
        guard
          let info = try CLPythonHostSupport.runApplicationSmoke(
            atRoot: runtimeRoot.path
          ) as? [String: Any]
        else {
          throw RuntimeError.executionFailed
        }
        resolve(info)
      } catch {
        reject("python_application_smoke_failed", error.localizedDescription, error)
      }
    }
  }

  @objc(execute:resolver:rejecter:)
  func execute(
    _ request: NSDictionary,
    resolver resolve: @escaping RCTPromiseResolveBlock,
    rejecter reject: @escaping RCTPromiseRejectBlock
  ) {
    Self.queue.async {
      do {
        _ = try Self.startIfNeeded()
        guard var command = request as? [String: Any] else {
          throw RuntimeError.invalidCommand
        }
        if command["runtimeConfiguration"] == nil,
          let runtimeConfiguration = Self.runtimeConfiguration()
        {
          command["runtimeConfiguration"] = runtimeConfiguration
        }
        guard JSONSerialization.isValidJSONObject(command) else {
          throw RuntimeError.invalidCommand
        }
        let requestData = try JSONSerialization.data(withJSONObject: command)
        guard let requestJSON = String(data: requestData, encoding: .utf8) else {
          throw RuntimeError.invalidCommand
        }
        let runtimeRoot = try Self.runtimeRoot()
        let responseJSON = try CLPythonHostSupport.executeCommandJSON(
          requestJSON,
          runtimeRoot: runtimeRoot.path
        )
        guard
          let responseData = responseJSON.data(using: .utf8),
          let response = try JSONSerialization.jsonObject(
            with: responseData
          ) as? [String: Any]
        else {
          throw RuntimeError.invalidResponse
        }
        Self.observeCommand(command, response: response)
        resolve(response)
      } catch {
        reject("python_command_failed", error.localizedDescription, error)
      }
    }
  }

  @objc(noteAppState:resolver:rejecter:)
  func noteAppState(
    _ state: String,
    resolver resolve: @escaping RCTPromiseResolveBlock,
    rejecter reject: @escaping RCTPromiseRejectBlock
  ) {
    Self.queue.async {
      _ = reject
      Self.ensureLifecycleInitialized()
      var updates: [String: Any] = [
        "appState": state,
        "appStateChangedAtMs": Self.nowMs(),
      ]
      if Self.activeRequestId != nil {
        if state == "active" {
          updates["state"] = "running"
          updates["foregroundedAtMs"] = Self.nowMs()
        } else {
          updates["state"] = "background"
          updates["backgroundedAtMs"] = Self.nowMs()
          updates["lastBackgroundedAtMs"] = Self.nowMs()
        }
      }
      Self.updateLifecycle(updates)
      resolve(Self.lifecycleStatus())
    }
  }

  @objc(getLifecycleStatus:rejecter:)
  func getLifecycleStatus(
    _ resolve: @escaping RCTPromiseResolveBlock,
    rejecter reject: @escaping RCTPromiseRejectBlock
  ) {
    Self.queue.async {
      _ = reject
      Self.ensureLifecycleInitialized()
      resolve(Self.lifecycleStatus())
    }
  }

  @objc(configure:resolver:rejecter:)
  func configure(
    _ configuration: NSDictionary,
    resolver resolve: @escaping RCTPromiseResolveBlock,
    rejecter reject: @escaping RCTPromiseRejectBlock
  ) {
    Self.queue.async {
      do {
        guard
          let proxyURL = configuration["proxyUrl"] as? String,
          !proxyURL.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
          let model = configuration["model"] as? String,
          !model.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
        else {
          throw RuntimeError.invalidConfiguration
        }

        let defaults = UserDefaults.standard
        defaults.set(
          proxyURL.trimmingCharacters(in: .whitespacesAndNewlines),
          forKey: "clcEmbeddedProxyURL"
        )
        defaults.set(
          model.trimmingCharacters(in: .whitespacesAndNewlines),
          forKey: "clcEmbeddedModel"
        )
        if let apiKey = configuration["apiKey"] as? String,
          !apiKey.isEmpty
        {
          defaults.set(apiKey, forKey: "clcEmbeddedProxyAPIKey")
        }
        guard Self.runtimeConfiguration() != nil else {
          throw RuntimeError.missingAPIKey
        }
        resolve(Self.publicConfiguration())
      } catch {
        reject(
          "python_configuration_failed",
          error.localizedDescription,
          error
        )
      }
    }
  }

  @objc(getConfiguration:rejecter:)
  func getConfiguration(
    _ resolve: @escaping RCTPromiseResolveBlock,
    rejecter reject: @escaping RCTPromiseRejectBlock
  ) {
    Self.queue.async {
      _ = reject
      resolve(Self.publicConfiguration())
    }
  }

  private static func startIfNeeded() throws -> [String: Any] {
    ensureLifecycleInitialized()
    if initialized, let runtimeInformation {
      return runtimeInformation
    }

    guard
      let resourcesURL = Bundle.main.url(
        forResource: "CrystalLatticePythonRuntimeResources",
        withExtension: "bundle"
      ),
      let resources = Bundle(url: resourcesURL),
      let appArchive = resources.url(
        forResource: "crystal_lattice_app",
        withExtension: "zip"
      )
    else {
      throw RuntimeError.resourcesMissing
    }

    let stdlibPath = Bundle.main.bundleURL
      .appendingPathComponent("python")
      .appendingPathComponent("lib")
      .appendingPathComponent("python3.12")
    guard FileManager.default.fileExists(atPath: stdlibPath.path) else {
      throw RuntimeError.resourcesMissing
    }

    guard
      let info = try CLPythonHostSupport.start(
        withStdlibPath: stdlibPath.path,
        appArchive: appArchive.path
      ) as? [String: Any]
    else {
      throw RuntimeError.initializationFailed
    }
    initialized = true
    runtimeInformation = info
    return info
  }

  private static func runtimeRoot() throws -> URL {
    guard
      let applicationSupport = FileManager.default.urls(
        for: .applicationSupportDirectory,
        in: .userDomainMask
      ).first
    else {
      throw RuntimeError.applicationSupportMissing
    }
    let root = applicationSupport.appendingPathComponent(
      "CrystalLatticeEmbeddedRuntime",
      isDirectory: true
    )
    try FileManager.default.createDirectory(
      at: root,
      withIntermediateDirectories: true
    )
    return root
  }

  private static func runtimeConfiguration() -> [String: String]? {
    let defaults = UserDefaults.standard
    let configuration = [
      "api_key": defaults.string(forKey: "clcEmbeddedProxyAPIKey") ?? "",
      "model": defaults.string(forKey: "clcEmbeddedModel") ?? "",
      "proxy_url": defaults.string(forKey: "clcEmbeddedProxyURL") ?? "",
    ]
    return configuration.values.allSatisfy { !$0.isEmpty }
      ? configuration
      : nil
  }

  private static func publicConfiguration() -> [String: Any] {
    let defaults = UserDefaults.standard
    let apiKey = defaults.string(forKey: "clcEmbeddedProxyAPIKey") ?? ""
    return [
      "hasApiKey": !apiKey.isEmpty,
      "inspectionOnly": defaults.bool(
        forKey: "clcEmbeddedInspectionOnly"
      ),
      "model": defaults.string(forKey: "clcEmbeddedModel") ?? "",
      "proxyUrl": defaults.string(forKey: "clcEmbeddedProxyURL") ?? "",
    ]
  }

  private static func nowMs() -> Double {
    Date().timeIntervalSince1970 * 1000
  }

  private static func ensureLifecycleInitialized() {
    if lifecycleInitialized {
      return
    }
    lifecycleInitialized = true
    var status = UserDefaults.standard.dictionary(
      forKey: lifecycleDefaultsKey
    ) ?? ["state": "idle"]
    let previousState = status["state"] as? String
    if previousState == "running" || previousState == "background" {
      status["state"] = "interrupted"
      status["interruptedAtMs"] = nowMs()
      status["recoverable"] = true
    }
    status["processStartedAtMs"] = nowMs()
    UserDefaults.standard.set(status, forKey: lifecycleDefaultsKey)
  }

  private static func updateLifecycle(_ updates: [String: Any]) {
    var status = UserDefaults.standard.dictionary(
      forKey: lifecycleDefaultsKey
    ) ?? [:]
    for (key, value) in updates {
      status[key] = value
    }
    UserDefaults.standard.set(status, forKey: lifecycleDefaultsKey)
  }

  private static func lifecycleStatus() -> [String: Any] {
    var status = UserDefaults.standard.dictionary(
      forKey: lifecycleDefaultsKey
    ) ?? ["state": "idle"]
    status["backgroundTaskActive"] =
      backgroundTaskIdentifier != .invalid
    status["backgroundTimeRemaining"] = backgroundTimeRemaining()
    return status
  }

  private static func backgroundTimeRemaining() -> Double {
    var remaining = 0.0
    let read = {
      remaining = UIApplication.shared.backgroundTimeRemaining
    }
    if Thread.isMainThread {
      read()
    } else {
      DispatchQueue.main.sync(execute: read)
    }
    return remaining.isFinite && remaining < 86_400 ? remaining : -1
  }

  private static func beginRequest(
    requestId: String,
    sessionId: String?
  ) {
    endBackgroundTask()
    activeRequestId = requestId
    activeSessionId = sessionId
    let startedAt = nowMs()
    let previousStatus = UserDefaults.standard.dictionary(
      forKey: lifecycleDefaultsKey
    ) ?? [:]
    var nextStatus: [String: Any] = [
      "appState": UIApplication.shared.applicationState == .active
        ? "active"
        : "background",
      "backgroundTaskActive": true,
      "recoverable": false,
      "requestId": requestId,
      "sessionId": sessionId ?? "",
      "startedAtMs": startedAt,
      "state": "running",
    ]
    if let lastBackgroundedAt =
      previousStatus["lastBackgroundedAtMs"]
    {
      nextStatus["lastBackgroundedAtMs"] = lastBackgroundedAt
    }
    UserDefaults.standard.set(
      nextStatus,
      forKey: lifecycleDefaultsKey
    )

    var identifier: UIBackgroundTaskIdentifier = .invalid
    let begin = {
      identifier = UIApplication.shared.beginBackgroundTask(
        withName: "CrystalLatticeEmbeddedRequest"
      ) {
        Self.queue.async {
          Self.expireActiveRequest()
        }
      }
    }
    if Thread.isMainThread {
      begin()
    } else {
      DispatchQueue.main.sync(execute: begin)
    }
    backgroundTaskIdentifier = identifier
    updateLifecycle([
      "backgroundTaskActive": identifier != .invalid,
      "backgroundTimeRemaining": backgroundTimeRemaining(),
    ])
  }

  private static func expireActiveRequest() {
    guard activeRequestId != nil else {
      endBackgroundTask()
      return
    }
    updateLifecycle([
      "backgroundTaskActive": false,
      "expiredAtMs": nowMs(),
      "recoverable": true,
      "state": "expired",
    ])
    activeRequestId = nil
    activeSessionId = nil
    endBackgroundTask()
  }

  private static func finishRequest(state: String) {
    guard activeRequestId != nil else {
      return
    }
    var updates: [String: Any] = [
      "backgroundTaskActive": false,
      "finishedAtMs": nowMs(),
      "recoverable": state != "completed",
      "state": state,
    ]
    if state == "completed" {
      updates["completedAtMs"] = nowMs()
    } else {
      updates["failedAtMs"] = nowMs()
    }
    updateLifecycle(updates)
    activeRequestId = nil
    activeSessionId = nil
    endBackgroundTask()
  }

  private static func endBackgroundTask() {
    let identifier = backgroundTaskIdentifier
    backgroundTaskIdentifier = .invalid
    guard identifier != .invalid else {
      return
    }
    DispatchQueue.main.async {
      UIApplication.shared.endBackgroundTask(identifier)
    }
  }

  private static func observeCommand(
    _ command: [String: Any],
    response: [String: Any]
  ) {
    let method = String(describing: command["method"] ?? "").uppercased()
    let rawPath = String(describing: command["path"] ?? "")
    let path = rawPath.split(separator: "?", maxSplits: 1).first.map(String.init)
      ?? rawPath
    let parts = path.split(separator: "/").map(String.init)
    let data = response["data"] as? [String: Any] ?? [:]

    if method == "POST",
      parts.count >= 3,
      parts[0] == "sessions",
      parts.last == "send_message" || parts.last == "messages",
      let requestId = data["request_id"] as? String
    {
      beginRequest(
        requestId: requestId,
        sessionId: parts.count > 1 ? parts[1] : nil
      )
      return
    }

    if method == "POST",
      parts.count >= 3,
      parts[0] == "sessions",
      parts.last == "cancel"
    {
      finishRequest(state: "cancelled")
      return
    }

    guard method == "GET", parts.first == "events",
      let events = data["events"] as? [[String: Any]]
    else {
      return
    }
    for event in events.reversed() {
      guard let type = event["type"] as? String else {
        continue
      }
      if type == "request_completed" {
        finishRequest(state: "completed")
        return
      }
      if type == "request_failed" {
        finishRequest(state: "failed")
        return
      }
      if type == "request_cancelled" || type == "request_canceled" {
        finishRequest(state: "cancelled")
        return
      }
    }
  }

  private enum RuntimeError: LocalizedError {
    case resourcesMissing
    case applicationSupportMissing
    case initializationFailed
    case executionFailed
    case invalidCommand
    case invalidConfiguration
    case invalidResponse
    case missingAPIKey

    var errorDescription: String? {
      switch self {
      case .resourcesMissing:
        return "The bundled Python resources could not be found."
      case .applicationSupportMissing:
        return "The application-support directory could not be created."
      case .initializationFailed:
        return "The bundled Python interpreter did not initialize."
      case .executionFailed:
        return "The bundled Python smoke program failed."
      case .invalidCommand:
        return "The embedded runtime command is not valid JSON."
      case .invalidConfiguration:
        return "The embedded runtime endpoint and model are required."
      case .invalidResponse:
        return "The embedded runtime returned an invalid response."
      case .missingAPIKey:
        return "Enter an API key before connecting the embedded runtime."
      }
    }
  }
}