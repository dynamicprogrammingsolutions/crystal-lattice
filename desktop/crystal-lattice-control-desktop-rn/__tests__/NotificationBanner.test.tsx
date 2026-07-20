/**
 * @format
 */

import React from 'react';
import ReactTestRenderer from 'react-test-renderer';

import { NotificationBanner, type NotificationVariant } from '../src/ui/NotificationBanner';

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

function renderBanner(props: {
  variant: NotificationVariant;
  title?: string;
  message?: string;
  onDismiss?: () => void;
  dismissLabel?: string;
}): ReactTestRenderer.ReactTestRenderer {
  let renderer: ReactTestRenderer.ReactTestRenderer | null = null;
  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(<NotificationBanner {...props} />);
  });
  return renderer!;
}

const VARIANTS: NotificationVariant[] = ['info', 'success', 'warning', 'error'];

describe('NotificationBanner', () => {
  test('renders title and message for each variant', () => {
    for (const variant of VARIANTS) {
      const renderer = renderBanner({
        variant,
        title: `${variant} title`,
        message: `${variant} message`,
      });
      const root = renderer.root;
      expect(hasText(root, `${variant} title`)).toBe(true);
      expect(hasText(root, `${variant} message`)).toBe(true);
    }
  });

  test('renders dismiss button when onDismiss is provided', () => {
    const onDismiss = jest.fn();
    const renderer = renderBanner({ variant: 'info', onDismiss });
    expect(() => findPressableByText(renderer.root, 'Dismiss')).not.toThrow();
  });

  test('does not render dismiss button when onDismiss is omitted', () => {
    const renderer = renderBanner({ variant: 'info' });
    expect(() => findPressableByText(renderer.root, 'Dismiss')).toThrow();
  });

  test('calls onDismiss when dismiss is pressed', () => {
    const onDismiss = jest.fn();
    const renderer = renderBanner({ variant: 'warning', onDismiss });
    const dismissPressable = findPressableByText(renderer.root, 'Dismiss');
    ReactTestRenderer.act(() => {
      dismissPressable.props.onPress();
    });
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });

  test('uses custom dismiss label', () => {
    const onDismiss = jest.fn();
    const renderer = renderBanner({
      variant: 'error',
      onDismiss,
      dismissLabel: 'Close',
    });
    expect(() => findPressableByText(renderer.root, 'Close')).not.toThrow();
  });
});