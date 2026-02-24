import React, { useMemo } from 'react';
import {
  Image,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import { useTheme, type Theme } from '../theme';

export type AttachmentLike = {
  id: string;
  type: string;
  content: any;
  metadata?: any;
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

export const AttachmentThumbnailStrip: React.FC<{
  attachments: AttachmentLike[];
  disabled?: boolean;
  onPress?: (attachment: AttachmentLike) => void;
  onPressManageAll?: () => void;
}> = ({ attachments, disabled, onPress, onPressManageAll }) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const scrollContentStyle = useMemo(() => {
    if (!onPressManageAll) {
      return styles.scrollContent;
    }
    return [styles.scrollContent, styles.scrollContentWithOverlayButton];
  }, [onPressManageAll, styles.scrollContent, styles.scrollContentWithOverlayButton]);

  if (!attachments.length) return null;

  return (
    <View style={styles.container}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={scrollContentStyle}
      >
        {attachments.map((attachment) => {
          const url = selectAttachmentUrl(attachment.content);
          const isImage = attachment.type === 'image' && url;
          const tile = (
            <View style={styles.tileInner}>
              {isImage ? (
                <Image source={{ uri: url ?? undefined }} style={styles.thumbnail} />
              ) : (
                <Icon
                  name={attachment.type === 'pdf' ? 'file-text' : 'paperclip'}
                  size={18}
                  color={theme.textSecondary}
                />
              )}
            </View>
          );

          if (!onPress) {
            return (
              <View key={attachment.id} style={styles.tile}>
                {tile}
              </View>
            );
          }

          return (
            <TouchableOpacity
              key={attachment.id}
              style={styles.tile}
              onPress={() => onPress(attachment)}
              disabled={disabled}
            >
              {tile}
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {onPressManageAll && (
        <TouchableOpacity
          style={styles.overlayManageButton}
          onPress={onPressManageAll}
          disabled={disabled}
        >
          <Icon
            name="edit-2"
            size={16}
            color={disabled ? theme.textMuted : theme.textSecondary}
          />
        </TouchableOpacity>
      )}
    </View>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    container: {
      position: 'relative',
      marginBottom: 4,
    },
    scrollContent: {
      paddingHorizontal: 10,
      paddingVertical: 4,
      gap: 8,
    },
    scrollContentWithOverlayButton: {
      paddingRight: 56,
    },
    tile: {
      width: 54,
      height: 54,
      borderRadius: 10,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      overflow: 'hidden',
    },
    tileInner: {
      flex: 1,
      alignItems: 'center',
      justifyContent: 'center',
    },
    thumbnail: {
      width: 54,
      height: 54,
      resizeMode: 'cover',
    },
    overlayManageButton: {
      position: 'absolute',
      right: 10,
      top: '50%',
      width: 34,
      height: 34,
      borderRadius: 17,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      transform: [{ translateY: -17 }],
      shadowColor: '#000000',
      shadowOpacity: 0.12,
      shadowRadius: 4,
      shadowOffset: { width: 0, height: 2 },
      elevation: 2,
    },
  });
