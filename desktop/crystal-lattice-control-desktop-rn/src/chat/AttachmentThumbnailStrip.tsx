import React, { useMemo } from 'react';
import {
  Image,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { selectAttachmentPreviewUrl } from '@crystal-lattice/frontend-sdk';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

export type AttachmentLike = {
  id: string;
  type: string;
  content: any;
  metadata?: any;
  previewUrl?: string | null;
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
  });
