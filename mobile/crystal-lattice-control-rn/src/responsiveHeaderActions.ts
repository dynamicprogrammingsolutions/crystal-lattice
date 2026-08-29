import { ACTIONS_MENU_BAR_ITEM_WIDTH } from '@crystal-lattice/frontend-rn-components';

export const MOBILE_HEADER_HORIZONTAL_GUTTER = 32;
export const MOBILE_HEADER_MIN_TITLE_WIDTH = 96;

export function getMobileHeaderMaxPinnedActions(windowWidth: number): number {
  const pinnedWidth =
    windowWidth -
    MOBILE_HEADER_HORIZONTAL_GUTTER -
    MOBILE_HEADER_MIN_TITLE_WIDTH -
    ACTIONS_MENU_BAR_ITEM_WIDTH;
  return Math.max(0, Math.floor(pinnedWidth / ACTIONS_MENU_BAR_ITEM_WIDTH));
}