import { describe, expect, it } from 'vitest';

import { isNotificationTtlElapsed } from './notificationRetention';

describe('notification presentation retention', () => {
  it('treats TTL as elapsed at the exact deadline', () => {
    const notification = {
      retention: {
        version: 1 as const,
        policy: 'ttl' as const,
        expires_at: '2026-08-02T12:00:00Z',
      },
    };

    expect(
      isNotificationTtlElapsed(
        notification,
        new Date('2026-08-02T11:59:59Z'),
      ),
    ).toBe(false);
    expect(
      isNotificationTtlElapsed(
        notification,
        new Date('2026-08-02T12:00:00Z'),
      ),
    ).toBe(true);
  });

  it('does not suppress non-TTL or malformed legacy retention', () => {
    expect(
      isNotificationTtlElapsed({
        retention: { policy: 'until_resolved' },
      }),
    ).toBe(false);
    expect(
      isNotificationTtlElapsed({
        retention: { policy: 'ttl', expires_at: 'not-a-date' },
      }),
    ).toBe(false);
  });
});