export type TabStripStyle =
  | 'toolbarTabs'
  | 'codeTabs'
  | 'underlineTabs'
  | 'roundedPills';

export const DEFAULT_TAB_STRIP_STYLE: TabStripStyle = 'toolbarTabs';

export function parseTabStripStyle(value: unknown): TabStripStyle | null {
  if (
    value === 'toolbarTabs' ||
    value === 'codeTabs' ||
    value === 'underlineTabs' ||
    value === 'roundedPills'
  ) {
    return value;
  }
  return null;
}
