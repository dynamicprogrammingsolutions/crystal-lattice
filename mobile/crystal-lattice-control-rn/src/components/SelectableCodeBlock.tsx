import Clipboard from '@react-native-clipboard/clipboard';
import React, { useCallback, useMemo } from 'react';
import { ScrollView, StyleSheet, Text, type TextStyle, View } from 'react-native';
import { SelectableTextView } from '@rob117/react-native-selectable-text';
import lowlight from 'lowlight';
import * as hljsStyles from 'react-syntax-highlighter/styles/hljs';
import { useTheme } from '../theme';
import type { MarkdownMessageVariant } from './MarkdownMessageContent';

type LowlightNode = {
  type: 'text' | 'element';
  value?: string;
  properties?: {
    className?: string[];
  };
  children?: LowlightNode[];
};

export type CodeToken = {
  text: string;
  style?: TextStyle;
};

export interface SelectableCodeBlockProps {
  code: string;
  language?: string;
  variant?: MarkdownMessageVariant;
}

function normalizeLanguage(language?: string): string {
  return (language || 'plaintext').trim().toLowerCase() || 'plaintext';
}

function isPlainTextLanguage(language: string): boolean {
  return ['text', 'txt', 'plain', 'plaintext'].includes(language);
}

function getHighlightStyle(isDarkCodeBlock: boolean): Record<string, TextStyle> {
  const styleSet = isDarkCodeBlock
    ? (hljsStyles as any).atomOneDark
    : (hljsStyles as any).atomOneLight;

  return (styleSet?.default || styleSet || {}) as Record<string, TextStyle>;
}

function styleForClassNames(
  classNames: string[],
  stylesheet: Record<string, TextStyle>,
): TextStyle | undefined {
  const style = classNames.reduce<TextStyle>((combinedStyle, className) => {
    return {
      ...combinedStyle,
      ...(stylesheet[className] || {}),
    };
  }, {});

  return Object.keys(style).length > 0 ? style : undefined;
}

function appendToken(tokens: CodeToken[], token: CodeToken) {
  if (!token.text) {
    return;
  }

  const previous = tokens[tokens.length - 1];
  if (previous && JSON.stringify(previous.style || {}) === JSON.stringify(token.style || {})) {
    previous.text += token.text;
    return;
  }

  tokens.push(token);
}

function flattenLowlightNodes(
  nodes: LowlightNode[],
  stylesheet: Record<string, TextStyle>,
  inheritedClassNames: string[] = [],
): CodeToken[] {
  return nodes.flatMap((node) => {
    if (node.type === 'text') {
      return [
        {
          text: node.value || '',
          style: styleForClassNames(inheritedClassNames, stylesheet),
        },
      ];
    }

    const classNames = node.properties?.className || [];
    return flattenLowlightNodes(
      node.children || [],
      stylesheet,
      inheritedClassNames.concat(classNames),
    );
  });
}

export function tokenizeCode(
  code: string,
  language: string | undefined,
  stylesheet: Record<string, TextStyle>,
): CodeToken[] {
  const normalizedLanguage = normalizeLanguage(language);

  if (!code) {
    return [];
  }

  if (isPlainTextLanguage(normalizedLanguage)) {
    return [{ text: code }];
  }

  try {
    const result = lowlight.getLanguage(normalizedLanguage)
      ? lowlight.highlight(normalizedLanguage, code)
      : lowlight.highlightAuto(code);
    const tokens = flattenLowlightNodes(result.value || [], stylesheet);
    const mergedTokens: CodeToken[] = [];
    tokens.forEach((token) => appendToken(mergedTokens, token));
    return mergedTokens.length > 0 ? mergedTokens : [{ text: code }];
  } catch {
    return [{ text: code }];
  }
}

const SelectableCodeBlock: React.FC<SelectableCodeBlockProps> = ({
  code,
  language,
}) => {
  const theme = useTheme();
  const isDarkCodeBlock = theme.codeBlockBg !== '#FFFFFF';
  const stylesheet = useMemo(() => getHighlightStyle(isDarkCodeBlock), [isDarkCodeBlock]);
  const tokens = useMemo(() => tokenizeCode(code, language, stylesheet), [code, language, stylesheet]);
  const lineHeight = Math.round(theme.typography.fontSize.code * 1.25);
  const baseCodeColor = stylesheet.hljs?.color || theme.text;

  const handleSelection = useCallback((event: { chosenOption: string; highlightedText: string }) => {
    if (event.chosenOption === 'Copy' && event.highlightedText) {
      Clipboard.setString(event.highlightedText);
    }
  }, []);

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
          <SelectableTextView
            menuOptions={['Copy']}
            onSelection={handleSelection}
            style={styles.selectableTextContainer}
          >
            <Text
              style={[
                styles.codeText,
                {
                  color: baseCodeColor,
                  fontSize: theme.typography.fontSize.code,
                  lineHeight,
                },
              ]}
            >
              {tokens.map((token, index) => (
                <Text
                  key={`${index}-${token.text.length}`}
                  style={token.style}
                >
                  {token.text}
                </Text>
              ))}
            </Text>
          </SelectableTextView>
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
  selectableTextContainer: {
    flexShrink: 0,
  },
  codeText: {
    fontFamily: 'Courier',
  },
});

export default React.memo(SelectableCodeBlock);