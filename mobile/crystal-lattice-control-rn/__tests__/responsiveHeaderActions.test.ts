import { ACTIONS_MENU_BAR_ITEM_WIDTH } from '@crystal-lattice/frontend-rn-components';

import {
  MOBILE_HEADER_HORIZONTAL_GUTTER,
  MOBILE_HEADER_MIN_TITLE_WIDTH,
  getMobileHeaderMaxPinnedActions,
} from '../src/responsiveHeaderActions';

describe('getMobileHeaderMaxPinnedActions', () => {
  const reservedWidth =
    MOBILE_HEADER_HORIZONTAL_GUTTER +
    MOBILE_HEADER_MIN_TITLE_WIDTH +
    ACTIONS_MENU_BAR_ITEM_WIDTH;

  test('reserves the title and overflow trigger before assigning pin slots', () => {
    expect(getMobileHeaderMaxPinnedActions(reservedWidth)).toBe(0);

    for (const expectedSlots of [1, 3, 6]) {
      expect(
        getMobileHeaderMaxPinnedActions(
          reservedWidth + ACTIONS_MENU_BAR_ITEM_WIDTH * expectedSlots,
        ),
      ).toBe(expectedSlots);
    }
  });

  test('uses additional screen width for additional complete action slots', () => {
    const narrowWidth = reservedWidth + ACTIONS_MENU_BAR_ITEM_WIDTH * 2;
    const wideWidth = narrowWidth + ACTIONS_MENU_BAR_ITEM_WIDTH * 4;

    expect(getMobileHeaderMaxPinnedActions(wideWidth)).toBeGreaterThan(
      getMobileHeaderMaxPinnedActions(narrowWidth),
    );
  });
});