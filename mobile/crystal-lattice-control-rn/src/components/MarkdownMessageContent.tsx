import React, { useMemo } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import Markdown from 'react-native-markdown-display';
import SyntaxHighlighter from 'react-native-syntax-highlighter';
import { atomOneDark } from 'react-syntax-highlighter/styles/hljs';

export type MarkdownMessageVariant = 'assistant' | 'tool' | 'system' | 'user';

export interface MarkdownMessageContentProps {
  text: string;
  variant?: MarkdownMessageVariant;
}

const MarkdownMessageContent: React.FC<MarkdownMessageContentProps> = ({
  text,
  variant = 'assistant',
}) => {
  const markdownStyle = useMemo(() => {
    const baseTextColor = variant === 'user' ? '#FFFFFF' : '#000000';

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
      code_inline: styles.inlineCode,
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
  }, [variant]);

  const rules = useMemo(
    () => ({
      // Fenced / block code
      fence: (node: any) => {
        const language = typeof node.lang === 'string' && node.lang.trim().length > 0
          ? node.lang.trim()
          : 'plaintext';
        const content = typeof node.content === 'string' ? node.content : '';

        return (
          <View key={node.key} style={styles.codeBlockOuter}>
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
                  style={atomOneDark as any}
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
          <View key={node.key} style={styles.codeBlockOuter}>
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
                  style={atomOneDark as any}
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
    [],
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
    backgroundColor: 'rgba(142, 142, 147, 0.16)',
    borderRadius: 3,
    paddingHorizontal: 3,
    paddingVertical: 1,
  },
  codeBlockContainer: {
    marginTop: 4,
    marginBottom: 4,
  },
  codeBlockOuter: {
    marginTop: 4,
    marginBottom: 4,
    borderRadius: 6,
    backgroundColor: 'rgba(28, 28, 30, 0.9)',
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
