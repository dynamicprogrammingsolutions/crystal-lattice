import React, { useCallback, useMemo } from 'react';
import { Alert, Linking, ScrollView, StyleSheet, Text, View } from 'react-native';
import { EnrichedMarkdownText, type MarkdownStyle } from 'react-native-enriched-markdown';
import SyntaxHighlighter from 'react-native-syntax-highlighter';
import * as hljsStyles from 'react-syntax-highlighter/styles/hljs';
import {
  deriveMarkdownTypography,
  useMarkdownDisplayPreferences,
} from '@crystal-lattice/frontend-rn-components';
import { useTheme } from '../theme';
import type { MarkdownMessageVariant } from './MarkdownMessageContent';
import SelectableCodeBlock from './SelectableCodeBlock';
import { splitMarkdownIntoSegments, type MarkdownSegment } from './markdownSegments';

type CodeBlockRenderingMode =
  | 'syntax-highlighter'
  | 'enriched-markdown'
  | 'selectable-code-block';

const CODE_BLOCK_RENDERING_MODE: CodeBlockRenderingMode = 'selectable-code-block';

function getCodeBlockRenderingMode(): CodeBlockRenderingMode {
  return CODE_BLOCK_RENDERING_MODE;
}

const LIST_STYLE_TUNING = {
  marginTop: 2,
  marginBottom: 2,
  bulletSize: 3,
  // Shared fallback values kept for compatibility with the upstream list style.
  gapWidth: 10,
  marginLeft: 37,
  markerFontWeight: 'normal',
  // Fork-only list controls. Marker margin is leading/start-side space before the marker.
  unorderedGapWidth: 15,
  unorderedMarginLeft: 30,
  unorderedMarkerMarginBefore: 10,
  orderedGapWidth: 10,
  orderedMarginLeft: 27,
  orderedMarkerMarginBefore: 0,
} as const;

export interface SelectableMarkdownMessageContentProps {
  text: string;
  variant?: MarkdownMessageVariant;
}

interface SyntaxHighlightedCodeBlockProps {
  language: string;
  code: string;
}

const SyntaxHighlightedCodeBlock: React.FC<SyntaxHighlightedCodeBlockProps> = ({
  language,
  code,
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
          {code}
        </SyntaxHighlighter>
      </ScrollView>
    </View>
  );
};

const SelectableMarkdownMessageContent: React.FC<SelectableMarkdownMessageContentProps> = ({
  text,
  variant,
}) => {
  const theme = useTheme();
  const { preferences } = useMarkdownDisplayPreferences();
  const codeBlockRenderingMode = getCodeBlockRenderingMode();
  const displayPreferenceKey =
    `${preferences.baseFontSize}:${preferences.headerSize}`;
  const segments = useMemo<MarkdownSegment[]>(() => {
    if (codeBlockRenderingMode !== 'enriched-markdown') {
      return splitMarkdownIntoSegments(text);
    }

    return text ? [{ type: 'markdown', markdown: text }] : [];
  }, [codeBlockRenderingMode, text]);

  const markdownStyle = useMemo<MarkdownStyle>(() => {
    const baseTextColor = theme.text;
    const typography = deriveMarkdownTypography(preferences);
    const messageFontSize = typography.body;

    const baseTextBlock = {
      fontSize: messageFontSize,
      lineHeight: typography.bodyLineHeight,
      color: baseTextColor,
    };

    const headingBase = {
      color: baseTextColor,
      fontWeight: '700',
      marginTop: 4,
      marginBottom: 2,
    } as const;

    return {
      paragraph: {
        ...baseTextBlock,
        marginTop: 10,
        marginBottom: 10,
      },
      h1: { ...headingBase, fontSize: typography.h1, lineHeight: typography.h1LineHeight },
      h2: { ...headingBase, fontSize: typography.h2, lineHeight: typography.h2LineHeight },
      h3: { ...headingBase, fontSize: typography.h3, lineHeight: typography.h3LineHeight },
      h4: { ...headingBase, fontSize: typography.h4, lineHeight: typography.h4LineHeight },
      h5: { ...headingBase, fontSize: typography.h5, lineHeight: typography.h5LineHeight },
      h6: { ...headingBase, fontSize: typography.h6, lineHeight: typography.h6LineHeight },
      strong: {
        fontWeight: 'bold',
      },
      em: {
        fontStyle: 'italic',
      },
      blockquote: {
        ...baseTextBlock,
        marginTop: 0,
        marginBottom: 10,
        backgroundColor: theme.surfaceAlt,
        borderColor: theme.border,
        borderWidth: 4,
        gapWidth: 8,
      },
      list: {
        ...baseTextBlock,
        fontFamily: '',
        fontWeight: '',
        marginTop: LIST_STYLE_TUNING.marginTop,
        marginBottom: LIST_STYLE_TUNING.marginBottom,
        bulletColor: baseTextColor,
        bulletSize: LIST_STYLE_TUNING.bulletSize,
        markerColor: baseTextColor,
        markerFontWeight: LIST_STYLE_TUNING.markerFontWeight,
        gapWidth: LIST_STYLE_TUNING.gapWidth,
        marginLeft: LIST_STYLE_TUNING.marginLeft,
        unorderedGapWidth: LIST_STYLE_TUNING.unorderedGapWidth,
        unorderedMarginLeft: LIST_STYLE_TUNING.unorderedMarginLeft,
        unorderedMarkerMarginBefore: LIST_STYLE_TUNING.unorderedMarkerMarginBefore,
        orderedGapWidth: LIST_STYLE_TUNING.orderedGapWidth,
        orderedMarginLeft: LIST_STYLE_TUNING.orderedMarginLeft,
        orderedMarkerMarginBefore: LIST_STYLE_TUNING.orderedMarkerMarginBefore,
      },
      taskList: {
        checkedColor: theme.primary,
        borderColor: theme.border,
        checkmarkColor: theme.textOnPrimary,
        checkedTextColor: baseTextColor,
        checkedStrikethrough: false,
      },
      table: {
        ...baseTextBlock,
        fontFamily: '',
        fontWeight: '',
        marginTop: 8,
        marginBottom: 12,
        headerFontFamily: '',
        headerBackgroundColor: theme.surfaceAlt,
        headerTextColor: baseTextColor,
        rowEvenBackgroundColor: theme.surface,
        rowOddBackgroundColor: theme.surfaceAlt,
        borderColor: theme.border,
        borderWidth: 1,
        borderRadius: 6,
        cellPaddingHorizontal: 10,
        cellPaddingVertical: 7,
      },
      code: {
        fontFamily: 'Courier',
        fontSize: theme.typography.fontSize.code,
        lineHeight: theme.typography.lineHeight.code,
        color: baseTextColor,
        backgroundColor: theme.inlineCodeBg,
        borderColor: theme.border,
      },
      codeBlock: {
        fontFamily: 'Courier',
        fontSize: theme.typography.fontSize.code,
        lineHeight: theme.typography.lineHeight.code,
        color: baseTextColor,
        marginTop: 4,
        marginBottom: 4,
        backgroundColor: theme.codeBlockBg,
        borderColor: theme.border,
        borderRadius: 6,
        borderWidth: 1,
        padding: 8,
      },
      link: {
        color: baseTextColor,
        underline: true,
      },
    };
  }, [preferences, theme]);

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
      if (codeBlockRenderingMode === 'syntax-highlighter') {
        return (
          <SyntaxHighlightedCodeBlock
            key={`code-${index}`}
            language={segment.language}
            code={segment.content}
          />
        );
      }

      if (codeBlockRenderingMode === 'selectable-code-block') {
        return (
          <SelectableCodeBlock
            key={`code-${index}`}
            language={segment.language}
            code={segment.content}
            variant={variant}
          />
        );
      }

      return null;
    }

    return (
      <EnrichedMarkdownText
        key={`markdown-${displayPreferenceKey}-${index}`}
        markdown={segment.markdown}
        markdownStyle={markdownStyle}
        onLinkPress={openLink}
        selectable
        flavor="github"
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
