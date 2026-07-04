# Provide Immediately Testable Local Runtime For App Review

Provide an immediately testable Crystal Lattice experience that satisfies App Review Guideline 2.1(a) and supports the long-term goal of making the mobile app useful for ordinary non-developer users without requiring desktop CLI setup.

## Requirements checklist

- [ ] Define the minimum complete functionality that matters for App Review.
- [ ] Provide an immediately testable path from first launch without requiring the reviewer to run the desktop CLI, join a private LAN, configure a local server, or provide their own API keys.
- [ ] Exercise the meaningful app surface during review:
  - [ ] Sessions.
  - [ ] Message send/receive.
  - [ ] Agent selection or built-in agent behavior.
  - [ ] App-level settings.
  - [ ] Relevant plugin/settings surfaces.
  - [ ] Representative tool call/result rendering.
  - [ ] Persistence across navigation/relaunch where applicable.
- [ ] Include at least one no-API-key local agent path that uses an actual local model or platform model capability.
- [ ] Add app-level settings where users can configure provider API keys for richer agents.
- [ ] Bundle or provide a built-in iOS-safe configuration with a fixed, reviewed set of agents/plugins/tools.
- [ ] Ensure all included plugins/tools are safe for iOS review and ordinary-user use.
- [ ] Ensure file access is limited to app sandbox, bundled resources, or explicit user-selected files.
- [ ] Ensure no downloaded executable/plugin code is required to unlock reviewed functionality.
- [ ] Ensure the local runtime/server continues to operate appropriately when the app goes to sleep or backgrounds, within iOS background execution constraints.
- [ ] Add App Review notes explaining exactly how to test the immediately available functionality.
- [ ] Add smoke tests or a manual smoke-test checklist for the reviewer path.
- [ ] Document any App Store policy constraints, iOS runtime constraints, model-size constraints, or background-execution limitations discovered during research.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/050-privacy-landing-page-compliance.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/060-app-store-connect-registration-package.md

## App Review Rationale

Apple App Review Guideline 2.1(a) requires submitted apps to be complete, functional, and reviewable. The current mobile app depends on connecting to an external Crystal Lattice backend. That can block review unless Apple receives an immediately testable path that exposes the app's meaningful functionality.

This task makes immediate testability a hard requirement for external TestFlight and App Store review.

The app should not depend on reviewers installing developer tools, running the desktop CLI, joining a private LAN, configuring provider credentials, or setting up their own backend.

Reference:

- https://developer.apple.com/app-store/review/guidelines/

## Long-Term Product Goal

This task should also support the long-term product goal that ordinary users, including non-developers, can complete simple useful tasks locally from the iOS app.

The target experience should feel more capable than a thin ChatGPT-style chat wrapper by preserving Crystal Lattice's agentic qualities:

- Sessions and state.
- Configured agents.
- Plugin-driven controls.
- Tool calls and visible tool results.
- App-level provider/settings management.
- Local files or user-selected files where iOS permits.

## Hard Requirements

The final solution must satisfy these requirements, regardless of implementation approach:

- It is immediately testable by Apple App Review.
- It exercises the meaningful app functionality, not just a static demo screen.
- It includes at least one no-API-key local agent path based on an actual local/platform model capability.
- It includes an app-level settings path for provider API keys.
- It uses only a fixed, reviewed set of bundled agents/plugins/tools for the built-in local/review mode.
- It does not require downloading executable code, unreviewed plugins, or new runtime behavior after App Review.
- It respects iOS sandboxing and user consent for files, network, photos, camera, and documents.
- It has a clear story for background/sleep behavior of the local runtime/server within iOS constraints.
- It has reviewer instructions that are specific enough for Apple to verify the app quickly.

## Ideas To Research

These are implementation ideas, not exclusive solutions. The final implementation may use one of these, combine them, or use a different approach if it satisfies the hard requirements and supports the long-term product goals.

### Preferred Idea: Bundled Local Runtime And Server

Bundle a local Crystal Lattice runtime inside the iOS app.

Potential shape:

- A bundled Python interpreter, if feasible and App Review-safe.
- A local server or in-process service compatible with the existing mobile frontend/backend interfaces.
- A built-in Crystal Lattice config.
- A fixed set of bundled agents.
- A fixed set of bundled plugins/tools.
- Local session persistence in the app sandbox.
- App-level settings for API keys.
- A no-API-key local agent using Apple Foundation Models where available, or another reviewed local model option.
- Optional provider-backed agents when the user enters API keys.

Research questions:

- Can the required Python runtime be bundled within acceptable app size, startup time, and App Review constraints?
- Can the runtime run without downloading executable code or plugins?
- Can the local server bind only locally and communicate safely with the React Native app?
- What iOS background modes, background tasks, or lifecycle constraints apply when the app sleeps/backgrounds?
- Can the local server resume cleanly after suspension?
- Should the runtime be an actual HTTP server or an in-process bridge that preserves the same backend contract?
- Which existing Python plugins are safe and small enough to bundle?
- Which plugins/tools must be rewritten, removed, or replaced for iOS sandboxing?
- How should local sessions/config be stored and migrated?
- How should logs/debug output be exposed without leaking sensitive data?

### Local No-API-Key Model Ideas

Explore actual local/model-backed options:

- Apple Foundation Models framework for supported devices/OS versions.
- Core ML model packaged with the app, if Foundation Models is unavailable or insufficient.
- A later version may evaluate other on-device model runtimes if they are App Review-safe, license-compatible, and practical for app size/performance.

Research questions:

- What iOS versions/devices support Apple Foundation Models?
- Can Foundation Models be used from React Native through a native module?
- What fallback is available on devices that do not support Apple Foundation Models?
- What model size/performance envelope is acceptable for a bundled Core ML model?
- What licensing applies to any bundled model?
- How should the app clearly communicate local-model availability and limitations?

### iOS-Safe Tool Ideas

Explore a fixed set of safe tools suitable for bundled local/review mode:

- Read bundled sample files.
- Read user-selected files via document picker.
- Search bundled documentation or sample knowledge base.
- Fetch a user-provided URL with clear user action.
- Save or export generated text through the share sheet.
- Save generated files inside the app sandbox.
- Summarize selected text or user-selected documents using the local/provider-backed agent.
- Provide web search only through a reviewed, bounded, privacy-conscious implementation.

Research questions:

- Which tools are safe enough for App Review and ordinary users?
- Which existing Crystal Lattice tools can be reused unchanged?
- Which tools require iOS-specific implementations?
- How should permissions be requested and explained?
- Which tools should be disabled in built-in local/review mode?

### Fallback Idea: Native/In-App Backend Adapter

If the bundled local runtime/server is not feasible, evaluate a native or React Native in-app backend adapter.

This should be treated as a fallback because it may require reimplementing backend behavior in Swift/TypeScript/native code and may duplicate existing Python backend logic.

Potential shape:

- Implement the needed backend contract directly in the app.
- Store sessions locally.
- Use native model APIs or Core ML for the no-API-key agent.
- Expose the same UI surfaces as the normal backend where practical.
- Keep behavior aligned with the real Crystal Lattice backend.

Research questions:

- How much of the backend contract must be implemented for meaningful review?
- How much duplication would this create?
- Can shared TypeScript packages reduce duplication?
- Would this path be safer/smaller than bundled Python?

### Limited Review/Demo Backend Fallback

If neither bundled local runtime nor native local backend is feasible in time, evaluate a hosted safe demo backend strictly as a fallback for App Review or limited demonstration.

This should not replace the long-term local-user goal.

Potential shape:

- A world-accessible demo connection.
- A sandboxed, rate-limited backend.
- Disposable sessions.
- No dangerous tools.
- No user secrets.
- No broad filesystem access.
- Review notes with exact connection instructions.

Research questions:

- What minimum hosted demo is enough for App Review?
- How can it be locked down safely?
- How are sessions cleaned up?
- How can it avoid exposing provider API keys or paid usage risk?
- How does this remain clearly limited so it does not become the long-term product architecture by accident?

## Background Execution Considerations

The task must explicitly research and document what "server should run in the background even when the app goes to sleep" can mean on iOS.

Questions to answer:

- Can the runtime continue active work while the app is backgrounded?
- Can it finish short tasks using background task APIs?
- Can it resume reliably after iOS suspends the app?
- Are any iOS background modes applicable and justifiable?
- What user experience should occur if iOS suspends the local runtime?
- How should the app persist session/request state before suspension?
- What behavior is acceptable for App Review and ordinary users?

The final implementation should be honest about iOS constraints. If indefinite background server execution is not permitted or reliable, the design must provide graceful suspension/resume semantics while still satisfying App Review testability.

## Acceptance Criteria

- A fresh install exposes an obvious testable path without desktop setup.
- Apple Review can exercise meaningful app functionality immediately.
- At least one no-API-key model-backed local agent path works on supported devices, with a documented fallback plan for unsupported devices.
- App-level API-key settings exist for optional richer provider-backed agents.
- Bundled/review-mode agents/plugins/tools are fixed, reviewed, and iOS-safe.
- The app does not download executable code or unreviewed plugins to unlock reviewed functionality.
- File/network/tool behavior respects iOS sandboxing and permissions.
- Background/sleep behavior is implemented or documented with clear iOS constraints and graceful recovery.
- App Review notes include exact steps, expected outputs, and any device/OS limitations.
- The chosen solution is documented with tradeoffs and does not close off future alternatives that better satisfy the hard requirements and long-term goals.
