import Foundation
import React

@objc(CrystalLatticePythonRuntime)
final class CrystalLatticePythonRuntime: NSObject {
  private static let queue = DispatchQueue(
    label: "com.dynamicprogrammingsolutions.crystallattice.python-runtime"
  )
  private static var initialized = false
  private static var runtimeInformation: [String: Any]?

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
        guard JSONSerialization.isValidJSONObject(request) else {
          throw RuntimeError.invalidCommand
        }
        let requestData = try JSONSerialization.data(withJSONObject: request)
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
        resolve(response)
      } catch {
        reject("python_command_failed", error.localizedDescription, error)
      }
    }
  }

  private static func startIfNeeded() throws -> [String: Any] {
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

  private enum RuntimeError: LocalizedError {
    case resourcesMissing
    case applicationSupportMissing
    case initializationFailed
    case executionFailed
    case invalidCommand
    case invalidResponse

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
      case .invalidResponse:
        return "The embedded runtime returned an invalid response."
      }
    }
  }
}