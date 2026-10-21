# Mobile action forms and results

Ordinary action dialogs use the available safe viewport, with a fixed title,
scrollable form/message body, and fixed Cancel/OK controls. Long forms can be
scrolled while the software keyboard is open. Short confirmations retain their
compact size.

Action-result modals keep the title, close button, and follow-up actions outside
the markdown scroll area. A small embedded form has its own bounded scroll
area. When both content and fields overflow, markdown receives approximately
two thirds of the middle area and fields receive one third; a shorter form uses
only the height it needs. In reduced-height viewports the fields can use more
space to fit a text input while markdown retains a line of content. The
variant label sits beside the title where it fits. Larger or keyboard-heavy
forms should open a follow-up dialog.

## Implementation boundaries

The shared `ApplicationActionForm` handles initialization, field rendering,
validation, and typed submission. `ApplicationActionDialogLayout` reuses it
and enables its bounded body when the host supplies `maxHeight`.

The mobile dialog and `ActionResultModal` measure their actual safe-area
containers after keyboard adjustment. iOS uses `KeyboardAvoidingView`;
Android uses the modal window's resize behavior. The result's keyboard
avoidance is disabled while its follow-up overlay is open, so the overlay
owns the keyboard adjustment once. The source remains inaccessible while the
follow-up is active, and hardware Back cancels the follow-up first.

Mobile modal hosts support portrait and landscape. Opening a dialog dismisses
the source field's keyboard, and closing/submitting it dismisses its keyboard
before releasing the form. Default action inputs disable Android fullscreen
IME editing so the dialog and its fixed controls remain visible in landscape.

`useActionFormScroll` measures the focused input against its own scroll
viewport after focus, layout, or keyboard presentation. Custom text-field
renderers must forward `params.onFocus` for this behavior. Markdown and form
scroll views have separate native identities, and result backdrops are
siblings of the content rather than touch wrappers around it.

Compact inline result cards keep their separate presentation. These changes
apply to existing plugin schemas; they do not introduce datetime selectors.

Android bundle tasks track the shared frontend source directories and fixture
directory as build inputs. Shared-component changes therefore rebuild the
release/e2e JavaScript bundle instead of reusing an asset made from older code.

## Automated verification

`MobileActionFormsHarness` mounts the production dialog, result modal, mobile
field renderers, and follow-up hook with neutral records from
`test/fixture/actionFormLayouts.ts`. It is a native UI harness without a network
backend. The separate real-backend component suite uses public HTTP actions,
`FetchTransport`, and `RestAgentBackend`.

From the mobile package:

```bash
npm run tsc
npm test -- --runInBand --runTestsByPath __tests__/ActionFormLayout.test.tsx
npm run test:components:integration -- --runTestsByPath __integration__/ActionDisplayForm.realBackend.integration.test.tsx
npm run detox:build:ios
npm run detox:test:action-forms:ios
npm run detox:build:android
npm run detox:test:action-forms:android
```

The Android test script prepares the selected emulator before launching Detox.
The iOS module launch flag and Android launch-properties path both support
`clcActionFormsHarness=1`. Native scenarios cover compact confirmations, three
and many fields, submission with the keyboard open, both markdown renderers,
small and oversized embedded forms, follow-up overlays, and larger typography
in portrait. The optional landscape scenario runs with
`CLC_TEST_ACTION_FORM_LANDSCAPE=1` before either native test command. Native
visibility and frame assertions establish containment;
component tests preserve values and validation across viewport changes.

## Manual checkpoint with existing plugins

Use the updated mobile app with an existing connected backend, or the iOS
Local agent. The plugins must be enabled for the session.

1. In an OpenAI Responses session with `auth_mode` set to `auto` or `chatgpt`,
   open the session action **Show ChatGPT usage report**. Use existing journal
   history long enough to require scrolling.
2. Scroll the report markdown in both directions. The title, close button, and
   **Apply date range** action should remain reachable without scrolling to the
   end of the markdown.
3. Tap the existing **From** and **To** text fields, scroll their separate
   field area if needed, and edit a supported date/time. With the keyboard
   open, the active input and follow-up controls should remain reachable.
   Apply a range and verify that the report refreshes.
4. With the cost-tracking application plugin enabled, open **Reset cost
   tracking** from a session's action menu. Focus and edit the **Bucket**
   field, inspect the dialog and Cancel/OK controls above the keyboard, and
   cancel. No reset is needed to inspect the form behavior.
5. Open **Show cost report** to inspect another real markdown result. Repeat
   with larger text and a reduced-height/landscape viewport.

The ChatGPT report still has embedded text fields at this checkpoint. Its
separate range dialog, native datetime selectors, and corrected date-only
boundaries are later changes. Reports can use existing local history without
another provider request. Backend plugin code is unchanged for this checkpoint;
a release app needs a new build to include the updated UI.