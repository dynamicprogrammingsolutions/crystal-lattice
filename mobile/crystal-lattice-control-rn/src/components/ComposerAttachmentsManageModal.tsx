import React, { useMemo } from 'react';
import {
  Image,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import {
  attachmentDraftStatusLabel,
  type AttachmentDraftStatus,
  selectAttachmentPreviewUrl,
} from '@crystal-lattice/frontend-sdk';

import { useTheme, type Theme } from '../theme';

export type ComposerAttachmentDraftRow = {
  draftId: string;
  type: string;
  content: any;
  title?: string;
  status?: AttachmentDraftStatus;
  errorMessage?: string | null;
};

function selectFilename(row: ComposerAttachmentDraftRow): string {
  const content = row.content;
  const raw = content && typeof content === 'object' ? content.filename ?? content.name : undefined;
  if (typeof raw === 'string' && raw.trim()) return raw.trim();
  if (typeof row.title === 'string' && row.title.trim()) return row.title.trim();
  return row.type;
}

export const ComposerAttachmentsManageModal: React.FC<{
  visible: boolean;
  title: string;
  attachments: ComposerAttachmentDraftRow[];
  disabled?: boolean;
  onMove: (draftId: string, direction: 'up' | 'down') => void;
  onEditMetadata: (draftId: string) => void;
  onDelete: (draftId: string) => void;
  onRequestClose: () => void;
}> = ({
  visible,
  title,
  attachments,
  disabled,
  onMove,
  onEditMetadata,
  onDelete,
  onRequestClose,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  if (!visible) {
    return null;
  }

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onRequestClose}>
      <View style={styles.overlay}>
        <Pressable style={StyleSheet.absoluteFill} onPress={onRequestClose} />
        <View style={styles.content}>
          <Text style={styles.title}>{title}</Text>
          {attachments.length === 0 ? (
            <Text style={styles.helperText}>No attachments.</Text>
          ) : (
            <ScrollView style={styles.list}>
              {attachments.map((row, idx) => {
                const url = selectAttachmentPreviewUrl(row.content);
                const isImage = row.type === 'image' && url;
                const filename = selectFilename(row);
                const canMoveUp = idx > 0;
                const canMoveDown = idx < attachments.length - 1;

                return (
                  <View key={row.draftId} style={styles.row}>
                    <View style={styles.previewBox}>
                      {isImage ? (
                        <Image
                          source={{ uri: url ?? undefined }}
                          style={styles.previewImage}
                        />
                      ) : (
                        <Icon
                          name={row.type === 'pdf' ? 'file-text' : 'paperclip'}
                          size={18}
                          color={theme.textSecondary}
                        />
                      )}
                    </View>

                    <View style={styles.metaColumn}>
                      <Text style={styles.filename} numberOfLines={1}>
                        {filename}
                      </Text>
                      <Text style={styles.subtle} numberOfLines={1}>
                        {row.status ? attachmentDraftStatusLabel(row.status, row.errorMessage) : row.type}
                      </Text>
                    </View>

                    <View style={styles.iconsColumn}>
                      <TouchableOpacity
                        style={styles.iconButton}
                        onPress={() => onMove(row.draftId, 'up')}
                        disabled={disabled || !canMoveUp}
                      >
                        <Icon
                          name="arrow-up"
                          size={16}
                          color={
                            disabled || !canMoveUp ? theme.textMuted : theme.textSecondary
                          }
                        />
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={styles.iconButton}
                        onPress={() => onMove(row.draftId, 'down')}
                        disabled={disabled || !canMoveDown}
                      >
                        <Icon
                          name="arrow-down"
                          size={16}
                          color={
                            disabled || !canMoveDown ? theme.textMuted : theme.textSecondary
                          }
                        />
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={styles.iconButton}
                        onPress={() => onEditMetadata(row.draftId)}
                        disabled={disabled}
                      >
                        <Icon
                          name="edit-2"
                          size={16}
                          color={disabled ? theme.textMuted : theme.textSecondary}
                        />
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={styles.iconButton}
                        onPress={() => onDelete(row.draftId)}
                        disabled={disabled}
                      >
                        <Icon
                          name="trash-2"
                          size={16}
                          color={disabled ? theme.textMuted : theme.danger}
                        />
                      </TouchableOpacity>
                    </View>
                  </View>
                );
              })}
            </ScrollView>
          )}

          <View style={styles.footerRow}>
            <TouchableOpacity style={styles.closeButton} onPress={onRequestClose}>
              <Text style={styles.closeButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    overlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      justifyContent: 'center',
      alignItems: 'center',
    },
    content: {
      width: '90%',
      maxHeight: '80%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      paddingHorizontal: 16,
      paddingVertical: 12,
    },
    title: {
      fontSize: 16,
      fontWeight: '600',
      color: theme.text,
      marginBottom: 8,
      textAlign: 'center',
    },
    helperText: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.textSecondary,
      marginBottom: 8,
    },
    list: {
      flexGrow: 0,
      flexShrink: 1,
      marginVertical: 8,
    },
    row: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 8,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.border,
    },
    previewBox: {
      width: 44,
      height: 44,
      borderRadius: 10,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surfaceAlt,
      overflow: 'hidden',
      alignItems: 'center',
      justifyContent: 'center',
      marginRight: 10,
    },
    previewImage: {
      width: 44,
      height: 44,
      resizeMode: 'cover',
    },
    metaColumn: {
      flex: 1,
      minWidth: 0,
    },
    filename: {
      fontSize: 13,
      fontWeight: '600',
      color: theme.text,
    },
    subtle: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textSecondary,
      marginTop: 2,
    },
    iconsColumn: {
      flexDirection: 'row',
      alignItems: 'center',
      marginLeft: 8,
    },
    iconButton: {
      paddingHorizontal: 6,
      paddingVertical: 6,
    },
    footerRow: {
      marginTop: 8,
      flexDirection: 'row',
      justifyContent: 'flex-end',
    },
    closeButton: {
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 8,
      backgroundColor: theme.surfaceAlt,
    },
    closeButtonText: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '600',
      color: theme.text,
    },
  });
