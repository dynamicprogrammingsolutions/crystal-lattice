import React, { useMemo } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import Markdown from 'react-native-markdown-display';
import SyntaxHighlighter from 'react-native-syntax-highlighter';
import * as hljsStyles from 'react-syntax-highlighter/styles/hljs';
import { useTheme } from '../theme';

export type MarkdownMessageVariant = 'assistant' | 'tool' | 'system' | 'user';

export interface MarkdownMessageContentProps {
  text: string;
  variant?: MarkdownMessageVariant;
}

const MarkdownMessageContent: React.FC<MarkdownMessageContentProps> = ({
  text,
  variant = 'assistant',
}) => {
  const theme = useTheme();

  const isDarkCodeBlock = useMemo(() => {
    return theme.codeBlockBg !== '#FFFFFF';
  }, [theme.codeBlockBg]);

  const markdownStyle = useMemo(() => {
    const baseTextColor = variant === 'user' ? theme.textOnPrimary : theme.text;

    return {
      body: {
        ...styles.bodyText,
        color: baseTextColor,
      },
      text: {
        ...styles.bodyText,
        color: baseTextColor,
      },
      strong: {
        fontWeight: '700',
      },
      em: {
        fontStyle: 'italic',
      },
      blockquote: {
        ...styles.blockquote,
        backgroundColor: theme.surfaceAlt,
        borderColor: theme.border,
      },
      code_inline: {
        ...styles.inlineCode,
        backgroundColor: theme.inlineCodeBg,
      },
      code_block: styles.codeBlockContainer,
      fence: styles.codeBlockContainer,
      bullet_list: styles.list,
      ordered_list: styles.list,
      list_item: styles.listItem,
      heading1: styles.heading,
      heading2: styles.heading,
      heading3: styles.heading,
      heading4: styles.heading,
      heading5: styles.heading,
      heading6: styles.heading,
    } as const;
  }, [variant, theme]);

  const rules = useMemo(
    () => ({
      // Fenced / block code
      fence: (node: any) => {
        const language = typeof node.lang === 'string' && node.lang.trim().length > 0
          ? node.lang.trim()
          : 'plaintext';
        const content = typeof node.content === 'string' ? node.content : '';

        return (
          <View
            key={node.key}
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
                  language={language}
                  style={
                    (isDarkCodeBlock
                      ? (hljsStyles as any).atomOneDark
                      : (hljsStyles as any).atomOneLight) as any
                  }
                  highlighter="hljs"
                  customStyle={styles.codeBlockInner}
                  PreTag={View as any}
                  CodeTag={Text as any}
                >
                  {content}
                </SyntaxHighlighter>
              </ScrollView>
            </ScrollView>
          </View>
        );
      },
      code_block: (node: any) => {
        // Some markdown variants may emit `code_block` instead of `fence`.
        const language = typeof node.lang === 'string' && node.lang.trim().length > 0
          ? node.lang.trim()
          : 'plaintext';
        const content = typeof node.content === 'string' ? node.content : '';

        return (
          <View
            key={node.key}
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
                  language={language}
                  style={
                    (isDarkCodeBlock
                      ? (hljsStyles as any).atomOneDark
                      : (hljsStyles as any).atomOneLight) as any
                  }
                  highlighter="hljs"
                  customStyle={styles.codeBlockInner}
                  PreTag={View as any}
                  CodeTag={Text as any}
                >
                  {content}
                </SyntaxHighlighter>
              </ScrollView>
            </ScrollView>
          </View>
        );
      },
    }),
    [isDarkCodeBlock, theme.border, theme.codeBlockBg],
  );

  return (
    <Markdown
      style={markdownStyle as any}
      rules={rules as any}
    >
      {text}
    </Markdown>
  );
};

const styles = StyleSheet.create({
  bodyText: {
    fontSize: 14,
  },
  heading: {
    fontWeight: '700',
    marginTop: 4,
    marginBottom: 2,
  },
  list: {
    marginVertical: 2,
  },
  listItem: {
    flexDirection: 'row',
  },
  inlineCode: {
    fontFamily: 'Courier',
    fontSize: 14,
    borderRadius: 3,
    paddingHorizontal: 3,
    paddingVertical: 1,
  },
  blockquote: {
    borderLeftWidth: 4,
    marginLeft: 2,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  codeBlockContainer: {
    marginTop: 4,
    marginBottom: 4,
  },
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

export default React.memo(MarkdownMessageContent);
