import React, { useMemo, useRef } from 'react';
import {
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  findNodeHandle,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

export type ComposerAttachmentDraftRow = {
  draftId: string;
  type: string;
  content: any;
  title?: string;
};

function selectAttachmentUrl(content: any): string | null {
  if (!content || typeof content !== 'object') return null;
  if (typeof content.url === 'string' && content.url) return content.url;
  if (typeof content.data_base64 === 'string' && content.data_base64) {
    const mimeType =
      typeof content.mime_type === 'string' && content.mime_type
        ? content.mime_type
        : 'application/octet-stream';
    return `data:${mimeType};base64,${content.data_base64}`;
  }
  return null;
}

function selectFilename(row: ComposerAttachmentDraftRow): string {
  const content = row.content;
  const raw = content && typeof content === 'object' ? content.filename ?? content.name : undefined;
  if (typeof raw === 'string' && raw.trim()) return raw.trim();
  if (typeof row.title === 'string' && row.title.trim()) return row.title.trim();
  return row.type;
}

export const ComposerAttachmentsExpandedPanel: React.FC<{
  attachments: ComposerAttachmentDraftRow[];
  disabled?: boolean;
  onMove: (draftId: string, direction: 'up' | 'down') => void;
  onEditMetadata: (draftId: string, anchorTag?: number) => void;
  onDelete: (draftId: string) => void;
}> = ({ attachments, disabled, onMove, onEditMetadata, onDelete }) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const editButtonRefs = useRef<Record<string, any>>({});

  return (
    <View style={styles.root}>
      {attachments.length === 0 ? (
        <Text style={styles.helperText}>No attachments.</Text>
      ) : (
        <ScrollView style={styles.list} nestedScrollEnabled>
          {attachments.map((row, idx) => {
            const url = selectAttachmentUrl(row.content);
            const isImage = row.type === 'image' && url;
            const filename = selectFilename(row);
            const canMoveUp = idx > 0;
            const canMoveDown = idx < attachments.length - 1;

            return (
              <View key={row.draftId} style={styles.row}>
                <View style={styles.previewBox}>
                  {isImage ? (
                    <Image source={{ uri: url ?? undefined }} style={styles.previewImage} />
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
                    {row.type}
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
                      color={disabled || !canMoveUp ? theme.textMuted : theme.textSecondary}
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
                      color={disabled || !canMoveDown ? theme.textMuted : theme.textSecondary}
                    />
                  </TouchableOpacity>
                  <View
                    ref={(ref) => {
                      editButtonRefs.current[row.draftId] = ref;
                    }}
                    collapsable={false}
                  >
                    <TouchableOpacity
                      style={styles.iconButton}
                      onPress={() => {
                        const ref = editButtonRefs.current[row.draftId];
                        const tag = ref ? (findNodeHandle(ref) as any) : null;
                        onEditMetadata(row.draftId, typeof tag === 'number' ? tag : undefined);
                      }}
                      disabled={disabled}
                    >
                      <Icon
                        name="edit-2"
                        size={16}
                        color={disabled ? theme.textMuted : theme.textSecondary}
                      />
                    </TouchableOpacity>
                  </View>
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
    </View>
  );
};

const createStyles = (theme: ReturnType<typeof useTheme>) =>
  StyleSheet.create({
    root: {
      marginHorizontal: 10,
      marginBottom: 8,
    },
    helperText: {
      fontSize: 13,
      color: theme.textSecondary,
      paddingVertical: 6,
    },
    list: {
      maxHeight: 220,
    },
    row: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 8,
      paddingHorizontal: 2,
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
      fontSize: 14,
      fontWeight: '500',
      color: theme.text,
    },
    subtle: {
      fontSize: 12,
      color: theme.textSecondary,
      marginTop: 2,
    },
    iconsColumn: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 6,
      marginLeft: 8,
    },
    iconButton: {
      paddingHorizontal: 6,
      paddingVertical: 6,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
  });
