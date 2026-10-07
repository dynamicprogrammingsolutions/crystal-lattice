import Foundation
import React
import Security
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
  private static let providerSettingsDefaultsKey =
    "clcEmbeddedProviderSettingsV3"
  private static let legacyProviderSettingsDefaultsKey =
    "clcEmbeddedProviderSettingsV2"
  private static let providerKeychainService =
    "com.dynamicprogrammingsolutions.crystallattice.embedded-provider-key"
  private static var activeWorkspaceGrantURLs: [String: URL] = [:]
  private static let embeddedSettings: [String: Any] = {
    guard
      let resourcesURL = Bundle.main.url(
        forResource: "CrystalLatticePythonRuntimeResources",
        withExtension: "bundle"
      ),
      let resources = Bundle(url: resourcesURL),
      let configURL = resources.url(
        forResource: "embedded-ios-config",
        withExtension: "json"
      ),
      let data = try? Data(contentsOf: configURL),
      let root = try? JSONSerialization.jsonObject(with: data)
        as? [String: Any],
      let settings = root["embedded_settings"] as? [String: Any]
    else {
      return [:]
    }
    return settings
  }()
  private static var providerOrder: [String] {
    embeddedSettings["profileOrder"] as? [String] ?? []
  }
  private static var providerDefinitions: [String: [String: Any]] {
    embeddedSettings["profiles"] as? [String: [String: Any]] ?? [:]
  }
  private static var configuredDefaultAgent: String {
    if let value = embeddedSettings["defaultAgent"] as? String,
      !value.isEmpty
    {
      return value
    }
    for profileId in providerOrder {
      if let agentId = providerDefinitions[profileId]?["agentId"] as? String,
        !agentId.isEmpty
      {
        return agentId
      }
    }
    return ""
  }

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
        let settings = try Self.settingsByApplying(configuration)
        try Self.applyAPIKeyUpdates(configuration)
        Self.saveProviderSettings(settings)
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

  @objc(validateConfiguration:resolver:rejecter:)
  func validateConfiguration(
    _ configuration: NSDictionary,
    resolver resolve: @escaping RCTPromiseResolveBlock,
    rejecter reject: @escaping RCTPromiseRejectBlock
  ) {
    Self.queue.async {
      do {
        _ = try Self.startIfNeeded()
        let candidate = try Self.candidateRuntimeConfiguration(configuration)
        let profileId =
          (configuration["profileId"] as? String)?.trimmingCharacters(
            in: .whitespacesAndNewlines
          ) ?? Self.profileId(
            forAgent: candidate["default_agent"] as? String
          )
        let command: [String: Any] = [
          "method": "POST",
          "path": "/embedded/runtime/validate",
          "body": ["profile_id": profileId],
          "runtimeConfiguration": candidate,
        ]
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
          ) as? [String: Any],
          let status = response["status"] as? Int
        else {
          throw RuntimeError.invalidResponse
        }
        if status >= 300 {
          let data = response["data"] as? [String: Any]
          throw RuntimeError.validationFailed(
            data?["detail"] as? String ?? "Provider validation failed."
          )
        }
        resolve(response["data"] ?? [:])
      } catch {
        reject(
          "python_configuration_validation_failed",
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

  @objc(registerWorkspaceDirectoryGrant:resolver:rejecter:)
  func registerWorkspaceDirectoryGrant(
    _ input: NSDictionary,
    resolver resolve: @escaping RCTPromiseResolveBlock,
    rejecter reject: @escaping RCTPromiseRejectBlock
  ) {
    Self.queue.async {
      do {
        guard
          let uri = input["uri"] as? String,
          let selectedURL = URL(string: uri),
          selectedURL.isFileURL,
          let bookmark = input["bookmark"] as? String,
          Data(base64Encoded: bookmark) != nil
        else {
          throw RuntimeError.invalidWorkspaceGrant
        }
        let records = try Self.loadWorkspaceGrantRecords()
        let existing = records.first { _, record in
          record["uri"] as? String == uri
        }
        let grantId = existing?.key ?? UUID().uuidString.lowercased()
        var nextRecords = records
        nextRecords[grantId] = [
          "uri": uri,
          "bookmark": bookmark,
          "displayName": selectedURL.lastPathComponent.isEmpty
            ? "Selected folder"
            : selectedURL.lastPathComponent,
        ]
        try Self.saveWorkspaceGrantRecords(nextRecords)
        let active = try Self.restoreWorkspaceGrant(
          grantId: grantId,
          record: nextRecords[grantId] ?? [:]
        )
        resolve([
          "grantId": grantId,
          "displayName": active["display_name"] as? String
            ?? "Selected folder",
        ])
      } catch {
        reject(
          "workspace_grant_failed",
          error.localizedDescription,
          error
        )
      }
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

  private static func defaultProviderSettings() -> [String: Any] {
    var providers: [String: Any] = [:]
    for profileId in providerOrder {
      guard let definition = providerDefinitions[profileId] else {
        continue
      }
      var profile: [String: Any] = [
        "enabled": definition["enabledByDefault"] as? Bool ?? false,
        "baseUrl": definition["baseUrl"] ?? "",
        "model": definition["model"] ?? "",
      ]
      if let authMode = definition["authMode"] {
        profile["authMode"] = authMode
      }
      if definition["usesBundledReviewerCA"] as? Bool == true {
        profile["tlsCaBundle"] = reviewerCABundlePath()
      }
      providers[profileId] = profile
    }
    return [
      "version": 3,
      "defaultAgent": configuredDefaultAgent,
      "reviewerVisible": false,
      "reviewerActivationConfigured": false,
      "providers": providers,
    ]
  }

  private static func reviewerCABundlePath() -> String {
    guard
      let resourcesURL = Bundle.main.url(
        forResource: "CrystalLatticePythonRuntimeResources",
        withExtension: "bundle"
      ),
      let resources = Bundle(url: resourcesURL),
      let caURL = resources.url(
        forResource: "reviewer-proxy-ca",
        withExtension: "pem"
      )
    else {
      return ""
    }
    return caURL.path
  }

  private static func normalizedProviderSettings(
    _ rawSettings: [String: Any]
  ) -> [String: Any] {
    let defaults = defaultProviderSettings()
    let rawProviders = rawSettings["providers"] as? [String: Any] ?? [:]
    let defaultProviders = defaults["providers"] as? [String: Any] ?? [:]
    var providers: [String: Any] = [:]
    for profileId in providerOrder {
      let rawProfile = rawProviders[profileId] as? [String: Any] ?? [:]
      let defaultProfile =
        defaultProviders[profileId] as? [String: Any] ?? [:]
      let baseUrl =
        (rawProfile["baseUrl"] as? String)?
          .trimmingCharacters(in: .whitespacesAndNewlines)
      let model =
        (rawProfile["model"] as? String)?
          .trimmingCharacters(in: .whitespacesAndNewlines)
      let requestedAuthMode =
        (rawProfile["authMode"] as? String)?
          .trimmingCharacters(in: .whitespacesAndNewlines)
          .lowercased()
      let authMode = ["api", "chatgpt"].contains(
        requestedAuthMode ?? ""
      )
        ? requestedAuthMode!
        : defaultProfile["authMode"] as? String ?? "api"
      let tlsCaBundle =
        (rawProfile["tlsCaBundle"] as? String)?
          .trimmingCharacters(in: .whitespacesAndNewlines)
      var profile: [String: Any] = [
        "enabled": rawProfile["enabled"] as? Bool
            ?? defaultProfile["enabled"] as? Bool
            ?? false,
        "baseUrl": profileId == "reviewer"
          ? defaultProfile["baseUrl"] as? String ?? ""
          : !(baseUrl ?? "").isEmpty
            ? baseUrl!
            : defaultProfile["baseUrl"] as? String ?? "",
        "model": profileId == "reviewer"
          ? defaultProfile["model"] as? String ?? ""
          : !(model ?? "").isEmpty
            ? model!
            : defaultProfile["model"] as? String ?? "",
      ]
      if profileId == "openai" {
        profile["authMode"] = authMode
      }
      if profileId == "reviewer" {
        profile["tlsCaBundle"] = reviewerCABundlePath()
      }
      providers[profileId] = profile
    }
    let requestedDefault =
      rawSettings["defaultAgent"] as? String ?? configuredDefaultAgent
    let reviewerVisible =
      rawSettings["reviewerVisible"] as? Bool
      ?? !apiKey(profileId: "reviewer").isEmpty
    let validAgents = Set(
      providerDefinitions.values.compactMap {
        $0["agentId"] as? String
      }
    )
    return [
      "version": 3,
      "defaultAgent": validAgents.contains(requestedDefault)
        ? requestedDefault
        : configuredDefaultAgent,
      "reviewerVisible": reviewerVisible,
      "reviewerActivationConfigured":
        rawSettings["reviewerActivationConfigured"] as? Bool ?? reviewerVisible,
      "profileOrder": providerOrder,
      "providers": providers,
    ]
  }

  private static func storedProviderSettings() -> [String: Any] {
    let defaults = UserDefaults.standard
    if let stored = defaults.dictionary(
      forKey: providerSettingsDefaultsKey
    ) {
      return normalizedProviderSettings(stored)
    }
    if let stored = defaults.dictionary(
      forKey: legacyProviderSettingsDefaultsKey
    ) {
      let migrated = migrateLegacyProviderSettings(stored)
      saveProviderSettings(migrated)
      return migrated
    }

    let legacyUrl = defaults.string(forKey: "clcEmbeddedProxyURL") ?? ""
    let legacyModel = defaults.string(forKey: "clcEmbeddedModel") ?? ""
    let legacyKey = defaults.string(forKey: "clcEmbeddedProxyAPIKey") ?? ""
    guard !legacyUrl.isEmpty || !legacyModel.isEmpty || !legacyKey.isEmpty else {
      let settings = defaultProviderSettings()
      saveProviderSettings(settings)
      return settings
    }

    var settings = defaultProviderSettings()
    var providers = settings["providers"] as? [String: Any] ?? [:]
    var compatible = providers["compatible"] as? [String: Any] ?? [:]
    if !legacyUrl.isEmpty {
      compatible["baseUrl"] = legacyUrl
    }
    if !legacyModel.isEmpty {
      compatible["model"] = legacyModel
    }
    compatible["enabled"] = true
    providers["compatible"] = compatible
    settings["providers"] = providers
    settings["defaultAgent"] =
      providerDefinitions["compatible"]?["agentId"] as? String
      ?? configuredDefaultAgent
    saveProviderSettings(settings)

    if !legacyKey.isEmpty {
      try? setAPIKey(legacyKey, profileId: "compatible")
    }
    defaults.removeObject(forKey: "clcEmbeddedProxyAPIKey")
    return settings
  }

  private static func migrateLegacyProviderSettings(
    _ legacy: [String: Any]
  ) -> [String: Any] {
    var migrated = defaultProviderSettings()
    let legacyProviders = legacy["providers"] as? [String: Any] ?? [:]
    var providers = migrated["providers"] as? [String: Any] ?? [:]
    for profileId in ["openai", "openrouter", "anthropic"] {
      if let profile = legacyProviders[profileId] as? [String: Any] {
        providers[profileId] = profile
      }
    }

    let legacyReviewer =
      legacyProviders["reviewer"] as? [String: Any] ?? [:]
    let legacyBaseUrl =
      legacyReviewer["baseUrl"] as? String ?? ""
    let reviewerBaseUrl =
      providerDefinitions["reviewer"]?["baseUrl"] as? String ?? ""
    let reviewerHost = URL(string: reviewerBaseUrl)?.host ?? ""
    let wasExternalReviewer =
      !reviewerHost.isEmpty && legacyBaseUrl.contains(reviewerHost)
    let targetProfileId = wasExternalReviewer ? "reviewer" : "compatible"
    var target = providers[targetProfileId] as? [String: Any] ?? [:]
    for key in ["enabled", "baseUrl", "model"] {
      if let value = legacyReviewer[key] {
        target[key] = value
      }
    }
    if wasExternalReviewer, let value = legacyReviewer["tlsCaBundle"] {
      target["tlsCaBundle"] = value
    }
    providers[targetProfileId] = target
    migrated["providers"] = providers

    let legacyDefault = legacy["defaultAgent"] as? String
    let reviewerAgent =
      providerDefinitions["reviewer"]?["agentId"] as? String
      ?? configuredDefaultAgent
    let compatibleAgent =
      providerDefinitions["compatible"]?["agentId"] as? String
      ?? configuredDefaultAgent
    migrated["defaultAgent"] =
      legacyDefault == "reviewer-claude"
        ? (wasExternalReviewer ? reviewerAgent : compatibleAgent)
        : legacyDefault ?? configuredDefaultAgent

    if !wasExternalReviewer {
      let legacyKey = apiKey(profileId: "reviewer")
      if !legacyKey.isEmpty {
        try? setAPIKey(legacyKey, profileId: "compatible")
        try? setAPIKey(nil, profileId: "reviewer")
      }
    } else {
      migrated["reviewerVisible"] = true
    }
    return normalizedProviderSettings(migrated)
  }

  private static func saveProviderSettings(_ settings: [String: Any]) {
    UserDefaults.standard.set(
      normalizedProviderSettings(settings),
      forKey: providerSettingsDefaultsKey
    )
  }

  private static func settingsByApplying(
    _ configuration: NSDictionary
  ) throws -> [String: Any] {
    var settings = storedProviderSettings()
    var providers = settings["providers"] as? [String: Any] ?? [:]
    if let reviewerVisible = configuration["reviewerVisible"] as? Bool {
      settings["reviewerVisible"] = reviewerVisible
      if reviewerVisible,
        settings["reviewerActivationConfigured"] as? Bool != true
      {
        var reviewer = providers["reviewer"] as? [String: Any] ?? [:]
        reviewer["enabled"] = true
        providers["reviewer"] = reviewer
        settings["reviewerActivationConfigured"] = true
      }
    }
    if let rawProviders = configuration["providers"] as? NSDictionary {
      for profileId in providerOrder {
        guard
          let rawProfile = rawProviders[profileId] as? NSDictionary
        else {
          continue
        }
        var profile = providers[profileId] as? [String: Any] ?? [:]
        if let enabled = rawProfile["enabled"] as? Bool
        {
          if profileId == "reviewer",
            profile["enabled"] as? Bool != enabled
          {
            settings["reviewerActivationConfigured"] = true
          }
          profile["enabled"] = enabled
        }
        if profileId != "reviewer",
          let baseUrl = rawProfile["baseUrl"] as? String
        {
          let normalized = baseUrl.trimmingCharacters(
            in: .whitespacesAndNewlines
          )
          guard !normalized.isEmpty else {
            throw RuntimeError.invalidConfiguration
          }
          profile["baseUrl"] = normalized
        }
        if profileId != "reviewer",
          let model = rawProfile["model"] as? String
        {
          let normalized = model.trimmingCharacters(
            in: .whitespacesAndNewlines
          )
          guard !normalized.isEmpty else {
            throw RuntimeError.invalidConfiguration
          }
          profile["model"] = normalized
        }
        if profileId == "openai",
          let authMode = rawProfile["authMode"] as? String
        {
          let normalized = authMode.trimmingCharacters(
            in: .whitespacesAndNewlines
          ).lowercased()
          guard ["api", "chatgpt"].contains(normalized) else {
            throw RuntimeError.invalidConfiguration
          }
          profile["authMode"] = normalized
        }
        providers[profileId] = profile
      }
    } else if configuration["proxyUrl"] != nil
      || configuration["model"] != nil
    {
      guard
        let proxyUrl = configuration["proxyUrl"] as? String,
        !proxyUrl.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
        let model = configuration["model"] as? String,
        !model.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
      else {
        throw RuntimeError.invalidConfiguration
      }
      var compatible = providers["compatible"] as? [String: Any] ?? [:]
      compatible["enabled"] = true
      compatible["baseUrl"] = proxyUrl.trimmingCharacters(
        in: .whitespacesAndNewlines
      )
      compatible["model"] = model.trimmingCharacters(
        in: .whitespacesAndNewlines
      )
      providers["compatible"] = compatible
    }
    settings["providers"] = providers
    if let defaultAgent = configuration["defaultAgent"] as? String {
      settings["defaultAgent"] = defaultAgent
    }
    return normalizedProviderSettings(settings)
  }

  private static func keyOverrides(
    from configuration: NSDictionary
  ) -> [String: Any] {
    var overrides: [String: Any] = [:]
    if let rawProviders = configuration["providers"] as? NSDictionary {
      for profileId in providerOrder {
        guard
          let rawProfile = rawProviders[profileId] as? NSDictionary
        else {
          continue
        }
        if rawProfile["clearApiKey"] as? Bool == true {
          overrides[profileId] = NSNull()
        } else if let apiKey = rawProfile["apiKey"] as? String,
          !apiKey.isEmpty
        {
          overrides[profileId] = apiKey
        }
      }
    } else if let apiKey = configuration["apiKey"] as? String,
      !apiKey.isEmpty
    {
      overrides["compatible"] = apiKey
    }
    return overrides
  }

  private static func applyAPIKeyUpdates(
    _ configuration: NSDictionary
  ) throws {
    for (profileId, value) in keyOverrides(from: configuration) {
      if value is NSNull {
        try setAPIKey(nil, profileId: profileId)
      } else if let apiKey = value as? String {
        try setAPIKey(apiKey, profileId: profileId)
      }
    }
  }

  private static func setAPIKey(
    _ apiKey: String?,
    profileId: String
  ) throws {
    let baseQuery: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrService as String: providerKeychainService,
      kSecAttrAccount as String: profileId,
    ]
    SecItemDelete(baseQuery as CFDictionary)
    guard let apiKey, !apiKey.isEmpty else {
      return
    }
    var addQuery = baseQuery
    addQuery[kSecValueData as String] = Data(apiKey.utf8)
    addQuery[kSecAttrAccessible as String] =
      kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
    let status = SecItemAdd(addQuery as CFDictionary, nil)
    guard status == errSecSuccess else {
      throw RuntimeError.keychainFailure(status)
    }
  }

  private static func apiKey(profileId: String) -> String {
    let query: [String: Any] = [
      kSecClass as String: kSecClassGenericPassword,
      kSecAttrService as String: providerKeychainService,
      kSecAttrAccount as String: profileId,
      kSecMatchLimit as String: kSecMatchLimitOne,
      kSecReturnData as String: true,
    ]
    var result: CFTypeRef?
    let status = SecItemCopyMatching(
      query as CFDictionary,
      &result
    )
    guard status == errSecSuccess,
      let data = result as? Data,
      let value = String(data: data, encoding: .utf8)
    else {
      return ""
    }
    return value
  }

  private static func profileId(forAgent agentId: String?) -> String {
    for profileId in providerOrder {
      if providerDefinitions[profileId]?["agentId"] as? String == agentId {
        return profileId
      }
    }
    return providerDefinitions["reviewer"] == nil
      ? providerOrder.first ?? ""
      : "reviewer"
  }

  private static func runtimeConfiguration(
    settings: [String: Any],
    overrides: [String: Any] = [:]
  ) -> [String: Any] {
    let normalized = normalizedProviderSettings(settings)
    let storedProfiles = normalized["providers"] as? [String: Any] ?? [:]
    var providers: [String: Any] = [:]
    for profileId in providerOrder {
      let stored = storedProfiles[profileId] as? [String: Any] ?? [:]
      let key: String
      if overrides[profileId] is NSNull {
        key = ""
      } else {
        key = overrides[profileId] as? String ?? apiKey(profileId: profileId)
      }
      var profile: [String: Any] = [
        "enabled": stored["enabled"] as? Bool ?? false,
        "base_url": stored["baseUrl"] as? String ?? "",
        "model": stored["model"] as? String ?? "",
        "api_key": key,
      ]
      if profileId == "openai" {
        profile["auth_mode"] = stored["authMode"] as? String ?? "api"
      }
      if profileId == "reviewer" {
        profile["tls_ca_bundle"] = stored["tlsCaBundle"] as? String ?? ""
      }
      providers[profileId] = profile
    }
    return [
      "version": 3,
      "default_agent": normalized["defaultAgent"] as? String
        ?? configuredDefaultAgent,
      "reviewer_visible": normalized["reviewerVisible"] as? Bool ?? false,
      "providers": providers,
      "workspace_grants": (try? activeWorkspaceGrants()) ?? [:],
    ]
  }

  private static func runtimeConfiguration() -> [String: Any]? {
    runtimeConfiguration(settings: storedProviderSettings())
  }

  private static func candidateRuntimeConfiguration(
    _ configuration: NSDictionary
  ) throws -> [String: Any] {
    runtimeConfiguration(
      settings: try settingsByApplying(configuration),
      overrides: keyOverrides(from: configuration)
    )
  }

  private static func publicConfiguration() -> [String: Any] {
    let settings = storedProviderSettings()
    let storedProfiles = settings["providers"] as? [String: Any] ?? [:]
    var providers: [String: Any] = [:]
    for profileId in providerOrder {
      let stored = storedProfiles[profileId] as? [String: Any] ?? [:]
      let definition = providerDefinitions[profileId] ?? [:]
      var profile: [String: Any] = [
        "id": profileId,
        "label": definition["label"] as? String ?? profileId,
        "agentId": definition["agentId"] as? String ?? "",
        "toolFamily": definition["toolFamily"] as? String ?? "",
        "enabled": stored["enabled"] as? Bool ?? false,
        "baseUrl": stored["baseUrl"] as? String ?? "",
        "model": stored["model"] as? String ?? "",
        "hasApiKey": !apiKey(profileId: profileId).isEmpty,
      ]
      if profileId == "openai" {
        profile["authMode"] = stored["authMode"] as? String ?? "api"
      }
      if profileId == "reviewer" {
        profile["tlsCaBundle"] = stored["tlsCaBundle"] as? String ?? ""
      }
      providers[profileId] = profile
    }
    let compatible = providers["compatible"] as? [String: Any] ?? [:]
    let requestedProfileId = profileId(
      forAgent: settings["defaultAgent"] as? String
    )
    let reviewerVisible = settings["reviewerVisible"] as? Bool ?? false
    let selectedProfileId =
      requestedProfileId == "reviewer" && !reviewerVisible
      ? ""
      : requestedProfileId
    let selectedProfile =
      providers[selectedProfileId] as? [String: Any] ?? [:]
    var result: [String: Any] = [
      "version": 3,
      "defaultAgent": settings["defaultAgent"] as? String
        ?? configuredDefaultAgent,
      "reviewerVisible": reviewerVisible,
      "profileOrder": providerOrder,
      "providers": providers,
      "hasApiKey": compatible["hasApiKey"] as? Bool ?? false,
      "inspectionOnly": UserDefaults.standard.bool(
        forKey: "clcEmbeddedInspectionOnly"
      ),
      "model": selectedProfile["model"] as? String ?? "",
      "proxyUrl": selectedProfile["baseUrl"] as? String ?? "",
    ]
    if !selectedProfileId.isEmpty {
      result["selectedProfileId"] = selectedProfileId
    }
    return result
  }

  private static func nowMs() -> Double {
    Date().timeIntervalSince1970 * 1000
  }

  private static func workspaceGrantsURL() throws -> URL {
    try runtimeRoot()
      .appendingPathComponent("config", isDirectory: true)
      .appendingPathComponent("workspace-grants.json", isDirectory: false)
  }

  private static func loadWorkspaceGrantRecords() throws
    -> [String: [String: Any]]
  {
    let url = try workspaceGrantsURL()
    guard FileManager.default.fileExists(atPath: url.path) else {
      return [:]
    }
    let data = try Data(contentsOf: url)
    return try JSONSerialization.jsonObject(with: data)
      as? [String: [String: Any]] ?? [:]
  }

  private static func saveWorkspaceGrantRecords(
    _ records: [String: [String: Any]]
  ) throws {
    let url = try workspaceGrantsURL()
    try FileManager.default.createDirectory(
      at: url.deletingLastPathComponent(),
      withIntermediateDirectories: true
    )
    let data = try JSONSerialization.data(
      withJSONObject: records,
      options: [.prettyPrinted, .sortedKeys]
    )
    try data.write(to: url, options: .atomic)
    try? FileManager.default.setAttributes(
      [.protectionKey: FileProtectionType.completeUntilFirstUserAuthentication],
      ofItemAtPath: url.path
    )
  }

  private static func restoreWorkspaceGrant(
    grantId: String,
    record: [String: Any]
  ) throws -> [String: Any] {
    guard
      let encodedBookmark = record["bookmark"] as? String,
      let bookmarkData = Data(base64Encoded: encodedBookmark)
    else {
      throw RuntimeError.invalidWorkspaceGrant
    }
    var stale = false
    let url = try URL(
      resolvingBookmarkData: bookmarkData,
      options: [.withoutUI],
      relativeTo: nil,
      bookmarkDataIsStale: &stale
    )
    if Self.activeWorkspaceGrantURLs[grantId] == nil {
      guard url.startAccessingSecurityScopedResource() else {
        throw RuntimeError.workspaceGrantUnavailable
      }
      Self.activeWorkspaceGrantURLs[grantId] = url
    }
    let storedDisplayName =
      (record["displayName"] as? String)?.trimmingCharacters(
        in: .whitespacesAndNewlines
      )
    return [
      "path": url.path,
      "display_name": storedDisplayName?.isEmpty == false
        ? storedDisplayName!
        : url.lastPathComponent,
      "available": true,
      "stale": stale,
    ]
  }

  private static func activeWorkspaceGrants() throws -> [String: Any] {
    let records = try loadWorkspaceGrantRecords()
    var result: [String: Any] = [:]
    for (grantId, record) in records {
      do {
        result[grantId] = try restoreWorkspaceGrant(
          grantId: grantId,
          record: record
        )
      } catch {
        result[grantId] = [
          "display_name": record["displayName"] as? String
            ?? "Selected folder",
          "available": false,
          "stale": false,
        ]
      }
    }
    return result
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
    case keychainFailure(OSStatus)
    case invalidWorkspaceGrant
    case workspaceGrantUnavailable
    case validationFailed(String)

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
        return "Every embedded provider endpoint and model must be non-empty."
      case .invalidResponse:
        return "The embedded runtime returned an invalid response."
      case .keychainFailure(let status):
        return "The provider API key could not be saved (Keychain status \(status))."
      case .invalidWorkspaceGrant:
        return "The selected workspace grant is invalid."
      case .workspaceGrantUnavailable:
        return "The selected workspace permission is unavailable."
      case .validationFailed(let detail):
        return detail
      }
    }
  }
}