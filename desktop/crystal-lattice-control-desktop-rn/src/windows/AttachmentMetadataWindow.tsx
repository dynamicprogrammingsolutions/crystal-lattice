import React, { useCallback, useMemo } from 'react';
import { Image, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import { ThemeProvider, useTheme } from '@crystal-lattice/frontend-rn-components';
import { selectAttachmentPreviewUrl } from '@crystal-lattice/frontend-sdk';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import {
  closeAttachmentMetadataWindow,
  useActiveAttachmentMetadataWindow,
} from './attachmentMetadataCoordinator';
import { AttachmentMetadataPopoverContent } from '../chat/AttachmentMetadataPopoverContent';

function selectFilename(content: any): string | null {
  if (!content || typeof content !== 'object') return null;
  const raw = content.filename ?? content.name;
  if (typeof raw === 'string' && raw.trim()) return raw.trim();
  return null;
}

export function AttachmentMetadataWindow(): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  return (
    <ThemeProvider theme={systemTheme}>
      <AttachmentMetadataWindowInner />
    </ThemeProvider>
  );
}

function AttachmentMetadataWindowInner(): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const active = useActiveAttachmentMetadataWindow();

  const close = useCallback(() => {
    closeAttachmentMetadataWindow(active?.state.id);
  }, [active?.state.id]);

  if (!active) {
    return (
      <View style={styles.emptyRoot}>
        <Text style={styles.emptyText}>No attachment selected.</Text>
        <TouchableOpacity style={styles.emptyButton} onPress={close}>
          <Text style={styles.emptyButtonText}>Close</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const { attachmentType, attachmentContent, metadataUi, initialMetadata } = active.state;
  const previewUrl = selectAttachmentPreviewUrl(attachmentContent);
  const filename = selectFilename(attachmentContent);

  const preview = (
    <View style={styles.previewRoot}>
      {attachmentType === 'image' && previewUrl ? (
        <Image source={{ uri: previewUrl }} style={styles.previewImage} />
      ) : (
        <View style={styles.previewFallback}>
          <Icon
            name={attachmentType === 'pdf' ? 'file-text' : 'paperclip'}
            size={28}
            color={theme.textSecondary}
          />
          <Text style={styles.previewFallbackText} numberOfLines={1}>
            {filename ?? attachmentType}
          </Text>
        </View>
      )}
    </View>
  );

  return (
    <View style={styles.root}>
      <AttachmentMetadataPopoverContent
        title={active.state.title}
        showTitle={false}
        header={preview}
        metadataUi={metadataUi}
        initialMetadata={initialMetadata}
        onCancel={() => {
          active.state.onCancel();
          close();
        }}
        onSave={(metadata) => {
          active.state.onSave(metadata);
          close();
        }}
      />
    </View>
  );
}

const createStyles = (theme: ReturnType<typeof useTheme>) =>
  StyleSheet.create({
    root: {
      flex: 1,
    },
    emptyRoot: {
      flex: 1,
      padding: 18,
      gap: 14,
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: theme.surface,
    },
    emptyText: {
      fontSize: 13,
      color: theme.textSecondary,
    },
    emptyButton: {
      paddingHorizontal: 14,
      paddingVertical: 10,
      borderRadius: 10,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surfaceAlt,
    },
    emptyButtonText: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.text,
    },
    previewRoot: {
      width: '100%',
      height: 220,
      borderRadius: 12,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surfaceAlt,
      overflow: 'hidden',
      marginBottom: 10,
    },
    previewImage: {
      width: '100%',
      height: '100%',
      resizeMode: 'contain',
      backgroundColor: '#000000',
    },
    previewFallback: {
      flex: 1,
      alignItems: 'center',
      justifyContent: 'center',
      gap: 10,
      paddingHorizontal: 14,
    },
    previewFallbackText: {
      fontSize: 12,
      fontWeight: '600',
      color: theme.textSecondary,
    },
  });
