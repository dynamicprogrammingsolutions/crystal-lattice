import { StyleSheet } from 'react-native';

import { createDesktopMessageBubbleStyles } from '../src/chat/DesktopMessageBubble';
import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';

test('desktop message content and footer consume responsive theme metrics', () => {
  const baseTheme = buildDesktopTheme(null);
  const theme = {
    ...baseTheme,
    typography: {
      fontSize: {
        ...baseTheme.typography.fontSize,
        tiny: 12,
        message: 16,
      },
      lineHeight: {
        ...baseTheme.typography.lineHeight,
        tiny: 17,
        message: 23,
      },
    },
  };
  const styles = createDesktopMessageBubbleStyles(theme);

  expect(StyleSheet.flatten(styles.footerText)).toMatchObject({
    fontSize: 12,
    lineHeight: 17,
  });
  expect(StyleSheet.flatten(styles.contentText)).toMatchObject({
    fontSize: 16,
    lineHeight: 23,
  });
});