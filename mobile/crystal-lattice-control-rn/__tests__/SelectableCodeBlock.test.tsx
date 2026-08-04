import React from 'react';
import TestRenderer from 'react-test-renderer';
import { Alert } from 'react-native';
import Clipboard from '@react-native-clipboard/clipboard';
import type { SelectableCodeToken } from '@ferenci84/react-native-selectable-code-block';
import SelectableCodeBlock, { tokenizeCode } from '../src/components/SelectableCodeBlock';

const tokenStyle = {
  'hljs-keyword': { color: '#ff0000' },
  'hljs-number': { color: '#00ff00' },
};

beforeEach(() => {
  jest.clearAllMocks();
});

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

test('SelectableCodeBlock renders selectable highlighted token data', () => {
  let renderer: TestRenderer.ReactTestRenderer;
  TestRenderer.act(() => {
    renderer = TestRenderer.create(
      <SelectableCodeBlock
        code={'const value = 1;\n'}
        language="ts"
      />,
    );
  });

  const selectableCodeBlockView = renderer!.root.find(
    (node) => String(node.type) === 'SelectableCodeBlockView',
  );

  expect(selectableCodeBlockView.props.menuOptions).toEqual(['Copy']);
  expect(selectableCodeBlockView.props.fontFamily).toBe('Courier');
  expect(selectableCodeBlockView.props.style).toEqual(
    expect.objectContaining({
      flexShrink: 0,
    }),
  );
  expect(selectableCodeBlockView.props.wrapLines).toBe(false);
  expect(
    selectableCodeBlockView.props.tokens
      .map((token: SelectableCodeToken) => token.text)
      .join(''),
  ).toBe('const value = 1;\n');
  expect(selectableCodeBlockView.props.tokens[0]).toEqual(
    expect.objectContaining({ text: expect.any(String) }),
  );
});

test('SelectableCodeBlock can copy the complete raw code from the toolbar', () => {
  const alertSpy = jest.spyOn(Alert, 'alert').mockImplementation(() => {});
  const code = 'const value = 1;\n';
  let renderer: TestRenderer.ReactTestRenderer;

  TestRenderer.act(() => {
    renderer = TestRenderer.create(
      <SelectableCodeBlock
        code={code}
        language="ts"
      />,
    );
  });

  const copyButton = renderer!.root.find(
    (node) => node.props.accessibilityLabel === 'Copy code',
  );

  TestRenderer.act(() => {
    copyButton.props.onPress();
  });

  expect(Clipboard.setString).toHaveBeenCalledWith(code);
  expect(alertSpy).toHaveBeenCalledWith('Copied', 'Copied to clipboard.');
});
