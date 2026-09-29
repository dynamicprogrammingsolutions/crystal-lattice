# Selectable RNMD Prose Without Desktop Scroll Capture

Correct the macOS read-only text scroll interception and make stable RNMD prose
selectable while preserving inline markdown styling and parent transcript
scrolling.

## Requirements checklist

- [ ] Starting a wheel/trackpad scroll with the pointer over read-only
      selectable text scrolls the transcript unless the child is an explicitly
      scrollable bounded region.
- [ ] RNMD paragraphs, headings, list text, and other approved prose are
      selectable on mobile and macOS.
- [ ] Bold, italic, strike-through, inline-code, and link presentation/behavior
      remain intact when prose becomes selectable.
- [ ] Selectable prose has no independent vertical scroll offset and does not
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
text input in `RCTUIScrollView`. Its source shows:

- the `scrollEnabled` prop is forwarded to that inner scroll view;
- disabling it constrains inner scrolling;
- `RCTUIScrollView.scrollWheel` forwards the event to its next responder when
  scrolling is disabled.

This directly matches the reported symptom and gives a high-confidence first
fix: make plain read-only inputs non-scrolling. It still needs a regression
test because responder-chain behavior depends on the mounted transcript.

## RNMD selection options

RNMD groups each sequence of inline nodes under a `textgroup` root `<Text>`.
Nested strong/emphasis/link nodes remain attributed children of that root.

React Native macOS's Fabric paragraph component implements
`selectable={true}` by swapping in a direct, non-editable, non-scrolling
`NSTextView` and copying the attributed text storage. iOS similarly uses a
non-scrolling `UITextView`; Android uses native selectable text behavior.
Therefore, overriding RNMD's `textgroup` rule to render `<Text selectable>` is
the lowest-risk styled-prose approach.

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

High for per-block selection. The likely desktop raw-text fix is one prop, and
the stable renderer already has the right inline grouping boundary. The simple
textgroup override does not provide selection across separate
headings/paragraphs/list items and therefore does not, by itself, satisfy the
continuous mixed-size selection goal in subtask 050.

## Execution plan

Status: Draft

Add or extend a deterministic production transcript harness containing a long
scrollable transcript and sufficiently tall raw read-only content. First write
a macOS UI regression that positions the pointer over the raw text and sends a
wheel gesture, then set `scrollEnabled={false}` (plus the existing read-only,
multiline reset props) and prove the parent moves. Also verify selection still
works.

After that boundary passes, add a shared RNMD `textgroup` rule that marks the
root inline `Text` selectable. Apply it to mobile and desktop stable renderers,
then verify selection, normal transcript scroll, links, headings, lists,
tables, inline code, and nested bounded scroll areas on native platforms.

Evaluate whether compatible RNMD blocks can share one selectable root `Text`.
If fidelity regresses, keep this subtask scoped to natural text groups and
treat it as the near-term stable path while subtask 050 validates the proper
single-attributed-view architecture.

### Implementation decisions and open questions

- Recommendation: fix and retain non-scrolling `TextInput` for plain/raw text.
- Recommendation: use selectable `Text` groups for styled RNMD output, because
  they preserve attributed children and avoid an inner scroll view on macOS.
- Recommendation: do not force incompatible block layout into a root RN
  `Text`. Per-group selection is acceptable as an interim RNMD enhancement,
  while cross-block and cross-size selection remains a required native-renderer
  feasibility target.
- Questions 1–3 above should be settled before final accessibility and link
  interaction acceptance is written.

### Documentation

- Update desktop markdown development documentation with the selectable text
  boundary and the requirement that plain read-only multiline inputs disable
  inner scrolling.
- Update mobile message-rendering guidance if the existing iOS
  `SelectablePlainText` platform split changes.
- Document any known per-block selection boundary for users only if it is
  visible enough to need explanation.

### Task checklist

- [ ] Add a native macOS reproduction for wheel input over raw selectable text.
- [ ] Disable inner scrolling on plain read-only text and prove parent scroll.
- [ ] Add the selectable RNMD textgroup rule on mobile and desktop.
- [ ] Verify formatting, links, lists, tables, and inline code.
- [ ] Verify iOS and Android selection/scroll interaction.
- [ ] Verify macOS selection/scroll interaction with XCUITest.
- [ ] Update documentation.

### Requirement verification

- In a long production transcript, begin wheel/trackpad scrolling over raw
  text, a markdown paragraph, a heading, a list item, and inline code; verify
  the transcript moves in each case.
- Select and copy a substring crossing bold/italic/plain runs within one text
  group and verify copied text order.
- Click an unselected link and drag through link text to validate the approved
  link/selection interaction.
- Verify intentionally bounded tool/reasoning/code scroll views still scroll
  themselves where designed.

### Additional implementation verification

- Component tests should assert `scrollEnabled={false}` for every plain
  read-only `TextInput` path and `selectable` on RNMD textgroup roots.
- Run existing transcript scroll/persistence suites to catch responder or
  geometry regressions.
- Inspect VoiceOver/accessibility output because selectable native text can
  change the accessibility subtree.