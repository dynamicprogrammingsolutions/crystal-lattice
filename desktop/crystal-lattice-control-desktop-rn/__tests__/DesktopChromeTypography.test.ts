import { StyleSheet } from 'react-native';
import {
  MARKDOWN_BASE_FONT_SIZES,
  applyDisplayTypographyPreset,
} from '../../../packages/frontend-rn-components/src/markdownDisplayPreferences';

import { createChatPaneStyles } from '../src/chat/ChatPane';
import { createConnectionsPanelStyles } from '../src/panels/ConnectionsPanel';
import { createSessionsPanelStyles } from '../src/panels/SessionsPanel';
import { createSessionTabsStyles } from '../src/tabs/SessionTabs';
import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';
import { createPanelHeaderStyles } from '../src/ui/PanelHeader';

const baseTheme = buildDesktopTheme(null);
const largestPreset =
  MARKDOWN_BASE_FONT_SIZES[MARKDOWN_BASE_FONT_SIZES.length - 1];
const theme = applyDisplayTypographyPreset(baseTheme, largestPreset);

test('panel headers consume semantic theme typography and colors', () => {
  const styles = createPanelHeaderStyles(theme);

  expect(StyleSheet.flatten(styles.title)).toMatchObject({
    fontSize: theme.typography.fontSize.secondary,
    lineHeight: theme.typography.lineHeight.secondary,
    color: theme.text,
  });
  expect(StyleSheet.flatten(styles.subtitle)).toMatchObject({
    fontSize: theme.typography.fontSize.tiny,
    lineHeight: theme.typography.lineHeight.tiny,
    color: theme.textSecondary,
  });
});

test('connection and session cards consume semantic theme typography and colors', () => {
  const connectionStyles = createConnectionsPanelStyles(theme);
  const sessionStyles = createSessionsPanelStyles(theme);

  expect(StyleSheet.flatten(connectionStyles.rowTitle)).toMatchObject({
    fontSize: theme.typography.fontSize.secondary,
    lineHeight: theme.typography.lineHeight.secondary,
    color: theme.text,
  });
  expect(StyleSheet.flatten(connectionStyles.rowMeta)).toMatchObject({
    fontSize: theme.typography.fontSize.tiny,
    lineHeight: theme.typography.lineHeight.tiny,
    color: theme.textSecondary,
  });
  expect(StyleSheet.flatten(sessionStyles.rowTitle)).toMatchObject({
    fontSize: theme.typography.fontSize.normal,
    lineHeight: theme.typography.lineHeight.normal,
    color: theme.text,
  });
  expect(StyleSheet.flatten(sessionStyles.rowSubtitle)).toMatchObject({
    fontSize: theme.typography.fontSize.secondary,
    lineHeight: theme.typography.lineHeight.secondary,
    color: theme.textSecondary,
  });
  expect(StyleSheet.flatten(sessionStyles.rowId)).toMatchObject({
    fontSize: theme.typography.fontSize.small,
    lineHeight: theme.typography.lineHeight.small,
    color: theme.textSecondary,
  });
  expect(StyleSheet.flatten(sessionStyles.rowMeta)).toMatchObject({
    fontSize: theme.typography.fontSize.tiny,
    lineHeight: theme.typography.lineHeight.tiny,
    color: theme.textMuted,
  });
  expect(StyleSheet.flatten(sessionStyles.openButtonText)).toMatchObject({
    fontSize: theme.typography.fontSize.tiny,
    lineHeight: theme.typography.lineHeight.tiny,
    color: theme.primary,
  });
});

test('session tabs and the chat header consume semantic theme typography and colors', () => {
  const tabStyles = createSessionTabsStyles(theme, 'codeTabs');
  const chatStyles = createChatPaneStyles(theme, 'codeTabs');

  expect(StyleSheet.flatten(tabStyles.tabTitle)).toMatchObject({
    fontSize: theme.typography.fontSize.small,
    lineHeight: theme.typography.lineHeight.small,
    color: theme.text,
  });
  expect(StyleSheet.flatten(tabStyles.tabMeta)).toMatchObject({
    fontSize: theme.typography.fontSize.tiny,
    lineHeight: theme.typography.lineHeight.tiny,
    color: theme.textSecondary,
  });
  expect(StyleSheet.flatten(chatStyles.title)).toMatchObject({
    fontSize: theme.typography.fontSize.normal,
    lineHeight: theme.typography.lineHeight.normal,
    color: theme.text,
  });
  expect(StyleSheet.flatten(chatStyles.subtitle)).toMatchObject({
    fontSize: theme.typography.fontSize.small,
    lineHeight: theme.typography.lineHeight.small,
    color: theme.textSecondary,
  });
});