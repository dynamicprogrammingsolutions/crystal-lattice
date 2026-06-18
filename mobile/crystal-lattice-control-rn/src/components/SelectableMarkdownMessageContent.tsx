import React, { useCallback, useMemo } from 'react';
import { Alert, Linking, ScrollView, StyleSheet, Text, View } from 'react-native';
import { EnrichedMarkdownText, type MarkdownStyle } from 'react-native-enriched-markdown';
import SyntaxHighlighter from 'react-native-syntax-highlighter';
import * as hljsStyles from 'react-syntax-highlighter/styles/hljs';
import { useTheme } from '../theme';
import type { MarkdownMessageVariant } from './MarkdownMessageContent';
import { splitMarkdownIntoSegments, type MarkdownSegment } from './markdownSegments';

export interface SelectableMarkdownMessageContentProps {
  text: string;
  variant?: MarkdownMessageVariant;
}

interface HighlightedCodeBlockProps {
  language: string;
  content: string;
}

const HighlightedCodeBlock: React.FC<HighlightedCodeBlockProps> = ({
  language,
  content,
}) => {
  const theme = useTheme();
  const isDarkCodeBlock = theme.codeBlockBg !== '#FFFFFF';

  const codeBlockInnerStyle = useMemo(
    () => ({
      ...styles.codeBlockInner,
      fontSize: theme.typography.fontSize.code,
    }),
    [theme.typography.fontSize.code],
  );

  return (
    <View
      style={[
        styles.codeBlockOuter,
        {
          backgroundColor: theme.codeBlockBg,
          borderColor: theme.border,
        },
      ]}
      testID="selectable-markdown-code-block"
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
};

const SelectableMarkdownMessageContent: React.FC<SelectableMarkdownMessageContentProps> = ({
  text,
  variant = 'assistant',
}) => {
  const theme = useTheme();
  const segments = useMemo(() => splitMarkdownIntoSegments(text), [text]);

  const markdownStyle = useMemo<MarkdownStyle>(() => {
    const baseTextColor = variant === 'user' ? theme.textOnPrimary : theme.text;
    const messageFontSize = theme.typography.fontSize.message;
    const lineHeight = Math.round(messageFontSize * 1.35);

    const baseBlock = {
      fontFamily: 'Courier',
      fontSize: messageFontSize,
      color: baseTextColor,
      lineHeight,
      marginTop: 0,
      marginBottom: 4,
    };

    return {
      paragraph: baseBlock,
      h1: { ...baseBlock, fontWeight: '700', marginTop: 4, marginBottom: 2 },
      h2: { ...baseBlock, fontWeight: '700', marginTop: 4, marginBottom: 2 },
      h3: { ...baseBlock, fontWeight: '700', marginTop: 4, marginBottom: 2 },
      h4: { ...baseBlock, fontWeight: '700', marginTop: 4, marginBottom: 2 },
      h5: { ...baseBlock, fontWeight: '700', marginTop: 4, marginBottom: 2 },
      h6: { ...baseBlock, fontWeight: '700', marginTop: 4, marginBottom: 2 },
      strong: { fontWeight: 'bold' },
      em: { fontStyle: 'italic' },
      blockquote: {
        ...baseBlock,
        backgroundColor: theme.surfaceAlt,
        borderColor: theme.border,
        borderWidth: 4,
        gapWidth: 8,
        marginBottom: 4,
      },
      list: {
        ...baseBlock,
        bulletColor: theme.textSecondary,
        bulletSize: 5,
        markerColor: theme.textSecondary,
        markerFontWeight: '500',
        gapWidth: 8,
        marginLeft: 18,
        marginBottom: 2,
      },
      code: {
        fontFamily: 'Courier',
        fontSize: messageFontSize,
        color: baseTextColor,
        backgroundColor: theme.inlineCodeBg,
        borderColor: theme.inlineCodeBg,
      },
      codeBlock: {
        ...baseBlock,
        fontSize: theme.typography.fontSize.code,
        backgroundColor: theme.codeBlockBg,
        borderColor: theme.border,
        borderRadius: 6,
        borderWidth: 1,
        padding: 8,
      },
      link: {
        color: theme.primary,
        underline: true,
      },
    };
  }, [theme, variant]);

  const openLink = useCallback(async ({ url }: { url: string }) => {
    try {
      await Linking.openURL(url);
    } catch (err) {
      console.log('Failed to open markdown link', err);
      Alert.alert('Unable to open link', url);
    }
  }, []);

  const renderSegment = (segment: MarkdownSegment, index: number) => {
    if (segment.type === 'code') {
      return (
        <HighlightedCodeBlock
          key={`code-${index}`}
          language={segment.language}
          content={segment.content}
        />
      );
    }

    return (
      <EnrichedMarkdownText
        key={`markdown-${index}`}
        markdown={segment.markdown}
        markdownStyle={markdownStyle}
        onLinkPress={openLink}
        selectable
        flavor="commonmark"
        md4cFlags={{ underline: false, latexMath: false }}
        testID="selectable-markdown-prose"
      />
    );
  };

  return <View>{segments.map(renderSegment)}</View>;
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

export default React.memo(SelectableMarkdownMessageContent);