import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import {
  emitDisplayPresentation,
  normalizeDisplayEnvelope,
} from '@crystal-lattice/frontend-sdk';

export const HUMAN_TIME_TELEMETRY_WARNING_DISPLAY_ID =
  'human-time-telemetry-warning';

/**
 * Warn the user once (per arm cycle) that time tracking is enabled but the
 * telemetry plugin is not available on the server — through the standard
 * plugin-notification display pipeline (the top orange warning banner), never
 * a popup. The stable display id means a re-armed warning replaces the
 * previous banner instead of stacking.
 */
export function emitHumanTimeTelemetryWarning(
  backend: AgentBackend,
  connectionId: string | null,
  _error: unknown,
): void {
  emitDisplayPresentation(
    backend,
    normalizeDisplayEnvelope({
      source: 'action_response',
      ownershipScope: 'connection',
      connectionId,
      display: {
        format: 'text',
        title: 'Time tracking',
        body:
          'Time tracking is enabled, but the telemetry plugin is not available on this server. ' +
          'Recorded time is kept and retried. Check the Telemetry plugin setting in Settings, ' +
          'or enable the duration-tracking plugin on the server.',
        variant: 'warning',
        presentation: 'banner',
        dismissible: true,
        display_id: HUMAN_TIME_TELEMETRY_WARNING_DISPLAY_ID,
      },
    }),
  );
}