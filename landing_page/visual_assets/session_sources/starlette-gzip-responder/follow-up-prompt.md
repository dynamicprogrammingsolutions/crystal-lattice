Based on what you already found, compare two fixes: adding the same
`128 * 1024` default directly to `GZipResponder`, or introducing a shared
module-level constant for the middleware and responder. Consider backwards
compatibility, default-drift risk, patch and review scope, and future
maintenance. No further repository inspection is needed. Which approach would
you choose for this fix, and why? Keep the final recommendation concise.