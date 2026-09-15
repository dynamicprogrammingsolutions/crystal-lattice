import {
  DESKTOP_SIDEBAR_WIDTH_POLICY,
  adjustDesktopSidebarWidth,
  getDesktopSidebarWidthBounds,
  normalizeDesktopSidebarWidth,
  parsePersistedDesktopSidebarWidth,
  resolveDesktopSidebarWidth,
  serializeDesktopSidebarWidth,
} from '../src/layout/desktopSidebarWidth';

describe('desktop sidebar width policy', () => {
  it('normalizes persisted and invalid values through the policy', () => {
    expect(parsePersistedDesktopSidebarWidth(null)).toBe(
      DESKTOP_SIDEBAR_WIDTH_POLICY.defaultWidth,
    );
    expect(parsePersistedDesktopSidebarWidth('not-a-width')).toBe(
      DESKTOP_SIDEBAR_WIDTH_POLICY.defaultWidth,
    );
    expect(
      normalizeDesktopSidebarWidth(
        DESKTOP_SIDEBAR_WIDTH_POLICY.minimumWidth -
          DESKTOP_SIDEBAR_WIDTH_POLICY.adjustmentStep,
      ),
    ).toBe(DESKTOP_SIDEBAR_WIDTH_POLICY.minimumWidth);
    expect(
      parsePersistedDesktopSidebarWidth(
        String(
          DESKTOP_SIDEBAR_WIDTH_POLICY.maximumWidth +
            DESKTOP_SIDEBAR_WIDTH_POLICY.adjustmentStep,
        ),
      ),
    ).toBe(DESKTOP_SIDEBAR_WIDTH_POLICY.maximumWidth);
    expect(
      serializeDesktopSidebarWidth(DESKTOP_SIDEBAR_WIDTH_POLICY.defaultWidth),
    ).toBe(String(DESKTOP_SIDEBAR_WIDTH_POLICY.defaultWidth));
  });

  it('caps the sidebar before it consumes the protected main workspace', () => {
    const fixedShellWidth =
      DESKTOP_SIDEBAR_WIDTH_POLICY.activityRailWidth +
      DESKTOP_SIDEBAR_WIDTH_POLICY.activityPanelSeparatorWidth +
      DESKTOP_SIDEBAR_WIDTH_POLICY.resizeHandleWidth;
    const constrainedMaximum =
      DESKTOP_SIDEBAR_WIDTH_POLICY.minimumWidth +
      DESKTOP_SIDEBAR_WIDTH_POLICY.adjustmentStep;
    const shellWidth =
      fixedShellWidth +
      constrainedMaximum +
      DESKTOP_SIDEBAR_WIDTH_POLICY.minimumMainWidth;

    expect(getDesktopSidebarWidthBounds(shellWidth)).toEqual({
      minimumWidth: DESKTOP_SIDEBAR_WIDTH_POLICY.minimumWidth,
      maximumWidth: constrainedMaximum,
    });
    expect(
      resolveDesktopSidebarWidth(
        DESKTOP_SIDEBAR_WIDTH_POLICY.maximumWidth,
        shellWidth,
      ),
    ).toBe(constrainedMaximum);
  });

  it('uses deterministic bounded increment and decrement steps', () => {
    expect(
      adjustDesktopSidebarWidth(
        DESKTOP_SIDEBAR_WIDTH_POLICY.defaultWidth,
        1,
        null,
      ),
    ).toBe(
      DESKTOP_SIDEBAR_WIDTH_POLICY.defaultWidth +
        DESKTOP_SIDEBAR_WIDTH_POLICY.adjustmentStep,
    );
    expect(
      adjustDesktopSidebarWidth(
        DESKTOP_SIDEBAR_WIDTH_POLICY.minimumWidth,
        -1,
        null,
      ),
    ).toBe(DESKTOP_SIDEBAR_WIDTH_POLICY.minimumWidth);
    expect(
      adjustDesktopSidebarWidth(
        DESKTOP_SIDEBAR_WIDTH_POLICY.maximumWidth,
        1,
        null,
      ),
    ).toBe(DESKTOP_SIDEBAR_WIDTH_POLICY.maximumWidth);
  });
});
