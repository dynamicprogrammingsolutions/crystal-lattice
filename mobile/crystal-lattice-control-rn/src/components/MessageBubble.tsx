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
import type { ApiMessage, UiSchemaElement } from '../api';
import MessageActionsBar from './MessageActionsBar';
import type { MessageActionKey, MessageActionDefinition } from '../messageActions';
import { selectDisplayContent, selectSingleLineContent } from '../messageUtils';
import MarkdownMessageContent from './MarkdownMessageContent';
import { AttachmentThumbnailStrip } from './AttachmentThumbnailStrip';
import {
  selectMultipartAttachments,
  type MessageAttachmentSnapshot,
} from '../messageAttachments';
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

const MessageAttachmentsPreview: React.FC<{
  message: ApiMessage;
  messageIndex: number;
  onBlue?: boolean;
  onOpenAttachment?: (attachment: MessageAttachmentSnapshot) => void;
}> = ({
  message,
  messageIndex,
  onBlue,
  onOpenAttachment,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const attachments = useMemo(
    () => selectMultipartAttachments(message, messageIndex),
    [message, messageIndex],
  );

  if (attachments.length === 0) return null;

  return (
    <View style={[styles.attachmentsWrapper, onBlue && styles.attachmentsWrapperOnBlue]}>
      <AttachmentThumbnailStrip
        attachments={attachments}
        onPress={onOpenAttachment ? (attachment) => {
          onOpenAttachment(attachment as MessageAttachmentSnapshot);
        } : undefined}
      />
    </View>
  );
};

export interface MessageBubbleProps {
  index: number;
  message: ApiMessage;
  onOpenAttachment?: (attachment: MessageAttachmentSnapshot) => void;
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
  onOpenAttachment,
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
        <MessageAttachmentsPreview
          message={message}
          messageIndex={index}
          onBlue
          onOpenAttachment={onOpenAttachment}
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
  onOpenAttachment,
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
        <MessageAttachmentsPreview
          message={message}
          messageIndex={index}
          onOpenAttachment={onOpenAttachment}
        />
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
  onOpenAttachment,
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

        <MessageAttachmentsPreview
          message={message}
          messageIndex={index}
          onOpenAttachment={onOpenAttachment}
        />

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
  onOpenAttachment,
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

        <MessageAttachmentsPreview
          message={message}
          messageIndex={index}
          onOpenAttachment={onOpenAttachment}
        />

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
  onOpenAttachment,
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
        onOpenAttachment={onOpenAttachment}
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
        onOpenAttachment={onOpenAttachment}
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
        onOpenAttachment={onOpenAttachment}
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
        onOpenAttachment={onOpenAttachment}
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
    rawReadonlyInput: {
      marginTop: 2,
      padding: 0,
      color: theme.text,
    },
  });

export default MessageBubble;
