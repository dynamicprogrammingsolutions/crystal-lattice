# External TestFlight Readiness

Prepare and, if approved, submit the app for external TestFlight testing with reviewer-access instructions.

## Requirements checklist

- [ ] Confirm the product owner wants external testers for this build.
- [ ] Create or update external tester group(s).
- [ ] Fill all required TestFlight external testing metadata.
- [ ] Provide Apple reviewer instructions and a usable backend/demo access path.
- [ ] Submit the build for TestFlight external review.
- [ ] Track review outcome and required fixes.

Parent Task: tasks/20260614-ios-testflight-github-fastlane/000-main.md
Depends On: tasks/20260614-ios-testflight-github-fastlane/090-first-testflight-dry-run.md

## Notes

Internal TestFlight testing is the first milestone. External testing introduces Apple TestFlight review requirements and reviewer-access risk. Because Crystal Lattice Control is useful only when connected to an agent/server environment, external review preparation must include a practical way for Apple to evaluate the app.

Possible reviewer access approaches:

- Provide a stable cloud connection link.
- Provide a bridge/server demo environment plus pairing instructions.
- Provide reviewer account credentials if the demo environment requires auth.
- Provide concise review notes explaining local-network behavior and what to test.

## Acceptance Criteria

- External tester setup is complete in App Store Connect.
- Reviewer notes are clear enough for someone unfamiliar with the project.
- External TestFlight build is submitted, approved, or any rejection/blocker is documented with next steps.
