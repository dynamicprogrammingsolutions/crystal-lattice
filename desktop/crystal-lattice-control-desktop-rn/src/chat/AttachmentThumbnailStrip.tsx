import React, { useMemo } from 'react';
import {
  ActivityIndicator,
  Image,
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

import { useTheme } from '@crystal-lattice/frontend-rn-components';

export type AttachmentLike = {
  id: string;
  type: string;
  content: any;
  metadata?: any;
  previewUrl?: string | null;
  status?: AttachmentDraftStatus;
  errorMessage?: string | null;
};

export const AttachmentThumbnailStrip: React.FC<{
  attachments: AttachmentLike[];
  disabled?: boolean;
  onPress?: (attachment: AttachmentLike) => void;
  expanded?: boolean;
  onToggleExpanded?: () => void;
}> = ({ attachments, disabled, onPress, expanded, onToggleExpanded }) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const scrollContentStyle = useMemo(() => {
    if (!onToggleExpanded) {
      return styles.scrollContent;
    }
    return [styles.scrollContent, styles.scrollContentWithOverlayButton];
  }, [onToggleExpanded, styles.scrollContent, styles.scrollContentWithOverlayButton]);

  if (!attachments.length) return null;

  return (
    <View style={styles.container}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={scrollContentStyle}>
        {attachments.map((attachment) => {
          const url = selectAttachmentPreviewUrl(attachment.content, attachment.previewUrl);
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
              {attachment.status && attachment.status !== 'ready' && (
                <View
                  style={[
                    styles.statusBadge,
                    attachment.status === 'failed' && styles.statusBadgeDanger,
                  ]}
                >
                  {attachment.status === 'uploading_to_server' ||
                  attachment.status === 'uploading_to_openai' ||
                  attachment.status === 'deleting' ? (
                    <ActivityIndicator size="small" color={theme.surface} />
                  ) : attachment.status === 'failed' ? (
                    <Icon name="alert-circle" size={12} color={theme.surface} />
                  ) : (
                    <Text style={styles.statusBadgeText}>
                      {attachmentDraftStatusLabel(attachment.status, attachment.errorMessage).slice(0, 1)}
                    </Text>
                  )}
                </View>
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

      {onToggleExpanded && (
        <TouchableOpacity
          style={styles.overlayManageButton}
          onPress={onToggleExpanded}
          disabled={disabled}
        >
          <Icon
            name={expanded ? 'chevron-up' : 'chevron-down'}
            size={16}
            color={disabled ? theme.textMuted : theme.textSecondary}
          />
        </TouchableOpacity>
      )}
    </View>
  );
};

const createStyles = (theme: ReturnType<typeof useTheme>) =>
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
      top: 6,
      width: 34,
      height: 34,
      borderRadius: 17,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      shadowColor: '#000000',
      shadowOpacity: 0.12,
      shadowRadius: 4,
      shadowOffset: { width: 0, height: 2 },
      elevation: 2,
    },
    statusBadge: {
      position: 'absolute',
      right: 4,
      bottom: 4,
      minWidth: 18,
      height: 18,
      borderRadius: 9,
      paddingHorizontal: 4,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: theme.textSecondary,
    },
    statusBadgeDanger: {
      backgroundColor: theme.danger,
    },
    statusBadgeText: {
      fontSize: 10,
      fontWeight: '700',
      color: theme.surface,
    },
  });
