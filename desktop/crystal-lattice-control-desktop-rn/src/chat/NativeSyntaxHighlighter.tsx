import React from 'react';
import {
  Platform,
  ScrollView,
  Text,
  type StyleProp,
  type TextStyle,
} from 'react-native';
import SyntaxHighlighter from 'react-syntax-highlighter/dist/cjs/default-highlight';
import { createStyleObject } from 'react-syntax-highlighter/dist/cjs/create-element';
import defaultStyle from 'react-syntax-highlighter/dist/cjs/styles/hljs/default-style';

interface SyntaxNode {
  type?: string;
  tagName?: string;
  value?: string;
  properties?: {
    className?: string[];
    style?: Record<string, unknown>;
  };
  children?: SyntaxNode[];
}

export interface NativeSyntaxHighlighterProps {
  children: string;
  language?: string;
  style?: Record<string, Record<string, unknown>>;
  fontFamily?: string;
  fontSize?: number;
  lineHeight?: number;
  customStyle?: StyleProp<TextStyle>;
  PreTag?: React.ComponentType<any>;
  CodeTag?: React.ComponentType<any>;
  highlighter?: 'hljs';
  [key: string]: unknown;
}

const styleCache = new Map<
  Record<string, Record<string, unknown>>,
  {
    transformedStyle: Record<string, Record<string, unknown>>;
    defaultColor: string;
  }
>();

const TOP_LEVEL_PROPERTIES_TO_REMOVE = [
  'color',
  'textShadow',
  'textAlign',
  'whiteSpace',
  'wordSpacing',
  'wordBreak',
  'wordWrap',
  'lineHeight',
  'MozTabSize',
  'OTabSize',
  'tabSize',
  'WebkitHyphens',
  'MozHyphens',
  'msHyphens',
  'hyphens',
  'fontFamily',
] as const;

function transformStylesheet(
  input: Record<string, Record<string, unknown>>,
) {
  const stylesheet = (Array.isArray(input) ? input[0] : input) as Record<
    string,
    Record<string, unknown>
  >;
  const cached = styleCache.get(stylesheet);
  if (cached) {
    return cached;
  }

  const transformedStyle = Object.entries(stylesheet).reduce<
    Record<string, Record<string, unknown>>
  >((nextStylesheet, [className, style]) => {
    nextStylesheet[className] = Object.entries(style).reduce<
      Record<string, unknown>
    >((nextStyle, [key, value]) => {
      if (key === 'overflowX' || key === 'overflow') {
        nextStyle.overflow = value === 'auto' ? 'scroll' : value;
      } else if (typeof value === 'string' && value.includes('em')) {
        const [number] = value.split('em');
        nextStyle[key] = Number(number) * 16;
      } else if (key === 'background') {
        nextStyle.backgroundColor = value;
      } else if (key !== 'display') {
        nextStyle[key] = value;
      }
      return nextStyle;
    }, {});
    return nextStylesheet;
  }, {});

  const topLevel = transformedStyle.hljs ?? {};
  const defaultColor =
    typeof topLevel.color === 'string' ? topLevel.color : '#000';
  TOP_LEVEL_PROPERTIES_TO_REMOVE.forEach(property => {
    delete topLevel[property];
  });
  if (topLevel.backgroundColor === 'none') {
    delete topLevel.backgroundColor;
  }

  const result = { transformedStyle, defaultColor };
  styleCache.set(stylesheet, result);
  return result;
}

function createNativeElement(options: {
  node: SyntaxNode;
  stylesheet: Record<string, Record<string, unknown>>;
  key: string;
  defaultColor: string;
  fontFamily: string;
  fontSize: number;
  lineHeight: number;
}): React.ReactNode {
  const {
    node,
    stylesheet,
    key,
    defaultColor,
    fontFamily,
    fontSize,
    lineHeight,
  } = options;
  const startingStyle = {
    fontFamily,
    fontSize,
    lineHeight,
    height: lineHeight,
  };

  if (node.type === 'text') {
    return (
      <Text key={key} style={{ color: defaultColor, ...startingStyle }}>
        {node.value}
      </Text>
    );
  }

  if (!node.tagName) {
    return null;
  }

  const style = createStyleObject(
    node.properties?.className ?? [],
    {
      color: defaultColor,
      ...(node.properties?.style ?? {}),
      ...startingStyle,
    },
    stylesheet,
  );
  const children = (node.children ?? []).map((child, index) =>
    createNativeElement({
      node: child,
      stylesheet,
      key: `${key}-${index}`,
      defaultColor:
        typeof style.color === 'string' ? style.color : defaultColor,
      fontFamily,
      fontSize,
      lineHeight,
    }),
  );

  return (
    <Text key={key} style={style}>
      {children}
    </Text>
  );
}

export default function NativeSyntaxHighlighter({
  children,
  style = defaultStyle,
  fontFamily = Platform.OS === 'ios' ? 'Menlo-Regular' : 'monospace',
  fontSize = 12,
  lineHeight = fontSize + 5,
  highlighter: _highlighter,
  ...rest
}: NativeSyntaxHighlighterProps): React.JSX.Element {
  const { transformedStyle, defaultColor } = transformStylesheet(style);
  const renderer = ({
    rows,
    stylesheet,
  }: {
    rows: SyntaxNode[];
    stylesheet: Record<string, Record<string, unknown>>;
  }) =>
    rows.map((node, index) =>
      createNativeElement({
        node,
        stylesheet,
        key: `code-segment-${index}`,
        defaultColor,
        fontFamily,
        fontSize,
        lineHeight,
      }),
    );
  const Highlighter = SyntaxHighlighter as React.ComponentType<any>;

  return (
    <Highlighter
      {...rest}
      style={transformedStyle}
      horizontal
      renderer={renderer}
      PreTag={rest.PreTag ?? ScrollView}
      CodeTag={rest.CodeTag ?? ScrollView}
    >
      {children}
    </Highlighter>
  );
}