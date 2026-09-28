import {
  pinnedComposerKeysForBar,
  resolveActiveRequestId,
  resolveComposerPrimaryLayout,
} from '../src/composerPrimaryAction';

describe('mobile composer primary action selection', () => {
  const preferenceKeys = ['cancel', 'softCancel', 'resend'];

  it.each([
    {
      name: 'all pinned while idle or all disabled',
      pinnedKeys: ['cancel', 'softCancel', 'resend'],
      requestActive: false,
      expected: {
        alternatingCancelKey: 'cancel',
        primaryKey: 'resend',
        hiddenKey: 'cancel',
      },
      bar: ['softCancel'],
    },
    {
      name: 'all pinned during a request',
      pinnedKeys: ['cancel', 'softCancel', 'resend'],
      requestActive: true,
      expected: {
        alternatingCancelKey: 'cancel',
        primaryKey: 'cancel',
        hiddenKey: 'resend',
      },
      bar: ['softCancel'],
    },
    {
      name: 'hard cancel only while idle',
      pinnedKeys: ['cancel'],
      requestActive: false,
      expected: {
        alternatingCancelKey: null,
        primaryKey: 'cancel',
        hiddenKey: null,
      },
      bar: [],
    },
    {
      name: 'hard cancel only during a request',
      pinnedKeys: ['cancel'],
      requestActive: true,
      expected: {
        alternatingCancelKey: null,
        primaryKey: 'cancel',
        hiddenKey: null,
      },
      bar: [],
    },
    {
      name: 'soft cancel only while idle',
      pinnedKeys: ['softCancel'],
      requestActive: false,
      expected: {
        alternatingCancelKey: null,
        primaryKey: 'softCancel',
        hiddenKey: null,
      },
      bar: [],
    },
    {
      name: 'soft cancel only during a request',
      pinnedKeys: ['softCancel'],
      requestActive: true,
      expected: {
        alternatingCancelKey: null,
        primaryKey: 'softCancel',
        hiddenKey: null,
      },
      bar: [],
    },
    {
      name: 'resend only while idle or all disabled',
      pinnedKeys: ['resend'],
      requestActive: false,
      expected: {
        alternatingCancelKey: null,
        primaryKey: 'resend',
        hiddenKey: null,
      },
      bar: [],
    },
    {
      name: 'resend only during a request',
      pinnedKeys: ['resend'],
      requestActive: true,
      expected: {
        alternatingCancelKey: null,
        primaryKey: 'resend',
        hiddenKey: null,
      },
      bar: [],
    },
    {
      name: 'both cancels while idle',
      pinnedKeys: ['cancel', 'softCancel'],
      requestActive: false,
      expected: {
        alternatingCancelKey: null,
        primaryKey: 'cancel',
        hiddenKey: null,
      },
      bar: ['softCancel'],
    },
    {
      name: 'both cancels during a request',
      pinnedKeys: ['cancel', 'softCancel'],
      requestActive: true,
      expected: {
        alternatingCancelKey: null,
        primaryKey: 'cancel',
        hiddenKey: null,
      },
      bar: ['softCancel'],
    },
    {
      name: 'hard cancel and resend while idle',
      pinnedKeys: ['cancel', 'resend'],
      requestActive: false,
      expected: {
        alternatingCancelKey: 'cancel',
        primaryKey: 'resend',
        hiddenKey: 'cancel',
      },
      bar: [],
    },
    {
      name: 'hard cancel and resend during a request',
      pinnedKeys: ['cancel', 'resend'],
      requestActive: true,
      expected: {
        alternatingCancelKey: 'cancel',
        primaryKey: 'cancel',
        hiddenKey: 'resend',
      },
      bar: [],
    },
    {
      name: 'soft cancel and resend while idle',
      pinnedKeys: ['softCancel', 'resend'],
      requestActive: false,
      expected: {
        alternatingCancelKey: 'softCancel',
        primaryKey: 'resend',
        hiddenKey: 'softCancel',
      },
      bar: [],
    },
    {
      name: 'soft cancel and resend during a request',
      pinnedKeys: ['softCancel', 'resend'],
      requestActive: true,
      expected: {
        alternatingCancelKey: 'softCancel',
        primaryKey: 'softCancel',
        hiddenKey: 'resend',
      },
      bar: [],
    },
  ])('$name', ({ pinnedKeys, requestActive, expected, bar }) => {
    const layout = resolveComposerPrimaryLayout({
      pinnedKeys,
      preferenceKeys,
      requestActive,
    });

    expect(layout).toEqual(expected);
    expect(pinnedComposerKeysForBar(pinnedKeys, layout)).toEqual(bar);
  });

  it('retains unrelated pinned actions in the normal bar', () => {
    const pinnedKeys = ['append', 'cancel', 'softCancel', 'resend'];
    const layout = resolveComposerPrimaryLayout({
      pinnedKeys,
      preferenceKeys,
      requestActive: false,
    });

    expect(pinnedComposerKeysForBar(pinnedKeys, layout)).toEqual([
      'append',
      'softCancel',
    ]);
  });

  it('treats an explicit live null request as authoritative over cache', () => {
    expect(
      resolveActiveRequestId(
        { activeRequestId: null },
        'stale-cached-request',
      ),
    ).toBeNull();
  });

  it('uses cached request state only before live state exists', () => {
    expect(resolveActiveRequestId(undefined, 'cached-request')).toBe(
      'cached-request',
    );
  });
});