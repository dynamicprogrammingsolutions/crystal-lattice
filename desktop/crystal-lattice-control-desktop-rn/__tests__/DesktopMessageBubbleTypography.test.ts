import { StyleSheet } from 'react-native';
import {
  MARKDOWN_BASE_FONT_SIZES,
  applyDisplayTypographyPreset,
} from '../../../packages/frontend-rn-components/src/markdownDisplayPreferences';

import { createDesktopMessageBubbleStyles } from '../src/chat/DesktopMessageBubble';
import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';

test('desktop message content and footer consume responsive theme metrics', () => {
  const baseTheme = buildDesktopTheme(null);
  const largestPreset =
    MARKDOWN_BASE_FONT_SIZES[MARKDOWN_BASE_FONT_SIZES.length - 1];
  const theme = applyDisplayTypographyPreset(baseTheme, largestPreset);
  const styles = createDesktopMessageBubbleStyles(theme);

  expect(StyleSheet.flatten(styles.footerText)).toMatchObject({
    fontSize: theme.typography.fontSize.tiny,
    lineHeight: theme.typography.lineHeight.tiny,
  });
  expect(StyleSheet.flatten(styles.contentText)).toMatchObject({
    fontSize: theme.typography.fontSize.message,
    lineHeight: theme.typography.lineHeight.message,
  });
  expect(StyleSheet.flatten(styles.systemText)).toMatchObject({
    fontSize: theme.typography.fontSize.message,
    lineHeight: theme.typography.lineHeight.message,
  });
});