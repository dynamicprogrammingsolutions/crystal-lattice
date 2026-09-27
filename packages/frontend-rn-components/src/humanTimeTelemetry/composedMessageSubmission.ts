/**
 * Mark a composed-message boundary and immediately continue the user action.
 *
 * Human-time telemetry is best-effort: boundary collection must never delay
 * or fail Send/Append. Provider callbacks queue persistence and upload work
 * internally, so this helper intentionally does not await them.
 */
export function runComposedMessageSubmission<Result>(
  recordBoundary: () => void,
  submit: () => Result,
): Result {
  try {
    recordBoundary();
  } catch {
    // Telemetry must never break the user action.
  }
  return submit();
}
