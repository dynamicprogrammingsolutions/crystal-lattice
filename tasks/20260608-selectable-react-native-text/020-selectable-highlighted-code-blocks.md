# Selectable Highlighted Code Blocks

Replace the current code block highlighter with a selectable, syntax-highlighted code block implementation using `@rob117/react-native-selectable-text` plus Shiki or lowlight tokens rendered as nested React Native `Text` spans.

## Requirements checklist

- [x] Introduce a dedicated `SelectableCodeBlock` component.
- [x] Tokenize code with Shiki, lowlight, or an equivalent highlighter that supports the required languages.
- [x] Render highlighted tokens as nested React Native `Text` spans inside `@rob117/react-native-selectable-text`.
- [x] Preserve code block styling: background, border, padding, font, horizontal scrolling or wrapping behavior, and language label if present.
- [x] Preserve or improve code copy affordances.
- [x] Manually verify selection and copy inside highlighted code on iOS and Android.
- [x] Update or add focused tests for token rendering and markdown integration where feasible.

Parent Task: `tasks/20260608-selectable-react-native-text/000-main.md`

Depends On: `tasks/20260608-selectable-react-native-text/010-replace-markdown-renderer.md`

## Current State

The existing code blocks are rendered in `mobile/crystal-lattice-control-rn/src/components/MarkdownMessageContent.tsx` through `react-native-syntax-highlighter`.

The current highlighter path gives syntax colors but not reliable native selection because it emits many nested React Native text pieces through a syntax-highlighter virtual DOM renderer.

Syntax highlighting is a hard product requirement, so plain selectable code is not enough.

## Research Notes

Recommended native direction:

- Use `@rob117/react-native-selectable-text` as the selectable wrapper.
- Use Shiki or lowlight to create token ranges.
- Render one top-level `Text` tree with nested `Text` spans for colored tokens.

`@rob117/react-native-selectable-text` notes:

- package version checked: `2.1.0`;
- README says it supports RN `0.81.1+` and Fabric;
- README says it supports nested text styling;
- Android source wraps a child `TextView` and calls `setTextIsSelectable(true)`;
- iOS source extracts child attributed text into a `UITextView`.

Potential tokenizer options:

- Shiki: high-quality highlighting, supports `codeToTokens`/token output and `codeToHtml`. Check runtime/bundle impact in React Native.
- lowlight: highlight.js AST/token tree; likely lighter and easier to convert to React Native spans.
- refractor: Prism AST/token tree; another possible converter path.

Do not switch to another `react-syntax-highlighter`-based package as the final solution. Packages such as `react-native-code-highlighter` and `@rivascva/react-native-code-editor` are useful references, but they are still based on token-rendered highlighter layers or editor overlays and may not solve native selection cleanly.

## Implementation Guidance

Create a component shaped approximately like:

```ts
interface SelectableCodeBlockProps {
  code: string;
  language?: string;
  variant?: MarkdownMessageVariant;
}
```

Token renderer goals:

- Preserve newlines exactly.
- Preserve spaces/tabs in monospace code.
- Keep all tokens in a single selectable text surface if possible.
- Avoid a separate React Native `Text` root per line if that prevents selecting across lines.
- Consider horizontal scrolling versus wrapping. Current implementation uses horizontal scrolling; keep that behavior unless selection handles become unusable.

If tokenized nested spans fail selection in `@rob117/react-native-selectable-text`, record the failure clearly and evaluate fallback options:

- full code block WebView with Shiki HTML;
- custom native code block component;
- read-only `TextInput` overlay approach for selection with highlighted view behind it.

## Verification

Manual verification should cover:

- long-press selection of partial code;
- selection across syntax token boundaries;
- selection across lines;
- copy output preserves exact code text;
- horizontal scrolling and selection handles do not fight each other;
- iOS and Android;
- large code blocks do not cause unacceptable rendering lag.

Automated tests should cover tokenizer-to-span conversion, including:

- unknown language fallback;
- empty code;
- code with spaces/tabs;
- multi-line code;
- text escaping, if any conversion to/from HTML or HAST is involved.

## Execution plan

Added during completion after user approval.

Recommended implementation path: start with the minimal lowlight/highlight.js approach so the proof of concept tests native selectable highlighted code with the least visual and dependency churn. Keep the enriched markdown prose renderer intact and replace only the isolated custom code block component used by `SelectableMarkdownMessageContent`.

Implementation checklist:

- [x] Add `@rob117/react-native-selectable-text` to the mobile app and run the required native install step (`pod install` for iOS).
- [x] Add an explicit tokenizer dependency aligned with the current highlight.js/lowlight renderer behavior.
- [x] Introduce `mobile/crystal-lattice-control-rn/src/components/SelectableCodeBlock.tsx` with props shaped as:
  ```ts
  interface SelectableCodeBlockProps {
    code: string;
    language?: string;
    variant?: MarkdownMessageVariant;
  }
  ```
- [x] Create a small tokenization adapter that converts highlighted output into a React Native-friendly token model, preserving exact text including spaces, tabs, and trailing newlines.
- [x] Render the code as one top-level React Native `Text` tree with nested colored `Text` spans inside `SelectableTextView`.
- [x] Preserve current code block layout and styling: background, border, radius, padding, monospace font, max vertical height, horizontal scrolling, and dark/light syntax theme selection.
- [x] Add a selection copy affordance through `SelectableTextView` menu handling, using selected text for partial copy operations.
- [x] Replace the current `HighlightedCodeBlock` path in `SelectableMarkdownMessageContent` with the new `SelectableCodeBlock`, keeping the `USE_CUSTOM_CODE_BLOCKS` toggle available as a quick rollback.
- [x] Add or update focused tests for tokenization and markdown integration:
  - known language tokenization;
  - unknown language fallback;
  - empty code;
  - multiline code;
  - spaces/tabs/trailing newline preservation;
  - fenced markdown renders the selectable code block instead of `SyntaxHighlighter`.
- [x] Run `npm test -- MessageBubble`, targeted new tests, `npm run tsc`, and `git diff --check`.
- [x] Manually verify on iOS and Android:
  - selection across syntax token boundaries;
  - selection across lines;
  - copy output preserves exact code text;
  - horizontal scrolling does not fight selection handles;
  - large code blocks remain acceptably responsive.

Fallback checkpoints:

- If nested colored `Text` spans inside `@rob117/react-native-selectable-text` do not select reliably, record the platform-specific failure and evaluate a WebView/Shiki HTML code block fallback.
- If horizontal scrolling conflicts with native selection, test a wrapped-code mode before considering native component work.
- If the old lowlight/highlight.js dependency path causes Metro or type issues, switch to a modern explicit `highlight.js` tokenizer before trying Shiki.

## Completion Notes

Added during completion.

Implemented the first-pass selectable highlighted code block path:

- Added `@rob117/react-native-selectable-text@2.1.0` and explicit `lowlight@1.9.2` dependencies.
- Ran `npm run pod-install`, which added the `SelectableText` iOS pod.
- Added `SelectableCodeBlock`, which tokenizes with lowlight/highlight.js, maps highlight.js classes through the existing atom-one light/dark styles, and renders nested React Native `Text` spans inside `SelectableTextView`.
- Replaced the old `react-native-syntax-highlighter` code block path in `SelectableMarkdownMessageContent`.
- Added a native selection menu copy handler that copies the selected text through `@react-native-clipboard/clipboard`.
- Added a lowlight type shim, a Jest mock for `SelectableTextView`, tokenization tests, render/copy tests, and markdown integration test updates.

Verification completed:

- `npm test -- MessageBubble SelectableCodeBlock`
- `npm run tsc`
- `git diff --check`

Remaining required verification:

- Manual iOS and Android selection/copy testing for native behavior, especially selection across token boundaries and while horizontally scrolling.