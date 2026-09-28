import {
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  resolveMarkdownRendererPreferences,
} from '@crystal-lattice/frontend-rn-components';

import { getMobileMarkdownRendererCapabilities } from '../src/markdownRendererPreferences';

test('enables the verified native code renderer on iOS', () => {
  expect(getMobileMarkdownRendererCapabilities('ios')).toEqual({
    enrichedMarkdown: true,
    selectableNativeCode: true,
  });
});

test('uses the stable code fallback on Android until native verification passes', () => {
  const capabilities = getMobileMarkdownRendererCapabilities('android');

  expect(capabilities).toEqual({
    enrichedMarkdown: true,
    selectableNativeCode: false,
  });
  expect(
    resolveMarkdownRendererPreferences(
      DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
      capabilities,
    ),
  ).toEqual({
    markdownRenderer: 'react-native-markdown-display',
    codeBlockRenderer: 'syntax-highlighter',
    markdownRendererFellBack: false,
    codeBlockRendererFellBack: true,
  });
});

test('falls back to stable renderers on unsupported platforms', () => {
  expect(getMobileMarkdownRendererCapabilities('web')).toEqual({
    enrichedMarkdown: false,
    selectableNativeCode: false,
  });
});