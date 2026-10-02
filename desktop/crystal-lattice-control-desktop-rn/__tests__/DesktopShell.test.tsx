import React from 'react';
import { StyleSheet, Text, type LayoutRectangle } from 'react-native';
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react-native';

import type { KeyValueStore } from '@crystal-lattice/frontend-sdk';
import { ThemeProvider } from '@crystal-lattice/frontend-rn-components';

import { DesktopShell } from '../src/layout/DesktopShell';
import {
  DESKTOP_SIDEBAR_WIDTH_POLICY,
  DESKTOP_SIDEBAR_WIDTH_STORAGE_KEY,
  adjustDesktopSidebarWidth,
  getDesktopSidebarWidthBounds,
  serializeDesktopSidebarWidth,
} from '../src/layout/desktopSidebarWidth';
import type { MacDragEvent } from '../src/native/MacDragView';
import { buildDesktopTheme } from '../src/theme/buildDesktopTheme';

function createStore(initialWidth?: number): KeyValueStore & {
  values: Map<string, string>;
  set: jest.Mock;
} {
  const values = new Map<string, string>();
  if (initialWidth !== undefined) {
    values.set(
      DESKTOP_SIDEBAR_WIDTH_STORAGE_KEY,
      serializeDesktopSidebarWidth(initialWidth),
    );
  }
  return {
    values,
    get: jest.fn(async key => values.get(key) ?? null),
    set: jest.fn(async (key, value) => {
      values.set(key, value);
    }),
    delete: jest.fn(async key => {
      values.delete(key);
    }),
  };
}

function layout(width: number): {
  nativeEvent: { layout: LayoutRectangle };
} {
  return {
    nativeEvent: {
      layout: { x: 0, y: 0, width, height: width },
    },
  };
}

function drag(translationX: number): MacDragEvent {
  return {
    translationX,
    translationY: 0,
    locationX: 0,
    locationY: 0,
    pageX: 0,
    pageY: 0,
  };
}

function shellWidthWithUnconstrainedMaximum(): number {
  return (
    DESKTOP_SIDEBAR_WIDTH_POLICY.activityRailWidth +
    DESKTOP_SIDEBAR_WIDTH_POLICY.activityPanelSeparatorWidth +
    DESKTOP_SIDEBAR_WIDTH_POLICY.resizeHandleWidth +
    DESKTOP_SIDEBAR_WIDTH_POLICY.maximumWidth +
    DESKTOP_SIDEBAR_WIDTH_POLICY.minimumMainWidth +
    DESKTOP_SIDEBAR_WIDTH_POLICY.adjustmentStep
  );
}

function renderShell(store: KeyValueStore) {
  return render(
    <ThemeProvider theme={buildDesktopTheme(null)}>
      <DesktopShell
        sidebarWidthStore={store}
        activityRail={<Text>Rail</Text>}
        panel={<Text>Panel</Text>}
        main={<Text>Main</Text>}
      />
    </ThemeProvider>,
  );
}

function renderedSidebarWidth(): number {
  return StyleSheet.flatten(
    screen.getByTestId('desktop-sidebar-panel').props.style,
  ).width;
}

describe('DesktopShell', () => {
  it('hydrates, pointer-adjusts, persists, and restores one bounded width', async () => {
    const loadedWidth = adjustDesktopSidebarWidth(
      DESKTOP_SIDEBAR_WIDTH_POLICY.defaultWidth,
      1,
      null,
    );
    const store = createStore(loadedWidth);
    const first = renderShell(store);

    await waitFor(() => expect(renderedSidebarWidth()).toBe(loadedWidth));
    fireEvent(
      screen.getByTestId('desktop-shell'),
      'layout',
      layout(shellWidthWithUnconstrainedMaximum()),
    );

    const handle = screen.getByTestId('desktop-sidebar-resize-handle');
    const translation = DESKTOP_SIDEBAR_WIDTH_POLICY.adjustmentStep;
    fireEvent(handle, 'dragStart', drag(0));
    fireEvent(handle, 'dragMove', drag(translation));
    expect(renderedSidebarWidth()).toBe(loadedWidth + translation);
    fireEvent(handle, 'dragEnd', drag(translation));

    const persisted = serializeDesktopSidebarWidth(loadedWidth + translation);
    await waitFor(() =>
      expect(store.set).toHaveBeenLastCalledWith(
        DESKTOP_SIDEBAR_WIDTH_STORAGE_KEY,
        persisted,
      ),
    );

    first.unmount();
    renderShell(store);
    await waitFor(() => expect(renderedSidebarWidth()).toBe(Number(persisted)));
  });

  it('supports deterministic keyboard and accessibility adjustments', async () => {
    const store = createStore();
    renderShell(store);
    await act(async () => {});

    const handle = screen.getByTestId('desktop-sidebar-resize-handle');
    const wider = adjustDesktopSidebarWidth(
      DESKTOP_SIDEBAR_WIDTH_POLICY.defaultWidth,
      1,
      null,
    );
    fireEvent(handle, 'keyIncrement');
    expect(renderedSidebarWidth()).toBe(wider);

    fireEvent(handle, 'accessibilityAction', {
      nativeEvent: { actionName: 'decrement' },
    });
    expect(renderedSidebarWidth()).toBe(
      DESKTOP_SIDEBAR_WIDTH_POLICY.defaultWidth,
    );
    expect(handle.props.accessibilityRole).toBe('adjustable');
    expect(handle.props.accessibilityActions).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ name: 'decrement' }),
        expect.objectContaining({ name: 'increment' }),
      ]),
    );
    await waitFor(() =>
      expect(store.set).toHaveBeenLastCalledWith(
        DESKTOP_SIDEBAR_WIDTH_STORAGE_KEY,
        serializeDesktopSidebarWidth(DESKTOP_SIDEBAR_WIDTH_POLICY.defaultWidth),
      ),
    );
  });

  it('protects main width and renders one separator at each shell boundary', async () => {
    const store = createStore(DESKTOP_SIDEBAR_WIDTH_POLICY.maximumWidth);
    renderShell(store);
    await waitFor(() =>
      expect(renderedSidebarWidth()).toBe(
        DESKTOP_SIDEBAR_WIDTH_POLICY.maximumWidth,
      ),
    );
    const constrainedShellWidth =
      DESKTOP_SIDEBAR_WIDTH_POLICY.activityRailWidth +
      DESKTOP_SIDEBAR_WIDTH_POLICY.activityPanelSeparatorWidth +
      DESKTOP_SIDEBAR_WIDTH_POLICY.resizeHandleWidth +
      DESKTOP_SIDEBAR_WIDTH_POLICY.minimumWidth +
      DESKTOP_SIDEBAR_WIDTH_POLICY.adjustmentStep +
      DESKTOP_SIDEBAR_WIDTH_POLICY.minimumMainWidth;
    fireEvent(
      screen.getByTestId('desktop-shell'),
      'layout',
      layout(constrainedShellWidth),
    );

    const bounds = getDesktopSidebarWidthBounds(constrainedShellWidth);
    expect(renderedSidebarWidth()).toBe(bounds.maximumWidth);
    expect(
      screen.getAllByTestId('desktop-activity-panel-separator'),
    ).toHaveLength(1);
    expect(
      screen.getAllByTestId('desktop-sidebar-main-separator'),
    ).toHaveLength(1);
    expect(
      StyleSheet.flatten(
        screen.getByTestId('desktop-shell-activity-rail').props.style,
      ),
    ).not.toHaveProperty('borderLeftWidth');
    expect(
      StyleSheet.flatten(
        screen.getByTestId('desktop-sidebar-panel').props.style,
      ),
    ).not.toHaveProperty('borderTopWidth');
  });
});
