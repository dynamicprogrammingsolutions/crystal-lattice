import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import { subscribeDisplayPresentation } from '@crystal-lattice/frontend-sdk';

import { emitHumanTimeTelemetryWarning } from '../src/humanTimeTelemetry/warning';

function createBackend(): AgentBackend {
  return {} as AgentBackend;
}

describe('human time telemetry warning', () => {
  it('emits a dismissible orange warning banner through the standard display pipeline', () => {
    const backend = createBackend();
    const received: unknown[] = [];
    const unsubscribe = subscribeDisplayPresentation(backend, (envelope) => {
      received.push(envelope);
    });

    emitHumanTimeTelemetryWarning(
      backend,
      'connection-a',
      new Error("HTTP 404 POST /actions: Unknown application plugin 'nope'"),
    );

    expect(received).toHaveLength(1);
    const envelope = received[0] as any;
    expect(envelope.source).toBe('action_response');
    expect(envelope.ownershipScope).toBe('connection');
    expect(envelope.connectionId).toBe('connection-a');
    expect(envelope.display.presentation).toBe('banner');
    expect(envelope.display.variant).toBe('warning');
    expect(envelope.display.dismissible).toBe(true);
    expect(envelope.display.format).toBe('text');
    expect(typeof envelope.display.body).toBe('string');
    expect(envelope.display.body.length).toBeGreaterThan(0);
    unsubscribe();
  });

  it('uses a stable display id so re-emissions replace instead of stacking', () => {
    const backend = createBackend();
    const received: unknown[] = [];
    const unsubscribe = subscribeDisplayPresentation(backend, (envelope) => {
      received.push(envelope);
    });

    emitHumanTimeTelemetryWarning(backend, 'connection-a', new Error('x'));
    emitHumanTimeTelemetryWarning(backend, 'connection-a', new Error('y'));

    const ids = received.map((envelope) => (envelope as any).display.display_id);
    expect(ids[0]).toBe(ids[1]);
    expect(ids[0]).toBe('human-time-telemetry-warning');
    unsubscribe();
  });
});