import type { ActionDisplayPayload } from '../types/plugins';

export type ActionDisplaySurface =
  | 'application_action'
  | 'session_action'
  | 'session_list_action'
  | 'message_action';
export type ActionDisplayHost = 'mobile' | 'desktop';

export function normalizeActionDisplayForSurface(options: {
  display: ActionDisplayPayload | undefined;
  surface: ActionDisplaySurface;
  host: ActionDisplayHost;
}): ActionDisplayPayload | null {
  const { display, host } = options;
  if (!display) {
    return null;
  }

  const presentation = display.presentation ?? 'modal';
  return {
    ...display,
    presentation:
      host === 'desktop' && presentation === 'modal'
        ? 'inline'
        : presentation,
  };
}