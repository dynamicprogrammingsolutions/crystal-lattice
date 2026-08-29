import React, { createContext, useCallback, useContext, useMemo } from 'react';
import type { Theme } from './theme';

export const MARKDOWN_BASE_FONT_SIZES = [14, 15, 16, 17] as const;

export type MarkdownBaseFontSize = (typeof MARKDOWN_BASE_FONT_SIZES)[number];
export type MarkdownHeaderSize = 'normal' | 'small';

export interface MarkdownDisplayPreferences {
  baseFontSize: MarkdownBaseFontSize;
  headerSize: MarkdownHeaderSize;
}

export interface MarkdownTypography {
  body: number;
  bodyLineHeight: number;
  h1: number;
  h1LineHeight: number;
  h2: number;
  h2LineHeight: number;
  h3: number;
  h3LineHeight: number;
  h4: number;
  h4LineHeight: number;
  h5: number;
  h5LineHeight: number;
  h6: number;
  h6LineHeight: number;
}

export const MARKDOWN_BASE_FONT_SIZE_OPTIONS: ReadonlyArray<{
  value: MarkdownBaseFontSize;
  label: string;
}> = [
  { value: 14, label: '14' },
  { value: 15, label: '15 (Default)' },
  { value: 16, label: '16' },
  { value: 17, label: '17' },
];

export const MARKDOWN_HEADER_SIZE_OPTIONS: ReadonlyArray<{
  value: MarkdownHeaderSize;
  label: string;
}> = [
  { value: 'normal', label: 'Normal' },
  { value: 'small', label: 'Small' },
];

export const DEFAULT_MARKDOWN_DISPLAY_PREFERENCES: MarkdownDisplayPreferences = {
  baseFontSize: 15,
  headerSize: 'normal',
};

type ResponsiveTypography = Pick<
  Theme['typography'],
  'fontSize' | 'lineHeight'
>;

export const DISPLAY_TYPOGRAPHY_PRESETS: Readonly<
  Record<MarkdownBaseFontSize, ResponsiveTypography>
> = {
  14: {
    fontSize: {
      tiny: 11,
      small: 12,
      secondary: 13,
      normal: 14,
      message: 14,
      large: 16,
      title: 18,
      screenTitle: 24,
      display: 28,
      code: 14,
    },
    lineHeight: {
      tiny: 14,
      small: 17,
      secondary: 18,
      normal: 20,
      message: 19,
      large: 22,
      title: 24,
      screenTitle: 30,
      display: 34,
      code: 19,
    },
  },
  15: {
    fontSize: {
      tiny: 11,
      small: 12,
      secondary: 13,
      normal: 14,
      message: 14,
      large: 16,
      title: 18,
      screenTitle: 24,
      display: 28,
      code: 14,
    },
    lineHeight: {
      tiny: 14,
      small: 17,
      secondary: 18,
      normal: 20,
      message: 19,
      large: 22,
      title: 24,
      screenTitle: 30,
      display: 34,
      code: 19,
    },
  },
  16: {
    fontSize: {
      tiny: 12,
      small: 13,
      secondary: 14,
      normal: 15,
      message: 16,
      large: 16,
      title: 18,
      screenTitle: 24,
      display: 28,
      code: 15,
    },
    lineHeight: {
      tiny: 15,
      small: 17,
      secondary: 20,
      normal: 21,
      message: 20,
      large: 22,
      title: 24,
      screenTitle: 30,
      display: 34,
      code: 20,
    },
  },
  17: {
    fontSize: {
      tiny: 13,
      small: 14,
      secondary: 15,
      normal: 16,
      message: 17,
      large: 17,
      title: 18,
      screenTitle: 24,
      display: 28,
      code: 16,
    },
    lineHeight: {
      tiny: 16,
      small: 18,
      secondary: 21,
      normal: 22,
      message: 21,
      large: 24,
      title: 24,
      screenTitle: 30,
      display: 34,
      code: 21,
    },
  },
};

const NORMAL_MARKDOWN_TYPOGRAPHY: Readonly<
  Record<MarkdownBaseFontSize, MarkdownTypography>
> = {
  14: {
    body: 14,
    bodyLineHeight: 19,
    h1: 30,
    h1LineHeight: 36,
    h2: 22,
    h2LineHeight: 27,
    h3: 17,
    h3LineHeight: 22,
    h4: 14,
    h4LineHeight: 20,
    h5: 14,
    h5LineHeight: 20,
    h6: 14,
    h6LineHeight: 20,
  },
  15: {
    body: 15,
    bodyLineHeight: 20,
    h1: 32,
    h1LineHeight: 38,
    h2: 24,
    h2LineHeight: 29,
    h3: 18,
    h3LineHeight: 23,
    h4: 15,
    h4LineHeight: 21,
    h5: 15,
    h5LineHeight: 21,
    h6: 15,
    h6LineHeight: 21,
  },
  16: {
    body: 16,
    bodyLineHeight: 21,
    h1: 34,
    h1LineHeight: 41,
    h2: 26,
    h2LineHeight: 32,
    h3: 19,
    h3LineHeight: 24,
    h4: 16,
    h4LineHeight: 23,
    h5: 16,
    h5LineHeight: 23,
    h6: 16,
    h6LineHeight: 23,
  },
  17: {
    body: 17,
    bodyLineHeight: 22,
    h1: 36,
    h1LineHeight: 43,
    h2: 27,
    h2LineHeight: 33,
    h3: 20,
    h3LineHeight: 25,
    h4: 17,
    h4LineHeight: 24,
    h5: 17,
    h5LineHeight: 24,
    h6: 17,
    h6LineHeight: 24,
  },
};

export function normalizeMarkdownBaseFontSize(value: unknown): MarkdownBaseFontSize {
  if (value === 13) return 14;
  if (value === 19) return 17;
  return typeof value === 'number' &&
    MARKDOWN_BASE_FONT_SIZES.includes(value as MarkdownBaseFontSize)
    ? (value as MarkdownBaseFontSize)
    : DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.baseFontSize;
}

export function normalizeMarkdownHeaderSize(value: unknown): MarkdownHeaderSize {
  return value === 'normal' || value === 'small'
    ? value
    : DEFAULT_MARKDOWN_DISPLAY_PREFERENCES.headerSize;
}

export function normalizeMarkdownDisplayPreferences(
  value: unknown,
): MarkdownDisplayPreferences {
  const record =
    value !== null && typeof value === 'object'
      ? (value as Record<string, unknown>)
      : {};
  return {
    baseFontSize: normalizeMarkdownBaseFontSize(record.baseFontSize),
    headerSize: normalizeMarkdownHeaderSize(record.headerSize),
  };
}

export function deriveMarkdownTypography(
  preferences: MarkdownDisplayPreferences,
): MarkdownTypography {
  const baseFontSize = normalizeMarkdownBaseFontSize(preferences.baseFontSize);
  const headerSize = normalizeMarkdownHeaderSize(preferences.headerSize);
  if (headerSize === 'small') {
    const preset = DISPLAY_TYPOGRAPHY_PRESETS[baseFontSize];
    return {
      body: baseFontSize,
      bodyLineHeight: preset.lineHeight.message,
      h1: baseFontSize,
      h1LineHeight: preset.lineHeight.message,
      h2: baseFontSize,
      h2LineHeight: preset.lineHeight.message,
      h3: baseFontSize,
      h3LineHeight: preset.lineHeight.message,
      h4: baseFontSize,
      h4LineHeight: preset.lineHeight.message,
      h5: baseFontSize,
      h5LineHeight: preset.lineHeight.message,
      h6: baseFontSize,
      h6LineHeight: preset.lineHeight.message,
    };
  }

  return NORMAL_MARKDOWN_TYPOGRAPHY[baseFontSize];
}

export function applyDisplayTypographyPreset(
  theme: Theme,
  baseFontSize: unknown,
): Theme {
  const preset = DISPLAY_TYPOGRAPHY_PRESETS[
    normalizeMarkdownBaseFontSize(baseFontSize)
  ];
  return {
    ...theme,
    typography: {
      fontSize: { ...preset.fontSize },
      lineHeight: { ...preset.lineHeight },
    },
  };
}

type MarkdownDisplayPreferenceUpdate =
  | MarkdownDisplayPreferences
  | ((current: MarkdownDisplayPreferences) => MarkdownDisplayPreferences);

interface MarkdownDisplayPreferencesContextValue {
  preferences: MarkdownDisplayPreferences;
  setPreferences: (update: MarkdownDisplayPreferenceUpdate) => void;
}

const MarkdownDisplayPreferencesContext =
  createContext<MarkdownDisplayPreferencesContextValue>({
    preferences: DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
    setPreferences: () => {},
  });

export interface MarkdownDisplayPreferencesProviderProps {
  value: MarkdownDisplayPreferences;
  onChange?: (preferences: MarkdownDisplayPreferences) => void;
  children: React.ReactNode;
}

export function MarkdownDisplayPreferencesProvider({
  value,
  onChange,
  children,
}: MarkdownDisplayPreferencesProviderProps): React.JSX.Element {
  const preferences = useMemo(
    () => normalizeMarkdownDisplayPreferences(value),
    [value.baseFontSize, value.headerSize],
  );
  const setPreferences = useCallback(
    (update: MarkdownDisplayPreferenceUpdate) => {
      const next =
        typeof update === 'function' ? update(preferences) : update;
      onChange?.(normalizeMarkdownDisplayPreferences(next));
    },
    [onChange, preferences],
  );
  const contextValue = useMemo(
    () => ({ preferences, setPreferences }),
    [preferences, setPreferences],
  );

  return (
    <MarkdownDisplayPreferencesContext.Provider value={contextValue}>
      {children}
    </MarkdownDisplayPreferencesContext.Provider>
  );
}

export function useMarkdownDisplayPreferences(): MarkdownDisplayPreferencesContextValue {
  return useContext(MarkdownDisplayPreferencesContext);
}