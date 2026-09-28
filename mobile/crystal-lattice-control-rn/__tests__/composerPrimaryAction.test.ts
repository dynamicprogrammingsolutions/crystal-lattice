import {
  pinnedComposerKeysForBar,
  resolveActiveRequestId,
  selectPrimaryComposerActionKey,
} from '../src/composerPrimaryAction';

describe('mobile composer primary action selection', () => {
  it('prefers the first enabled pinned action', () => {
    expect(
      selectPrimaryComposerActionKey({
        pinnedKeys: ['append', 'cancel', 'softCancel', 'resend'],
        preferenceKeys: ['cancel', 'softCancel', 'resend'],
        isDisabled: (key) => key === 'cancel',
      }),
    ).toBe('softCancel');
  });

  it('uses the first candidate as a disabled placeholder', () => {
    expect(
      selectPrimaryComposerActionKey({
        pinnedKeys: ['cancel', 'resend'],
        preferenceKeys: ['cancel', 'softCancel', 'resend'],
        isDisabled: () => true,
      }),
    ).toBe('cancel');
  });

  it('does not select an unpinned preferred action', () => {
    expect(
      selectPrimaryComposerActionKey({
        pinnedKeys: ['append'],
        preferenceKeys: ['cancel', 'softCancel', 'resend'],
        isDisabled: () => false,
      }),
    ).toBeNull();
  });

  it('removes only the selected action from the normal pinned bar', () => {
    expect(
      pinnedComposerKeysForBar(
        ['append', 'cancel', 'softCancel', 'resend'],
        'cancel',
      ),
    ).toEqual(['append', 'softCancel', 'resend']);
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