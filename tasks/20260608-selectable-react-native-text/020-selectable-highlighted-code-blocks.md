# Selectable Highlighted Code Blocks

Replace the current code block highlighter with a selectable, syntax-highlighted code block implementation using `@rob117/react-native-selectable-text` plus Shiki or lowlight tokens rendered as nested React Native `Text` spans.

## Requirements checklist

- [ ] Introduce a dedicated `SelectableCodeBlock` component.
- [ ] Tokenize code with Shiki, lowlight, or an equivalent highlighter that supports the required languages.
- [ ] Render highlighted tokens as nested React Native `Text` spans inside `@rob117/react-native-selectable-text`.
- [ ] Preserve code block styling: background, border, padding, font, horizontal scrolling or wrapping behavior, and language label if present.
- [ ] Preserve or improve code copy affordances.
- [ ] Manually verify selection and copy inside highlighted code on iOS and Android.
- [ ] Update or add focused tests for token rendering and markdown integration where feasible.

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