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
Resend. An unconfirmed send acknowledgement remains under the existing
status-check/retry recovery guard until reconciliation establishes whether a
request exists.

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
