import React from 'react';
import TestRenderer from 'react-test-renderer';
import Clipboard from '@react-native-clipboard/clipboard';
import { Text } from 'react-native';
import SelectableCodeBlock, { tokenizeCode } from '../src/components/SelectableCodeBlock';

const tokenStyle = {
  'hljs-keyword': { color: '#ff0000' },
  'hljs-number': { color: '#00ff00' },
};

function collectText(children: unknown): string {
  if (typeof children === 'string') {
    return children;
  }

  if (Array.isArray(children)) {
    return children.map(collectText).join('');
  }

  if (React.isValidElement(children)) {
    return collectText((children.props as { children?: unknown }).children);
  }

  return '';
}

test('tokenizeCode highlights known languages', () => {
  const tokens = tokenizeCode('const value = 1;\n', 'ts', tokenStyle);

  expect(tokens.map((token) => token.text).join('')).toBe('const value = 1;\n');
  expect(tokens).toEqual(
    expect.arrayContaining([
      expect.objectContaining({
        text: 'const',
        style: { color: '#ff0000' },
      }),
      expect.objectContaining({
        text: '1',
        style: { color: '#00ff00' },
      }),
    ]),
  );
});

test('tokenizeCode preserves empty and plain text code exactly', () => {
  expect(tokenizeCode('', 'ts', tokenStyle)).toEqual([]);

  const code = '  value\t=\t1;\n\n';
  expect(tokenizeCode(code, 'plaintext', tokenStyle)).toEqual([{ text: code }]);
});

test('tokenizeCode falls back for unknown languages while preserving text', () => {
  const code = '  value\t=\t1;\nnext();\n';
  const tokens = tokenizeCode(code, 'not-a-real-language', tokenStyle);

  expect(tokens.map((token) => token.text).join('')).toBe(code);
});

test('SelectableCodeBlock renders selectable highlighted spans and copies selected text', () => {
  let renderer: TestRenderer.ReactTestRenderer;
  TestRenderer.act(() => {
    renderer = TestRenderer.create(
      <SelectableCodeBlock
        code={'const value = 1;\n'}
        language="ts"
      />,
    );
  });

  const selectableTextView = renderer!.root.find((node) => String(node.type) === 'SelectableTextView');
  const textNodes = renderer!.root.findAllByType(Text);

  expect(selectableTextView.props.menuOptions).toEqual(['Copy']);
  expect(textNodes.map((node) => collectText(node.props.children)).join('')).toContain('const value = 1;\n');

  TestRenderer.act(() => {
    selectableTextView.props.onSelection({
      chosenOption: 'Copy',
      highlightedText: 'value',
    });
  });

  expect(Clipboard.setString).toHaveBeenCalledWith('value');
});