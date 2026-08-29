import React, { useMemo } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import Markdown from 'react-native-markdown-display';
import SyntaxHighlighter from 'react-native-syntax-highlighter';
import * as hljsStyles from 'react-syntax-highlighter/styles/hljs';
import {
  deriveMarkdownTypography,
  useMarkdownDisplayPreferences,
} from '@crystal-lattice/frontend-rn-components';
import { useTheme } from '../theme';

export type MarkdownMessageVariant = 'assistant' | 'tool' | 'system' | 'user';

export interface MarkdownMessageContentProps {
  text: string;
  variant?: MarkdownMessageVariant;
}

function inlineCodeText(node: any, children: any): string {
  if (typeof node?.content === 'string') {
    return node.content;
  }
  if (typeof children === 'string') {
    return children;
  }
  if (Array.isArray(children)) {
    return children
      .map((child) => {
        if (typeof child === 'string') {
          return child;
        }
        return typeof child?.props?.children === 'string' ? child.props.children : '';
      })
      .join('');
  }
  return '';
}

const MarkdownMessageContent: React.FC<MarkdownMessageContentProps> = ({
  text,
  variant = 'assistant',
}) => {
  const theme = useTheme();
  const { preferences } = useMarkdownDisplayPreferences();

  const isDarkCodeBlock = useMemo(() => {
    return theme.codeBlockBg !== '#FFFFFF';
  }, [theme.codeBlockBg]);

  const markdownStyle = useMemo(() => {
    const baseTextColor = variant === 'user' ? theme.textOnPrimary : theme.text;
    const typography = deriveMarkdownTypography(preferences);
    const messageFontSize = typography.body;
    const headingStyle = (fontSize: number, lineHeight: number) => ({
      ...styles.heading,
      fontSize,
      lineHeight,
    });

    return {
      body: {
        ...styles.bodyText,
        fontSize: messageFontSize,
        lineHeight: typography.bodyLineHeight,
        color: baseTextColor,
      },
      text: {
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
        fontSize: theme.typography.fontSize.code,
        lineHeight: theme.typography.lineHeight.code,
        backgroundColor: theme.inlineCodeBg,
      },
      code_block: styles.codeBlockContainer,
      fence: styles.codeBlockContainer,
      bullet_list: styles.list,
      ordered_list: styles.list,
      list_item: styles.listItem,
      heading1: headingStyle(typography.h1, typography.h1LineHeight),
      heading2: headingStyle(typography.h2, typography.h2LineHeight),
      heading3: headingStyle(typography.h3, typography.h3LineHeight),
      heading4: headingStyle(typography.h4, typography.h4LineHeight),
      heading5: headingStyle(typography.h5, typography.h5LineHeight),
      heading6: headingStyle(typography.h6, typography.h6LineHeight),
    } as const;
  }, [preferences, variant, theme]);

  const codeBlockInnerStyle = useMemo(
    () => ({
      ...styles.codeBlockInner,
      fontSize: theme.typography.fontSize.code,
    }),
    [theme.typography.fontSize.code],
  );

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
                  customStyle={codeBlockInnerStyle}
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
                  customStyle={codeBlockInnerStyle}
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
      code_inline: (node: any, children: any) => {
        const content = inlineCodeText(node, children);
        return (
          <Text
            key={node.key}
            style={[
              styles.inlineCode,
              {
                fontSize: theme.typography.fontSize.code,
                lineHeight: theme.typography.lineHeight.code,
                backgroundColor: theme.inlineCodeBg,
                color: variant === 'user' ? theme.textOnPrimary : theme.text,
              },
            ]}
            selectable
          >
            {content}
          </Text>
        );
      },
    }),
    [
      codeBlockInnerStyle,
      isDarkCodeBlock,
      theme.border,
      theme.codeBlockBg,
      theme.inlineCodeBg,
      theme.text,
      theme.textOnPrimary,
      theme.typography.fontSize.code,
      theme.typography.lineHeight.code,
      preferences,
      variant,
    ],
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
