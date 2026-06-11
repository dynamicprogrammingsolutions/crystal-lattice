# Selectable Plain Text Surfaces

Introduce a reusable selectable text component for non-markdown text in the mobile app, covering message content, reasoning/thinking blocks, labels, titles, subtitles, footers, and other long text that users may want to copy.

## Requirements checklist

- [ ] Create a custom selectable plain-text component so the implementation can be replaced later without touching every call site.
- [ ] Apply it to non-markdown message content such as user, system, tool, raw text, reasoning/thinking, footers, titles, and snippets.
- [ ] Apply it to session footer/title/subtitle text where long-press selection is useful.
- [ ] Handle text that is also clickable/tappable, including session rows and link-like labels.
- [ ] Preserve current styling and layout.
- [ ] Manually verify long-press selection does not break normal tap/click behavior.
- [ ] Add focused tests for rendered states where feasible.

Parent Task: `tasks/20260608-selectable-react-native-text/000-main.md`

Depends On: `tasks/20260608-selectable-react-native-text/010-replace-markdown-renderer.md`

## Current State

Non-markdown text appears across:

- `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
- `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx`
- related small components under `mobile/crystal-lattice-control-rn/src/components/`

Examples to inspect:

- user message text;
- system message text;
- tool result text and collapsed tool hints;
- assistant reasoning/thinking expanded text;
- footer elements under assistant messages;
- message headers/titles;
- session row title/subtitle/preview/footer text;
- link source/citation titles and snippets.

Some existing fields already use `TextInput` when editing or raw-viewing messages, but that is not a consistent reusable solution.

## Implementation Guidance

Create a small component, for example:

```ts
interface SelectablePlainTextProps {
  text?: string;
  children?: React.ReactNode;
  style?: StyleProp<TextStyle>;
  numberOfLines?: number;
  onPress?: () => void;
  selectableMode?: 'text' | 'readonly-input';
}
```

The exact API can differ, but keep these design goals:

- centralize the selectable implementation;
- allow switching between React Native `Text selectable`, read-only `TextInput`, `react-native-uitextview`, or another native component later;
- keep callers visually similar to current `Text` usage;
- support `numberOfLines` and compact labels where needed;
- avoid accidentally opening the keyboard for read-only content;
- support long-press selection without swallowing normal tap behavior.

Readonly `TextInput` is acceptable for long plain text blocks, especially tool output and reasoning, but it may be awkward for inline or compact labels. Use it behind the custom component only where it behaves well.

For clickable surfaces like session rows:

- prefer row `onPress` for tap navigation;
- make inner long text selectable where possible;
- test whether long press on child selectable text prevents accidental row navigation;
- if necessary, expose a press/long-press split or add a copy action in the row context menu.

## Verification

Manual verification should cover:

- user/system/tool/assistant non-markdown text selection;
- expanded reasoning/thinking selection;
- message footer selection;
- session row title/subtitle/footer selection;
- normal tap behavior still works for clickable rows and links;
- collapsed one-line hints remain visually compact;
- iOS and Android behavior.

Automated tests should cover at least:

- component renders text and children paths;
- `numberOfLines` is passed through when supported;
- onPress/clickable mode still wires the callback;
- message components render the new wrapper in key branches.