import React, { useMemo, useState } from 'react';
import {
  Alert,
  Linking,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import Clipboard from '@react-native-clipboard/clipboard';
import type { ApiMessage, UiSchemaElement } from '../api';
import MessageActionsBar from './MessageActionsBar';
import type { MessageActionKey, MessageActionDefinition } from '../messageActions';
import { selectDisplayContent, selectSingleLineContent } from '../messageUtils';
import MarkdownMessageContent from './MarkdownMessageContent';
import { AttachmentThumbnailStrip, type AttachmentLike } from './AttachmentThumbnailStrip';
import { useTheme, type Theme } from '../theme';
import { extractByPath, renderTemplate, formatValueForElement, evaluateCondition } from '../uiSchemaUtils';

type MultipartPart = {
  type?: string;
  content?: any;
  metadata?: any;
};

function selectMultipartParts(message: ApiMessage): MultipartPart[] {
  const parts = (message as any)?.multipartContent;
  return Array.isArray(parts) ? (parts as MultipartPart[]) : [];
}

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

const MessageAttachments: React.FC<{ message: ApiMessage; onBlue?: boolean }> = ({
  message,
  onBlue,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const parts = selectMultipartParts(message);

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

  return (
    <View style={[styles.attachmentsWrapper, onBlue && styles.attachmentsWrapperOnBlue]}>
      <AttachmentThumbnailStrip
        attachments={attachments}
        onPress={async (attachment) => {
          const url = selectAttachmentUrl(attachment.content);
          const isPdf = attachment.type === 'pdf' && url;
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
          Clipboard.setString(url);
          Alert.alert('Copied', 'Attachment URL copied to clipboard.');
        }}
      />
    </View>
  );
};

export interface MessageBubbleProps {
  index: number;
  message: ApiMessage;
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

const UserMessageBubble: React.FC<MessageBubbleProps> = ({
  index,
  message,
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
      if (condition != null && !evaluateCondition(condition, message as Record<string, unknown>)) return;
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
          <Text style={styles.headerText}>{`[${index}] User`}</Text>
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
        <Text style={styles.headerText}>{`[${index}] User`}</Text>
        <MessageAttachments
          message={message}
          onBlue
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
  const role = 'system';
  const footerParts = useMemo(() => {
    const elements = footerElements || [];
    const parts: string[] = [];
    elements.forEach((el) => {
      if (!el || el.ui_type !== 'message_footer') return;
      const condition = (el as any).condition;
      if (condition != null && !evaluateCondition(condition, message as Record<string, unknown>)) return;
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
          <Text style={styles.headerText}>{`[${index}] System`}</Text>
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
        <Text style={styles.headerText}>{`[${index}] System`}</Text>
        <MessageAttachments message={message} />
        {content ? (
          <Text
            style={styles.systemText}
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

const ToolMessageBubble: React.FC<MessageBubbleProps> = ({
  index,
  message,
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
      if (condition != null && !evaluateCondition(condition, message as Record<string, unknown>)) return;
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
              onPress={() => setExpanded((prev) => !prev)}
            >
              <Icon
                name={expanded ? 'chevron-up' : 'chevron-down'}
                size={14}
                color={theme.textSecondary}
              />
            </TouchableOpacity>
          )}
        </View>

        <MessageAttachments message={message} />

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
  const content = selectDisplayContent(message);
  const reasoning = typeof (message.metadata as any)?.reasoning === 'string'
    ? (message.metadata as any).reasoning
    : undefined;
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
      if (condition != null && !evaluateCondition(condition, message as Record<string, unknown>)) return;
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
            {toolCallNames.length > 0 && (
              <TouchableOpacity
                style={styles.collapseIconButton}
                onPress={() => setToolCallsExpanded((prev) => !prev)}
              >
                <Icon
                  name={toolCallsExpanded ? 'chevron-up' : 'chevron-down'}
                  size={14}
                  color={theme.textSecondary}
                />
              </TouchableOpacity>
            )}
            {reasoning && (
              <TouchableOpacity
                style={styles.collapseIconButton}
                onPress={() => setReasoningExpanded((prev) => !prev)}
              >
                <Icon
                  name={reasoningExpanded ? 'chevron-up' : 'chevron-down'}
                  size={14}
                  color={theme.textSecondary}
                />
              </TouchableOpacity>
            )}
          </View>
        </View>

        <MessageAttachments message={message} />

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
          >
            Reasoning hidden (tap chevron to expand).
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

        {toolCallNames.length > 0 && !toolCallsExpanded && (
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
      fontSize: 12,
      color: theme.textSecondary,
    },
    systemText: {
      fontSize: 13,
      color: theme.text,
      fontFamily: 'Courier',
      fontStyle: 'italic',
    },
    reasoningText: {
      fontSize: 12,
      color: theme.textSecondary,
      fontStyle: 'italic',
      fontFamily: 'Courier',
    },
    toolCallItem: {
      marginBottom: 8,
    },
    toolCallName: {
      fontSize: 13,
      color: theme.text,
      fontWeight: '600',
      marginBottom: 2,
      fontFamily: 'Courier',
    },
    toolCallArgs: {
      fontSize: 11,
      color: theme.textSecondary,
      fontFamily: 'Courier',
      marginLeft: 8,
    },
    contentText: {
      fontSize: 14,
      color: theme.text,
      fontFamily: 'Courier',
    },
    // User messages share the same foreground color as other
    // messages; only the background changes per theme.
    userContentText: {
      color: theme.text,
    },
    collapseIconButton: {
      paddingHorizontal: 4,
      paddingVertical: 2,
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
      fontSize: 11,
      color: theme.textSecondary,
      fontStyle: 'italic',
    },
    footerRow: {
      marginTop: 4,
    },
    footerText: {
      fontSize: 11,
      color: theme.textSecondary,
      fontFamily: 'Courier',
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
      fontSize: 14,
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
      fontSize: 14,
      fontWeight: '600',
    },
    editButtonTextSecondary: {
      color: theme.text,
      fontSize: 14,
      fontWeight: '600',
    },
    attachmentsWrapper: {
      marginTop: 6,
      marginBottom: 2,
    },
    attachmentsWrapperOnBlue: {
      marginTop: 8,
    },
    rawReadonlyInput: {
      marginTop: 2,
      padding: 0,
      color: theme.text,
    },
  });

export default MessageBubble;
