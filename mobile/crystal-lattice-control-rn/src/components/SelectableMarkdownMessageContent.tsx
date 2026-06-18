import React, { useCallback, useMemo } from 'react';
import { Alert, Linking, ScrollView, StyleSheet, Text, View } from 'react-native';
import { EnrichedMarkdownText } from 'react-native-enriched-markdown';
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
}) => {
  const segments = useMemo(() => splitMarkdownIntoSegments(text), [text]);

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