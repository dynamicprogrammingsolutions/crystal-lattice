import type { ActionDisplayPayload } from '../types/plugins';

export type ActionDisplaySurface = 'session_action' | 'session_list_action';
export type ActionDisplayHost = 'mobile' | 'desktop';

export function normalizeActionDisplayForSurface(options: {
  display: ActionDisplayPayload | undefined;
  surface: ActionDisplaySurface;
  host: ActionDisplayHost;
}): ActionDisplayPayload | null {
  const { display, surface, host } = options;
  if (!display) {
    return null;
  }

  // Session list actions do not currently present rich display payloads on either platform.
  if (surface === 'session_list_action') {
    return null;
  }

  if (host === 'desktop') {
    return {
      ...display,
      presentation: 'inline',
    };
  }

  if (display.presentation === 'banner') {
    return {
      ...display,
      presentation: 'inline',
    };
  }

  return display;
}