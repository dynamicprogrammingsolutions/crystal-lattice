# Edit messages through the composer

Replace inline message editing in desktop and mobile with a clearly marked main-composer mode and tracked modification progress.

Parent Task: tasks/20261006-chat-operation-ux/000-main.md
Depends On: tasks/20261006-chat-operation-ux/010-request-and-action-progress.md

## Requirements checklist

- [x] **E1 (R4):** Modify loads the selected message into the main editor on both platforms; warning-colored context above it identifies the message index, the send title changes, and appropriate composer actions are disabled.
- [x] **E2 (R4):** Submitting the edit shows top progress and a spinning send button until modification completes.
- [x] **E3 (R6, R7):** Editing and submission preserve scrolling, keyboard dismissal, and useful transcript height, proven with Detox iOS/Android and macOS XCTest from the worktree.

## Questions requiring approval

Parent decisions 1 and 2 govern Save edit, the disabled actions, ordinary draft restoration, and edit lifetime across navigation. All parent decisions, including geometry targets, were approved on 2026-10-06.

## Supporting details

Both hosts modify user, assistant, and system text through `ChatController.modifyMessage`. Tool messages are excluded. The server's existing PATCH modifies the target canonical index and publishes `message_modified`; it does not start a model request. Keep role, metadata, and multipart behavior intact.

Desktop's native composer supports imperative `setText` and `focus`; its draft hook persists ordinary changes. Mobile `ChatComposer` owns local text and has a full-screen expanded composer; its handle currently supports only get/clear. Feeding an edit by changing `initialComposeText` alone will not reliably update the mounted editor.

## Execution plan
Status: Approved

### Design

Add an explicit ordinary-versus-edit composer mode in each host with connection/session identity, canonical target index, original content, and edit buffer. Preserve the existing ordinary draft/attachment storage boundary. Under the recommended policy, entering edit snapshots the ordinary composer state; editing routes changes to the edit buffer; save/cancel restores ordinary composition. Navigation must never apply one session's edit to another.

Give mobile's mounted composer an explicit text-replacement/mode contract and feed the same mode into its expanded editor. Desktop uses the native text-view imperative methods. Implement keyboard submission and the primary button through one mode-aware handler so Return cannot append/send while the user is editing.

Render warning-colored **Editing message [index]** plus an accessible Cancel edit control immediately above the composer. Use theme warning tokens and text so color is not the only signal. Use the approved visible save title on desktop, mobile inline composer, and mobile expanded editor.

Submit through the existing modification operation. Register a dedicated modification activity in the shared progress presentation from 010 and derive Send busy state from that activity. Hold edit-submission guards through acknowledgement and the transcript's confirmed updated state. A delayed network response must not replace a newer buffer/session state.

Remove inline editor props, text surfaces, Save/Cancel rows, and edit-specific transcript dependencies from message renderers when their consumers have moved. Continue rendering the canonical message until the modification succeeds. Preserve the existing set of editable roles and ordinary message actions.

### Verification design

Use a real local backend to seed messages and an ordinary draft with attachments. Invoke the production Modify action for user, assistant, and system messages, including index 0 and a nonzero index. Assert visible target context and title, approved disabled controls, exact message replacement at the selected index, and preservation of role/metadata/multipart content through the public API.

Exercise save, Cancel edit, failed modification, keyboard submission, mobile expand/collapse, session/tab switching, and leaving a pane outside the desktop warm set under the approved edit-lifetime policy. Keep text on a failed save and allow another attempt; do not treat failed HTTP acknowledgement as success.

Native tests delay modification acknowledgement through a local forwarding proxy so top progress and the button spinner can be observed. While editing and while submission is pending, swipe/wheel over actual messages and demonstrate movement. Show/hide the mobile keyboard and check the viewport. Test a multiline edit longer than the composer height so it scrolls within the bounded editor rather than consuming the transcript.

### Implementation decisions and open questions

- Save edit, exact disabled controls, ordinary draft restoration, and navigation policy were approved with the parent plan.
- The recommended operation preserves current PATCH semantics and introduces no implicit generation.
- Existing normal draft persistence must not store edited message text as an ordinary draft. Avoid a new disk-cache schema.
- Keep hard/soft request cancellation available when applicable; modification busy state must not masquerade as a cancellable model request.
- Removal of inline editor props is an internal consumer change; verify all real consumers before removing them.

### Documentation

Update desktop controls/actions and mobile composer/actions with entering, saving, cancelling, and leaving edit mode, including expanded-composer behavior. Extend native test instructions with the new edit cases.

### Task checklist

- [x] Confirm parent edit-policy decisions and document the approved interpretation.
- [x] Implement separate edit mode/buffer and safe ordinary draft ownership in both hosts.
- [x] Route mounted and expanded editors, visible title, warning context, Cancel edit, and keyboard submission through that mode.
- [x] Add scoped edit guards and modification activity/spinner lifetime.
- [x] Remove inline message editors and their obsolete dependencies.
- [x] Preserve existing multipart content through the retained-history core edit path, with regressions for user, assistant, and system roles.
- [x] Extend real-backend component and native suites with save/cancel/failure/navigation flows.
- [x] Run Detox iOS/Android and XCTest edit, scrolling, keyboard, and geometry cases.
- [x] Update documentation and parent R4/R6/R7 evidence.

### Requirement verification

- **E1:** Production message action → main composer → public PATCH → updated message in both `ChatOperations.realBackend.integration.test.tsx` suites; Detox and XCTest assert visible index/warning context/title and approved action eligibility. Real backend inspection confirms only the selected message content changed.
- **E2:** Native delayed-acknowledgement cases assert top modification progress and Send spinner until the approved completion boundary, then return to ordinary composition.
- **E3:** Each platform's edit/native scenarios include actual transcript movement and native height bounds; iOS/Android additionally prove keyboard dismissal and viewport expansion. Use the exact parent native test commands.

### Additional implementation verification

Check ordinary draft persistence, attachment preservation, noneditable tool results, read-only snapshots, mobile expanded-composer continuity, desktop native text replacement, and no duplicate modification on repeated primary/keyboard submission. Run affected message-renderer/composer component tests and TypeScript checks.

## Implementation Notes

- Edits use an independent connection/session-scoped buffer; ordinary text and attachments retain their existing ownership. Native editor text replacement and mobile expanded-editor mode are wired. Save uses the existing PATCH, then confirms the updated transcript before exiting edit mode.
- Inline editor branches and props were removed from both message renderers. Mobile now exposes Hide keyboard in both composer sizes and dismisses the keyboard on transcript drag. Full edit/failure/navigation verification is still in progress.
- The normal keyboard-visible composer uses a compact input and overflow menu; edit context shares that toolbar row and retains the index when text truncates. The expanded editor also renders live activity. Ordinary attachment drafts are held above pane remounts and remain separate from the edited message.
- Real HTTP editor tests now cover Save edit, Cancel edit, ordinary draft restoration, role/metadata/multipart preservation, and the existing PATCH boundary. A safe core correction was necessary to preserve the already-approved content-only modification contract; all 44 focused core/history cases pass.
- The iOS native edit workflow passes its warning/index/title, save progress, scrolling, keyboard, and geometry checks. macOS and Android native evidence remain outstanding.
- The latest complete HTTP suites also verify a rejected edit acknowledgement leaves the selected edit buffer intact and the backend message unchanged before retry. The native suites now include edit navigation/eviction retention and scrolling while edit acknowledgement is pending.
- Complete macOS and iOS native suites now pass with edit retention across navigation/eviction, ordinary draft restoration, pending Save progress, and actual transcript movement. Android's final command remains the outstanding E3 verification.

## Completion Notes

Completed October 10, 2026. E1–E3 and parent R4 are verified through complete
macOS XCTest and iOS/Android Detox commands, all exiting 0. Editing uses the
main composer, visible canonical index/warning context and Save edit,
independent ordinary drafts, scoped guards, and pending-save top/button
progress. Native checks include navigation/eviction retention and actual
scrolling while modification acknowledgement is delayed; mobile also
demonstrates keyboard dismissal and the 30% transcript floor.

Both production HTTP component suites pass edit cancellation, rejected-save
buffer retention, expanded mobile editing, and successful content-only PATCH.
Public inspection and the 44 focused core/history cases prove preservation
of role/metadata/multipart content, including the necessary retained-history
correction. Documentation is maintained in the owning desktop/mobile pages.
Final commands/artifacts are recorded in
`tasks/20261006-chat-operation-ux/000-main.md`. Human gesture/visual review
is separate from this automated evidence. No remaining required scope.