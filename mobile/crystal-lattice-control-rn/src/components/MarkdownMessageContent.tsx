import React, { useMemo } from 'react';
import { StyleSheet, Text } from 'react-native';
import Markdown from 'react-native-markdown-display';
import {
  deriveMarkdownTypography,
  useMarkdownDisplayPreferences,
  type CodeBlockRendererId,
} from '@crystal-lattice/frontend-rn-components';
import { useTheme } from '../theme';
import ConfiguredCodeBlock from './ConfiguredCodeBlock';

export type MarkdownMessageVariant = 'assistant' | 'tool' | 'system' | 'user';

export interface MarkdownMessageContentProps {
  text: string;
  variant?: MarkdownMessageVariant;
  codeBlockRenderer?: CodeBlockRendererId;
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
  codeBlockRenderer = 'syntax-highlighter',
}) => {
  const theme = useTheme();
  const { preferences } = useMarkdownDisplayPreferences();

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

  const rules = useMemo(
    () => ({
      // Fenced / block code
      fence: (node: any) => {
        const language = typeof node.lang === 'string' && node.lang.trim().length > 0
          ? node.lang.trim()
          : 'plaintext';
        const content = typeof node.content === 'string' ? node.content : '';

        return (
          <ConfiguredCodeBlock
            key={node.key}
            renderer={codeBlockRenderer}
            language={language}
            code={content}
          />
        );
      },
      code_block: (node: any) => {
        // Some markdown variants may emit `code_block` instead of `fence`.
        const language = typeof node.lang === 'string' && node.lang.trim().length > 0
          ? node.lang.trim()
          : 'plaintext';
        const content = typeof node.content === 'string' ? node.content : '';

        return (
          <ConfiguredCodeBlock
            key={node.key}
            renderer={codeBlockRenderer}
            language={language}
            code={content}
          />
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
      codeBlockRenderer,
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
});

export default React.memo(MarkdownMessageContent);
