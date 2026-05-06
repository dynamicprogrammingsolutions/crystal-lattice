import React, { useMemo, useState } from 'react';
import {
  ActivityIndicator,
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
import { selectAttachmentPreviewUrl } from '@crystal-lattice/frontend-sdk';
import { ApplicationActionDialogLayout } from '@crystal-lattice/frontend-rn-components';
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

function resolveInterceptorPromptButtonLabel(
  pending: Record<string, unknown>,
  buttonId: string,
): string {
  const buttons = pending.buttons;
  if (!Array.isArray(buttons)) return buttonId;
  for (const raw of buttons) {
    if (!raw || typeof raw !== 'object') continue;
    const id = (raw as { id?: unknown }).id;
    const label = (raw as { label?: unknown }).label;
    if (id === buttonId && typeof label === 'string' && label) return label;
  }
  return buttonId;
}

function selectMultipartParts(message: ApiMessage): MultipartPart[] {
  const parts = (message as any)?.multipartContent;
  return Array.isArray(parts) ? (parts as MultipartPart[]) : [];
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
          const url = selectAttachmentPreviewUrl(attachment.content);
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
  onToolInterceptorPromptSubmit?: (args: {
    messageIndex: number;
    promptId: string;
    buttonId: string;
    values: Record<string, unknown>;
  }) => void | Promise<void>;
  toolInterceptorPromptSubmittingKey?: string | null;
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
        <View style={styles.headerRow}>
          <Text style={styles.headerText}>{`[${index}] System`}</Text>
          <View style={styles.headerIconsRow}>
            {compiledContent && (
              <TouchableOpacity
                style={styles.collapseIconButton}
                onPress={() => setCompiledExpanded((prev) => !prev)}
                testID="system-compiled-toggle"
              >
                <Icon
                  name={compiledExpanded ? 'chevron-up' : 'chevron-down'}
                  size={14}
                  color={theme.textSecondary}
                />
              </TouchableOpacity>
            )}
          </View>
        </View>
        <MessageAttachments message={message} />
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
  onToolInterceptorPromptSubmit,
  toolInterceptorPromptSubmittingKey = null,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [reasoningExpanded, setReasoningExpanded] = useState(false);
  const [toolCallsExpanded, setToolCallsExpanded] = useState(false);
  const [webSourcesExpanded, setWebSourcesExpanded] = useState(false);
  const content = selectDisplayContent(message);
  const reasoning = typeof (message.metadata as any)?.reasoning === 'string'
    ? (message.metadata as any).reasoning
    : undefined;
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
  const mdIntercept = (message.metadata || {}) as Record<string, any>;
  const interceptionCurrent = mdIntercept.interception_current;
  const rawPending =
    interceptionCurrent && typeof interceptionCurrent === 'object'
      ? interceptionCurrent.pending_prompt
      : null;
  const hasInterceptorPrompt =
    rawPending &&
    typeof rawPending === 'object' &&
    Array.isArray(rawPending.buttons) &&
    rawPending.buttons.length > 0;
  const interceptorDialog = hasInterceptorPrompt
    ? (() => {
        const inputs = Array.isArray(rawPending.inputs) ? rawPending.inputs : [];
        return {
          kind: inputs.length ? 'form' : 'confirm',
          title:
            typeof rawPending.title === 'string' && rawPending.title
              ? rawPending.title
              : 'Tool confirmation',
          message: typeof rawPending.message === 'string' ? rawPending.message : '',
          inputs,
          buttons: rawPending.buttons,
        };
      })()
    : null;
  const promptIdForSubmit =
    hasInterceptorPrompt && typeof rawPending.id === 'string' ? rawPending.id : '';
  const submitKey =
    promptIdForSubmit !== '' ? `${index}:${promptIdForSubmit}` : '';
  const storedAnswerRaw =
    interceptionCurrent && typeof interceptionCurrent === 'object'
      ? (interceptionCurrent as Record<string, unknown>).answer
      : null;
  const storedAnswer =
    storedAnswerRaw && typeof storedAnswerRaw === 'object' && storedAnswerRaw !== null
      ? (storedAnswerRaw as Record<string, unknown>)
      : null;
  const answerPromptId =
    storedAnswer && typeof storedAnswer.prompt_id === 'string' ? storedAnswer.prompt_id : '';
  const answerButtonId =
    storedAnswer && typeof storedAnswer.button_id === 'string' ? storedAnswer.button_id : '';
  const answerForThisPrompt =
    hasInterceptorPrompt &&
    answerPromptId !== '' &&
    answerPromptId === promptIdForSubmit &&
    answerButtonId !== '';
  const selectedChoiceLabel =
    answerForThisPrompt && rawPending && typeof rawPending === 'object'
      ? resolveInterceptorPromptButtonLabel(rawPending as Record<string, unknown>, answerButtonId)
      : '';
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
            <TouchableOpacity
              style={styles.linkSectionToggle}
              onPress={() => setWebSourcesExpanded((prev) => !prev)}
            >
              <Text style={styles.linkSectionLabel}>{`Sources (${webSearchSources.length})`}</Text>
              <Icon
                name={webSourcesExpanded ? 'chevron-up' : 'chevron-down'}
                size={14}
                color={theme.textSecondary}
              />
            </TouchableOpacity>

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

        {interceptorDialog && onToolInterceptorPromptSubmit && promptIdForSubmit ? (
          <View style={styles.interceptorPromptWrap}>
            {answerForThisPrompt ? (
              <View style={styles.interceptorAnswerSummary}>
                <Icon name="check-circle" size={16} color={theme.textSecondary} />
                <View style={styles.interceptorAnswerSummaryTextCol}>
                  <Text style={styles.interceptorAnswerSummaryTitle}>
                    {(typeof rawPending.title === 'string' && rawPending.title) ||
                      'Tool confirmation'}
                  </Text>
                  <Text style={styles.interceptorAnswerSummaryChoice}>
                    Selected: {selectedChoiceLabel || answerButtonId}
                  </Text>
                </View>
              </View>
            ) : toolInterceptorPromptSubmittingKey === submitKey ? (
              <View style={styles.interceptorSubmittingRow}>
                <ActivityIndicator size="small" color={theme.primary} />
                <Text style={styles.interceptorSubmittingText}>Sending choice…</Text>
              </View>
            ) : (
              <ApplicationActionDialogLayout
                dialog={interceptorDialog}
                titleFallback="Tool confirmation"
                density="compact"
                onSubmit={(payload) => {
                  const bid =
                    typeof payload.buttonId === 'string' && payload.buttonId
                      ? payload.buttonId
                      : 'ok';
                  void onToolInterceptorPromptSubmit({
                    messageIndex: index,
                    promptId: promptIdForSubmit,
                    buttonId: bid,
                    values: payload.values || {},
                  });
                }}
                onCancel={() => {}}
                showCancelButton={false}
                disabled={false}
                style={styles.interceptorPromptLayout}
              />
            )}
          </View>
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
  onToolInterceptorPromptSubmit,
  toolInterceptorPromptSubmittingKey,
}) => {
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
        onToolInterceptorPromptSubmit={onToolInterceptorPromptSubmit}
        toolInterceptorPromptSubmittingKey={toolInterceptorPromptSubmittingKey}
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
    },
    linkSectionLabel: {
      fontSize: 11,
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
      fontSize: 13,
      color: theme.text,
      fontWeight: '600',
    },
    linkItemUrl: {
      marginTop: 2,
      fontSize: 11,
      color: theme.primary,
      textDecorationLine: 'underline',
    },
    linkItemSnippet: {
      marginTop: 4,
      fontSize: 11,
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
    interceptorPromptWrap: {
      marginTop: 10,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      padding: 8,
      backgroundColor: theme.surfaceAlt,
    },
    interceptorPromptLayout: {
      width: '100%',
      backgroundColor: 'transparent',
      padding: 0,
      borderRadius: 0,
    },
    interceptorAnswerSummary: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      gap: 8,
      paddingVertical: 4,
    },
    interceptorAnswerSummaryTextCol: {
      flex: 1,
      minWidth: 0,
    },
    interceptorAnswerSummaryTitle: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.text,
      marginBottom: 2,
    },
    interceptorAnswerSummaryChoice: {
      fontSize: 13,
      color: theme.textSecondary,
    },
    interceptorSubmittingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 10,
      paddingVertical: 6,
    },
    interceptorSubmittingText: {
      fontSize: 13,
      color: theme.textSecondary,
    },
    rawReadonlyInput: {
      marginTop: 2,
      padding: 0,
      color: theme.text,
    },
  });

export default MessageBubble;
