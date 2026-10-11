# Session Chat composer and actions

This page describes mobile-specific composition, placement, persistence, and
eligibility for controls in `SessionChatScreen`. Shared action-menu rendering,
rich-control contracts, and request cancellation semantics remain owned by the
shared frontend packages.

## Composer layout

Session Chat renders model and reasoning settings as compact dropdowns and web
search as a compact Boolean toggle. The shared pinned-action bar is explicitly
configured for two rows with the leftover row below. Compact setting controls
come first; ordinary pinned actions occupy the lower right-aligned action row.
Composer actions contain Resend, Append, Append as, hard Cancel, and Soft
cancel.

The message input has a dynamic primary pinned action above Send. Placement is
stateless and depends only on pinning and whether a request is active. Resend
pairs with hard Cancel when both are pinned, otherwise with Soft cancel when
those two are pinned. The pair shares the side slot: Resend appears while idle
and during the all-disabled submission gap, while the paired Cancel appears
during an active request. The other pair member is hidden from the normal
pinned bar.

If both Cancel actions are pinned, the unpaired one remains in the normal bar.
With no Resend/Cancel pair, the first pinned action in hard Cancel, Soft
cancel, Resend order occupies the side slot and no other action is hidden.
Enabled state changes styling and interaction, not placement.

Fresh preferences pin Append, hard Cancel, and Resend. Existing stored pin
choices remain authoritative.

Each side control is 44 points square; the inline input has a 94-point minimum
height. Send uses the paper-plane `send` icon and Resend uses `repeat`. The
Send icon becomes a spinner during both request submission and the full
active-request lifetime; the maximized composer uses the same state.

The in-frame `maximize-2` control opens a full-screen editor backed by the same
draft, attachments, validation, persistence, and send path. `minimize-2`
collapses without discarding edits. The large native text surface is intended
to support iOS three-finger editing gestures; that operating-system gesture
requires human simulator/device verification.

## Request-action eligibility

An active request disables duplicate Send/Resend starts and enables hard and
soft Cancel, but does not globally disable model/reasoning/web settings,
plugin actions, attachments, Append, or reload. Append has separate local
in-flight state, and attachment operations retain their own pick/upload
guards. Eligible concurrent operations use the normal backend path and rely on
the server to accept or reject them.

A fatal request error clears the matching active-request UI state immediately;
the later completion event remains idempotent. Live controller state,
including an explicit null request ID, takes precedence over cached state so
Resend becomes available without a manual refresh. Draft text does not disable
Resend. An unconfirmed send acknowledgement keeps its original payload under
the Resend/Cancel recovery guard. Current request status alone does not prove
whether that unacknowledged operation was accepted.

The top Session actions also expose Resend, hard Cancel, and Soft cancel.
These entries reuse the same handlers and request-state eligibility as their
Composer action counterparts.

The frontend SDK's
[request cancellation documentation](../../../../packages/frontend-sdk/docs/development/request-cancellation.md)
owns the portable hard/soft cancellation contract.

## Rich settings and actions

`SessionChatScreen` consumes normalized rich config controls and session
actions from the shared frontend SDK.

- Config controls at `composer` use the same effective value and
  `SessionSettingsController` mutations as the full Session Settings modal.
- Rich dropdowns support discovered options, explicit custom string values,
  and reset.
- Session actions default to the header and may opt into the composer through
  `rich_ui.placements`.
- Rich toggle/list controls invoke the ordinary action and keep its dialog as
  fallback.
- Program-provided session actions remain above plugin-contributed actions in
  the complete menu; each group retains its own declared order.
- Connection-scoped pin preferences preserve explicit user choices; plugin
  `default_pinned` values apply only before a preference is stored.

See the shared React Native
[actions menu components](../../../../packages/frontend-rn-components/docs/development/actions-menu-components.md)
and frontend SDK
[rich session UI implementation](../../../../packages/frontend-sdk/docs/development/rich-session-ui.md)
for portable component and normalized-control behavior.

## Editing and progress

Modify uses the same inline or expanded main composer. Warning-colored
**Editing message [index]** context uses the canonical zero-based message
index, and the primary control visibly reads **Save edit**. Save modifies the
selected user, assistant, or system message and confirms the updated transcript;
it does not start a model response. Ordinary draft text and attachment drafts
remain separate and return after saving or Cancel edit. A failed save retains
the edit buffer. Edit identity and attachments stay scoped to the
connection/session across navigation in the connected workspace.

Append, Append as, Resend, and attachment mutations are disabled during
editing. Cancellation of existing model work and unrelated controls retain
their ordinary eligibility. The Save control spins during modification, and
the compact top status row identifies the message being saved.

Both composer sizes expose **Hide keyboard**. The inline control appears while
the keyboard is visible and clears after native dismissal. Both editors use
keyboard avoidance on Android's fullscreen activity. Dragging the transcript also
dismisses the keyboard. The normal composer keeps its bounded input height
when editing long messages.

While the keyboard is visible, the inline composer uses a compact input and
keeps its actions in the overflow menu. Edit context shares that toolbar row.
Hiding the keyboard restores the pinned controls and ordinary attachment
previews. Ordinary attachment previews stay separate from message editing.

The compact status row above the transcript also shows ordinary request
submission and generation. Application actions track independent operation
identities and leave unrelated actions usable; finishing one does not hide
another's progress.

## Verification and entry points

Maintainer entry points:

- `src/SessionChatScreen.tsx`
- `src/composerPrimaryAction.ts`
- `src/components/SessionSettingsModal.tsx`
- `src/testing/MobileRichSessionUiHarness.tsx`

Focused coverage includes:

- `__tests__/composerPrimaryAction.test.ts`
- `__tests__/RichSessionUi.test.tsx`
- Session Chat component tests
- `e2e/richSessionUi.e2e.test.ts`

The focused production Chat HTTP integration is:

```bash
npm run test:integration -- --runTestsByPath __integration__/ChatOperations.realBackend.integration.test.tsx
```

The native request, edit, and recovery workflows use a real backend, the
production connected navigation/screens, and a forwarding acknowledgement
proxy. After building the native apps, run:

```bash
npx detox test -c ios.sim.release e2e/chatOperations.e2e.test.ts --cleanup
scripts/prepare_android_detox_emulator.sh
npx detox test -c android.emu.e2e e2e/chatOperations.e2e.test.ts --cleanup
```

The suite uses the largest current typography preset, actual transcript
gestures, keyboard controls, and native frame measurements. It verifies that
the transcript retains at least 30% of the usable chat height and that status
and recovery stay above it. Continuous production polling requires explicit
bounded UI readiness checks with Detox synchronization disabled.
