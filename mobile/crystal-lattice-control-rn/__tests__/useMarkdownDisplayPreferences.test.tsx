import { act, renderHook, waitFor } from '@testing-library/react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

import {
  MARKDOWN_DISPLAY_PREFERENCES_STORAGE_KEY,
  usePersistedMarkdownDisplayPreferences,
} from '../src/useMarkdownDisplayPreferences';

beforeEach(async () => {
  await AsyncStorage.clear();
});

test('hydrates defaults and persists changes', async () => {
  const { result } = renderHook(() => usePersistedMarkdownDisplayPreferences());
  await waitFor(() => expect(result.current.hydrated).toBe(true));
  expect(result.current.preferences).toEqual({
    baseFontSize: 15,
    headerSize: 'normal',
    markdownRenderer: 'react-native-markdown-display',
    codeBlockRenderer: 'selectable-native',
  });

  act(() => {
    result.current.setPreferences({
      baseFontSize: 16,
      headerSize: 'small',
      markdownRenderer: 'react-native-enriched-markdown',
      codeBlockRenderer: 'syntax-highlighter',
    });
  });
  expect(result.current.preferences).toEqual({
    baseFontSize: 16,
    headerSize: 'small',
    markdownRenderer: 'react-native-enriched-markdown',
    codeBlockRenderer: 'syntax-highlighter',
  });
  await waitFor(async () =>
    expect(
      await AsyncStorage.getItem(MARKDOWN_DISPLAY_PREFERENCES_STORAGE_KEY),
    ).toBe(
      '{"baseFontSize":16,"headerSize":"small","markdownRenderer":"react-native-enriched-markdown","codeBlockRenderer":"syntax-highlighter"}',
    ),
  );
});

test.each([
  [13, 14],
  [19, 17],
] as const)('migrates legacy stored size %s to %s', async (stored, expected) => {
  await AsyncStorage.setItem(
    MARKDOWN_DISPLAY_PREFERENCES_STORAGE_KEY,
    `{"baseFontSize":${stored},"headerSize":"normal"}`,
  );
  const { result } = renderHook(() => usePersistedMarkdownDisplayPreferences());
  await waitFor(() => expect(result.current.hydrated).toBe(true));
  expect(result.current.preferences.baseFontSize).toBe(expected);
  await waitFor(async () =>
    expect(
      await AsyncStorage.getItem(MARKDOWN_DISPLAY_PREFERENCES_STORAGE_KEY),
    ).toBe(
      `{"baseFontSize":${expected},"headerSize":"normal","markdownRenderer":"react-native-markdown-display","codeBlockRenderer":"selectable-native"}`,
    ),
  );
});

test('adds renderer defaults without changing typography-only preferences', async () => {
  await AsyncStorage.setItem(
    MARKDOWN_DISPLAY_PREFERENCES_STORAGE_KEY,
    '{"baseFontSize":16,"headerSize":"small"}',
  );

  const { result } = renderHook(() => usePersistedMarkdownDisplayPreferences());
  await waitFor(() => expect(result.current.hydrated).toBe(true));

  expect(result.current.preferences).toEqual({
    baseFontSize: 16,
    headerSize: 'small',
    markdownRenderer: 'react-native-markdown-display',
    codeBlockRenderer: 'selectable-native',
  });
});

test('normalizes partially invalid stored values', async () => {
  await AsyncStorage.setItem(
    MARKDOWN_DISPLAY_PREFERENCES_STORAGE_KEY,
    '{"baseFontSize":17,"headerSize":"large","markdownRenderer":"react-native-enriched-markdown","codeBlockRenderer":"invalid"}',
  );
  const { result } = renderHook(() => usePersistedMarkdownDisplayPreferences());
  await waitFor(() => expect(result.current.hydrated).toBe(true));
  expect(result.current.preferences).toEqual({
    baseFontSize: 17,
    headerSize: 'normal',
    markdownRenderer: 'react-native-enriched-markdown',
    codeBlockRenderer: 'selectable-native',
  });
});