# Replace Markdown Renderer With Enriched Markdown

Replace assistant markdown rendering with `react-native-enriched-markdown` so rich markdown prose becomes natively selectable, while preserving the current custom syntax highlighter for fenced code blocks during this first step.

## Requirements checklist

- [ ] Install and wire a React Native compatible `react-native-enriched-markdown` version.
- [ ] Replace `react-native-markdown-display` usage in assistant markdown rendering with enriched markdown.
- [ ] Preserve current custom code block rendering behavior and syntax highlighting for fenced code blocks.
- [ ] Preserve styling, theme colors, link behavior, inline code appearance, headings, lists, blockquotes, and message layout as closely as practical.
- [ ] Add or update focused component tests where feasible.
- [ ] Manually verify selection behavior for markdown prose on iOS and Android.

Parent Task: `tasks/20260608-selectable-react-native-text/000-main.md`

## Current State

The app currently renders markdown through:

- `mobile/crystal-lattice-control-rn/src/components/MarkdownMessageContent.tsx`

Current dependency versions in `mobile/crystal-lattice-control-rn/package.json`:

- `react-native`: `0.82.1`
- `react`: `19.1.1`
- `react-native-markdown-display`: `^7.0.2`
- `react-native-syntax-highlighter`: `^2.1.0`

`MarkdownMessageContent.tsx` currently:

- imports `Markdown` from `react-native-markdown-display`;
- defines `fence` and `code_block` custom rules;
- renders code blocks with `react-native-syntax-highlighter`;
- wraps code blocks in vertical and horizontal `ScrollView`s;
- defines inline code with a custom `Text selectable`, which does not solve multi-element selection.

`MessageBubble.tsx` renders assistant markdown content at the assistant message content branch. The raw mode branch already uses a read-only `TextInput`, but raw mode is not an acceptable substitute for markdown mode.

## Research Notes

`react-native-enriched-markdown` is promising for selectable markdown prose and copy behavior. It advertises:

- native text selection and copy support;
- custom text selection context menu items;
- copy-as-markdown behavior;
- support for iOS, Android, macOS, and web;
- New Architecture/Fabric requirement on native platforms.

Compatibility table from its README:

- `0.4.x` supports RN `0.81`, `0.82`, `0.83`, and `0.84`.
- `0.6.0` supports RN `0.83+`, not RN `0.82`.

Unless this task intentionally includes a React Native upgrade, start by evaluating `react-native-enriched-markdown@0.4.x` against the current RN `0.82.1` app.

Important caveat: package source inspection indicates its code blocks are styled monospace blocks, not syntax-highlighted code. For this subtask, keep current custom syntax highlighter code blocks rather than relying on enriched markdown code block rendering.

## Implementation Guidance

Investigate whether `react-native-enriched-markdown` supports custom renderers or a way to exclude/override code blocks. If it does not expose custom renderers, segment the markdown into ordered pieces:

- markdown chunks without fenced code blocks rendered through enriched markdown;
- fenced code chunks rendered through the existing code block component.

Prefer a small helper that parses/splits fenced code blocks robustly. Do not use fragile line-by-line regex if a Markdown parser already available in the app can safely identify fences.

Keep the resulting public component API close to the existing `MarkdownMessageContent` props:

```ts
export interface MarkdownMessageContentProps {
  text: string;
  variant?: MarkdownMessageVariant;
}
```

## Verification

Run mobile tests after code changes:

```bash
cd mobile/crystal-lattice-control-rn
npm test -- MessageBubble
```

Manual verification should cover:

- long-press selection across bold/italic/inline-code/link spans;
- selection across paragraph boundaries, headings, lists, and blockquotes;
- link tapping still works;
- fenced code blocks still syntax-highlight;
- streaming assistant messages still render acceptably;
- iOS and Android behavior if both platforms are in scope.