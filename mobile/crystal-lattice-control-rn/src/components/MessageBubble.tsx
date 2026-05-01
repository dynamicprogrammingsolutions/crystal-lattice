import React, { useCallback, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Linking,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import RNFS from 'react-native-fs';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import {
  downloadSessionAttachment,
  selectAttachmentPreviewUrl,
  selectSessionAssetId,
} from '@crystal-lattice/frontend-sdk';
import ImageModal from 'react-native-image-modal';
import Share from 'react-native-share';
import { saveDocuments } from '@react-native-documents/picker';
import {
  CameraRoll,
  iosRequestAddOnlyGalleryPermission,
} from '@react-native-camera-roll/camera-roll';
import type { ApiMessage, UiSchemaElement } from '../api';
import MessageActionsBar from './MessageActionsBar';
import type { MessageActionKey, MessageActionDefinition } from '../messageActions';
import { selectDisplayContent, selectSingleLineContent } from '../messageUtils';
import MarkdownMessageContent from './MarkdownMessageContent';
import { AttachmentThumbnailStrip, type AttachmentLike } from './AttachmentThumbnailStrip';
import { useTheme, type Theme } from '../theme';
import { extractByPath, renderTemplate, formatValueForElement, evaluateCondition } from '../uiSchemaUtils';

const CHEVRON_ICON_SIZE = 16;
const CHEVRON_HIT_SLOP = { top: 4, bottom: 4, left: 4, right: 4 };

function toSingleLinePreview(text: string, maxLen = 160): string {
  const normalized = text.replace(/\s+/g, ' ').trim();
  if (!normalized) return '';
  if (normalized.length <= maxLen) return normalized;
  return `${normalized.slice(0, Math.max(0, maxLen - 1))}...`;
}

type MultipartPart = {
  type?: string;
  content?: any;
  metadata?: any;
};

type WebLinkEntry = {
  url?: string;
  title?: string;
  content?: string;
  snippet?: string;
};

function selectWebLinkEntries(value: any): WebLinkEntry[] {
  if (!Array.isArray(value)) return [];
  return value.filter((entry): entry is WebLinkEntry => {
    if (!entry || typeof entry !== 'object') return false;
    return typeof (entry as any).url === 'string' || typeof (entry as any).title === 'string';
  });
}

function selectMultipartParts(message: ApiMessage): MultipartPart[] {
  const parts = (message as any)?.multipartContent;
  return Array.isArray(parts) ? (parts as MultipartPart[]) : [];
}

function extensionFromMimeType(mimeType: string): string {
  switch (mimeType) {
    case 'image/png':
      return 'png';
    case 'image/jpeg':
      return 'jpg';
    case 'image/webp':
      return 'webp';
    case 'image/gif':
      return 'gif';
    default:
      return 'bin';
  }
}

function attachmentFilename(attachment: AttachmentLike): string {
  const content = attachment.content;
  if (content && typeof content === 'object' && typeof content.filename === 'string' && content.filename) {
    return content.filename;
  }
  const mimeType = attachmentMimeType(attachment);
  return `attachment-${attachment.id}.${extensionFromMimeType(mimeType)}`;
}

function attachmentMimeType(attachment: AttachmentLike): string {
  const content = attachment.content;
  if (content && typeof content === 'object' && typeof content.mime_type === 'string' && content.mime_type) {
    return content.mime_type;
  }
  return attachment.type === 'image' ? 'image/png' : 'application/octet-stream';
}

function parseDataUrl(url: string): { mimeType: string; dataBase64: string } | null {
  const match = url.match(/^data:([^;]+);base64,(.+)$/i);
  if (!match) return null;
  return {
    mimeType: match[1] || 'application/octet-stream',
    dataBase64: match[2] || '',
  };
}

const MessageAttachments: React.FC<{
  message: ApiMessage;
  onBlue?: boolean;
  backend?: AgentBackend | null;
  sessionId?: string;
}> = ({
  message,
  onBlue,
  backend,
  sessionId,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const parts = selectMultipartParts(message);
  const [fullResolutionUriById, setFullResolutionUriById] = useState<Record<string, string>>({});
  const [loadingFullResolutionById, setLoadingFullResolutionById] = useState<Record<string, boolean>>({});
  const localFilePromisesRef = useRef<Partial<Record<string, Promise<string>>>>({});

  if (parts.length === 0) return null;

  const attachments: AttachmentLike[] = parts.map((part, idx) => {
    const type = typeof part?.type === 'string' ? part.type : 'attachment';
    return {
      id: `${idx}`,
      type,
      content: part?.content,
      metadata: part?.metadata,
    };
  });

  const ensureAttachmentLocalFile = useCallback(
    async (attachment: AttachmentLike, options?: { preferOriginal?: boolean }): Promise<string> => {
      const preferOriginal = !!options?.preferOriginal;
      if (preferOriginal && fullResolutionUriById[attachment.id]) {
        return fullResolutionUriById[attachment.id];
      }
      const existingPromise = localFilePromisesRef.current[attachment.id];
      if (existingPromise) {
        return existingPromise;
      }

      const promise = (async () => {
        const filename = attachmentFilename(attachment);
        const mimeType = attachmentMimeType(attachment);
        const assetId = selectSessionAssetId(attachment.content);
        const pluginId = resolveAttachmentDownloadPluginId(attachment);
        const cacheDir = `${RNFS.CachesDirectoryPath}/attachment-previews`;
        await RNFS.mkdir(cacheDir);
        const targetPath = `${cacheDir}/${attachment.id}-${filename}`;

        if (
          preferOriginal &&
          backend &&
          sessionId &&
          assetId &&
          pluginId
        ) {
          const downloaded = await downloadSessionAttachment({
            backend,
            sessionId,
            assetId,
            pluginId,
          });
          await RNFS.writeFile(targetPath, downloaded.data_base64, 'base64');
          return `file://${targetPath}`;
        }

        const previewUrl = selectAttachmentPreviewUrl(attachment.content, attachment.previewUrl);
        if (typeof previewUrl !== 'string' || !previewUrl) {
          throw new Error('No image source available for this attachment.');
        }

        const dataUrl = parseDataUrl(previewUrl);
        if (dataUrl) {
          await RNFS.writeFile(targetPath, dataUrl.dataBase64, 'base64');
          return `file://${targetPath}`;
        }

        const normalized = previewUrl.startsWith('file://') ? previewUrl : previewUrl;
        if (normalized.startsWith('http://') || normalized.startsWith('https://')) {
          const result = RNFS.downloadFile({ fromUrl: normalized, toFile: targetPath });
          const downloaded = await result.promise;
          if (downloaded.statusCode && downloaded.statusCode >= 400) {
            throw new Error(`Failed to download image (${downloaded.statusCode}).`);
          }
          return `file://${targetPath}`;
        }

        if (normalized.startsWith('file://')) {
          return normalized;
        }

        throw new Error('Unsupported image source.');
      })();

      localFilePromisesRef.current[attachment.id] = promise;
      if (preferOriginal) {
        setLoadingFullResolutionById((prev) => ({ ...prev, [attachment.id]: true }));
      }

      try {
        const localUri = await promise;
        if (preferOriginal) {
          setFullResolutionUriById((prev) => ({ ...prev, [attachment.id]: localUri }));
        }
        return localUri;
      } finally {
        delete localFilePromisesRef.current[attachment.id];
        if (preferOriginal) {
          setLoadingFullResolutionById((prev) => ({ ...prev, [attachment.id]: false }));
        }
      }
    },
    [backend, fullResolutionUriById, sessionId],
  );

  const handleSaveToFile = useCallback(
    async (attachment: AttachmentLike) => {
      const localUri = await ensureAttachmentLocalFile(attachment, { preferOriginal: true });
      const result = await saveDocuments({
        sourceUris: [localUri],
        mimeType: attachmentMimeType(attachment),
        fileName: attachmentFilename(attachment),
        copy: true,
      });
      const saved = result[0];
      if (saved?.error) {
        throw new Error(saved.error);
      }
      return saved?.name || attachmentFilename(attachment);
    },
    [ensureAttachmentLocalFile],
  );

  const handleSaveToPhotos = useCallback(
    async (attachment: AttachmentLike) => {
      const localUri = await ensureAttachmentLocalFile(attachment, { preferOriginal: true });
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
    async (attachment: AttachmentLike) => {
      const localUri = await ensureAttachmentLocalFile(attachment, { preferOriginal: true });
      await Share.open({
        url: localUri,
        type: attachmentMimeType(attachment),
        filename: attachmentFilename(attachment),
        failOnCancel: false,
      });
    },
    [ensureAttachmentLocalFile],
  );

  const handleZoomStart = useCallback(
    (attachment: AttachmentLike, scale: number) => {
      if (scale <= 1.01 || fullResolutionUriById[attachment.id] || loadingFullResolutionById[attachment.id]) {
        return;
      }
      void ensureAttachmentLocalFile(attachment, { preferOriginal: true });
    },
    [ensureAttachmentLocalFile, fullResolutionUriById, loadingFullResolutionById],
  );

  return (
    <View style={[styles.attachmentsWrapper, onBlue && styles.attachmentsWrapperOnBlue]}>
      <AttachmentThumbnailStrip
        attachments={attachments}
        onPress={async (attachment) => {
          const url = selectAttachmentPreviewUrl(attachment.content);
          const isPdf = attachment.type === 'pdf' && url;
          const isImage = attachment.type === 'image' && url;
          if (typeof url !== 'string' || !url) {
            return;
          }
          if (isPdf && (url.startsWith('http://') || url.startsWith('https://'))) {
            try {
              await Linking.openURL(url);
              return;
            } catch (err) {
              console.log('Failed to open attachment url', err);
            }
          }
          if (!isImage) {
            Alert.alert('Unavailable', 'This attachment cannot be previewed here.');
          }
        }}
        renderTile={({ attachment, tile }) => {
          const previewUrl = selectAttachmentPreviewUrl(attachment.content, attachment.previewUrl);
          if (attachment.type !== 'image' || typeof previewUrl !== 'string' || !previewUrl) {
            return tile;
          }
          const displayUri = fullResolutionUriById[attachment.id] || previewUrl;
          return (
            <ImageModal
              source={{ uri: displayUri }}
              style={styles.imageModalTile}
              resizeMode="cover"
              modalImageResizeMode="contain"
              overlayBackgroundColor="rgba(10, 16, 24, 0.92)"
              swipeToDismiss
              renderFooter={(close) => (
                <View style={styles.previewFooter}>
                  {loadingFullResolutionById[attachment.id] && !fullResolutionUriById[attachment.id] ? (
                    <View style={styles.previewLoadingRow}>
                      <ActivityIndicator size="small" color={theme.surface} />
                      <Text style={styles.previewLoadingText}>Loading full resolution...</Text>
                    </View>
                  ) : null}
                  <View style={styles.previewFooterActions}>
                    <TouchableOpacity
                      style={[styles.previewFooterButton, styles.previewFooterButtonSecondary]}
                      onPress={() => void handleSaveToFile(attachment).then(
                        (savedName) => Alert.alert('Saved', `Saved ${savedName}`),
                        (err: any) => Alert.alert('Save failed', err?.message || 'Unable to save file.'),
                      )}
                    >
                      <Text style={styles.previewFooterButtonSecondaryText}>Save to File</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.previewFooterButton, styles.previewFooterButtonSecondary]}
                      onPress={() => void handleSaveToPhotos(attachment).then(
                        () => Alert.alert('Saved', 'Image saved to Photos.'),
                        (err: any) => Alert.alert('Save failed', err?.message || 'Unable to save to Photos.'),
                      )}
                    >
                      <Text style={styles.previewFooterButtonSecondaryText}>Save to Photos</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.previewFooterButton, styles.previewFooterButtonPrimary]}
                      onPress={() => void handleShareAttachment(attachment).catch((err: any) => {
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
              )}
              onMove={(position) => handleZoomStart(attachment, position.scale)}
            />
          );
        }}
      />
    </View>
  );
};

export interface MessageBubbleProps {
  index: number;
  message: ApiMessage;
  backend?: AgentBackend | null;
  sessionId?: string;
  isActive?: boolean;
  pinnedActions?: MessageActionKey[];
  onAction?: (action: MessageActionKey, index: number, message: ApiMessage) => void;
  onChangePinnedForRole?: (role: string, pinned: MessageActionKey[]) => void;
  allowedActions?: MessageActionKey[];
  isEditing?: boolean;
  editingText?: string;
  onChangeEditingText?: (text: string) => void;
  onSubmitEdit?: (index: number, message: ApiMessage, newText: string) => void;
  onCancelEdit?: () => void;
  renderMode?: 'markdown' | 'raw';
  footerElements?: UiSchemaElement[];
  pluginActionDefs?: MessageActionDefinition[];
}

function resolveAttachmentDownloadPluginId(attachment: AttachmentLike): string | null {
  const metadata = attachment.metadata;
  if (
    metadata &&
    typeof metadata === 'object' &&
    typeof (metadata as any).download_plugin_id === 'string' &&
    (metadata as any).download_plugin_id
  ) {
    return String((metadata as any).download_plugin_id);
  }
  return null;
}


const UserMessageBubble: React.FC<MessageBubbleProps> = ({
  index,
  message,
  backend,
  sessionId,
  isActive,
  pinnedActions,
  onAction,
  onChangePinnedForRole,
  allowedActions,
  isEditing,
  editingText,
  onChangeEditingText,
  onSubmitEdit,
  onCancelEdit,
  renderMode,
  footerElements,
  pluginActionDefs,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const content = selectDisplayContent(message);
  const role = 'user';
  const footerParts = useMemo(() => {
    const elements = footerElements || [];
    const parts: string[] = [];
    elements.forEach((el) => {
      if (!el || el.ui_type !== 'message_footer') return;
      const condition = (el as any).condition;
      if (condition != null && !evaluateCondition(condition, message)) return;
      const rawValue = extractByPath(message, el.data);
      const valueForTemplate = formatValueForElement(el, rawValue);
      if (valueForTemplate === null || valueForTemplate === undefined || valueForTemplate === '') return;
      const text = renderTemplate(el.template ?? '{{data}}', valueForTemplate);
      if (text) parts.push(text);
    });
    return parts;
  }, [footerElements, message]);

  if (isEditing && onChangeEditingText && onSubmitEdit && onCancelEdit) {
    return (
      <View style={styles.row}>
        <View style={[styles.bubble, styles.userBubble]}>
          <Text style={[styles.headerText, styles.standaloneHeaderText]}>{`[${index}] User`}</Text>
          <TextInput
            style={[styles.editInput, styles.editInputOnBlue]}
            value={editingText ?? ''}
            onChangeText={onChangeEditingText}
            multiline
          />
          <View style={styles.editButtonsRow}>
            <TouchableOpacity
              style={[styles.editButton, styles.editButtonSecondary]}
              onPress={onCancelEdit}
            >
              <Text style={styles.editButtonTextSecondary}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.editButton, styles.editButtonPrimary]}
              onPress={() => onSubmitEdit(index, message, editingText ?? '')}
            >
              <Text style={styles.editButtonTextPrimary}>Save</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.userBubble]}>
        <Text style={[styles.headerText, styles.standaloneHeaderText]}>{`[${index}] User`}</Text>
        <MessageAttachments
          message={message}
          onBlue
          backend={backend}
          sessionId={sessionId}
        />
        {content ? (
          <Text
            style={[styles.contentText, styles.userContentText]}
            selectable
          >
            {content}
          </Text>
        ) : null}
        {footerParts.length > 0 && (
          <View style={styles.footerRow}>
            <Text style={styles.footerText}>{footerParts.join('   ')}</Text>
          </View>
        )}
        {pinnedActions && onAction && onChangePinnedForRole && (
          <MessageActionsBar
            pinned={pinnedActions}
            onChangePinned={(next) => onChangePinnedForRole(role, next)}
            onAction={(action) => onAction(action, index, message)}
            availableActions={allowedActions}
            extraActions={pluginActionDefs}
            isActive={isActive}
          />
        )}
      </View>
    </View>
  );
};

const SystemMessageBubble: React.FC<MessageBubbleProps> = ({
  index,
  message,
  backend,
  sessionId,
  isActive,
  pinnedActions,
  onAction,
  onChangePinnedForRole,
  allowedActions,
  isEditing,
  editingText,
  onChangeEditingText,
  onSubmitEdit,
  onCancelEdit,
  renderMode,
  footerElements,
  pluginActionDefs,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [compiledExpanded, setCompiledExpanded] = useState(false);
  const content = selectDisplayContent(message);
  const compiledContent = typeof (message.metadata as any)?.compiled_content === 'string'
    ? (message.metadata as any).compiled_content
    : undefined;
  const role = 'system';
  const footerParts = useMemo(() => {
    const elements = footerElements || [];
    const parts: string[] = [];
    elements.forEach((el) => {
      if (!el || el.ui_type !== 'message_footer') return;
      const condition = (el as any).condition;
      if (condition != null && !evaluateCondition(condition, message)) return;
      const rawValue = extractByPath(message, el.data);
      const valueForTemplate = formatValueForElement(el, rawValue);
      if (valueForTemplate === null || valueForTemplate === undefined || valueForTemplate === '') return;
      const text = renderTemplate(el.template ?? '{{data}}', valueForTemplate);
      if (text) parts.push(text);
    });
    return parts;
  }, [footerElements, message]);

  if (isEditing && onChangeEditingText && onSubmitEdit && onCancelEdit) {
    return (
      <View style={styles.row}>
        <View style={[styles.bubble, styles.otherBubble, styles.toolSystemBubble]}>
          <Text style={[styles.headerText, styles.standaloneHeaderText]}>{`[${index}] System`}</Text>
          <TextInput
            style={styles.editInput}
            value={editingText ?? ''}
            onChangeText={onChangeEditingText}
            multiline
          />
          <View style={styles.editButtonsRow}>
            <TouchableOpacity
              style={[styles.editButton, styles.editButtonSecondary]}
              onPress={onCancelEdit}
            >
              <Text style={styles.editButtonTextSecondary}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.editButton, styles.editButtonPrimary]}
              onPress={() => onSubmitEdit(index, message, editingText ?? '')}
            >
              <Text style={styles.editButtonTextPrimary}>Save</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.otherBubble, styles.toolSystemBubble]}>
        <View style={styles.headerRow}>
          <Text style={styles.headerText}>{`[${index}] System`}</Text>
          <View style={styles.headerIconsRow}>
            {compiledContent && (
              <TouchableOpacity
                style={styles.collapseIconButton}
                hitSlop={CHEVRON_HIT_SLOP}
                onPress={() => setCompiledExpanded((prev) => !prev)}
                testID="system-compiled-toggle"
              >
                <Icon
                  name={compiledExpanded ? 'chevron-up' : 'chevron-down'}
                  size={CHEVRON_ICON_SIZE}
                  color={theme.textSecondary}
                />
              </TouchableOpacity>
            )}
          </View>
        </View>
        <MessageAttachments message={message} backend={backend} sessionId={sessionId} />
        {content ? (
          <Text
            style={styles.systemText}
            selectable
          >
            {content}
          </Text>
        ) : null}
        {compiledContent && compiledExpanded && (
          <View style={styles.collapsibleContainerReasoning}>
            <ScrollView
              style={styles.collapsibleScroll}
              nestedScrollEnabled
            >
              <Text
                style={styles.reasoningText}
                selectable
                testID="system-compiled-content"
              >
                {compiledContent}
              </Text>
            </ScrollView>
          </View>
        )}
        {compiledContent && !compiledExpanded && (
          <Text
            style={styles.collapsedHintText}
            selectable
          >
            Compiled system prompt hidden (tap chevron to expand).
          </Text>
        )}
        {footerParts.length > 0 && (
          <View style={styles.footerRow}>
            <Text style={styles.footerText}>{footerParts.join('   ')}</Text>
          </View>
        )}
        {pinnedActions && onAction && onChangePinnedForRole && (
          <MessageActionsBar
            pinned={pinnedActions}
            onChangePinned={(next) => onChangePinnedForRole(role, next)}
            onAction={(action) => onAction(action, index, message)}
            availableActions={allowedActions}
            extraActions={pluginActionDefs}
            isActive={isActive}
          />
        )}
      </View>
    </View>
  );
};

const ToolMessageBubble: React.FC<MessageBubbleProps> = ({
  index,
  message,
  backend,
  sessionId,
  isActive,
  pinnedActions,
  onAction,
  onChangePinnedForRole,
  allowedActions,
  renderMode,
  footerElements,
  pluginActionDefs,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [expanded, setExpanded] = useState(false);
  const content = selectDisplayContent(message);
  const singleLine = selectSingleLineContent(message);
  const hasContent = !!content;
  const role = 'tool';
  const toolName =
    typeof (message.metadata as any)?.tool_name === 'string'
      ? (message.metadata as any).tool_name
      : undefined;
  const footerParts = useMemo(() => {
    const elements = footerElements || [];
    const parts: string[] = [];
    elements.forEach((el) => {
      if (!el || el.ui_type !== 'message_footer') return;
      const condition = (el as any).condition;
      if (condition != null && !evaluateCondition(condition, message)) return;
      const rawValue = extractByPath(message, el.data);
      const valueForTemplate = formatValueForElement(el, rawValue);
      if (valueForTemplate === null || valueForTemplate === undefined || valueForTemplate === '') return;
      const text = renderTemplate(el.template ?? '{{data}}', valueForTemplate);
      if (text) parts.push(text);
    });
    return parts;
  }, [footerElements, message]);

  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.otherBubble, styles.toolSystemBubble]}>
        <View style={styles.headerRow}>
          <Text style={styles.headerText}>
            {`[${index}] Tool`}
            {toolName && ` (${toolName})`}
          </Text>
          {hasContent && (
            <TouchableOpacity
              style={styles.collapseIconButton}
              hitSlop={CHEVRON_HIT_SLOP}
              onPress={() => setExpanded((prev) => !prev)}
            >
              <Icon
                name={expanded ? 'chevron-up' : 'chevron-down'}
                size={CHEVRON_ICON_SIZE}
                color={theme.textSecondary}
              />
            </TouchableOpacity>
          )}
        </View>

        <MessageAttachments message={message} backend={backend} sessionId={sessionId} />

        {hasContent && expanded && (
          <View style={styles.collapsibleContainerTool}>
            <ScrollView
              style={styles.collapsibleScroll}
              nestedScrollEnabled
            >
              <Text
                style={styles.contentText}
                selectable
              >
                {content}
              </Text>
            </ScrollView>
          </View>
        )}

        {hasContent && !expanded && (
          <Text
            style={styles.collapsedHintText}
            selectable
          >
            {singleLine || 'Tool result hidden (tap to expand).'}
          </Text>
        )}

        {!hasContent && (
          <Text
            style={styles.collapsedHintText}
            selectable
          >
            No tool output.
          </Text>
        )}
        {footerParts.length > 0 && (
          <View style={styles.footerRow}>
            <Text style={styles.footerText}>{footerParts.join('   ')}</Text>
          </View>
        )}
        {pinnedActions && onAction && onChangePinnedForRole && (
          <MessageActionsBar
            pinned={pinnedActions}
            onChangePinned={(next) => onChangePinnedForRole(role, next)}
            onAction={(action) => onAction(action, index, message)}
            availableActions={allowedActions}
            extraActions={pluginActionDefs}
            isActive={isActive}
          />
        )}
      </View>
    </View>
  );
};

const AssistantMessageBubble: React.FC<MessageBubbleProps> = ({
  index,
  message,
  backend,
  sessionId,
  isActive,
  pinnedActions,
  onAction,
  onChangePinnedForRole,
  allowedActions,
  isEditing,
  editingText,
  onChangeEditingText,
  onSubmitEdit,
  onCancelEdit,
  renderMode,
  footerElements,
  pluginActionDefs,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [reasoningExpanded, setReasoningExpanded] = useState(false);
  const [toolCallsExpanded, setToolCallsExpanded] = useState(false);
  const [webSourcesExpanded, setWebSourcesExpanded] = useState(false);
  const content = selectDisplayContent(message);
  const hasContent = !!content;
  const reasoning = typeof (message.metadata as any)?.reasoning === 'string'
    ? (message.metadata as any).reasoning
    : undefined;
  const reasoningSingleLine = useMemo(() => {
    if (!reasoning) return '';
    return toSingleLinePreview(reasoning);
  }, [reasoning]);
  const citations = useMemo(
    () => selectWebLinkEntries((message.metadata as any)?.url_citations),
    [message.metadata],
  );
  const webSearchSources = useMemo(
    () => selectWebLinkEntries((message.metadata as any)?.web_search_sources),
    [message.metadata],
  );
  const toolCalls = Array.isArray((message.metadata as any)?.tool_calls)
    ? (message.metadata as any).tool_calls
    : [];
  const toolCallNames = useMemo(() => {
    const names: string[] = [];
    for (const tc of toolCalls) {
      if (typeof tc === 'object' && tc !== null) {
        const func = tc.function || {};
        const name = typeof func === 'object' && func !== null && typeof func.name === 'string'
          ? func.name
          : typeof tc.type === 'string'
          ? tc.type
          : 'tool';
        names.push(name);
      }
    }
    return names;
  }, [toolCalls]);
  const distinctToolCallNames = useMemo(
    () => Array.from(new Set(toolCallNames)),
    [toolCallNames],
  );
  const role = 'assistant';
  const footerParts = useMemo(() => {
    const elements = footerElements || [];
    const parts: string[] = [];
    elements.forEach((el) => {
      if (!el || el.ui_type !== 'message_footer') return;
      const condition = (el as any).condition;
      if (condition != null && !evaluateCondition(condition, message)) return;
      const rawValue = extractByPath(message, el.data);
      const valueForTemplate = formatValueForElement(el, rawValue);
      if (valueForTemplate === null || valueForTemplate === undefined || valueForTemplate === '') return;
      const text = renderTemplate(el.template ?? '{{data}}', valueForTemplate);
      if (text) parts.push(text);
    });
    return parts;
  }, [footerElements, message]);

  const openWebLink = async (url: string) => {
    try {
      await Linking.openURL(url);
    } catch (err) {
      console.log('Failed to open web link', err);
      Alert.alert('Unable to open link', url);
    }
  };

  if (isEditing && onChangeEditingText && onSubmitEdit && onCancelEdit) {
    return (
      <View style={styles.row}>
        <View style={[styles.bubble, styles.otherBubble]}>
          <View style={styles.headerRow}>
            <Text style={styles.headerText}>{`[${index}] Assistant`}</Text>
          </View>
          <TextInput
            style={styles.editInput}
            value={editingText ?? ''}
            onChangeText={onChangeEditingText}
            multiline
          />
          <View style={styles.editButtonsRow}>
            <TouchableOpacity
              style={[styles.editButton, styles.editButtonSecondary]}
              onPress={onCancelEdit}
            >
              <Text style={styles.editButtonTextSecondary}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.editButton, styles.editButtonPrimary]}
              onPress={() => onSubmitEdit(index, message, editingText ?? '')}
            >
              <Text style={styles.editButtonTextPrimary}>Save</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.otherBubble]}>
        <View style={styles.headerRow}>
          <Text style={styles.headerText}>{`[${index}] Assistant`}</Text>
          <View style={styles.headerIconsRow}>
            {reasoning && (
              <TouchableOpacity
                style={styles.collapseIconButton}
                hitSlop={CHEVRON_HIT_SLOP}
                onPress={() => setReasoningExpanded((prev) => !prev)}
              >
                <Icon
                  name={reasoningExpanded ? 'chevron-up' : 'chevron-down'}
                  size={CHEVRON_ICON_SIZE}
                  color={theme.textSecondary}
                />
              </TouchableOpacity>
            )}
            {!reasoning && !hasContent && toolCallNames.length > 0 && (
              <TouchableOpacity
                style={styles.collapseIconButton}
                hitSlop={CHEVRON_HIT_SLOP}
                onPress={() => setToolCallsExpanded((prev) => !prev)}
              >
                <Icon
                  name={toolCallsExpanded ? 'chevron-up' : 'chevron-down'}
                  size={CHEVRON_ICON_SIZE}
                  color={theme.textSecondary}
                />
              </TouchableOpacity>
            )}
          </View>
        </View>

        <MessageAttachments message={message} backend={backend} sessionId={sessionId} />

        {reasoning && reasoningExpanded && (
          <View style={styles.collapsibleContainerReasoning}>
            <ScrollView
              style={styles.collapsibleScroll}
              nestedScrollEnabled
            >
              <Text
                style={styles.reasoningText}
                selectable
              >
                {reasoning}
              </Text>
            </ScrollView>
          </View>
        )}

        {reasoning && !reasoningExpanded && (
          <Text
            style={styles.collapsedHintText}
            selectable
            numberOfLines={1}
          >
            {reasoningSingleLine ? `Reasoning: ${reasoningSingleLine}` : 'Reasoning'}
          </Text>
        )}

        {content ? (
          renderMode === 'raw' ? (
            <TextInput
              style={[styles.contentText, styles.rawReadonlyInput]}
              value={content}
              editable={false}
              multiline
            />
          ) : (
            <MarkdownMessageContent
              text={content}
              variant="assistant"
            />
          )
        ) : null}

        {citations.length > 0 && (
          <View style={styles.linkSection}>
            <Text style={styles.linkSectionLabel}>Citations</Text>
            {citations.map((entry, idx) => {
              const label = entry.title || entry.url || `Citation ${idx + 1}`;
              return (
                <TouchableOpacity
                  key={`${entry.url || label}-${idx}`}
                  style={styles.linkItem}
                  onPress={() => entry.url && openWebLink(entry.url)}
                  disabled={!entry.url}
                >
                  <Text style={styles.linkItemTitle}>{`${idx + 1}. ${label}`}</Text>
                  {entry.url ? <Text style={styles.linkItemUrl}>{entry.url}</Text> : null}
                  {entry.content ? <Text style={styles.linkItemSnippet}>{entry.content}</Text> : null}
                </TouchableOpacity>
              );
            })}
          </View>
        )}

        {webSearchSources.length > 0 && (
          <View style={styles.linkSection}>
            <View
              style={styles.linkSectionToggle}
            >
              <Text style={styles.linkSectionLabel}>{`Sources (${webSearchSources.length})`}</Text>
              <TouchableOpacity
                style={styles.collapseIconButton}
                hitSlop={CHEVRON_HIT_SLOP}
                onPress={() => setWebSourcesExpanded((prev) => !prev)}
              >
                <Icon
                  name={webSourcesExpanded ? 'chevron-up' : 'chevron-down'}
                  size={CHEVRON_ICON_SIZE}
                  color={theme.textSecondary}
                />
              </TouchableOpacity>
            </View>

            {webSourcesExpanded ? (
              webSearchSources.map((entry, idx) => {
                const label = entry.title || entry.url || `Source ${idx + 1}`;
                const snippet = entry.snippet || entry.content;
                return (
                  <TouchableOpacity
                    key={`${entry.url || label}-${idx}`}
                    style={styles.linkItem}
                    onPress={() => entry.url && openWebLink(entry.url)}
                    disabled={!entry.url}
                  >
                    <Text style={styles.linkItemTitle}>{`${idx + 1}. ${label}`}</Text>
                    {entry.url ? <Text style={styles.linkItemUrl}>{entry.url}</Text> : null}
                    {snippet ? <Text style={styles.linkItemSnippet}>{snippet}</Text> : null}
                  </TouchableOpacity>
                );
              })
            ) : (
              <Text style={styles.collapsedHintText}>Consulted sources hidden (tap chevron to expand).</Text>
            )}
          </View>
        )}

        {toolCallNames.length > 0 && (reasoning || hasContent) && (
          <View style={styles.disclosureRow}>
            <Text
              style={[styles.collapsedHintText, styles.disclosureText]}
              selectable
              numberOfLines={1}
            >
              {toolCallNames.length} tool call{toolCallNames.length !== 1 ? 's' : ''}: {distinctToolCallNames.join(', ')}
            </Text>
            <TouchableOpacity
              style={[styles.collapseIconButton, styles.disclosureChevronButton]}
              hitSlop={CHEVRON_HIT_SLOP}
              onPress={() => setToolCallsExpanded((prev) => !prev)}
            >
              <Icon
                name={toolCallsExpanded ? 'chevron-up' : 'chevron-down'}
                size={CHEVRON_ICON_SIZE}
                color={theme.textSecondary}
              />
            </TouchableOpacity>
          </View>
        )}

        {toolCallNames.length > 0 && toolCallsExpanded && (
          <View style={styles.collapsibleContainerTool}>
            <ScrollView
              style={styles.collapsibleScroll}
              nestedScrollEnabled
            >
              {toolCalls.map((tc: any, idx: number) => {
                const func = tc.function || {};
                const toolName =
                  typeof func === 'object' &&
                  func !== null &&
                  typeof func.name === 'string'
                    ? func.name
                    : typeof tc.type === 'string'
                      ? tc.type
                      : 'tool';
                const callId = tc.id || tc.tool_call_id;

                const toolCallPreviews = Array.isArray(
                  (message.metadata as any)?.tool_call_previews,
                )
                  ? (message.metadata as any).tool_call_previews
                  : [];
                const previewObj = toolCallPreviews.find(
                  (p: any) => p && p.id === callId,
                );
                const preview = previewObj?.preview || '';

                const displayText =
                  preview ||
                  (typeof func === 'object' && func !== null && func.arguments
                    ? typeof func.arguments === 'string'
                      ? func.arguments
                      : JSON.stringify(func.arguments, null, 2)
                    : typeof tc.arguments === 'string'
                      ? tc.arguments
                      : JSON.stringify(tc.arguments || {}, null, 2));

                return (
                  <View
                    key={callId || idx}
                    style={styles.toolCallItem}
                  >
                    <Text style={styles.toolCallName}>{toolName}</Text>
                    <Text
                      style={styles.toolCallArgs}
                      selectable
                    >
                      {displayText}
                    </Text>
                  </View>
                );
              })}
            </ScrollView>
          </View>
        )}
        {toolCallNames.length > 0 && !toolCallsExpanded && !reasoning && !hasContent && (
          <Text style={styles.collapsedHintText}>
            {toolCallNames.length} tool call{toolCallNames.length !== 1 ? 's' : ''}: {distinctToolCallNames.join(', ')}
          </Text>
        )}
        {footerParts.length > 0 && (
          <View style={styles.footerRow}>
            <Text style={styles.footerText}>{footerParts.join('   ')}</Text>
          </View>
        )}
        {pinnedActions && onAction && onChangePinnedForRole && (
          <MessageActionsBar
            pinned={pinnedActions}
            onChangePinned={(next) => onChangePinnedForRole(role, next)}
            onAction={(action) => onAction(action, index, message)}
            availableActions={allowedActions}
            extraActions={pluginActionDefs}
            isActive={isActive}
          />
        )}
      </View>
    </View>
  );
};

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  index,
  message,
  backend,
  sessionId,
  isActive,
  pinnedActions,
  onAction,
  onChangePinnedForRole,
  allowedActions,
  isEditing,
  editingText,
  onChangeEditingText,
  onSubmitEdit,
  onCancelEdit,
  renderMode,
  footerElements,
  pluginActionDefs,
}) => {
  console.log("Rendering MessageBubble", { index, role: message.role });
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const role = message.role || 'unknown';

  if (role === 'user') {
    return (
      <UserMessageBubble
        index={index}
        message={message}
        backend={backend}
        sessionId={sessionId}
        isActive={isActive}
        pinnedActions={pinnedActions}
        onAction={onAction}
        onChangePinnedForRole={onChangePinnedForRole}
        allowedActions={allowedActions}
        isEditing={isEditing}
        editingText={editingText}
        onChangeEditingText={onChangeEditingText}
        onSubmitEdit={onSubmitEdit}
        onCancelEdit={onCancelEdit}
        footerElements={footerElements}
        pluginActionDefs={pluginActionDefs}
      />
    );
  }
  if (role === 'system') {
    return (
      <SystemMessageBubble
        index={index}
        message={message}
        backend={backend}
        sessionId={sessionId}
        isActive={isActive}
        pinnedActions={pinnedActions}
        onAction={onAction}
        onChangePinnedForRole={onChangePinnedForRole}
        allowedActions={allowedActions}
        isEditing={isEditing}
        editingText={editingText}
        onChangeEditingText={onChangeEditingText}
        onSubmitEdit={onSubmitEdit}
        onCancelEdit={onCancelEdit}
        renderMode={renderMode}
        footerElements={footerElements}
        pluginActionDefs={pluginActionDefs}
      />
    );
  }
  if (role === 'tool') {
    return (
      <ToolMessageBubble
        index={index}
        message={message}
        backend={backend}
        sessionId={sessionId}
        isActive={isActive}
        pinnedActions={pinnedActions}
        onAction={onAction}
        onChangePinnedForRole={onChangePinnedForRole}
        allowedActions={allowedActions}
        renderMode={renderMode}
        footerElements={footerElements}
        pluginActionDefs={pluginActionDefs}
      />
    );
  }
  if (role === 'assistant') {
    return (
      <AssistantMessageBubble
        index={index}
        message={message}
        backend={backend}
        sessionId={sessionId}
        isActive={isActive}
        pinnedActions={pinnedActions}
        onAction={onAction}
        onChangePinnedForRole={onChangePinnedForRole}
        allowedActions={allowedActions}
        isEditing={isEditing}
        editingText={editingText}
        onChangeEditingText={onChangeEditingText}
        onSubmitEdit={onSubmitEdit}
        onCancelEdit={onCancelEdit}
        renderMode={renderMode}
        footerElements={footerElements}
        pluginActionDefs={pluginActionDefs}
      />
    );
  }

  // Fallback for unexpected roles
  const content = selectDisplayContent(message);
  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.otherBubble]}>
        <Text style={styles.headerText}>{`[${index}] ${role}`}</Text>
        {content ? (
          <Text
            style={styles.contentText}
            selectable
          >
            {content}
          </Text>
        ) : null}
        {/* Footer elements are not rendered for unknown roles. */}
        {pinnedActions && onAction && onChangePinnedForRole && (
          <MessageActionsBar
            pinned={pinnedActions}
            onChangePinned={(next) => onChangePinnedForRole(role, next)}
            onAction={(action) => onAction(action, index, message)}
            availableActions={allowedActions}
            isActive={isActive}
          />
        )}
      </View>
    </View>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    row: {
      marginBottom: 8,
    },
    bubble: {
      paddingVertical: 8,
      paddingHorizontal: 12,
      borderRadius: 8,
    },
    userBubble: {
      backgroundColor: theme.bubbleUserBg,
    },
    otherBubble: {
      backgroundColor: 'transparent',
    },
    toolSystemBubble: {
      borderWidth: 1,
      borderColor: theme.bubbleSystemBorder,
    },
    headerRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 4,
    },
    headerIconsRow: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    headerText: {
      fontSize: theme.typography.fontSize.small,
      color: theme.textSecondary,
    },
    standaloneHeaderText: {
      marginBottom: 4,
    },
    systemText: {
      fontSize: theme.typography.fontSize.secondary,
      color: theme.text,
      fontFamily: 'Courier',
      fontStyle: 'italic',
    },
    reasoningText: {
      fontSize: theme.typography.fontSize.small,
      color: theme.textSecondary,
      fontStyle: 'italic',
      fontFamily: 'Courier',
    },
    toolCallItem: {
      marginBottom: 8,
    },
    toolCallName: {
      fontSize: theme.typography.fontSize.secondary,
      color: theme.text,
      fontWeight: '600',
      marginBottom: 2,
      fontFamily: 'Courier',
    },
    toolCallArgs: {
      fontSize: theme.typography.fontSize.tiny,
      color: theme.textSecondary,
      fontFamily: 'Courier',
      marginLeft: 8,
    },
    contentText: {
      fontSize: theme.typography.fontSize.message,
      color: theme.text,
      fontFamily: 'Courier',
    },
    // User messages share the same foreground color as other
    // messages; only the background changes per theme.
    userContentText: {
      color: theme.text,
    },
    collapseIconButton: {
      paddingHorizontal: 6,
      paddingVertical: 4,
    },
    collapsibleContainerTool: {
      marginTop: 4,
      maxHeight: 220,
      borderRadius: 6,
      backgroundColor: theme.bubbleToolBg,
      overflow: 'hidden',
    },
    collapsibleContainerReasoning: {
      marginTop: 4,
      maxHeight: 160,
      borderRadius: 6,
      backgroundColor: theme.bubbleToolBg,
      overflow: 'hidden',
    },
    collapsibleScroll: {
      paddingHorizontal: 4,
      paddingVertical: 4,
    },
    collapsedHintText: {
      marginTop: 2,
      fontSize: theme.typography.fontSize.tiny,
      color: theme.textSecondary,
      fontStyle: 'italic',
    },
    footerRow: {
      marginTop: 4,
    },
    footerText: {
      fontSize: theme.typography.fontSize.tiny,
      color: theme.textSecondary,
      fontFamily: 'Courier',
    },
    linkSection: {
      marginTop: 8,
      paddingTop: 6,
      borderTopWidth: 1,
      borderTopColor: theme.border,
    },
    linkSectionToggle: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingHorizontal: 2,
      paddingVertical: 2,
    },
    disclosureRow: {
      flexDirection: 'row',
      alignItems: 'center',
      marginTop: 2,
    },
    disclosureText: {
      flexShrink: 1,
      marginRight: 8,
    },
    disclosureChevronButton: {
      marginLeft: 'auto',
    },
    linkSectionLabel: {
      fontSize: theme.typography.fontSize.tiny,
      color: theme.textSecondary,
      fontWeight: '600',
      textTransform: 'uppercase',
      letterSpacing: 0.4,
    },
    linkItem: {
      marginTop: 6,
      paddingVertical: 6,
      paddingHorizontal: 8,
      borderRadius: 6,
      backgroundColor: theme.bubbleToolBg,
    },
    linkItemTitle: {
      fontSize: theme.typography.fontSize.secondary,
      color: theme.text,
      fontWeight: '600',
    },
    linkItemUrl: {
      marginTop: 2,
      fontSize: theme.typography.fontSize.tiny,
      color: theme.primary,
      textDecorationLine: 'underline',
    },
    linkItemSnippet: {
      marginTop: 4,
      fontSize: theme.typography.fontSize.tiny,
      color: theme.textSecondary,
    },
    editInput: {
      marginTop: 4,
      minHeight: 60,
      maxHeight: 140,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 6,
      paddingHorizontal: 8,
      paddingVertical: 6,
      fontSize: theme.typography.fontSize.message,
      fontFamily: 'Courier',
      backgroundColor: theme.surface,
      color: theme.text,
    },
    editInputOnBlue: {
      backgroundColor: theme.surface,
    },
    editButtonsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      marginTop: 6,
    },
    editButton: {
      paddingHorizontal: 10,
      paddingVertical: 4,
      borderRadius: 6,
      marginLeft: 8,
    },
    editButtonPrimary: {
      backgroundColor: theme.primary,
    },
    editButtonSecondary: {
      backgroundColor: theme.surfaceAlt,
    },
    editButtonTextPrimary: {
      color: theme.textOnPrimary,
      fontSize: theme.typography.fontSize.normal,
      fontWeight: '600',
    },
    editButtonTextSecondary: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      fontWeight: '600',
    },
    attachmentsWrapper: {
      marginTop: 6,
      marginBottom: 2,
    },
    attachmentsWrapperOnBlue: {
      marginTop: 8,
    },
    imageModalTile: {
      width: 54,
      height: 54,
      borderRadius: 10,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      overflow: 'hidden',
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
    rawReadonlyInput: {
      marginTop: 2,
      padding: 0,
      color: theme.text,
    },
  });

export default MessageBubble;
