import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Linking,
  Modal,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import RNFS from 'react-native-fs';
import {
  CameraRoll,
  iosRequestAddOnlyGalleryPermission,
} from '@react-native-camera-roll/camera-roll';
import { gestureHandlerRootHOC } from 'react-native-gesture-handler';
import { ImageZoom } from '@likashefqet/react-native-image-zoom';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import {
  downloadSessionAttachment,
  selectAttachmentPreviewUrl,
  selectSessionAssetId,
} from '@crystal-lattice/frontend-sdk';

import type { AttachmentLike } from './AttachmentThumbnailStrip';
import {
  attachmentFilename,
  attachmentMimeType,
  parseDataUrl,
  resolveAttachmentDownloadPluginId,
  type MessageAttachmentSnapshot,
} from '../messageAttachments';
import {
  saveLocalDocument,
  shareLocalDocument,
} from '../utils/generatedFileActions';
import { useTheme, type Theme } from '../theme';

function attachmentViewerCacheKey(
  attachment: MessageAttachmentSnapshot,
  sessionId?: string,
): string {
  const assetId = selectSessionAssetId(attachment.content);
  const pluginId = resolveAttachmentDownloadPluginId(attachment);
  if (assetId) {
    return [
      'session',
      sessionId || '',
      'asset',
      assetId,
      'plugin',
      pluginId || '',
    ].join(':');
  }
  return [
    'session',
    sessionId || '',
    'message',
    attachment.messageIndex ?? 'stream',
    'part',
    attachment.partIndex,
  ].join(':');
}

function attachmentCacheFilePrefix(cacheKey: string): string {
  return cacheKey.replace(/[^a-zA-Z0-9._-]+/g, '-');
}

export const AttachmentViewerHost: React.FC<{
  backend?: AgentBackend | null;
  sessionId?: string;
  attachment: MessageAttachmentSnapshot | null;
  onRequestClose: () => void;
}> = ({ backend, sessionId, attachment, onRequestClose }) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const localFilePromisesRef = useRef<Partial<Record<string, Promise<string>>>>({});
  const fullResolutionPromisesRef = useRef<Partial<Record<string, Promise<string>>>>({});
  const fullResolutionUriByKeyRef = useRef<Record<string, string>>({});
  const [activeImageSource, setActiveImageSource] = useState<{
    key: string;
    uri: string;
  } | null>(null);

  const selectedKey = attachment?.cacheKey ?? null;
  const previewUrl = attachment
    ? selectAttachmentPreviewUrl(attachment.content, attachment.previewUrl)
    : null;
  const isImage =
    attachment?.type === 'image' && typeof previewUrl === 'string' && previewUrl.length > 0;
  const cacheKey = attachment ? attachmentViewerCacheKey(attachment, sessionId) : null;

  useEffect(() => {
    if (!attachment || !isImage || typeof previewUrl !== 'string' || !cacheKey) {
      setActiveImageSource(null);
      return;
    }
    setActiveImageSource({
      key: cacheKey,
      uri: fullResolutionUriByKeyRef.current[cacheKey] || previewUrl,
    });
  }, [attachment, cacheKey, isImage, previewUrl]);

  const ensureAttachmentLocalFile = useCallback(
    async (targetAttachment: AttachmentLike & { cacheKey?: string }, options?: { preferOriginal?: boolean }) => {
      const preferOriginal = !!options?.preferOriginal;
      const key =
        'partIndex' in targetAttachment
          ? attachmentViewerCacheKey(targetAttachment as MessageAttachmentSnapshot, sessionId)
          : targetAttachment.cacheKey ?? targetAttachment.id;
      if (preferOriginal && fullResolutionUriByKeyRef.current[key]) {
        return fullResolutionUriByKeyRef.current[key];
      }

      const existingPromise = localFilePromisesRef.current[key];
      if (existingPromise) {
        return existingPromise;
      }

      const promise = (async () => {
        const filename = attachmentFilename(targetAttachment);
        const assetId = selectSessionAssetId(targetAttachment.content);
        const pluginId = resolveAttachmentDownloadPluginId(targetAttachment);
        const cacheDir = `${RNFS.CachesDirectoryPath}/attachment-previews`;
        await RNFS.mkdir(cacheDir);
        const targetPath = `${cacheDir}/${attachmentCacheFilePrefix(key)}-${filename}`;

        if (preferOriginal && backend && sessionId && assetId && pluginId) {
          const downloaded = await downloadSessionAttachment({
            backend,
            sessionId,
            assetId,
            pluginId,
          });
          await RNFS.writeFile(targetPath, downloaded.data_base64, 'base64');
          return `file://${targetPath}`;
        }

        const sourceUrl = selectAttachmentPreviewUrl(
          targetAttachment.content,
          targetAttachment.previewUrl,
        );
        if (typeof sourceUrl !== 'string' || !sourceUrl) {
          throw new Error('No image source available for this attachment.');
        }

        const dataUrl = parseDataUrl(sourceUrl);
        if (dataUrl) {
          await RNFS.writeFile(targetPath, dataUrl.dataBase64, 'base64');
          return `file://${targetPath}`;
        }

        if (sourceUrl.startsWith('http://') || sourceUrl.startsWith('https://')) {
          const result = RNFS.downloadFile({ fromUrl: sourceUrl, toFile: targetPath });
          const downloaded = await result.promise;
          if (downloaded.statusCode && downloaded.statusCode >= 400) {
            throw new Error(`Failed to download image (${downloaded.statusCode}).`);
          }
          return `file://${targetPath}`;
        }

        if (sourceUrl.startsWith('file://')) {
          return sourceUrl;
        }

        throw new Error('Unsupported image source.');
      })();

      localFilePromisesRef.current[key] = promise;

      try {
        const localUri = await promise;
        if (preferOriginal) {
          fullResolutionUriByKeyRef.current = {
            ...fullResolutionUriByKeyRef.current,
            [key]: localUri,
          };
        }
        return localUri;
      } finally {
        delete localFilePromisesRef.current[key];
      }
    },
    [backend, sessionId],
  );

  const downloadFullResolutionFile = useCallback(
    async (targetAttachment: MessageAttachmentSnapshot) => {
      const key = attachmentViewerCacheKey(targetAttachment, sessionId);
      if (fullResolutionUriByKeyRef.current[key]) {
        const cachedUri = fullResolutionUriByKeyRef.current[key];
        setActiveImageSource({ key, uri: cachedUri });
        return cachedUri;
      }

      const existingPromise = fullResolutionPromisesRef.current[key];
      if (existingPromise) {
        return existingPromise;
      }

      const promise = (async () => {
        const assetId = selectSessionAssetId(targetAttachment.content);
        if (!backend || !sessionId || !assetId) {
          throw new Error('Full-size download is unavailable for this attachment.');
        }

        const pluginId = resolveAttachmentDownloadPluginId(targetAttachment);
        const filename = attachmentFilename(targetAttachment);
        const cacheDir = `${RNFS.CachesDirectoryPath}/attachment-previews`;
        await RNFS.mkdir(cacheDir);
        const targetPath = `${cacheDir}/${attachmentCacheFilePrefix(key)}-full-${filename}`;
        const downloaded = await downloadSessionAttachment({
          backend,
          sessionId,
          assetId,
          pluginId: pluginId ?? '',
        });
        await RNFS.writeFile(targetPath, downloaded.data_base64, 'base64');
        return `file://${targetPath}`;
      })();

      fullResolutionPromisesRef.current[key] = promise;

      try {
        const localUri = await promise;
        fullResolutionUriByKeyRef.current = {
          ...fullResolutionUriByKeyRef.current,
          [key]: localUri,
        };
        setActiveImageSource({ key, uri: localUri });
        return localUri;
      } finally {
        delete fullResolutionPromisesRef.current[key];
      }
    },
    [backend, sessionId],
  );

  const handleSaveToFile = useCallback(
    async (targetAttachment: MessageAttachmentSnapshot) => {
      const localUri = await ensureAttachmentLocalFile(targetAttachment, { preferOriginal: true });
      return saveLocalDocument({
        localUri,
        mimeType: attachmentMimeType(targetAttachment),
        fileName: attachmentFilename(targetAttachment),
      });
    },
    [ensureAttachmentLocalFile],
  );

  const handleSaveToPhotos = useCallback(
    async (targetAttachment: MessageAttachmentSnapshot) => {
      const localUri = await ensureAttachmentLocalFile(targetAttachment, { preferOriginal: true });
      if (Platform.OS === 'ios') {
        const status = await iosRequestAddOnlyGalleryPermission();
        if (!['granted', 'limited'].includes(status)) {
          throw new Error('Photo Library permission was not granted.');
        }
      }
      await CameraRoll.saveAsset(localUri, { type: 'photo' });
    },
    [ensureAttachmentLocalFile],
  );

  const handleShareAttachment = useCallback(
    async (targetAttachment: MessageAttachmentSnapshot) => {
      const localUri = await ensureAttachmentLocalFile(targetAttachment, { preferOriginal: true });
      await shareLocalDocument({
        localUri,
        mimeType: attachmentMimeType(targetAttachment),
        fileName: attachmentFilename(targetAttachment),
      });
    },
    [ensureAttachmentLocalFile],
  );

  useEffect(() => {
    if (!attachment) {
      return;
    }

    if (isImage) {
      return;
    }

    const url = selectAttachmentPreviewUrl(attachment.content, attachment.previewUrl);
    const openExternal = async () => {
      if (
        attachment.type === 'pdf' &&
        typeof url === 'string' &&
        (url.startsWith('http://') || url.startsWith('https://'))
      ) {
        try {
          await Linking.openURL(url);
          onRequestClose();
          return;
        } catch (err) {
          console.log('Failed to open attachment url', err);
        }
      }
      Alert.alert('Unavailable', 'This attachment cannot be previewed here.');
      onRequestClose();
    };

    void openExternal();
  }, [attachment, isImage, onRequestClose]);

  if (!attachment || !isImage || typeof previewUrl !== 'string') {
    return null;
  }

  const key = cacheKey ?? selectedKey ?? attachment.cacheKey;
  const displayUri =
    activeImageSource?.key === key
      ? activeImageSource.uri
      : fullResolutionUriByKeyRef.current[key] || previewUrl;
  const fullResolutionLoaded = !!fullResolutionUriByKeyRef.current[key];

  return (
    <Modal
      visible
      transparent
      animationType="fade"
      statusBarTranslucent
      onRequestClose={onRequestClose}
      supportedOrientations={[
        'portrait',
        'portrait-upside-down',
        'landscape',
        'landscape-left',
        'landscape-right',
      ]}
    >
      <GestureAttachmentViewerModalContent>
        <View style={styles.modalOverlay}>
          <View style={styles.zoomArea}>
            <ImageZoom
              key={key}
              uri={displayUri}
              style={styles.zoomImage}
              minScale={1}
              maxScale={6}
              doubleTapScale={3}
              isPinchEnabled
              isPanEnabled
              isDoubleTapEnabled
            />
          </View>
          <AttachmentViewerFooter
            styles={styles}
            theme={theme}
            attachment={attachment}
            fullResolutionLoaded={fullResolutionLoaded}
            onLoadFullResolution={downloadFullResolutionFile}
            onSaveToFile={handleSaveToFile}
            onSaveToPhotos={handleSaveToPhotos}
            onShareAttachment={handleShareAttachment}
            close={onRequestClose}
          />
        </View>
      </GestureAttachmentViewerModalContent>
    </Modal>
  );
};

const AttachmentViewerFooter: React.FC<{
  styles: ReturnType<typeof createStyles>;
  theme: Theme;
  attachment: MessageAttachmentSnapshot;
  fullResolutionLoaded: boolean;
  onLoadFullResolution: (attachment: MessageAttachmentSnapshot) => Promise<string>;
  onSaveToFile: (attachment: MessageAttachmentSnapshot) => Promise<string>;
  onSaveToPhotos: (attachment: MessageAttachmentSnapshot) => Promise<void>;
  onShareAttachment: (attachment: MessageAttachmentSnapshot) => Promise<void>;
  close: () => void;
}> = React.memo(({
  styles,
  theme,
  attachment,
  fullResolutionLoaded,
  onLoadFullResolution,
  onSaveToFile,
  onSaveToPhotos,
  onShareAttachment,
  close,
}) => {
  const [loadingFullResolution, setLoadingFullResolution] = useState(false);
  const [fullResolutionError, setFullResolutionError] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(fullResolutionLoaded);

  const handleLoadFullResolution = useCallback(() => {
    setLoadingFullResolution(true);
    setFullResolutionError(null);
    void onLoadFullResolution(attachment).then(
      () => {
        setLoaded(true);
      },
      (err: any) => {
        setFullResolutionError(err?.message || 'Unable to load the full-size image.');
      },
    ).finally(() => {
      setLoadingFullResolution(false);
    });
  }, [attachment, onLoadFullResolution]);

  return (
    <View style={styles.previewFooter} pointerEvents="auto">
      {loadingFullResolution && !loaded ? (
        <View style={styles.previewLoadingRow}>
          <ActivityIndicator size="small" color={theme.surface} />
          <Text style={styles.previewLoadingText}>Loading full resolution...</Text>
        </View>
      ) : null}
      {fullResolutionError ? (
        <Text style={styles.previewErrorText}>{fullResolutionError}</Text>
      ) : null}
      <View style={styles.previewFooterActions}>
        <TouchableOpacity
          style={[
            styles.previewFooterButton,
            loaded ? styles.previewFooterButtonSecondary : styles.previewFooterButtonPrimary,
          ]}
          onPress={handleLoadFullResolution}
          disabled={loadingFullResolution || loaded}
        >
          {loadingFullResolution ? (
            <ActivityIndicator size="small" color={theme.textOnPrimary} />
          ) : (
            <Text
              style={
                loaded
                  ? styles.previewFooterButtonSecondaryText
                  : styles.previewFooterButtonPrimaryText
              }
            >
              {loaded ? 'Full Size Loaded' : 'Load Full Size'}
            </Text>
          )}
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.previewFooterButton, styles.previewFooterButtonSecondary]}
          onPress={() => void onSaveToFile(attachment).then(
            (savedName) => Alert.alert('Saved', `Saved ${savedName}`),
            (err: any) => Alert.alert('Save failed', err?.message || 'Unable to save file.'),
          )}
        >
          <Text style={styles.previewFooterButtonSecondaryText}>Save to File</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.previewFooterButton, styles.previewFooterButtonSecondary]}
          onPress={() => void onSaveToPhotos(attachment).then(
            () => Alert.alert('Saved', 'Image saved to Photos.'),
            (err: any) => Alert.alert('Save failed', err?.message || 'Unable to save to Photos.'),
          )}
        >
          <Text style={styles.previewFooterButtonSecondaryText}>Save to Photos</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.previewFooterButton, styles.previewFooterButtonPrimary]}
          onPress={() => void onShareAttachment(attachment).catch((err: any) => {
            Alert.alert('Share failed', err?.message || 'Unable to share image.');
          })}
        >
          <Text style={styles.previewFooterButtonPrimaryText}>Share</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.previewFooterButton, styles.previewFooterButtonSecondary]}
          onPress={close}
        >
          <Text style={styles.previewFooterButtonSecondaryText}>Close</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
});

const AttachmentViewerModalContent: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <View style={modalContentStyles.root}>{children}</View>
);

const GestureAttachmentViewerModalContent = gestureHandlerRootHOC(AttachmentViewerModalContent);

const modalContentStyles = StyleSheet.create({
  root: {
    flex: 1,
  },
});

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    modalOverlay: {
      flex: 1,
      backgroundColor: 'rgba(10, 16, 24, 0.92)',
      justifyContent: 'space-between',
    },
    zoomArea: {
      flex: 1,
      minHeight: 0,
    },
    zoomImage: {
      flex: 1,
      width: '100%',
      height: '100%',
    },
    previewFooter: {
      paddingHorizontal: 16,
      paddingBottom: 18,
      paddingTop: 10,
      backgroundColor: 'rgba(10, 16, 24, 0.68)',
    },
    previewLoadingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 10,
      gap: 8,
    },
    previewLoadingText: {
      color: theme.surface,
      fontSize: theme.typography.fontSize.small,
      fontWeight: '600',
    },
    previewErrorText: {
      color: theme.surface,
      fontSize: theme.typography.fontSize.small,
      fontWeight: '600',
      marginBottom: 10,
      textAlign: 'center',
    },
    previewFooterActions: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      justifyContent: 'center',
      gap: 8,
    },
    previewFooterButton: {
      minWidth: 110,
      borderRadius: 10,
      paddingHorizontal: 12,
      paddingVertical: 10,
      alignItems: 'center',
      justifyContent: 'center',
    },
    previewFooterButtonPrimary: {
      backgroundColor: theme.primary,
    },
    previewFooterButtonSecondary: {
      backgroundColor: theme.surface,
    },
    previewFooterButtonPrimaryText: {
      color: theme.textOnPrimary,
      fontSize: theme.typography.fontSize.secondary,
      fontWeight: '700',
    },
    previewFooterButtonSecondaryText: {
      color: theme.text,
      fontSize: theme.typography.fontSize.secondary,
      fontWeight: '700',
    },
  });

export default AttachmentViewerHost;