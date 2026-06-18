# Selectable React Native Message Text

Improve text selection in the React Native mobile chat UI so users can long-press and select/copy prose, reasoning, code blocks, and other message/session text without losing markdown rendering or syntax highlighting.

## Task checklist

- [x] `tasks/20260608-selectable-react-native-text/010-replace-markdown-renderer.md`
- [ ] `tasks/20260608-selectable-react-native-text/020-selectable-highlighted-code-blocks.md`
  - Depends on `tasks/20260608-selectable-react-native-text/010-replace-markdown-renderer.md`
- [ ] `tasks/20260608-selectable-react-native-text/030-selectable-plain-text-surfaces.md`
  - Depends on `tasks/20260608-selectable-react-native-text/010-replace-markdown-renderer.md`

## Background

The mobile app currently uses React Native `0.82.1`, React `19.1.1`, and `react-native-markdown-display` `^7.0.2` in `mobile/crystal-lattice-control-rn/package.json`.

Relevant local files:

- `mobile/crystal-lattice-control-rn/src/components/MarkdownMessageContent.tsx`
- `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
- `mobile/crystal-lattice-control-rn/__tests__/MessageBubble.test.tsx`

Current markdown code block rendering is custom:

- `MarkdownMessageContent.tsx` defines `fence` and `code_block` rules.
- Both rules render `react-native-syntax-highlighter` inside nested `ScrollView`s.
- Inline code has `selectable`, but that does not solve selection across a full markdown tree.

The key product issue is that React Native `Text selectable` does not reliably behave like browser selection across rich, nested markdown nodes. Users need to select arbitrary ranges in assistant responses, expanded thinking/reasoning, tool output, user/system text, and code blocks.

## Research Summary

`react-native-enriched-markdown` is the best candidate for selectable native markdown prose. It advertises text selection/copy support, custom selection context menu items, copy-as-markdown behavior, and Fabric/New Architecture support. It supports fenced code blocks as a markdown element, but package source inspection showed code blocks are styled monospace blocks, not token-level syntax-highlighted code.

Important compatibility note:

- Current app: React Native `0.82.1`.
- `react-native-enriched-markdown@0.4.x` compatibility table supports RN `0.82`.
- `react-native-enriched-markdown@0.6.0` compatibility table supports RN `0.83+`.
- React Native has newer stable versions available, but upgrading RN is not required for a first spike if using `0.4.x`.

Because syntax highlighting is a hard requirement, enriched markdown alone is not enough. The recommended path is:

1. Replace the markdown renderer with `react-native-enriched-markdown`, keeping the current code highlighter as a custom code block element for now.
2. Replace the code highlighter with a selectable highlighted native approach using `@rob117/react-native-selectable-text` plus Shiki or lowlight tokens rendered as nested React Native `Text` spans.
3. Introduce a reusable selectable plain-text component for non-markdown message text and session/message labels, with special handling where long-press selection competes with tap/click behavior.

## Sources Checked

- React Native `Text` docs: https://reactnative.dev/docs/text
- React Native `TextInput` docs: https://reactnative.dev/docs/textinput
- `react-native-markdown-display`: https://github.com/iamacup/react-native-markdown-display
- `react-native-syntax-highlighter`: https://github.com/conorhastings/react-native-syntax-highlighter
- `react-native-enriched-markdown`: https://github.com/software-mansion-labs/react-native-enriched-markdown
- Enriched markdown code block renderer source:
  - Android: https://raw.githubusercontent.com/software-mansion-labs/react-native-enriched-markdown/main/android/src/main/java/com/swmansion/enriched/markdown/renderer/CodeBlockRenderer.kt
  - iOS: https://raw.githubusercontent.com/software-mansion-labs/react-native-enriched-markdown/main/ios/renderer/CodeBlockRenderer.m
- `@rob117/react-native-selectable-text`: https://github.com/Rob117/react-native-selectable-text
- Shiki: https://shiki.style/guide/install
- lowlight: https://github.com/wooorm/lowlight
- refractor: https://github.com/wooorm/refractor

## Implementation Notes

Follow the mobile app guidelines in `mobile/crystal-lattice-control-rn/AGENTS.md`.

Keep changes scoped to the mobile React Native app unless native dependency installation requires iOS/Android project changes. If upgrading React Native becomes necessary, treat that as a separate explicit planning checkpoint before making the upgrade.

Verification should include real-device or simulator manual checks for long-press selection on iOS and Android because Jest cannot prove native selection behavior.