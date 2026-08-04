/**
 * @format
 */

import React from 'react';
import ReactTestRenderer from 'react-test-renderer';

import { NotificationTestingWindow } from '../src/windows/NotificationTestingWindow';

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

let renderer: ReactTestRenderer.ReactTestRenderer | null = null;

afterEach(() => {
  if (renderer) {
    ReactTestRenderer.act(() => {
      renderer!.unmount();
    });
    renderer = null;
  }
});

test('renders title, close, and four variant buttons', () => {
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(<NotificationTestingWindow />);
  });
  const root = renderer!.root;

  expect(hasText(root, 'Notification Testing')).toBe(true);
  expect(() => findPressableByText(root, 'Close')).not.toThrow();
  expect(() => findPressableByText(root, 'Show Info')).not.toThrow();
  expect(() => findPressableByText(root, 'Show Success')).not.toThrow();
  expect(() => findPressableByText(root, 'Show Warning')).not.toThrow();
  expect(() => findPressableByText(root, 'Show Error')).not.toThrow();
});

test('shows helper text when no banners are visible', () => {
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(<NotificationTestingWindow />);
  });
  const root = renderer!.root;

  expect(hasText(root, 'Press a button above to show a notification banner.')).toBe(true);
});

test('pressing a variant button shows a notification banner', () => {
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(<NotificationTestingWindow />);
  });
  const root = renderer!.root;

  expect(hasText(root, 'This is an informational notification banner.')).toBe(false);

  const infoButton = findPressableByText(root, 'Show Info');
  ReactTestRenderer.act(() => {
    infoButton.props.onPress();
  });

  expect(hasText(root, 'Info')).toBe(true);
  expect(hasText(root, 'This is an informational notification banner.')).toBe(true);
});

test('pressing multiple variant buttons shows multiple banners', () => {
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(<NotificationTestingWindow />);
  });
  const root = renderer!.root;

  const successButton = findPressableByText(root, 'Show Success');
  const warningButton = findPressableByText(root, 'Show Warning');

  ReactTestRenderer.act(() => {
    successButton.props.onPress();
  });
  ReactTestRenderer.act(() => {
    warningButton.props.onPress();
  });

  expect(hasText(root, 'The operation completed successfully.')).toBe(true);
  expect(hasText(root, 'Something needs your attention.')).toBe(true);
});

test('dismissing a banner removes it', () => {
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(<NotificationTestingWindow />);
  });
  const root = renderer!.root;

  const errorButton = findPressableByText(root, 'Show Error');
  ReactTestRenderer.act(() => {
    errorButton.props.onPress();
  });

  expect(hasText(root, 'The operation failed. Please try again.')).toBe(true);

  const dismissButton = findPressableByText(root, 'Dismiss');
  ReactTestRenderer.act(() => {
    dismissButton.props.onPress();
  });

  expect(hasText(root, 'The operation failed. Please try again.')).toBe(false);
});