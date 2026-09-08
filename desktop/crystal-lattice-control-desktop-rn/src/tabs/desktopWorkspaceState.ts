import { moveReorderValues } from '@crystal-lattice/frontend-rn-components';

export interface DesktopSessionTab {
  tabId: string;
  connectionId: string;
  sessionId: string;
  title: string;
  subtitle?: string | null;
}

export type DesktopActiveWorkspace =
  | { kind: 'home' }
  | { kind: 'session'; tabId: string };

export interface DesktopWorkspaceState {
  permanentTabs: DesktopSessionTab[];
  previewTab: DesktopSessionTab | null;
  activeWorkspace: DesktopActiveWorkspace;
}

export const INITIAL_DESKTOP_WORKSPACE_STATE: DesktopWorkspaceState = {
  permanentTabs: [],
  previewTab: null,
  activeWorkspace: { kind: 'home' },
};

export type DesktopWorkspaceAction =
  | { type: 'hydrate'; state: DesktopWorkspaceState }
  | { type: 'selectHome' }
  | { type: 'selectTab'; tabId: string }
  | { type: 'openPreview'; tab: DesktopSessionTab }
  | { type: 'openPermanent'; tab: DesktopSessionTab }
  | { type: 'promotePreview'; tabId?: string }
  | { type: 'closeTab'; tabId: string }
  | { type: 'reorderPermanent'; fromIndex: number; toIndex: number }
  | {
      type: 'updatePresentations';
      connectionId: string;
      presentations: Record<string, { title: string; subtitle: string | null }>;
    }
  | { type: 'removeConnection'; connectionId: string }
  | { type: 'clear' };

function updateTab(
  current: DesktopSessionTab,
  incoming: DesktopSessionTab,
): DesktopSessionTab {
  return {
    ...current,
    title: incoming.title || current.title,
    subtitle:
      incoming.subtitle !== undefined ? incoming.subtitle : current.subtitle,
  };
}

function tabExists(state: DesktopWorkspaceState, tabId: string): boolean {
  return (
    state.previewTab?.tabId === tabId ||
    state.permanentTabs.some(tab => tab.tabId === tabId)
  );
}

function selectAfterClose(
  permanentTabs: readonly DesktopSessionTab[],
  removedIndex: number,
): DesktopActiveWorkspace {
  if (permanentTabs.length === 0) return { kind: 'home' };
  const neighborIndex = Math.min(removedIndex, permanentTabs.length - 1);
  return { kind: 'session', tabId: permanentTabs[neighborIndex].tabId };
}

export function desktopWorkspaceReducer(
  state: DesktopWorkspaceState,
  action: DesktopWorkspaceAction,
): DesktopWorkspaceState {
  if (action.type === 'hydrate') return action.state;
  if (action.type === 'selectHome') {
    return { ...state, activeWorkspace: { kind: 'home' } };
  }
  if (action.type === 'selectTab') {
    if (!tabExists(state, action.tabId)) return state;
    return {
      ...state,
      activeWorkspace: { kind: 'session', tabId: action.tabId },
    };
  }
  if (action.type === 'openPreview') {
    const permanentIndex = state.permanentTabs.findIndex(
      tab => tab.tabId === action.tab.tabId,
    );
    if (permanentIndex >= 0) {
      const permanentTabs = [...state.permanentTabs];
      permanentTabs[permanentIndex] = updateTab(
        permanentTabs[permanentIndex],
        action.tab,
      );
      return {
        ...state,
        permanentTabs,
        previewTab:
          state.previewTab?.tabId === action.tab.tabId
            ? null
            : state.previewTab,
        activeWorkspace: { kind: 'session', tabId: action.tab.tabId },
      };
    }
    return {
      ...state,
      previewTab:
        state.previewTab?.tabId === action.tab.tabId
          ? updateTab(state.previewTab, action.tab)
          : action.tab,
      activeWorkspace: { kind: 'session', tabId: action.tab.tabId },
    };
  }
  if (action.type === 'openPermanent') {
    const permanentIndex = state.permanentTabs.findIndex(
      tab => tab.tabId === action.tab.tabId,
    );
    if (permanentIndex >= 0) {
      const permanentTabs = [...state.permanentTabs];
      permanentTabs[permanentIndex] = updateTab(
        permanentTabs[permanentIndex],
        action.tab,
      );
      return {
        ...state,
        permanentTabs,
        activeWorkspace: { kind: 'session', tabId: action.tab.tabId },
      };
    }
    const promoted =
      state.previewTab?.tabId === action.tab.tabId
        ? updateTab(state.previewTab, action.tab)
        : action.tab;
    return {
      permanentTabs: [...state.permanentTabs, promoted],
      previewTab:
        state.previewTab?.tabId === action.tab.tabId ? null : state.previewTab,
      activeWorkspace: { kind: 'session', tabId: action.tab.tabId },
    };
  }
  if (action.type === 'promotePreview') {
    const preview = state.previewTab;
    if (!preview || (action.tabId && preview.tabId !== action.tabId)) {
      return state;
    }
    return {
      permanentTabs: [...state.permanentTabs, preview],
      previewTab: null,
      activeWorkspace: { kind: 'session', tabId: preview.tabId },
    };
  }
  if (action.type === 'closeTab') {
    if (state.previewTab?.tabId === action.tabId) {
      return {
        ...state,
        previewTab: null,
        activeWorkspace:
          state.activeWorkspace.kind === 'session' &&
          state.activeWorkspace.tabId === action.tabId
            ? state.permanentTabs.length > 0
              ? {
                  kind: 'session',
                  tabId:
                    state.permanentTabs[state.permanentTabs.length - 1].tabId,
                }
              : { kind: 'home' }
            : state.activeWorkspace,
      };
    }
    const removedIndex = state.permanentTabs.findIndex(
      tab => tab.tabId === action.tabId,
    );
    if (removedIndex < 0) return state;
    const permanentTabs = state.permanentTabs.filter(
      tab => tab.tabId !== action.tabId,
    );
    return {
      ...state,
      permanentTabs,
      activeWorkspace:
        state.activeWorkspace.kind === 'session' &&
        state.activeWorkspace.tabId === action.tabId
          ? selectAfterClose(permanentTabs, removedIndex)
          : state.activeWorkspace,
    };
  }
  if (action.type === 'reorderPermanent') {
    return {
      ...state,
      permanentTabs: moveReorderValues(
        state.permanentTabs,
        action.fromIndex,
        action.toIndex,
      ),
    };
  }
  if (action.type === 'updatePresentations') {
    const update = (tab: DesktopSessionTab): DesktopSessionTab => {
      if (tab.connectionId !== action.connectionId) return tab;
      const presentation = action.presentations[tab.sessionId];
      if (!presentation) return tab;
      if (
        tab.title === presentation.title &&
        tab.subtitle === presentation.subtitle
      ) {
        return tab;
      }
      return {
        ...tab,
        title: presentation.title || tab.title,
        subtitle: presentation.subtitle,
      };
    };
    return {
      ...state,
      permanentTabs: state.permanentTabs.map(update),
      previewTab: state.previewTab ? update(state.previewTab) : null,
    };
  }
  if (action.type === 'removeConnection') {
    const permanentTabs = state.permanentTabs.filter(
      tab => tab.connectionId !== action.connectionId,
    );
    const previewTab =
      state.previewTab?.connectionId === action.connectionId
        ? null
        : state.previewTab;
    const activeTabId =
      state.activeWorkspace.kind === 'session'
        ? state.activeWorkspace.tabId
        : null;
    const activeStillExists =
      activeTabId === null ||
      permanentTabs.some(tab => tab.tabId === activeTabId) ||
      previewTab?.tabId === activeTabId;
    return {
      permanentTabs,
      previewTab,
      activeWorkspace: activeStillExists
        ? state.activeWorkspace
        : permanentTabs.length > 0
        ? {
            kind: 'session',
            tabId: permanentTabs[0].tabId,
          }
        : previewTab
        ? { kind: 'session', tabId: previewTab.tabId }
        : { kind: 'home' },
    };
  }
  return INITIAL_DESKTOP_WORKSPACE_STATE;
}

export function getDesktopWorkspaceTabs(
  state: DesktopWorkspaceState,
): DesktopSessionTab[] {
  return state.previewTab
    ? [...state.permanentTabs, state.previewTab]
    : state.permanentTabs;
}

export function getActiveDesktopSessionTab(
  state: DesktopWorkspaceState,
): DesktopSessionTab | null {
  if (state.activeWorkspace.kind !== 'session') return null;
  const activeTabId = state.activeWorkspace.tabId;
  return (
    getDesktopWorkspaceTabs(state).find(tab => tab.tabId === activeTabId) ??
    null
  );
}
