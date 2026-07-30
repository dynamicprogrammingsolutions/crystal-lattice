/**
 * @format
 */

import React from 'react';
import ReactTestRenderer from 'react-test-renderer';

import { SnapshotReadonlyBanner } from '../src/chat/SnapshotReadonlyBanner';

function findPressableByText(
  root: ReactTestRenderer.ReactTestInstance,
  text: string,
): ReactTestRenderer.ReactTestInstance {
  const all = root.findAll((node: any) => typeof node.props?.onPress === 'function');
  for (const node of all) {
    const texts = (node as ReactTestRenderer.ReactTestInstance).findAll(
      (n: any) =>
        typeof n === 'object' &&
        n !== null &&
        n.children?.some?.((c: any) => typeof c === 'string' && c === text),
    );
    if (texts.length > 0) {
      return node as ReactTestRenderer.ReactTestInstance;
    }
  }
  throw new Error(`No pressable with text "${text}" found`);
}

function hasText(
  root: ReactTestRenderer.ReactTestInstance,
  text: string,
): boolean {
  const all = root.findAll((node: any) => typeof node === 'object' && node !== null);
  for (const node of all) {
    const children = (node as ReactTestRenderer.ReactTestInstance).children ?? [];
    if (children.some((c: any) => typeof c === 'string' && c.includes(text))) {
      return true;
    }
  }
  return false;
}

test('renders snapshot id and read-only label with a Live button', () => {
  const onClear = jest.fn();
  let renderer: ReactTestRenderer.ReactTestRenderer | null = null;
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <SnapshotReadonlyBanner snapshotId="snap-1" onClear={onClear} />,
    );
  });
  const root = renderer!.root;

  expect(hasText(root, 'Viewing snapshot')).toBe(true);
  expect(hasText(root, 'snap-1')).toBe(true);
  expect(hasText(root, 'Read-only')).toBe(true);
  expect(() => findPressableByText(root, 'Live')).not.toThrow();
});

test('calls onClear when Live is pressed', () => {
  const onClear = jest.fn();
  let renderer: ReactTestRenderer.ReactTestRenderer | null = null;
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <SnapshotReadonlyBanner snapshotId="snap-1" onClear={onClear} />,
    );
  });
  const root = renderer!.root;

  const livePressable = findPressableByText(root, 'Live');

  ReactTestRenderer.act(() => {
    livePressable.props.onPress();
  });

  expect(onClear).toHaveBeenCalledTimes(1);
});

test('disables the Live button when disabled prop is true', () => {
  const onClear = jest.fn();
  let renderer: ReactTestRenderer.ReactTestRenderer | null = null;
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <SnapshotReadonlyBanner snapshotId="snap-1" onClear={onClear} disabled />,
    );
  });
  const root = renderer!.root;

  const livePressable = findPressableByText(root, 'Live');
  expect(livePressable.props.disabled).toBe(true);
});