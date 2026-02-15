import React, { useMemo } from 'react';
import { Image, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useTheme, type Theme } from '../theme';

export type MultipartPartDraft = {
  draftId: string;
  type: string;
  content: any;
  metadata?: any;
};

function toDataUrlFromContent(content: any): string | null {
  if (!content || typeof content !== 'object') return null;
  if (typeof content.url === 'string' && content.url) return content.url;
  if (typeof content.data_base64 === 'string' && content.data_base64) {
    const mimeType = typeof content.mime_type === 'string' ? content.mime_type : 'application/octet-stream';
    return `data:${mimeType};base64,${content.data_base64}`;
  }
  return null;
}

function selectFilename(part: MultipartPartDraft): string {
  const content = part.content;
  const filename = content && typeof content === 'object' ? (content.filename ?? content.name) : undefined;
  if (typeof filename === 'string' && filename.trim()) return filename.trim();
  return part.type;
}

export const ComposerAttachmentsList: React.FC<{
  title: string;
  attachments: MultipartPartDraft[];
  onRemove: (draftId: string) => void;
  onMove: (draftId: string, direction: 'up' | 'down') => void;
  disabled?: boolean;
}> = ({ title, attachments, onRemove, onMove, disabled }) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  if (attachments.length === 0) return null;

  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      {attachments.map((part, idx) => {
        const url = toDataUrlFromContent(part.content);
        const filename = selectFilename(part);
        const isImage = part.type === 'image' && url;
        return (
          <View
            key={part.draftId}
            style={styles.row}
          >
            <View style={styles.preview}>
              {isImage ? (
                <Image
                  source={{ uri: url ?? undefined }}
                  style={styles.thumbnail}
                />
              ) : (
                <Icon
                  name={part.type === 'pdf' ? 'file-text' : 'paperclip'}
                  size={18}
                  color={theme.textSecondary}
                />
              )}
            </View>

            <View style={styles.meta}>
              <Text
                style={styles.filename}
                numberOfLines={1}
              >
                {filename}
              </Text>
              <Text style={styles.typeText}>{part.type}</Text>
            </View>

            <View style={styles.controls}>
              <TouchableOpacity
                onPress={() => onMove(part.draftId, 'up')}
                disabled={disabled || idx === 0}
                style={styles.iconButton}
              >
                <Icon
                  name="arrow-up"
                  size={16}
                  color={idx === 0 || disabled ? theme.border : theme.textSecondary}
                />
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => onMove(part.draftId, 'down')}
                disabled={disabled || idx === attachments.length - 1}
                style={styles.iconButton}
              >
                <Icon
                  name="arrow-down"
                  size={16}
                  color={idx === attachments.length - 1 || disabled ? theme.border : theme.textSecondary}
                />
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => onRemove(part.draftId)}
                disabled={disabled}
                style={styles.iconButton}
              >
                <Icon
                  name="x"
                  size={16}
                  color={disabled ? theme.border : theme.textSecondary}
                />
              </TouchableOpacity>
            </View>
          </View>
        );
      })}
    </View>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    section: {
      marginBottom: 8,
    },
    sectionTitle: {
      fontSize: 12,
      fontWeight: '600',
      color: theme.textSecondary,
      marginBottom: 6,
    },
    row: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingHorizontal: 10,
      paddingVertical: 8,
      backgroundColor: theme.surface,
      borderColor: theme.border,
      borderWidth: 1,
      borderRadius: 10,
      marginBottom: 6,
    },
    preview: {
      width: 44,
      height: 44,
      borderRadius: 10,
      backgroundColor: theme.surfaceAlt,
      alignItems: 'center',
      justifyContent: 'center',
      overflow: 'hidden',
      marginRight: 10,
    },
    thumbnail: {
      width: 44,
      height: 44,
      resizeMode: 'cover',
    },
    meta: {
      flex: 1,
      minWidth: 0,
    },
    filename: {
      fontSize: 13,
      color: theme.text,
      fontWeight: '600',
    },
    typeText: {
      fontSize: 11,
      color: theme.textSecondary,
      marginTop: 1,
    },
    controls: {
      flexDirection: 'row',
      alignItems: 'center',
      marginLeft: 8,
    },
    iconButton: {
      paddingHorizontal: 6,
      paddingVertical: 6,
    },
  });
