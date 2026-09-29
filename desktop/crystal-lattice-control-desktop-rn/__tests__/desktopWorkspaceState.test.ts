import {
  INITIAL_DESKTOP_WORKSPACE_STATE,
  desktopWorkspaceReducer,
  getDesktopSessionTabKind,
  getDesktopWorkspaceTabs,
  type DesktopSessionTab,
} from '../src/tabs/desktopWorkspaceState';
import {
  parsePersistedOpenTabsState,
  serializePersistedOpenTabsState,
} from '../src/tabs/openTabsStorage';

function tab(id: string): DesktopSessionTab {
  return {
    tabId: `connection:${id}`,
    connectionId: 'connection',
    sessionId: id,
    title: id,
    subtitle: null,
  };
}

describe('desktop workspace state', () => {
  it('reports preview and permanent membership by composite identity', () => {
    const state = desktopWorkspaceReducer(
      desktopWorkspaceReducer(INITIAL_DESKTOP_WORKSPACE_STATE, {
        type: 'openPermanent',
        tab: tab('one'),
      }),
      {
        type: 'openPreview',
        tab: tab('two'),
      },
    );
    expect(getDesktopSessionTabKind(state, 'connection', 'one')).toBe(
      'permanent',
    );
    expect(getDesktopSessionTabKind(state, 'connection', 'two')).toBe(
      'preview',
    );
    expect(getDesktopSessionTabKind(state, 'other', 'one')).toBeNull();
  });

  it('keeps one preview after permanent tabs and promotes it in place', () => {
    let state = desktopWorkspaceReducer(INITIAL_DESKTOP_WORKSPACE_STATE, {
      type: 'openPermanent',
      tab: tab('one'),
    });
    state = desktopWorkspaceReducer(state, {
      type: 'openPreview',
      tab: tab('two'),
    });
    expect(getDesktopWorkspaceTabs(state).map(item => item.sessionId)).toEqual([
      'one',
      'two',
    ]);
    expect(state.previewTab?.sessionId).toBe('two');

    state = desktopWorkspaceReducer(state, {
      type: 'promotePreview',
      tabId: tab('two').tabId,
    });
    expect(state.previewTab).toBeNull();
    expect(state.permanentTabs.map(item => item.sessionId)).toEqual([
      'one',
      'two',
    ]);
    expect(state.activeWorkspace).toEqual({
      kind: 'session',
      tabId: tab('two').tabId,
    });
  });

  it('replaces preview without disturbing permanent order', () => {
    let state = desktopWorkspaceReducer(INITIAL_DESKTOP_WORKSPACE_STATE, {
      type: 'openPermanent',
      tab: tab('one'),
    });
    state = desktopWorkspaceReducer(state, {
      type: 'openPreview',
      tab: tab('two'),
    });
    state = desktopWorkspaceReducer(state, {
      type: 'openPreview',
      tab: tab('three'),
    });
    expect(state.permanentTabs.map(item => item.sessionId)).toEqual(['one']);
    expect(state.previewTab?.sessionId).toBe('three');
  });

  it('migrates v1 tabs as permanent and round-trips active preview in v2', () => {
    const migrated = parsePersistedOpenTabsState(
      JSON.stringify({
        version: 1,
        activeTabId: 'connection:two',
        tabs: [
          {
            connectionId: 'connection',
            sessionId: 'one',
            title: 'one',
          },
          {
            connectionId: 'connection',
            sessionId: 'two',
            title: 'two',
          },
        ],
      }),
    );
    expect(migrated?.permanentTabs).toHaveLength(2);
    expect(migrated?.previewTab).toBeNull();

    const withPreview = desktopWorkspaceReducer(migrated!, {
      type: 'openPreview',
      tab: tab('three'),
    });
    expect(
      parsePersistedOpenTabsState(serializePersistedOpenTabsState(withPreview)),
    ).toEqual(withPreview);
  });
});
