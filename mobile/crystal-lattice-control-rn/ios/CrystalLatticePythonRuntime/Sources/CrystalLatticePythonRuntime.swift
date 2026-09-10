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
      let stdlibArchive = resources.url(
        forResource: "python312",
        withExtension: "zip"
      )
    else {
      throw RuntimeError.resourcesMissing
    }

    guard
      let info = try CLPythonHostSupport.start(
        withStdlibArchive: stdlibArchive.path
      ) as? [String: Any]
    else {
      throw RuntimeError.initializationFailed
    }
    initialized = true
    runtimeInformation = info
    return info
  }

  private enum RuntimeError: LocalizedError {
    case resourcesMissing
    case initializationFailed
    case executionFailed

    var errorDescription: String? {
      switch self {
      case .resourcesMissing:
        return "The bundled Python resources could not be found."
      case .initializationFailed:
        return "The bundled Python interpreter did not initialize."
      case .executionFailed:
        return "The bundled Python smoke program failed."
      }
    }
  }
}