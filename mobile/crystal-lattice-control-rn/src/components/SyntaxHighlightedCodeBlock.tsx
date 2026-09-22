import React, { useMemo } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import SyntaxHighlighter from 'react-native-syntax-highlighter';
import * as hljsStyles from 'react-syntax-highlighter/styles/hljs';

import { useTheme } from '../theme';

export interface SyntaxHighlightedCodeBlockProps {
  language?: string;
  code: string;
  testID?: string;
}

const SyntaxHighlightedCodeBlock: React.FC<
  SyntaxHighlightedCodeBlockProps
> = ({
  language,
  code,
  testID = 'markdown-code-renderer-syntax-highlighter',
}) => {
  const theme = useTheme();
  const isDarkCodeBlock = theme.codeBlockBg !== '#FFFFFF';
  const normalizedLanguage =
    typeof language === 'string' && language.trim().length > 0
      ? language.trim()
      : 'plaintext';
  const codeBlockInnerStyle = useMemo(
    () => ({
      ...styles.codeBlockInner,
      fontSize: theme.typography.fontSize.code,
    }),
    [theme.typography.fontSize.code],
  );

  return (
    <View
      testID={testID}
      style={[
        styles.codeBlockOuter,
        {
          backgroundColor: theme.codeBlockBg,
          borderColor: theme.border,
        },
      ]}
    >
      <ScrollView
        style={styles.codeBlockScrollVertical}
        contentContainerStyle={styles.codeBlockScrollVerticalContent}
        nestedScrollEnabled
      >
        <ScrollView
          horizontal
          style={styles.codeBlockScrollHorizontal}
          contentContainerStyle={styles.codeBlockScrollHorizontalContent}
          showsHorizontalScrollIndicator
        >
          <SyntaxHighlighter
            language={normalizedLanguage}
            style={
              (isDarkCodeBlock
                ? (hljsStyles as any).atomOneDark
                : (hljsStyles as any).atomOneLight) as any
            }
            highlighter="hljs"
            fontFamily="Courier"
            fontSize={theme.typography.fontSize.code}
            lineHeight={theme.typography.lineHeight.code}
            customStyle={codeBlockInnerStyle}
            PreTag={View as any}
            CodeTag={Text as any}
          >
            {code}
          </SyntaxHighlighter>
        </ScrollView>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  codeBlockOuter: {
    marginTop: 4,
    marginBottom: 4,
    borderRadius: 6,
    borderWidth: 1,
    overflow: 'hidden',
  },
  codeBlockScrollVertical: {
    maxHeight: 260,
  },
  codeBlockScrollVerticalContent: {
    paddingHorizontal: 0,
    paddingVertical: 0,
  },
  codeBlockScrollHorizontal: {
    paddingHorizontal: 0,
    paddingVertical: 0,
  },
  codeBlockScrollHorizontalContent: {
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  codeBlockInner: {
    backgroundColor: 'transparent',
    padding: 0,
    margin: 0,
  },
});

export default React.memo(SyntaxHighlightedCodeBlock);