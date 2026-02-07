import React, { useMemo } from 'react';
import { Platform, ScrollView, StyleSheet, Text, View } from 'react-native';
import Markdown from 'react-native-markdown-display';
import SyntaxHighlighter from 'react-native-syntax-highlighter';
import { atomOneDark, atomOneLight } from 'react-syntax-highlighter/styles/hljs';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

export type MarkdownRenderMode = 'markdown' | 'raw';

export type MarkdownMessageVariant = 'assistant' | 'tool' | 'system' | 'user';

export interface MarkdownMessageContentProps {
  text: string;
  renderMode?: MarkdownRenderMode;
  variant?: MarkdownMessageVariant;
}

interface MarkdownErrorBoundaryProps {
  fallback: React.ReactNode;
  children: React.ReactNode;
}

interface MarkdownErrorBoundaryState {
  hasError: boolean;
}

class MarkdownErrorBoundary extends React.PureComponent<
  MarkdownErrorBoundaryProps,
  MarkdownErrorBoundaryState
> {
  state: MarkdownErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): MarkdownErrorBoundaryState {
    return { hasError: true };
  }

  render(): React.ReactNode {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

function MarkdownMessageContent({
  text,
  renderMode = 'raw',
  variant = 'assistant',
}: MarkdownMessageContentProps): React.JSX.Element {
  const theme = useTheme();

  const baseTextColor = variant === 'user' ? theme.textOnPrimary : theme.text;

  const fallback = (
    <Text style={[styles.bodyText, { color: baseTextColor }]}>{text}</Text>
  );

  const markdownStyle = useMemo(() => {
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
  }, [baseTextColor, theme.border, theme.inlineCodeBg, theme.surfaceAlt]);

  const isDarkCodeBlock = useMemo(() => {
    // `buildDesktopTheme` currently sets `codeBlockBg` to either a dark gray or pure white.
    return theme.codeBlockBg !== '#FFFFFF';
  }, [theme.codeBlockBg]);

  const rules = useMemo(
    () => ({
      fence: (node: any) => {
        const language =
          typeof node.lang === 'string' && node.lang.trim().length > 0
            ? node.lang.trim()
            : 'plaintext';
        const content = typeof node.content === 'string' ? node.content : '';

        return (
          <View
            key={node.key}
            style={[
              styles.codeBlockOuter,
              { backgroundColor: theme.codeBlockBg, borderColor: theme.border },
            ]}
          >
            <ScrollView
              horizontal
              style={styles.codeBlockScrollHorizontal}
              contentContainerStyle={styles.codeBlockScrollHorizontalContent}
              showsHorizontalScrollIndicator
            >
              <SyntaxHighlighter
                language={language}
                style={(isDarkCodeBlock ? atomOneDark : atomOneLight) as any}
                highlighter="hljs"
                customStyle={styles.codeBlockInner}
                PreTag={View as any}
                CodeTag={Text as any}
              >
                {content}
              </SyntaxHighlighter>
            </ScrollView>
          </View>
        );
      },
      code_block: (node: any) => {
        const language =
          typeof node.lang === 'string' && node.lang.trim().length > 0
            ? node.lang.trim()
            : 'plaintext';
        const content = typeof node.content === 'string' ? node.content : '';

        return (
          <View
            key={node.key}
            style={[
              styles.codeBlockOuter,
              { backgroundColor: theme.codeBlockBg, borderColor: theme.border },
            ]}
          >
            <ScrollView
              horizontal
              style={styles.codeBlockScrollHorizontal}
              contentContainerStyle={styles.codeBlockScrollHorizontalContent}
              showsHorizontalScrollIndicator
            >
              <SyntaxHighlighter
                language={language}
                style={(isDarkCodeBlock ? atomOneDark : atomOneLight) as any}
                highlighter="hljs"
                customStyle={styles.codeBlockInner}
                PreTag={View as any}
                CodeTag={Text as any}
              >
                {content}
              </SyntaxHighlighter>
            </ScrollView>
          </View>
        );
      },
    }),
    [isDarkCodeBlock, theme.codeBlockBg],
  );

  if (renderMode !== 'markdown') {
    return fallback;
  }

  return (
    <MarkdownErrorBoundary fallback={fallback}>
      <Markdown style={markdownStyle as any} rules={rules as any}>
        {text}
      </Markdown>
    </MarkdownErrorBoundary>
  );
}

const styles = StyleSheet.create({
  bodyText: {
    fontSize: 13,
    lineHeight: 18,
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
    fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
    fontSize: 13,
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
  codeBlockScrollHorizontal: {
    paddingHorizontal: 0,
    paddingVertical: 0,
  },
  codeBlockScrollHorizontalContent: {
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  codeBlockInner: {
    backgroundColor: 'transparent',
    padding: 0,
    margin: 0,
  },
});

export default React.memo(MarkdownMessageContent);
