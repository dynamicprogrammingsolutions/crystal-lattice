import { useEffect, useMemo, useState } from 'react';
import { useColorScheme } from 'react-native';

import type { Theme } from '@crystal-lattice/frontend-rn-components';

import { DesktopWindowManager, desktopWindowEvents } from '../windows/desktopWindowManager';
import { buildDesktopThemeWithFallback } from './buildDesktopTheme';
import type { MacOSSystemThemePayload } from './types';

function coercePayload(value: unknown): MacOSSystemThemePayload | null {
  if (!value || typeof value !== 'object') return null;
  const obj = {...(value as any)};
  if (obj.appearance !== 'light' && obj.appearance !== 'dark') return null;

  const keys: Array<keyof Omit<MacOSSystemThemePayload, 'appearance'>> = [
    'accent',
    'windowBackground',
    'controlBackground',
    'separator',
    'text',
    'textSecondary',
    'textMuted',
    'danger',
    'success',
  ];
  for (const key of keys) {
    if (typeof obj[key] !== 'string' || obj[key].length === 0) {
      return null;
    }
  }

  return obj as MacOSSystemThemePayload;
}

export function useDesktopTheme(): Theme {
  const scheme = useColorScheme();
  const fallbackAppearance = scheme === 'dark' ? 'dark' : 'light';

  const [payload, setPayload] = useState<MacOSSystemThemePayload | null>(null);

  const debugEnabled = typeof __DEV__ !== 'undefined' ? __DEV__ : false;

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      if (!DesktopWindowManager?.getSystemTheme) {
        return;
      }
      try {
        const result = {...(await DesktopWindowManager.getSystemTheme())};
        const coerced = coercePayload(result);
        if (!cancelled) {
          if (coerced) {
            if (debugEnabled) {
              console.log('[desktop-theme] received payload', {
                source: 'getSystemTheme',
                payload: coerced,
              });
            }
          }
          setPayload(coerced ? { ...coerced } : null);
        }
      } catch {
        // Ignore; fall back to static palette.
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!desktopWindowEvents) return;
    const sub = desktopWindowEvents.addListener('systemThemeChanged', (eventPayload: any) => {
      eventPayload = {...eventPayload};
      const coerced = coercePayload(eventPayload);
      if (!coerced) {
        return;
      }

      if (debugEnabled) {
        console.log('[desktop-theme] received payload', {
          source: 'systemThemeChanged',
          payload: coerced,
        });
      }
      setPayload({ ...coerced });
    });
    return () => sub.remove();
  }, []);

  return useMemo(
    () => buildDesktopThemeWithFallback(payload, payload?.appearance ?? fallbackAppearance),
    [fallbackAppearance, payload],
  );
}
