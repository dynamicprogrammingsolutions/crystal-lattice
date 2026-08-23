# Provide A Testable Path For Google Play Review

Ensure Google reviewers can exercise meaningful Crystal Lattice Control
functionality without a private LAN, developer tooling, or reviewer-supplied API
keys, while preserving the product's self-hosted operating model.

## Requirements checklist

- [ ] A fresh Play-installed build exposes an obvious, functional review path
      that does not require the reviewer to operate a separate Crystal Lattice
      server.
- [ ] Reviewers can exercise sessions, message send/receive, representative
      agent/tool output, navigation, settings, and persistence.
- [ ] The path does not introduce an unapproved public production bridge or
      cloud-agent service.
- [ ] No reviewer must supply personal API keys or access a private company LAN.
- [ ] Included runtime/agents/tools are fixed, safe, and do not download
      executable code.
- [ ] Reviewer instructions state exact steps, expected results, limitations,
      and any network/device requirements.
- [ ] The solution is shared with iOS where practical rather than creating two
      inconsistent demo products.
- [ ] Internal testing may proceed with known testers' self-hosted environments,
      but closed/production readiness remains blocked until this task is
      complete.

Parent Task: tasks/20260820-android-google-play-github-fastlane/000-main.md
Depends On: tasks/20260820-android-google-play-github-fastlane/050-google-play-privacy-and-app-content.md
Depends On: tasks/20260820-android-google-play-github-fastlane/060-play-console-registration-package.md

## Required reading

Read the parent task's `Shared required reading`, then:

- `tasks/20260614-ios-testflight-github-fastlane/085-app-review-local-runtime-and-testable-mode.md`
- `mobile/crystal-lattice-control-rn/App.tsx`
- `mobile/crystal-lattice-control-rn/src/ConnectedRoot.tsx`
- `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
- Play app access instructions:
  https://support.google.com/googleplay/android-developer/answer/9859455#app_access
- Android background work:
  https://developer.android.com/develop/background-work/background-tasks
- Dynamic code policy context:
  https://support.google.com/googleplay/android-developer/answer/9888379

## Product constraint

Dynamic Programming Solutions Kft. currently operates:

- No production bridge.
- No public cloud-agent service.
- No developer-operated account service.

Do not silently create one to satisfy review. A hosted review-only backend is a
material architecture/security/cost decision and requires explicit approval.

## Candidate approaches

Preferred:

- Reuse a cross-platform bundled/local runtime or in-app backend adapter created
  for the iOS review task, with Android-specific lifecycle, storage, and model
  integrations.

Acceptable with approval:

- A tightly sandboxed, rate-limited, disposable review-only service with no
  dangerous tools or user secrets.

Insufficient:

- Static screenshots or fake UI with no functional session/message behavior.
- Instructions requiring reviewers to clone the repository or start a desktop
  server.
- A private LAN address.
- Reviewer-provided AI-provider credentials.

## Minimum review scenario

1. Launch the app.
2. Select a clearly labeled local/review experience.
3. See at least one session or create one.
4. Send a message and receive a model-backed or deterministic functional
   response.
5. Observe a representative tool/action result.
6. Navigate away and return without losing required state.
7. Inspect app-level settings and relevant connection/runtime information.
8. Follow privacy/support links.

## Execution plan

Status: Draft

Coordinate with the iOS review-mode task before selecting architecture. Define
one product-level review experience and implement platform adapters only where
native lifecycle/model/storage behavior differs. Validate policy, dependency
size, offline/network behavior, sandboxing, and background/resume semantics.

### Implementation decisions and open questions

- Decision: no Android-only static demo.
- Decision: no unapproved public production service.
- Recommendation: prioritize a shared local/in-app runtime path.
- Material open question: whether the shared local runtime is technically and
  policy-feasible on both platforms.
- Material open question: if hosted fallback is required, approve ownership,
  budget, abuse controls, retention, and shutdown plan first.

### Documentation

- Add exact Play App access/reviewer instructions to the registration package.
- Document platform lifecycle limits and recovery behavior in package
  development docs.
- Do not advertise a hosted/public service unless it actually exists as an
  approved product.

### Task checklist

- [ ] Compare Android needs with the iOS review-mode plan.
- [ ] Select and approve architecture.
- [ ] Define the minimum reviewer scenario.
- [ ] Implement Android-specific runtime/lifecycle integration.
- [ ] Add safe fixed agents/tools and test data.
- [ ] Add persistence and recovery behavior.
- [ ] Write exact reviewer instructions.
- [ ] Run fresh-install review smoke test on a Play-delivered build.

### Requirement verification

- Fresh install: human reviewer can complete the scenario without external
  setup.
- Functional behavior: real session/message/action state changes, not static
  placeholders.
- Security: no executable-code download, broad filesystem access, or exposed
  provider secrets.
- Lifecycle: background/suspend/relaunch behavior matches documented limits.
- Cross-platform consistency: shared review behavior compared with iOS.

### Additional implementation verification

- Test offline and unavailable-runtime errors.
- Test abuse/rate limits if any hosted fallback is approved.
- Verify reviewer instructions against the exact submitted build.