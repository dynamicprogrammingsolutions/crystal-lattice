import React, { useMemo, useState } from 'react';
import {
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import type { ApiMessage, UiSchemaElement } from '@crystal-lattice/frontend-sdk';
import {
  extractByPath,
  formatValueForElement,
  renderTemplate,
  selectDisplayContent,
  selectSingleLineContent,
} from '@crystal-lattice/frontend-sdk';
import { MacTextView } from '@crystal-lattice/react-native-mac-text-view';
import { useTheme, type Theme } from '@crystal-lattice/frontend-rn-components';

import { AttachmentThumbnailStrip, type AttachmentLike } from './AttachmentThumbnailStrip';

import type { MessageActionKey, MessageActionDefinition } from './messageActions';
import { PinnedMessageActionsBar } from './PinnedMessageActionsBar';
import MarkdownMessageContent from './MarkdownMessageContent';

export interface DesktopMessageBubbleProps {
  index: number;
  message: ApiMessage;
  onAction?: (action: MessageActionKey, index: number, message: ApiMessage) => void;
  allowedActions?: MessageActionKey[];
  isEditing?: boolean;
  editingInitialText?: string;
  editingText?: string;
  onChangeEditingText?: (text: string) => void;
  onSubmitEdit?: (index: number, message: ApiMessage, newText: string) => void;
  onCancelEdit?: () => void;
  renderMode?: 'markdown' | 'raw';
  footerElements?: UiSchemaElement[];
  pluginActionDefs?: MessageActionDefinition[];
}

function toSingleLinePreview(text: string, maxLen = 160): string {
  const normalized = text.replace(/\s+/g, ' ').trim();
  if (!normalized) return '';
  if (normalized.length <= maxLen) return normalized;
  return `${normalized.slice(0, Math.max(0, maxLen - 1))}…`;
}

const EMPTY_TOOL_CALLS: any[] = [];

function buildMessageAttachments(message: ApiMessage, prefix: string): AttachmentLike[] {
  const parts = Array.isArray((message as any).multipartContent)
    ? (((message as any).multipartContent as any[]) ?? [])
    : [];
  const metadata = (message as any).metadata;
  const display = metadata && typeof metadata === 'object' ? (metadata as any).display : null;
  const allParts =
    display && typeof display === 'object' && display.type === 'image'
      ? [
          ...parts,
          {
            type: 'image',
            content: (display as any).content,
            metadata: (display as any).metadata,
          },
        ]
      : parts;

  return allParts
    .map((part, idx) => {
      if (!part || typeof part !== 'object') {
        return null;
      }
      const type = typeof (part as any).type === 'string' ? (part as any).type : 'attachment';
      const attachment: AttachmentLike = {
        id: `${prefix}:${idx}:${type}`,
        type,
        content: (part as any).content,
      };
      if (Object.prototype.hasOwnProperty.call(part as any, 'metadata')) {
        (attachment as any).metadata = (part as any).metadata;
      }

      return attachment;
    })
    .filter((v): v is AttachmentLike => v != null);
}

const MessageAttachmentsStrip: React.FC<{
  message: ApiMessage;
  idPrefix: string;
  onPress?: (attachment: AttachmentLike) => void;
}> = ({
  message,
  idPrefix,
  onPress,
}) => {
  const attachments = useMemo(
    () => buildMessageAttachments(message, idPrefix),
    [idPrefix, message],
  );

  if (attachments.length === 0) {
    return null;
  }

  return <AttachmentThumbnailStrip attachments={attachments} onPress={onPress} />;
};

const UserMessageBubble: React.FC<DesktopMessageBubbleProps> = ({
  index,
  message,
  onAction,
  allowedActions,
  isEditing,
  editingInitialText,
  editingText,
  onChangeEditingText,
  onSubmitEdit,
  onCancelEdit,
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
          <MacTextView
            style={[styles.editInput, styles.editInputOnBlue]}
            initialText={editingInitialText ?? editingText ?? ''}
            autoGrow
            minHeight={60}
            maxHeight={140}
            addToHeight={8}
            onChangeText={onChangeEditingText}
            onSubmit={(text) => onSubmitEdit(index, message, text)}
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
        <View style={styles.headerRow}>
          <Text style={styles.headerText}>{`[${index}] User`}</Text>
	          {onAction ? (
	            <PinnedMessageActionsBar
	              role={role}
	              onAction={(action) => onAction(action, index, message)}
	              availableActions={allowedActions}
	              extraActions={pluginActionDefs}
	            />
	          ) : null}
        </View>
        <MessageAttachmentsStrip
          message={message}
          idPrefix={`user:${index}`}
        />
        {content ? (
          <Text style={[styles.contentText, styles.userContentText]} selectable>
            {content}
          </Text>
        ) : null}
        {footerParts.length > 0 && (
          <View style={styles.footerRow}>
            <Text style={styles.footerText}>{footerParts.join('   ')}</Text>
          </View>
        )}
      </View>
    </View>
  );
};

const SystemMessageBubble: React.FC<DesktopMessageBubbleProps> = ({
  index,
  message,
  onAction,
  allowedActions,
  isEditing,
  editingInitialText,
  editingText,
  onChangeEditingText,
  onSubmitEdit,
  onCancelEdit,
  footerElements,
  pluginActionDefs,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [editHeight, setEditHeight] = useState(60);
  const content = selectDisplayContent(message);
  const role = 'system';
  const footerParts = useMemo(() => {
    const elements = footerElements || [];
    const parts: string[] = [];
    elements.forEach((el) => {
      if (!el || el.ui_type !== 'message_footer') return;
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
          <MacTextView
            style={[styles.editInput, { height: editHeight }]}
            initialText={editingInitialText ?? editingText ?? ''}
            autoGrow
            minHeight={60}
            maxHeight={140}
            addToHeight={16}
            onHeightChange={setEditHeight}
            onChangeText={onChangeEditingText}
            onSubmit={(text) => onSubmitEdit(index, message, text)}
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
	          {onAction ? (
	            <PinnedMessageActionsBar
	              role={role}
	              onAction={(action) => onAction(action, index, message)}
	              availableActions={allowedActions}
	              extraActions={pluginActionDefs}
	            />
	          ) : null}
        </View>
        <MessageAttachmentsStrip
          message={message}
          idPrefix={`system:${index}`}
        />
        {content ? (
          <Text style={styles.systemText} selectable>
            {content}
          </Text>
        ) : null}
        {footerParts.length > 0 && (
          <View style={styles.footerRow}>
            <Text style={styles.footerText}>{footerParts.join('   ')}</Text>
          </View>
        )}
      </View>
    </View>
  );
};

const ToolMessageBubble: React.FC<DesktopMessageBubbleProps> = ({
  index,
  message,
  onAction,
  allowedActions,
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
          <View style={styles.headerIconsRow}>
	            {onAction ? (
	              <PinnedMessageActionsBar
	                role={role}
	                onAction={(action) => onAction(action, index, message)}
	                availableActions={allowedActions}
	                extraActions={pluginActionDefs}
	              />
	            ) : null}
          </View>
        </View>

        <MessageAttachmentsStrip
          message={message}
          idPrefix={`tool:${index}`}
        />

        {hasContent && (
          <View>
		    <TouchableOpacity
		      style={styles.disclosureRow}
		      activeOpacity={0.85}
		      testID={`tool-result-disclosure-${index}`}
		      onPress={() => setExpanded((prev) => !prev)}
		    >
		      <Text
		        style={[styles.collapsedHintText, styles.disclosureText]}
		        selectable
		        numberOfLines={1}
		      >
		        {singleLine || 'Tool result hidden (tap to expand).'}
		      </Text>
		      <View style={[styles.collapseIconButton, styles.disclosureChevronButton]}>
		        <Icon
		          name={expanded ? 'chevron-up' : 'chevron-down'}
		          size={14}
		          color={theme.textSecondary}
		        />
		      </View>
		    </TouchableOpacity>
            {expanded && (
              <View style={styles.collapsibleContainerTool}>
                <ScrollView
                  style={styles.collapsibleScroll}
                  nestedScrollEnabled
                  testID={`tool-result-scroll-${index}`}
                >
                  <MacTextView
                    style={styles.readOnlyBoundedText}
                    initialText={content}
                    editable={false}
                    autoGrow
                    minHeight={theme.typography.lineHeight.message}
                    textColor={theme.text}
                    fontSize={theme.typography.fontSize.message}
                    fontFamily="Menlo"
                    lineHeight={theme.typography.lineHeight.message}
                    textContainerInset={0}
                    testID={`tool-result-${index}`}
                  />
                </ScrollView>
              </View>
            )}
          </View>
        )}

        {!hasContent && (
          <Text style={styles.collapsedHintText} selectable>
            No tool output.
          </Text>
        )}

        {footerParts.length > 0 && (
          <View style={styles.footerRow}>
            <Text style={styles.footerText}>{footerParts.join('   ')}</Text>
          </View>
        )}
      </View>
    </View>
  );
};

const AssistantMessageBubble: React.FC<DesktopMessageBubbleProps> = ({
  index,
  message,
  onAction,
  allowedActions,
  isEditing,
  editingInitialText,
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
  const [editHeight, setEditHeight] = useState(60);
  const [reasoningExpanded, setReasoningExpanded] = useState(false);
  const [toolCallsExpanded, setToolCallsExpanded] = useState(false);
  const content = selectDisplayContent(message);
  const reasoning =
    typeof (message.metadata as any)?.reasoning === 'string'
      ? (message.metadata as any).reasoning
      : undefined;
  const reasoningSingleLine = useMemo(() => {
    if (!reasoning) return '';
    return toSingleLinePreview(reasoning);
  }, [reasoning]);
  const toolCalls = Array.isArray((message.metadata as any)?.tool_calls)
    ? (message.metadata as any).tool_calls
    : EMPTY_TOOL_CALLS;
  const toolCallNames = useMemo(() => {
    const names: string[] = [];
    for (const tc of toolCalls) {
      if (typeof tc === 'object' && tc !== null) {
        const func = (tc as any).function || {};
        const name =
          typeof func === 'object' && func !== null && typeof func.name === 'string'
            ? func.name
            : typeof (tc as any).type === 'string'
              ? (tc as any).type
              : 'tool';
        names.push(name);
      }
    }
    return names;
  }, [toolCalls]);
  const distinctToolCallNames = useMemo(() => Array.from(new Set(toolCallNames)), [toolCallNames]);
  const role = 'assistant';
  const footerParts = useMemo(() => {
    const elements = footerElements || [];
    const parts: string[] = [];
    elements.forEach((el) => {
      if (!el || el.ui_type !== 'message_footer') return;
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
          <MacTextView
            style={[styles.editInput, { height: editHeight }]}
            initialText={editingInitialText ?? editingText ?? ''}
            autoGrow
            minHeight={60}
            maxHeight={140}
            onHeightChange={setEditHeight}
            onChangeText={onChangeEditingText}
            onSubmit={(text) => onSubmitEdit(index, message, text)}
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
	            {onAction ? (
	              <PinnedMessageActionsBar
	                role={role}
	                onAction={(action) => onAction(action, index, message)}
	                availableActions={allowedActions}
	                extraActions={pluginActionDefs}
	              />
	            ) : null}
          </View>
        </View>

        <MessageAttachmentsStrip
          message={message}
          idPrefix={`assistant:${index}`}
        />

        {reasoning && (
          <TouchableOpacity
            style={styles.disclosureRow}
            activeOpacity={0.85}
            testID={`assistant-reasoning-disclosure-${index}`}
            onPress={() => setReasoningExpanded((prev) => !prev)}
          >
            <Text
              style={[styles.collapsedHintText, styles.disclosureText]}
              selectable
              numberOfLines={1}
            >
              {reasoningSingleLine ? `Reasoning: ${reasoningSingleLine}` : 'Reasoning'}
            </Text>
            <View style={[styles.collapseIconButton, styles.disclosureChevronButton]}>
              <Icon
                name={reasoningExpanded ? 'chevron-up' : 'chevron-down'}
                size={14}
                color={theme.textSecondary}
              />
            </View>
          </TouchableOpacity>
        )}

        {reasoning && reasoningExpanded && (
          <View style={styles.collapsibleContainerReasoning}>
            <ScrollView
              style={styles.collapsibleScroll}
              nestedScrollEnabled
              testID={`assistant-reasoning-scroll-${index}`}
            >
              <MacTextView
                style={styles.readOnlyBoundedText}
                initialText={reasoning}
                editable={false}
                autoGrow
                minHeight={theme.typography.lineHeight.small}
                textColor={theme.textSecondary}
                fontSize={theme.typography.fontSize.small}
                fontFamily="Menlo"
                lineHeight={theme.typography.lineHeight.small}
                italic
                textContainerInset={0}
                testID={`assistant-reasoning-${index}`}
              />
            </ScrollView>
          </View>
        )}

        {content ? (
          renderMode === 'raw' ? (
            <MacTextView
              style={styles.rawReadonlyInput}
              initialText={content}
              editable={false}
              autoGrow
              minHeight={theme.typography.lineHeight.message}
              textColor={theme.text}
              fontSize={theme.typography.fontSize.message}
              fontFamily="Menlo"
              lineHeight={theme.typography.lineHeight.message}
              textContainerInset={0}
              testID={`assistant-raw-message-${index}`}
            />
          ) : (
            <MarkdownMessageContent text={content} variant="assistant" />
          )
        ) : null}

        {toolCallNames.length > 0 && (
          <TouchableOpacity
            style={styles.disclosureRow}
            activeOpacity={0.85}
            testID={`assistant-tool-calls-disclosure-${index}`}
            onPress={() => setToolCallsExpanded((prev) => !prev)}
          >
            <Text
              style={[styles.collapsedHintText, styles.disclosureText]}
              selectable
              numberOfLines={1}
            >
              {toolCallNames.length} tool call{toolCallNames.length !== 1 ? 's' : ''}:{' '}
              {distinctToolCallNames.join(', ')}
            </Text>
            <View style={[styles.collapseIconButton, styles.disclosureChevronButton]}>
              <Icon
                name={toolCallsExpanded ? 'chevron-up' : 'chevron-down'}
                size={14}
                color={theme.textSecondary}
              />
            </View>
          </TouchableOpacity>
        )}

        {toolCallNames.length > 0 && toolCallsExpanded && (
          <View style={styles.collapsibleContainerTool}>
            <ScrollView
              style={styles.collapsibleScroll}
              nestedScrollEnabled
              testID={`assistant-tool-calls-scroll-${index}`}
            >
              {toolCalls.map((tc: any, idx: number) => {
                const func = tc.function || {};
                const toolName =
                  typeof func === 'object' && func !== null && typeof func.name === 'string'
                    ? func.name
                    : typeof tc.type === 'string'
                      ? tc.type
                      : 'tool';
                const callId = tc.id || tc.tool_call_id;

                const toolCallPreviews = Array.isArray((message.metadata as any)?.tool_call_previews)
                  ? (message.metadata as any).tool_call_previews
                  : [];
                const previewObj = toolCallPreviews.find((p: any) => p && p.id === callId);
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
                  <View key={callId || idx} style={styles.toolCallItem}>
                    <Text style={styles.toolCallName}>{toolName}</Text>
                    <MacTextView
                      style={styles.toolCallArgsReadOnly}
                      initialText={displayText}
                      editable={false}
                      autoGrow
                      minHeight={theme.typography.lineHeight.tiny}
                      textColor={theme.textSecondary}
                      fontSize={theme.typography.fontSize.tiny}
                      fontFamily="Menlo"
                      lineHeight={theme.typography.lineHeight.tiny}
                      textContainerInset={0}
                      testID={`assistant-tool-call-${index}-${idx}`}
                    />
                  </View>
                );
              })}
            </ScrollView>
          </View>
        )}

        {footerParts.length > 0 && (
          <View style={styles.footerRow}>
            <Text style={styles.footerText}>{footerParts.join('   ')}</Text>
          </View>
        )}
      </View>
    </View>
  );
};

export const DesktopMessageBubble: React.FC<DesktopMessageBubbleProps> = ({
  index,
  message,
  onAction,
  allowedActions,
  isEditing,
  editingInitialText,
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
  const role = message.role || 'unknown';

  if (role === 'user') {
    return (
      <UserMessageBubble
        index={index}
        message={message}
        allowedActions={allowedActions}
        onAction={onAction}
        isEditing={isEditing}
        editingInitialText={editingInitialText}
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
  if (role === 'system') {
    return (
      <SystemMessageBubble
        index={index}
        message={message}
        allowedActions={allowedActions}
        onAction={onAction}
        isEditing={isEditing}
        editingInitialText={editingInitialText}
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
        allowedActions={allowedActions}
        onAction={onAction}
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
        allowedActions={allowedActions}
        onAction={onAction}
        isEditing={isEditing}
        editingInitialText={editingInitialText}
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
  const content = selectDisplayContent(message);

  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.otherBubble]}>
        <Text style={styles.headerText}>{`[${index}] ${role}`}</Text>
        {content ? (
          <Text style={styles.contentText} selectable>
            {content}
          </Text>
        ) : null}
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
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
    },
    systemText: {
      fontSize: theme.typography.fontSize.message,
      lineHeight: theme.typography.lineHeight.message,
      color: theme.text,
      fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
      fontStyle: 'italic',
    },
    reasoningText: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
      fontStyle: 'italic',
      fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
    },
    toolCallItem: {
      marginBottom: 8,
    },
    toolCallName: {
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      color: theme.text,
      fontWeight: '600',
      marginBottom: 2,
      fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
    },
    toolCallArgs: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textSecondary,
      fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
      marginLeft: 8,
    },
    toolCallArgsReadOnly: {
      width: '98%',
      marginLeft: 8,
    },
    contentText: {
      fontSize: theme.typography.fontSize.message,
      lineHeight: theme.typography.lineHeight.message,
      color: theme.text,
      fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
    },
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
    readOnlyBoundedText: {
      width: '100%',
    },
    collapsedHintText: {
      marginTop: 2,
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textSecondary,
      fontStyle: 'italic',
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
    footerRow: {
      marginTop: 4,
    },
    footerText: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textSecondary,
      fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
    },
    editInput: {
      marginTop: 4,
      minHeight: 60,
      maxHeight: 140,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 6,
      paddingHorizontal: 4,
      paddingVertical: 4,
      fontSize: theme.typography.fontSize.message,
      lineHeight: theme.typography.lineHeight.message,
      fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
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
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '600',
    },
    editButtonTextSecondary: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '600',
    },
    rawReadonlyInput: {
      marginTop: 2,
      width: '100%',
    },
  });

export { createStyles as createDesktopMessageBubbleStyles };
export default DesktopMessageBubble;
