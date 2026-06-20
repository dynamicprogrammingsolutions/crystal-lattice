import React, { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, type TextStyle, View } from 'react-native';
import {
  SelectableCodeBlockView,
  type SelectableCodeToken,
} from '@ferenci84/react-native-selectable-code-block';
import Icon from 'react-native-vector-icons/Feather';
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

function colorValueToString(value: TextStyle['color']): string | undefined {
  return typeof value === 'string' ? value : undefined;
}

function codeTokenToSelectableToken(token: CodeToken): SelectableCodeToken {
  const style = token.style || {};

  return {
    text: token.text,
    color: colorValueToString(style.color),
    backgroundColor: colorValueToString(style.backgroundColor),
    fontWeight: typeof style.fontWeight === 'string' ? style.fontWeight : undefined,
    fontStyle: style.fontStyle,
    textDecorationLine: style.textDecorationLine,
  };
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
  const [wrapLines, setWrapLines] = useState(false);
  const isDarkCodeBlock = theme.codeBlockBg !== '#FFFFFF';
  const stylesheet = useMemo(() => getHighlightStyle(isDarkCodeBlock), [isDarkCodeBlock]);
  const tokens = useMemo(() => tokenizeCode(code, language, stylesheet), [code, language, stylesheet]);
  const selectableTokens = useMemo(
    () => tokens.map(codeTokenToSelectableToken),
    [tokens],
  );
  const lineHeight = Math.round(theme.typography.fontSize.code * 1.25);
  const baseCodeColor = colorValueToString(stylesheet.hljs?.color) || theme.text;
  const selectableCodeBlock = (
    <SelectableCodeBlockView
      tokens={selectableTokens}
      fontFamily="Courier"
      fontSize={theme.typography.fontSize.code}
      lineHeight={lineHeight}
      color={baseCodeColor}
      wrapLines={wrapLines}
      menuOptions={['Copy']}
      style={StyleSheet.flatten([
        styles.selectableTextContainer,
        wrapLines && styles.selectableTextContainerWrapped,
      ])}
    />
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
      <View style={[styles.codeBlockToolbar, { borderBottomColor: theme.border }]}>
        <Pressable
          accessibilityLabel={wrapLines ? 'Disable line wrapping' : 'Enable line wrapping'}
          accessibilityRole="button"
          accessibilityState={{ selected: wrapLines }}
          hitSlop={8}
          onPress={() => setWrapLines((current) => !current)}
          style={[
            styles.wrapButton,
            {
              backgroundColor: wrapLines ? theme.primary : theme.surfaceAlt,
              borderColor: wrapLines ? theme.primary : theme.border,
            },
          ]}
        >
          <Icon
            name="align-left"
            size={15}
            color={wrapLines ? theme.textOnPrimary : theme.text}
          />
        </Pressable>
      </View>
      <ScrollView
        style={styles.codeBlockScrollVertical}
        contentContainerStyle={styles.codeBlockScrollVerticalContent}
        nestedScrollEnabled
      >
        {wrapLines ? (
          <View style={styles.codeBlockWrappedContent}>
            {selectableCodeBlock}
          </View>
        ) : (
          <ScrollView
            horizontal
            style={styles.codeBlockScrollHorizontal}
            contentContainerStyle={styles.codeBlockScrollHorizontalContent}
            showsHorizontalScrollIndicator
          >
            {selectableCodeBlock}
          </ScrollView>
        )}
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
  codeBlockToolbar: {
    alignItems: 'center',
    borderBottomWidth: StyleSheet.hairlineWidth,
    flexDirection: 'row',
    justifyContent: 'flex-end',
    minHeight: 32,
    paddingHorizontal: 6,
  },
  wrapButton: {
    alignItems: 'center',
    borderRadius: 6,
    borderWidth: StyleSheet.hairlineWidth,
    height: 24,
    justifyContent: 'center',
    width: 28,
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
  codeBlockWrappedContent: {
    paddingHorizontal: 8,
    paddingVertical: 6,
  },
  selectableTextContainer: {
    flexShrink: 0,
  },
  selectableTextContainerWrapped: {
    flexShrink: 1,
    width: '100%',
  },
});

export default React.memo(SelectableCodeBlock);