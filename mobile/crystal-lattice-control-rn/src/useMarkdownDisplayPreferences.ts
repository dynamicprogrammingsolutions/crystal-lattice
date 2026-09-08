import { useCallback, useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  normalizeMarkdownDisplayPreferences,
  type MarkdownDisplayPreferences,
} from '@crystal-lattice/frontend-rn-components';

export const MARKDOWN_DISPLAY_PREFERENCES_STORAGE_KEY =
  'clc_markdown_display_preferences_v1';

export function usePersistedMarkdownDisplayPreferences() {
  const [preferences, setPreferencesState] =
    useState<MarkdownDisplayPreferences>(
      DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
    );
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(MARKDOWN_DISPLAY_PREFERENCES_STORAGE_KEY)
      .then((raw) => {
        if (!raw) return;
        try {
          const parsed = JSON.parse(raw);
          const normalized = normalizeMarkdownDisplayPreferences(parsed);
          setPreferencesState(normalized);
          const serialized = JSON.stringify(normalized);
          if (serialized !== raw) {
            void AsyncStorage.setItem(
              MARKDOWN_DISPLAY_PREFERENCES_STORAGE_KEY,
              serialized,
            );
          }
        } catch {
          setPreferencesState(DEFAULT_MARKDOWN_DISPLAY_PREFERENCES);
        }
      })
      .finally(() => setHydrated(true));
  }, []);

  const setPreferences = useCallback(
    (next: MarkdownDisplayPreferences) => {
      const normalized = normalizeMarkdownDisplayPreferences(next);
      setPreferencesState(normalized);
      void AsyncStorage.setItem(
        MARKDOWN_DISPLAY_PREFERENCES_STORAGE_KEY,
        JSON.stringify(normalized),
      );
    },
    [],
  );

  return { preferences, setPreferences, hydrated };
}