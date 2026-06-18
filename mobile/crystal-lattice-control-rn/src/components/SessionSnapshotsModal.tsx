import React, { useMemo } from 'react';
import {
  ActivityIndicator,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import PanelModalFrame from './PanelModalFrame';
import { useTheme, type Theme } from '../theme';

export interface SessionSnapshotSummary {
  snapshot_id: string;
  created_at: string;
  reason?: string | null;
}

export interface SessionSnapshotsModalProps {
  visible: boolean;
  snapshotsLoading: boolean;
  snapshotItems: SessionSnapshotSummary[];
  selectedSnapshotId: string | null;
  onRequestClose: () => void;
  onCreateSnapshot: () => void | Promise<void>;
  onClearSelectedSnapshot: () => void | Promise<void>;
  onSelectSnapshot: (snapshotId: string) => void | Promise<void>;
  onRestoreSnapshot: (snapshotId: string) => void | Promise<void>;
  onDeleteSnapshot: (snapshotId: string) => void | Promise<void>;
}

const SessionSnapshotsModal: React.FC<SessionSnapshotsModalProps> = ({
  visible,
  snapshotsLoading,
  snapshotItems,
  selectedSnapshotId,
  onRequestClose,
  onCreateSnapshot,
  onClearSelectedSnapshot,
  onSelectSnapshot,
  onRestoreSnapshot,
  onDeleteSnapshot,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  return (
    <PanelModalFrame
      visible={visible}
      title="Snapshots"
      subtitle="Browse readonly snapshots, restore one, or return to the live session."
      onRequestClose={onRequestClose}
      scroll
      scrollTestID="session-snapshots-scroll"
    >
      <View style={styles.topActionsRow}>
        <TouchableOpacity
          style={[styles.button, styles.secondaryButton, styles.topActionButton]}
          onPress={() => {
            void onCreateSnapshot();
          }}
          disabled={snapshotsLoading}
        >
          <Text style={styles.buttonTextSecondary}>Create</Text>
        </TouchableOpacity>
        {selectedSnapshotId ? (
          <TouchableOpacity
            style={[styles.button, styles.secondaryButton, styles.topActionButton]}
            onPress={() => {
              void onClearSelectedSnapshot();
            }}
          >
            <Text style={styles.buttonTextSecondary}>Live session</Text>
          </TouchableOpacity>
        ) : null}
      </View>

      {snapshotsLoading ? (
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color={theme.textSecondary} />
        </View>
      ) : snapshotItems.length === 0 ? (
        <Text style={styles.emptyText}>No snapshots yet.</Text>
      ) : (
        snapshotItems.map((item) => {
          const isSelected = selectedSnapshotId === item.snapshot_id;
          return (
            <View
              key={item.snapshot_id}
              testID={`snapshot-item-${item.snapshot_id}`}
              style={styles.snapshotItem}
            >
              <View style={styles.snapshotContent}>
                <Text style={styles.snapshotName}>{item.reason || 'snapshot'}</Text>
                <Text style={styles.snapshotMeta}>{item.created_at}</Text>
                <Text style={styles.snapshotMeta}>{item.snapshot_id}</Text>
              </View>
              <View
                testID={`snapshot-actions-${item.snapshot_id}`}
                style={styles.snapshotActionsRow}
              >
                <TouchableOpacity
                  style={[styles.button, styles.secondaryButton, styles.smallButton]}
                  onPress={() => {
                    void onSelectSnapshot(item.snapshot_id);
                  }}
                >
                  <Text style={styles.buttonTextSecondary}>
                    {isSelected ? 'Selected' : 'Select'}
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.button, styles.secondaryButton, styles.smallButton]}
                  onPress={() => {
                    void onRestoreSnapshot(item.snapshot_id);
                  }}
                >
                  <Text style={styles.buttonTextSecondary}>Restore</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.button, styles.secondaryButton, styles.smallButton]}
                  onPress={() => {
                    void onDeleteSnapshot(item.snapshot_id);
                  }}
                >
                  <Text style={styles.buttonTextSecondary}>Delete</Text>
                </TouchableOpacity>
              </View>
            </View>
          );
        })
      )}
    </PanelModalFrame>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    topActionsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      gap: 8,
      marginBottom: 10,
    },
    loadingRow: {
      minHeight: 40,
      alignItems: 'center',
      justifyContent: 'center',
    },
    emptyText: {
      fontSize: theme.typography.fontSize.small,
      color: theme.textSecondary,
      paddingVertical: 12,
    },
    snapshotItem: {
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.divider,
      paddingVertical: 10,
    },
    snapshotContent: {
      minWidth: 0,
    },
    snapshotName: {
      fontSize: theme.typography.fontSize.normal,
      fontWeight: '600',
      color: theme.text,
    },
    snapshotMeta: {
      fontSize: theme.typography.fontSize.small,
      color: theme.textSecondary,
      marginTop: 2,
    },
    snapshotActionsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      flexWrap: 'wrap',
      gap: 8,
      marginTop: 8,
      marginBottom: 4,
    },
    button: {
      minHeight: 32,
      borderRadius: 8,
      paddingHorizontal: 12,
      paddingVertical: 6,
      justifyContent: 'center',
      alignItems: 'center',
    },
    secondaryButton: {
      backgroundColor: theme.surfaceAlt,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
    },
    topActionButton: {
      minWidth: 90,
    },
    smallButton: {
      minWidth: 72,
    },
    buttonTextSecondary: {
      color: theme.text,
      fontSize: theme.typography.fontSize.small,
      fontWeight: '600',
    },
  });

export default SessionSnapshotsModal;