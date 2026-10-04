import React, { useMemo } from 'react';
import { Platform, StyleSheet, Text, View } from 'react-native';
import Markdown from 'react-native-markdown-display';
import {
  atomOneDark,
  atomOneLight,
} from 'react-syntax-highlighter/dist/cjs/styles/hljs';

import {
  deriveMarkdownTypography,
  useMarkdownDisplayPreferences,
  useTheme,
  type MarkdownDisplayPreferences,
} from '@crystal-lattice/frontend-rn-components';

import SyntaxHighlighter from './NativeSyntaxHighlighter';

export type MarkdownMessageVariant = 'assistant' | 'tool' | 'system' | 'user';

export interface MarkdownMessageContentProps {
  text: string;
  variant?: MarkdownMessageVariant;
}

export function createDesktopMarkdownTypographyStyles(
  preferences: Pick<
    MarkdownDisplayPreferences,
    'baseFontSize' | 'headerSize'
  >,
) {
  const typography = deriveMarkdownTypography(preferences);
  const textStyle = {
    fontSize: typography.body,
    lineHeight: typography.bodyLineHeight,
  };
  const headingStyle = (fontSize: number, lineHeight: number) => ({
    fontSize,
    lineHeight,
    fontWeight: '700' as const,
    marginTop: 4,
    marginBottom: 2,
  });
  return {
    text: textStyle,
    heading1: headingStyle(typography.h1, typography.h1LineHeight),
    heading2: headingStyle(typography.h2, typography.h2LineHeight),
    heading3: headingStyle(typography.h3, typography.h3LineHeight),
    heading4: headingStyle(typography.h4, typography.h4LineHeight),
    heading5: headingStyle(typography.h5, typography.h5LineHeight),
    heading6: headingStyle(typography.h6, typography.h6LineHeight),
  };
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

interface MarkdownErrorBoundaryProps {
  fallback: React.ReactNode;
  children: React.ReactNode;
}

interface MarkdownErrorBoundaryState {
  hasError: boolean;
}

function SelectableCodeText(props: any): React.JSX.Element {
  return (
    <Text
      {...props}
      style={[props.style, styles.selectableCodeText]}
      selectable
      accessibilityLabel="Markdown code block"
      testID="desktop-markdown-code-block"
    />
  );
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
  variant = 'assistant',
}: MarkdownMessageContentProps): React.JSX.Element {
  const theme = useTheme();
  const { preferences } = useMarkdownDisplayPreferences();
  const typographyStyles = useMemo(
    () => createDesktopMarkdownTypographyStyles(preferences),
    [preferences],
  );

  const baseTextColor = variant === 'user' ? theme.bubbleUserText : theme.text;

  const fallback = (
    <Text style={[typographyStyles.text, { color: baseTextColor }]}>{text}</Text>
  );

  const markdownStyle = useMemo(() => {
    return {
      body: {
        ...typographyStyles.text,
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
      heading1: typographyStyles.heading1,
      heading2: typographyStyles.heading2,
      heading3: typographyStyles.heading3,
      heading4: typographyStyles.heading4,
      heading5: typographyStyles.heading5,
      heading6: typographyStyles.heading6,
    } as const;
  }, [
    baseTextColor,
    theme.border,
    theme.inlineCodeBg,
    theme.surfaceAlt,
    theme.typography.fontSize.code,
    theme.typography.lineHeight.code,
    typographyStyles,
  ]);

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
            accessible
            accessibilityLabel="Markdown code block"
            testID="desktop-markdown-code-block"
            style={[
              styles.codeBlockOuter,
              { backgroundColor: theme.codeBlockBg, borderColor: theme.border },
            ]}
          >
            <SyntaxHighlighter
              language={language}
              style={(isDarkCodeBlock ? atomOneDark : atomOneLight) as any}
              highlighter="hljs"
              fontFamily="Menlo"
              fontSize={theme.typography.fontSize.code}
              lineHeight={theme.typography.lineHeight.code}
              customStyle={styles.codeBlockInner}
              PreTag={View as any}
              CodeTag={SelectableCodeText as any}
            >
              {content}
            </SyntaxHighlighter>
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
            accessible
            accessibilityLabel="Markdown code block"
            testID="desktop-markdown-code-block"
            style={[
              styles.codeBlockOuter,
              { backgroundColor: theme.codeBlockBg, borderColor: theme.border },
            ]}
          >
            <SyntaxHighlighter
              language={language}
              style={(isDarkCodeBlock ? atomOneDark : atomOneLight) as any}
              highlighter="hljs"
              fontFamily="Menlo"
              fontSize={theme.typography.fontSize.code}
              lineHeight={theme.typography.lineHeight.code}
              customStyle={styles.codeBlockInner}
              PreTag={View as any}
              CodeTag={SelectableCodeText as any}
            >
              {content}
            </SyntaxHighlighter>
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
                backgroundColor: theme.inlineCodeBg,
                color: baseTextColor,
                fontSize: theme.typography.fontSize.code,
                lineHeight: theme.typography.lineHeight.code,
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
      baseTextColor,
      isDarkCodeBlock,
      theme.border,
      theme.codeBlockBg,
      theme.inlineCodeBg,
      theme.typography.fontSize.code,
      theme.typography.lineHeight.code,
    ],
  );

  return (
    <MarkdownErrorBoundary fallback={fallback}>
      <Markdown style={markdownStyle as any} rules={rules as any}>
        {text}
      </Markdown>
    </MarkdownErrorBoundary>
  );
}

const styles = StyleSheet.create({
  list: {
    marginVertical: 2,
  },
  listItem: {
    flexDirection: 'row',
  },
  inlineCode: {
    fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
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
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
  codeBlockInner: {
    backgroundColor: 'transparent',
    padding: 0,
    margin: 0,
    alignSelf: 'stretch',
  },
  selectableCodeText: {
    flexShrink: 1,
  },
});

export default React.memo(MarkdownMessageContent);
