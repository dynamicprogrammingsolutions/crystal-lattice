import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';

import { ThemeProvider, useTheme } from '@crystal-lattice/frontend-rn-components';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { DesktopWindowManager } from './desktopWindowManager';
import {
  clearActiveSessionSnapshotsWindow,
  useActiveSessionSnapshotsWindow,
} from './sessionSnapshotsCoordinator';

export interface SessionSnapshotSummary {
  snapshot_id: string;
  session_id?: string;
  created_at: string;
  reason?: string | null;
}

export function SessionSnapshotsWindow(): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  return (
    <ThemeProvider theme={systemTheme}>
      <SessionSnapshotsWindowInner />
    </ThemeProvider>
  );
}

function SessionSnapshotsWindowInner(): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const active = useActiveSessionSnapshotsWindow();

  const [snapshotItems, setSnapshotItems] = useState<SessionSnapshotSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(null);
  const [busySnapshotId, setBusySnapshotId] = useState<string | null>(null);
  const [clearingSelected, setClearingSelected] = useState(false);

  const backend = active?.state.backend ?? null;
  const sessionId = active?.state.sessionId ?? null;

  const closeWindow = useCallback(() => {
    if (active?.state.id) {
      clearActiveSessionSnapshotsWindow(active.state.id);
    }
    DesktopWindowManager?.closeReactWindow({ windowKey: 'sessionSnapshots' });
  }, [active]);

  const loadSnapshots = useCallback(async () => {
    if (!backend || !sessionId) {
      setSnapshotItems([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const items = await backend.listSessionSnapshots(sessionId);
      setSnapshotItems(items);
    } catch (err: any) {
      const message =
        typeof err?.message === 'string' && err.message
          ? err.message
          : 'Failed to load snapshots.';
      setError(message);
      setSnapshotItems([]);
    } finally {
      setLoading(false);
    }
  }, [backend, sessionId]);

  const refreshSelectedSnapshot = useCallback(async () => {
    if (!backend || !sessionId) {
      setSelectedSnapshotId(null);
      return;
    }
    try {
      const next = await backend.getSelectedSessionSnapshot(sessionId);
      setSelectedSnapshotId(next);
    } catch {
      setSelectedSnapshotId(null);
    }
  }, [backend, sessionId]);

  useEffect(() => {
    if (!active) {
      setSnapshotItems([]);
      setError(null);
      setStatusMessage(null);
      setSelectedSnapshotId(null);
      return;
    }
    void loadSnapshots();
    void refreshSelectedSnapshot();
  }, [active?.state.id, loadSnapshots, refreshSelectedSnapshot]);

  const handleCreateSnapshot = useCallback(async () => {
    if (!backend || !sessionId) {
      return;
    }
    setCreating(true);
    setError(null);
    setStatusMessage('Creating snapshot…');
    try {
      await backend.createSessionSnapshot(sessionId, { reason: 'manual' });
      setStatusMessage('Snapshot created.');
      await loadSnapshots();
    } catch (err: any) {
      const message =
        typeof err?.message === 'string' && err.message
          ? err.message
          : 'Failed to create snapshot.';
      setError(message);
      setStatusMessage(null);
    } finally {
      setCreating(false);
    }
  }, [backend, loadSnapshots, sessionId]);

  const handleSelectSnapshot = useCallback(
    async (snapshotId: string) => {
      if (!backend || !sessionId) {
        return;
      }
      setBusySnapshotId(snapshotId);
      setError(null);
      try {
        await backend.selectSessionSnapshot(sessionId, snapshotId);
        await refreshSelectedSnapshot();
        setStatusMessage('Viewing snapshot.');
      } catch (err: any) {
        const message =
          typeof err?.message === 'string' && err.message
            ? err.message
            : 'Failed to select snapshot.';
        setError(message);
        setStatusMessage(null);
      } finally {
        setBusySnapshotId(null);
      }
    },
    [backend, refreshSelectedSnapshot, sessionId],
  );

  const handleClearSelectedSnapshot = useCallback(async () => {
    if (!backend || !sessionId) {
      return;
    }
    setClearingSelected(true);
    setError(null);
    try {
      await backend.clearSelectedSessionSnapshot(sessionId);
      await refreshSelectedSnapshot();
      setStatusMessage('Returned to live session.');
    } catch (err: any) {
      const message =
        typeof err?.message === 'string' && err.message
          ? err.message
          : 'Failed to return to live session.';
      setError(message);
      setStatusMessage(null);
    } finally {
      setClearingSelected(false);
    }
  }, [backend, refreshSelectedSnapshot, sessionId]);

  const handleRestoreSnapshot = useCallback(
    async (snapshotId: string) => {
      if (!backend || !sessionId) {
        return;
      }
      setBusySnapshotId(snapshotId);
      setError(null);
      setStatusMessage('Restoring snapshot…');
      try {
        await backend.restoreSessionSnapshot(sessionId, snapshotId);
        await refreshSelectedSnapshot();
        await loadSnapshots();
        setStatusMessage('Snapshot restored.');
      } catch (err: any) {
        const message =
          typeof err?.message === 'string' && err.message
            ? err.message
            : 'Failed to restore snapshot.';
        setError(message);
        setStatusMessage(null);
      } finally {
        setBusySnapshotId(null);
      }
    },
    [backend, loadSnapshots, refreshSelectedSnapshot, sessionId],
  );

  const handleDeleteSnapshot = useCallback(
    async (snapshotId: string) => {
      if (!backend || !sessionId) {
        return;
      }
      setBusySnapshotId(snapshotId);
      setError(null);
      try {
        await backend.deleteSessionSnapshot(sessionId, snapshotId);
        if (selectedSnapshotId === snapshotId) {
          await refreshSelectedSnapshot();
        }
        await loadSnapshots();
        setStatusMessage('Snapshot deleted.');
      } catch (err: any) {
        const message =
          typeof err?.message === 'string' && err.message
            ? err.message
            : 'Failed to delete snapshot.';
        setError(message);
        setStatusMessage(null);
      } finally {
        setBusySnapshotId(null);
      }
    },
    [backend, loadSnapshots, refreshSelectedSnapshot, selectedSnapshotId, sessionId],
  );

  if (!active) {
    return <View style={styles.root} />;
  }

  const showSpinner = (loading || creating || clearingSelected || busySnapshotId !== null) && !error;

  return (
    <View style={styles.root}>
      <View style={styles.headerRow}>
        <View style={styles.header}>
          <Text style={styles.title}>Snapshots</Text>
          <Text style={styles.subtitle} numberOfLines={1}>
            Session: {active.state.sessionId}
          </Text>
        </View>

        <Pressable
          style={(state) => {
            const hovered = (state as any).hovered as boolean | undefined;
            return [
              styles.closeButton,
              (hovered || state.pressed) && styles.closeButtonHovered,
            ];
          }}
          onPress={closeWindow}
        >
          <Text style={styles.closeButtonText}>Close</Text>
        </Pressable>
      </View>

      <View style={styles.statusLine}>
        {showSpinner ? <ActivityIndicator size="small" color={theme.primary} /> : null}
        {error ? (
          <Text style={[styles.statusText, styles.statusTextError]} numberOfLines={2}>
            {error}
          </Text>
        ) : statusMessage ? (
          <Text style={styles.statusText} numberOfLines={1}>
            {statusMessage}
          </Text>
        ) : null}
      </View>

      <View style={styles.listContainer}>
        <ScrollView style={styles.list} contentContainerStyle={styles.listContent}>
          <View style={styles.topActionsRow}>
            <Pressable
              style={(state) => {
                const hovered = (state as any).hovered as boolean | undefined;
                return [
                  styles.createButton,
                  (hovered || state.pressed) && styles.createButtonPressed,
                  creating && styles.createButtonBusy,
                ];
              }}
              onPress={() => {
                void handleCreateSnapshot();
              }}
              disabled={creating || loading}
            >
              {creating ? (
                <ActivityIndicator size="small" color={theme.textOnPrimary} />
              ) : (
                <Text style={styles.createButtonText}>Create</Text>
              )}
            </Pressable>
            {selectedSnapshotId ? (
              <Pressable
                style={(state) => {
                  const hovered = (state as any).hovered as boolean | undefined;
                  return [
                    styles.liveButton,
                    (hovered || state.pressed) && styles.liveButtonPressed,
                    clearingSelected && styles.liveButtonBusy,
                  ];
                }}
                onPress={() => {
                  void handleClearSelectedSnapshot();
                }}
                disabled={clearingSelected}
              >
                {clearingSelected ? (
                  <ActivityIndicator size="small" color={theme.text} />
                ) : (
                  <Text style={styles.liveButtonText}>Live session</Text>
                )}
              </Pressable>
            ) : null}
          </View>

          {loading && snapshotItems.length === 0 ? (
            <View style={styles.loadingRow}>
              <ActivityIndicator size="small" color={theme.textSecondary} />
              <Text style={styles.helperText}>Loading snapshots…</Text>
            </View>
          ) : null}

          {!loading && snapshotItems.length === 0 ? (
            <Text style={styles.helperText}>No snapshots yet.</Text>
          ) : null}

          {snapshotItems.length > 0
            ? snapshotItems.map((item) => {
                const isSelected = selectedSnapshotId === item.snapshot_id;
                const isBusy = busySnapshotId === item.snapshot_id;
                return (
                  <View key={item.snapshot_id} style={styles.snapshotItem}>
                    <View style={styles.snapshotContent}>
                      <Text style={styles.snapshotName}>{item.reason || 'snapshot'}</Text>
                      <Text style={styles.snapshotMeta}>{item.created_at}</Text>
                      <Text style={styles.snapshotMeta}>{item.snapshot_id}</Text>
                    </View>
                    <View style={styles.snapshotActionsRow}>
                      <Pressable
                        style={(state) => {
                          const hovered = (state as any).hovered as boolean | undefined;
                          return [
                            styles.itemButton,
                            (hovered || state.pressed) && styles.itemButtonPressed,
                            isSelected && styles.itemButtonSelected,
                          ];
                        }}
                        onPress={() => {
                          void handleSelectSnapshot(item.snapshot_id);
                        }}
                        disabled={isBusy || isSelected}
                      >
                        <Text style={styles.itemButtonText}>
                          {isSelected ? 'Selected' : 'Select'}
                        </Text>
                      </Pressable>
                      <Pressable
                        style={(state) => {
                          const hovered = (state as any).hovered as boolean | undefined;
                          return [
                            styles.itemButton,
                            (hovered || state.pressed) && styles.itemButtonPressed,
                          ];
                        }}
                        onPress={() => {
                          void handleRestoreSnapshot(item.snapshot_id);
                        }}
                        disabled={isBusy}
                      >
                        <Text style={styles.itemButtonText}>Restore</Text>
                      </Pressable>
                      <Pressable
                        style={(state) => {
                          const hovered = (state as any).hovered as boolean | undefined;
                          return [
                            styles.itemButton,
                            (hovered || state.pressed) && styles.itemButtonPressed,
                          ];
                        }}
                        onPress={() => {
                          void handleDeleteSnapshot(item.snapshot_id);
                        }}
                        disabled={isBusy}
                      >
                        <Text style={styles.itemButtonText}>Delete</Text>
                      </Pressable>
                    </View>
                  </View>
                );
              })
            : null}
        </ScrollView>
      </View>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const borderWidth = 1;
  return StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: theme.background,
      padding: 16,
      gap: 12,
    },
    headerRow: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: 12,
    },
    header: {
      gap: 4,
      flex: 1,
    },
    closeButton: {
      borderWidth,
      borderColor: theme.primary,
      backgroundColor: theme.primary,
      borderRadius: 10,
      paddingHorizontal: 12,
      paddingVertical: 7,
      alignItems: 'center',
      justifyContent: 'center',
    },
    closeButtonHovered: {
      opacity: 0.92,
    },
    closeButtonText: {
      fontSize: 12,
      fontWeight: '800',
      color: theme.textOnPrimary,
    },
    title: {
      fontSize: 16,
      fontWeight: '800',
      color: theme.text,
    },
    subtitle: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    statusLine: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      minHeight: 18,
    },
    statusText: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    statusTextError: {
      color: theme.danger,
    },
    helperText: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    listContainer: {
      flex: 1,
      borderWidth,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
    },
    list: {
      flex: 1,
    },
    listContent: {
      padding: 12,
      gap: 12,
    },
    topActionsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      gap: 8,
    },
    createButton: {
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderRadius: 10,
      backgroundColor: theme.primary,
      minWidth: 90,
      alignItems: 'center',
      justifyContent: 'center',
    },
    createButtonPressed: {
      opacity: 0.85,
    },
    createButtonBusy: {
      opacity: 0.85,
    },
    createButtonText: {
      fontSize: 12,
      fontWeight: '800',
      color: theme.textOnPrimary,
    },
    liveButton: {
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderRadius: 10,
      backgroundColor: theme.surfaceAlt,
      borderWidth,
      borderColor: theme.border,
      minWidth: 110,
      alignItems: 'center',
      justifyContent: 'center',
    },
    liveButtonPressed: {
      opacity: 0.85,
    },
    liveButtonBusy: {
      opacity: 0.85,
    },
    liveButtonText: {
      fontSize: 12,
      fontWeight: '700',
      color: theme.text,
    },
    loadingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      paddingVertical: 8,
    },
    snapshotItem: {
      paddingVertical: 10,
      borderBottomWidth: borderWidth,
      borderBottomColor: theme.border,
      gap: 8,
    },
    snapshotContent: {
      gap: 2,
    },
    snapshotName: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.text,
    },
    snapshotMeta: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    snapshotActionsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      gap: 8,
    },
    itemButton: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 8,
      backgroundColor: theme.surfaceAlt,
      borderWidth,
      borderColor: theme.border,
      minWidth: 72,
      alignItems: 'center',
      justifyContent: 'center',
    },
    itemButtonPressed: {
      opacity: 0.85,
    },
    itemButtonSelected: {
      backgroundColor: theme.primaryMuted,
      borderColor: theme.primary,
    },
    itemButtonText: {
      fontSize: 11,
      fontWeight: '700',
      color: theme.text,
    },
  });
}