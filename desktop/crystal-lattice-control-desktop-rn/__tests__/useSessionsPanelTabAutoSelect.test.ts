import {
  INITIAL_SESSIONS_PANEL_SELECTION_STATE,
  sessionsPanelSelectionReducer,
  type ActiveTabSelection,
  type SessionsPanelSelectionState,
} from '../src/panels/useSessionsPanelTabAutoSelect';

const HOME: ActiveTabSelection = {
  tabId: null,
  connectionId: null,
  sessionId: null,
};

function tab(connectionId: string, sessionId: string): ActiveTabSelection {
  return {
    tabId: `${connectionId}:${sessionId}`,
    connectionId,
    sessionId,
  };
}

function reconcile(
  state: SessionsPanelSelectionState,
  {
    connectionId = 'connection-a',
    activeTab = HOME,
    enabled = true,
    nowMs = 100,
  }: {
    connectionId?: string | null;
    activeTab?: ActiveTabSelection;
    enabled?: boolean;
    nowMs?: number;
  } = {},
): SessionsPanelSelectionState {
  return sessionsPanelSelectionReducer(state, {
    type: 'reconcile',
    connectionId,
    activeTab,
    enabled,
    nowMs,
  });
}

function applyPending(
  state: SessionsPanelSelectionState,
  nowMs = 101,
): SessionsPanelSelectionState {
  if (!state.pending) {
    throw new Error('Expected a pending tab selection');
  }
  return sessionsPanelSelectionReducer(state, {
    type: 'applyPending',
    intentKey: state.pending.intentKey,
    nowMs,
  });
}

describe('Sessions-panel tab selection state', () => {
  it('follows a tab only when it belongs to the focused connection', () => {
    const pending = reconcile(INITIAL_SESSIONS_PANEL_SELECTION_STATE, {
      activeTab: tab('connection-a', 'session-a'),
    });
    expect(pending.pending?.sessionId).toBe('session-a');
    expect(applyPending(pending).selection).toEqual({
      sessionId: 'session-a',
      source: 'activeTab',
      tabId: 'connection-a:session-a',
    });

    const otherConnection = reconcile(INITIAL_SESSIONS_PANEL_SELECTION_STATE, {
      connectionId: 'connection-a',
      activeTab: tab('connection-b', 'session-b'),
    });
    expect(otherConnection.pending).toBeNull();
    expect(otherConnection.selection).toBeNull();
  });

  it('clears an automatic selection when Home or a non-followable tab becomes active', () => {
    const selected = applyPending(
      reconcile(INITIAL_SESSIONS_PANEL_SELECTION_STATE, {
        activeTab: tab('connection-a', 'session-a'),
      }),
    );

    const home = reconcile(selected, { activeTab: HOME });
    expect(home.selection).toBeNull();

    const selectedAgain = applyPending(
      reconcile(home, {
        activeTab: tab('connection-a', 'session-a'),
        nowMs: 200,
      }),
      201,
    );
    const crossConnection = reconcile(selectedAgain, {
      activeTab: tab('connection-b', 'session-b'),
      nowMs: 300,
    });
    expect(crossConnection.selection).toBeNull();
    expect(crossConnection.pending).toBeNull();
  });

  it('preserves a manual selection when following is disabled or impossible', () => {
    const following = reconcile(INITIAL_SESSIONS_PANEL_SELECTION_STATE, {
      activeTab: tab('connection-a', 'session-a'),
    });
    const manual = sessionsPanelSelectionReducer(following, {
      type: 'manualSelect',
      sessionId: 'manual-session',
    });

    const disabled = reconcile(manual, {
      activeTab: tab('connection-a', 'session-b'),
      enabled: false,
      nowMs: 200,
    });
    expect(disabled.selection).toEqual({
      sessionId: 'manual-session',
      source: 'manual',
    });

    const differentConnection = reconcile(disabled, {
      activeTab: tab('connection-b', 'session-c'),
      enabled: true,
      nowMs: 300,
    });
    expect(differentConnection.selection).toEqual({
      sessionId: 'manual-session',
      source: 'manual',
    });
  });

  it('resets either selection source when the focused connection changes', () => {
    const manual = sessionsPanelSelectionReducer(
      reconcile(INITIAL_SESSIONS_PANEL_SELECTION_STATE),
      {
        type: 'manualSelect',
        sessionId: 'manual-session',
      },
    );
    const switched = reconcile(manual, {
      connectionId: 'connection-b',
      activeTab: tab('connection-b', 'session-b'),
      enabled: false,
    });
    expect(switched.selection).toBeNull();
    expect(switched.pending).toBeNull();
  });

  it('cancels delayed automatic selection after a manual click', () => {
    const pending = reconcile(INITIAL_SESSIONS_PANEL_SELECTION_STATE, {
      activeTab: tab('connection-a', 'delayed-session'),
    });
    const intentKey = pending.pending?.intentKey;
    expect(intentKey).toBeTruthy();

    const manual = sessionsPanelSelectionReducer(pending, {
      type: 'manualSelect',
      sessionId: 'manual-session',
    });
    const staleApply = sessionsPanelSelectionReducer(manual, {
      type: 'applyPending',
      intentKey: intentKey!,
      nowMs: 200,
    });
    expect(staleApply.selection).toEqual({
      sessionId: 'manual-session',
      source: 'manual',
    });
    expect(staleApply.pending).toBeNull();
  });

  it('arms following when the focused connection catches up to the active tab', () => {
    const waiting = reconcile(INITIAL_SESSIONS_PANEL_SELECTION_STATE, {
      connectionId: 'connection-a',
      activeTab: tab('connection-b', 'session-b'),
    });
    expect(waiting.pending).toBeNull();

    const switched = reconcile(waiting, {
      connectionId: 'connection-b',
      activeTab: tab('connection-b', 'session-b'),
      nowMs: 200,
    });
    expect(switched.pending?.sessionId).toBe('session-b');
    expect(applyPending(switched, 201).selection?.sessionId).toBe('session-b');
  });
});
