# Selectable RNMD Prose Without Desktop Scroll Capture

Correct the macOS read-only text scroll interception and make stable RNMD prose
selectable while preserving inline markdown styling and parent transcript
scrolling.

## Requirements checklist

- [x] Starting a wheel/trackpad scroll with the pointer over read-only
      selectable text scrolls the transcript unless the child is an explicitly
      scrollable bounded region.
- [ ] RNMD paragraphs, headings, list text, and other approved prose are
      selectable on mobile and macOS.
- [ ] Bold, italic, strike-through, inline-code, and link presentation/behavior
      remain intact when prose becomes selectable.
- [x] Selectable prose has no independent vertical scroll offset and does not
      clip or under-measure its content.
- [ ] Selection and scrolling are verified at native interaction boundaries,
      not only through React component props.

Parent Task: `tasks/20260918-markdown-renderers-selectable-text/000-main.md`

## Open requirement questions

1. Can a custom RNMD renderer place multiple compatible blocks under one
   selectable root `Text` without losing required block layout? If not,
   per-textgroup selection is an interim stable-renderer improvement only; the
   native renderer in subtask 050 owns continuous selection across font sizes.
2. Should selectable prose include list markers and table cells, or only their
   textual contents?
3. On a link, what interaction takes precedence between click-to-open and
   drag-to-select?

## Desktop scroll cause and likely correction

The assistant raw-message path in
`desktop/.../DesktopMessageBubble.tsx` uses:

```tsx
<TextInput value={content} editable={false} multiline />
```

It does not set `scrollEnabled={false}`. React Native macOS wraps multiline
text input in a native scroll view. Its source shows:

- the `scrollEnabled` prop is forwarded to that inner scroll view;
- disabling it constrains inner scrolling;
- the scroll view's `scrollWheel` forwards the event to its next responder when
  scrolling is disabled.

This directly matches the reported symptom and gives a high-confidence first
fix: make plain read-only inputs non-scrolling. It still needs a regression
test because responder-chain behavior depends on the mounted transcript.

## Current macOS text-selection finding

The desktop package and lockfile now pin `react-native-macos` 0.81.8, rather
than the 0.81.1 cited in earlier research. The installed Fabric
`RCTParagraphComponentView.mm` creates a non-editable `NSTextView` for
`Text selectable` and has special click/drag handling. This shows that the
prop has an implementation, but it does not establish that selection works in
this application's nested `Pressable` or accessibility wrappers. The user
reports that `selectable` by itself has not been sufficient. Earlier
react-native-macos Fabric builds also had a reported `Text selectable` failure
(microsoft/react-native-macos issue #2844).

React Native documents `Text selectable` as a selection API, and documents
`TextInput editable={false}` and `scrollEnabled={false}` as supported input
behaviors. Neither is a macOS-specific recommendation for every layout. The
installed macOS multiline `TextInput` uses a native text view inside a scroll
view, so disabling its scrolling is necessary for the raw message input.
For this partial pass, first trial `Text selectable` on exactly one
non-clickable field and wait for human verification before deciding how to
render other plain copyable fields.

## RNMD selection options

RNMD groups each sequence of inline nodes under a `textgroup` root `<Text>`.
Nested strong/emphasis/link nodes remain attributed children of that root.

React Native macOS's Fabric paragraph component implements
`selectable={true}` by swapping in a direct, non-editable, non-scrolling
`NSTextView` and copying the attributed text storage. iOS similarly uses a
non-scrolling `UITextView`; Android uses native selectable text behavior.
The earlier RNMD proposal was to override its `textgroup` rule with
`<Text selectable>`. The macOS application still needs native evidence that
this is actually selectable in context; it is deferred from this pass.

A read-only `TextInput` remains suitable for a plain string, especially on
iOS, but is not a drop-in renderer for RNMD leaves:

- it cannot contain RNMD's nested styled text children;
- flattening a group to a `value` loses inline style and link behavior;
- one input per leaf would fragment selection more than one selectable
  textgroup.

If selectable `Text` groups fail native interaction tests on a platform, the
next fallback should be an attributed native text primitive from subtask 050,
not a silent loss of markdown formatting.

## Feasibility assessment

High confidence in a focused raw-text scroll correction, pending a mounted
native regression. RNMD has the right inline grouping boundary for a
potential later selection experiment, but the reported macOS behavior makes
per-block selection unverified. A simple textgroup override would not provide
selection across separate headings/paragraphs/list items and would not, by
itself, satisfy the continuous mixed-size selection goal in subtask 050.

## Requested partial delivery

This pass targets the first and fourth requirements and a limited part of the
second on macOS only. First try `Text selectable` on the chat header session
ID, with human verification before deciding the selection method for the
other proposed plain fields: chat title/subtitle and static message footers.
Any trial of title/subtitle/ID inside clickable Sessions panel or home
collection rows needs a second human verification before those changes begin.
Keep the requirements checklist and the larger task scope intact. There are
no mobile application changes or mobile verification in this pass. The second
requirement remains incomplete while RNMD paragraphs, headings, lists, and
other prose are deferred. The third and full fifth requirements remain open.

## Execution plan

Status: Approved

First exercise the production `ChatPane` and `DesktopMessageBubble` in a
deterministic long transcript. Add a native macOS regression that toggles an
assistant message to raw view, positions the pointer over a tall selectable
multiline body, and wheels. Measure the parent transcript's offset before and
after. Reproduce interception first. Render static plaintext with `Text
selectable` so React Native paragraph layout owns the complete height and no
input-owned vertical scroll offset exists.

On the production chat header's session ID alone, add `Text selectable` with
a stable test identifier. Keep the existing layout and verify the unchanged
session ID and text props with a focused component test. Run available native
macOS interaction checks, then stop for the requested **human verification
gate**: in the desktop app, drag across the chat header session ID, copy and
paste it, and confirm no unexpected scroll or focus behavior. A passing prop
test does not pass the gate. Do not select a method or modify any other
copyable plain field before the user reports the result.

After that human result, decide whether the non-clickable chat header
title/subtitle and static user/system/tool/assistant message footers should
use `Text selectable` or a non-editable, non-scrolling `TextInput`. Check
selection, full copied value, layout, and wheel routing. Before changing
**any** selectable text in clickable Sessions panel rows or
`DesktopSessionCollectionItem` home/watchlist/history cards, stop for a
second explicit human verification of the chosen method and interaction
contract. Then trial ID/title/subtitle only when selection and the existing
single/double click, explicit open button, drag handle, and accessibility
behaviors coexist. Leave conflicting fields unchanged.

Verify existing deliberately bounded tool/reasoning scrolling separately.
Check that newly copyable plain text has no independent vertical offset,
clipping, or under-measured transcript rows. Document the behavior observed
on macOS. RNMD paragraphs/rules, styled links and markdown, cross-block
selection, and mobile work remain deferred.

### Implementation decisions and open questions

- Use `Text selectable` for static plaintext, including assistant raw text,
  bounded reasoning/tool content, tool-call arguments, chat metadata, and
  message/session footers. Reserve the repository-owned `MacTextView` for
  editable multiline controls.
- First human gate: the user confirms selection/copy and layout of the chat
  header ID in the real desktop app before any other field is made selectable.
- User-approved decision: retain `Text selectable` for the chat header ID.
  Spelling and grammar menu entries are not ideal but are acceptable there.
- Use normal selectable text inside intentionally bounded reasoning/tool
  regions. Preserve syntax highlighting in markdown code blocks, remove
  nested scrolling entirely, and make their root code text selectable.
- Second human gate: the user confirms the chosen method and expected click
  interaction before any clickable Sessions or home collection row changes.
  Titles, subtitles, and footers should copy the rendered value; IDs should
  copy the full value. Any field that conflicts with navigation stays
  unchanged.
- Do not introduce an RNMD `textgroup` override while the reported text-block
  leak is under investigation. Do not change mobile.
- Questions 1–3 above remain open for the deferred RNMD work. The separate
  native renderer in subtask 050 still owns mixed-size cross-block selection.

### Documentation

- Update desktop markdown/message-rendering development guidance with
  the measured read-only raw text scroll behavior, working copyable fields,
  and any click conflicts. Leave RNMD prose guidance as pending work.

### Task checklist

- [x] Reproduce and measure wheel interception over the production desktop raw
      assistant body using a native macOS test and long transcript.
- [x] Replace the raw read-only `TextInput` with ordinary selectable text and
      prove wheel routing and full-height layout.
- [x] Trial `Text selectable` on only the desktop chat header session ID,
      with focused component test; native selection awaits the human gate.
- [x] Human gate 1: user verified that `Text selectable` selects, but rejected
      the editing menu initially; the user subsequently accepted the spelling
      entries and chose to retain the selectable header ID.
- [x] Render expanded reasoning, tool results, and tool-call arguments as
      selectable text while retaining bounded parent scrolling.
- [x] Make syntax-highlighted markdown code selectable, unbounded, and
      non-scrollable; verify wheel input scrolls the transcript.
- [x] Make chat title/subtitle, static message footers, and the session status
      footer selectable after gate 1.
- [x] Remove read-only display behavior added to `MacTextView`, restore native
      spelling/grammar preferences, and use fixed-height `MacTextView` only for
      desktop plugin-provided multiline action editing.
- [ ] Human gate 2: user verifies the method and click contract before any
      selectable text changes in clickable Sessions/home collection rows.
- [ ] Trial title/subtitle/ID in clickable rows after gate 2 only if native
      selection and existing row actions both work.
- [x] Update desktop development documentation for behavior implemented in
      this stage and record partial requirement evidence.

### Requirement verification

- Requirement 1: native macOS `ChatPane` tests begin wheel scrolling over
  ordinary message text, a tall raw assistant block, and a markdown code
  block and confirm the transcript moves. Separate native tests begin the
  same gesture over expanded reasoning and tool-result content and confirm
  the explicitly bounded region moves while the transcript row stays fixed.
- Requirement 2, staged partial evidence: user selects/copies the complete
  chat header session ID and confirms normal layout before other changes.
  After gate 1, verify any other added non-clickable fields at the same
  native boundary. After gate 2, verify copy plus normal single/double-click
  actions for any changed Sessions/home collection rows. Leave the
  requirement unchecked until RNMD prose is done.
- Requirement 4: the 90-line raw selectable paragraph measures taller than
  the viewport and is revealed by scrolling the transcript. Reasoning and
  tool results measure their full text content inside their declared bounded
  parents. Markdown code has no nested scroll boundary and expands to its
  complete wrapped height.
- Requirement 5, partial evidence: use actual wheel, drag selection, keyboard
  copy, and row click gestures on macOS; leave the requirement unchecked
  pending RNMD native interaction verification.

### Additional implementation verification

- Add a focused component regression for desktop raw input props and the
  single chat header ID trial. Run focused transcript scroll/range tests and
  desktop type checks for the first stage; run Sessions UI checks only after
  that stage is authorized. Check accessibility labels if selection changes
  the tree.

## Implementation Notes

- The user approved execution with two explicit human gates: selection/copy
  of the chat header ID before choosing other plain fields, and a separate
  verification before any clickable Sessions or home row changes.
- Added `scrollEnabled={false}` to the desktop raw assistant input and trialed
  `selectable` on the chat header session ID only. Both focused Jest
  regressions failed before the change and pass afterward. These prove the
  rendered props, not native selection or copied content.
- Added a long assistant fixture to the production ChatPane range navigation
  harness and an XCUITest that toggles its actual message action and wheels
  over the raw input. The native test fails: a control wheel gesture over
  adjacent plain text moves the transcript, but the same gesture over the
  raw `TextInput` does not move its parent row. The 90-line input measures
  taller than the visible transcript, so this is not just a short-content
  geometry case.
- Native source inspection explains the result: the macOS multiline input
  owns a `RCTUIScrollView` whose disabled scrolling constrains the clip view;
  the `scrollWheel` forwarding override belongs to `RCTCustomScrollView`
  used by the outer transcript. This finding led to replacing the raw input
  with the repository-owned native text view rather than trying to correct
  the framework input from JavaScript.
- Human verification confirmed the header `Text selectable` trial was
  selectable. The user later accepted the AppKit spelling/grammar entries and
  requested restoring this version because the replacement input was not
  selectable.
- Initial implementation, later superseded: the raw React Native `TextInput`,
  expanded reasoning/tool content, and tool-call arguments temporarily used
  read-only auto-growing `MacTextView` instances. That stage added wheel
  forwarding, clip reset, a copy-only menu, forced text-checking state, and
  display-only typography props to the shared native component.
- Markdown code blocks retain the syntax highlighter but no longer mount any
  nested `ScrollView`. Long lines wrap, the block expands beyond the viewport,
  its root code `Text` is selectable, and a native wheel test proves input
  over the code block moves the transcript.
- Follow-up correction: static read-only `MacTextView` usage was removed after
  its native-to-JavaScript auto-grow event could be lost during Fabric mount
  and collapse long text to the one-line fallback. Raw assistant text,
  expanded reasoning/tool content, and tool-call arguments now use `Text
  selectable`, matching the existing user-message path.
- The chat title/subtitle, all message footers, and the session status footer
  are selectable. Clickable Sessions and home collection rows remain unchanged
  pending their separate human interaction gate.
- Audit of commit `0665d097` found that `setEditable:` forced every editable
  `MacTextView` spelling, grammar, correction, substitution, link, and data
  detection option on. Those assignments and the read-only copy menu, wheel
  forwarding, clip reset, and display-only typography props were removed.
  User preferences once again control AppKit text-checking options.
- No application-level Space-key submit or blur handler was found in the
  plugin action form. Desktop `multiline` action fields now use a fixed-height
  editable `MacTextView`; a new `submitOnEnter={false}` mode preserves ordinary
  newline entry. Single-line action fields remain React Native `TextInput`.
- Final verification on October 4, 2026:
  - focused desktop Jest: 19/19 passing across static selectable surfaces,
    chat header/footer fields, action multiline fields, and markdown code;
  - desktop TypeScript and the shared `react-native-mac-text-view` package
    TypeScript checks both pass;
  - native `ActionDisplayWindowUITests`: 2/2 passing, including typing
    `alpha beta` through the plugin multiline field without Space dropping
    focus;
  - native `TranscriptRangeNavigationUITests`: 5/5 passing for range
    preservation, raw text and markdown-code transcript scrolling, and
    bounded reasoning/tool scrolling.

### Draft desktop RNMD follow-up (not executed)

The next selectable-text modification should remain desktop-only and begin at
RNMD's `textgroup` boundary. Override `textgroup` with `Text selectable` so
paragraphs, headings, blockquotes, list contents, table-cell prose, nested
strong/emphasis/strike/inline-code runs, and inline links retain their existing
children and styles under one selectable root for each compatible group.

Do not independently make every styled leaf selectable when it already sits
inside a selectable textgroup; that would fragment selection. Keep fenced and
indented code on their existing syntax-highlighted selectable path. Treat list
markers separately because RNMD renders them outside the content textgroup,
and retain current layout if making the marker selectable changes alignment.

Add focused renderer tests for paragraphs, all heading sizes, unordered and
ordered list content, blockquotes, table cells, nested emphasis/strike/code,
and links. Add a macOS native harness containing those elements and verify
drag selection/copy plus transcript wheel routing. Link click versus drag
selection remains a human verification gate: clicking must still open the
link, while a drag that begins on link text must not unexpectedly navigate.
This per-textgroup pass does not promise selection across separate markdown
blocks and does not include mobile changes.