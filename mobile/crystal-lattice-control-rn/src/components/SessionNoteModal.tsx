import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { MAX_SESSION_NOTE_LENGTH } from '../homeWorkspaceState';
import { useTheme, type Theme } from '../theme';
import PanelModalFrame from './PanelModalFrame';

interface SessionNoteModalProps {
  visible: boolean;
  sessionId: string | null;
  note: string | null;
  onSave: (note: string) => void;
  onRemove: () => void;
  onRequestClose: () => void;
}

const SessionNoteModal: React.FC<SessionNoteModalProps> = ({
  visible,
  sessionId,
  note,
  onSave,
  onRemove,
  onRequestClose,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [draft, setDraft] = useState(note ?? '');

  useEffect(() => {
    if (visible) setDraft(note ?? '');
  }, [note, sessionId, visible]);

  const confirmRemove = () => {
    Alert.alert(
      'Remove Note',
      'Remove this permanent note from every connection using this session ID?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () => {
            onRemove();
            onRequestClose();
          },
        },
      ],
    );
  };

  return (
    <PanelModalFrame
      visible={visible}
      title={note ? 'Edit Session Note' : 'Add Session Note'}
      subtitle={sessionId ? `Session ${sessionId}` : undefined}
      onRequestClose={onRequestClose}
      contentStyle={styles.modal}
      testID="session-note-modal"
    >
      <TextInput
        testID="session-note-input"
        accessibilityLabel="Session note"
        style={styles.input}
        multiline
        maxLength={MAX_SESSION_NOTE_LENGTH}
        placeholder="Add a note stored on this device"
        placeholderTextColor={theme.textSecondary}
        value={draft}
        onChangeText={setDraft}
        textAlignVertical="top"
      />
      <Text style={styles.counter}>
        {draft.length}/{MAX_SESSION_NOTE_LENGTH}
      </Text>
      <View style={styles.actions}>
        {note ? (
          <TouchableOpacity
            testID="session-note-remove"
            style={[styles.button, styles.removeButton]}
            onPress={confirmRemove}
          >
            <Text style={styles.removeText}>Remove Note</Text>
          </TouchableOpacity>
        ) : null}
        <View style={styles.actionsSpacer} />
        <TouchableOpacity
          testID="session-note-cancel"
          style={[styles.button, styles.secondaryButton]}
          onPress={onRequestClose}
        >
          <Text style={styles.secondaryText}>Cancel</Text>
        </TouchableOpacity>
        <TouchableOpacity
          testID="session-note-save"
          style={[styles.button, styles.primaryButton]}
          onPress={() => {
            onSave(draft);
            onRequestClose();
          }}
        >
          <Text style={styles.primaryText}>Save</Text>
        </TouchableOpacity>
      </View>
    </PanelModalFrame>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    modal: {
      width: '90%',
      maxWidth: 520,
    },
    input: {
      minHeight: 140,
      maxHeight: 280,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 10,
      paddingHorizontal: 12,
      paddingVertical: 10,
      color: theme.text,
      backgroundColor: theme.surfaceAlt,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
    },
    counter: {
      marginTop: 4,
      color: theme.textSecondary,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      textAlign: 'right',
    },
    actions: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      marginTop: 12,
    },
    actionsSpacer: {
      flex: 1,
    },
    button: {
      borderRadius: 8,
      paddingHorizontal: 12,
      paddingVertical: 9,
    },
    primaryButton: {
      backgroundColor: theme.primary,
    },
    secondaryButton: {
      backgroundColor: theme.surfaceAlt,
    },
    removeButton: {
      backgroundColor: theme.dangerMuted,
    },
    primaryText: {
      color: theme.textOnPrimary,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '600',
    },
    secondaryText: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '600',
    },
    removeText: {
      color: theme.danger,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '600',
    },
  });

export default SessionNoteModal;