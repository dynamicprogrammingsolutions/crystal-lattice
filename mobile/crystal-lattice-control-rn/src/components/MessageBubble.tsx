import React, { useState } from 'react';
import {
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import type { ApiMessage } from '../api';
import MessageActionsBar from './MessageActionsBar';
import type { MessageActionKey } from '../messageActions';
import { selectDisplayContent } from '../messageUtils';
import MarkdownMessageContent from './MarkdownMessageContent';

export interface MessageBubbleProps {
  index: number;
  message: ApiMessage;
  pinnedActions?: MessageActionKey[];
  onAction?: (action: MessageActionKey, index: number, message: ApiMessage) => void;
  onChangePinnedForRole?: (role: string, pinned: MessageActionKey[]) => void;
  allowedActions?: MessageActionKey[];
  isEditing?: boolean;
  editingText?: string;
  onChangeEditingText?: (text: string) => void;
  onSubmitEdit?: (index: number, message: ApiMessage, newText: string) => void;
  onCancelEdit?: () => void;
}

const UserMessageBubble: React.FC<MessageBubbleProps> = ({
  index,
  message,
  pinnedActions,
  onAction,
  onChangePinnedForRole,
  allowedActions,
  isEditing,
  editingText,
  onChangeEditingText,
  onSubmitEdit,
  onCancelEdit,
}) => {
  const content = selectDisplayContent(message);
  const role = 'user';

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
        {content ? <Text style={[styles.contentText, styles.userContentText]}>{content}</Text> : null}
        {pinnedActions && onAction && onChangePinnedForRole && (
          <MessageActionsBar
            pinned={pinnedActions}
            onChangePinned={(next) => onChangePinnedForRole(role, next)}
            onAction={(action) => onAction(action, index, message)}
            availableActions={allowedActions}
          />
        )}
      </View>
    </View>
  );
};

const SystemMessageBubble: React.FC<MessageBubbleProps> = ({
  index,
  message,
  pinnedActions,
  onAction,
  onChangePinnedForRole,
  allowedActions,
  isEditing,
  editingText,
  onChangeEditingText,
  onSubmitEdit,
  onCancelEdit,
}) => {
  const content = selectDisplayContent(message);
  const role = 'system';

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
        {content ? <Text style={styles.systemText}>{content}</Text> : null}
        {pinnedActions && onAction && onChangePinnedForRole && (
          <MessageActionsBar
            pinned={pinnedActions}
            onChangePinned={(next) => onChangePinnedForRole(role, next)}
            onAction={(action) => onAction(action, index, message)}
            availableActions={allowedActions}
          />
        )}
      </View>
    </View>
  );
};

const ToolMessageBubble: React.FC<MessageBubbleProps> = ({
  index,
  message,
  pinnedActions,
  onAction,
  onChangePinnedForRole,
  allowedActions,
}) => {
  const [expanded, setExpanded] = useState(false);
  const content = selectDisplayContent(message);
  const hasContent = !!content;
  const role = 'tool';

  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.otherBubble, styles.toolSystemBubble]}>
        <View style={styles.headerRow}>
          <Text style={styles.headerText}>{`[${index}] Tool`}</Text>
          {hasContent && (
            <TouchableOpacity
              style={styles.collapseIconButton}
              onPress={() => setExpanded((prev) => !prev)}
            >
              <Icon
                name={expanded ? 'chevron-up' : 'chevron-down'}
                size={14}
                color="#8E8E93"
              />
            </TouchableOpacity>
          )}
        </View>

        {hasContent && expanded && (
          <View style={styles.collapsibleContainerTool}>
            <ScrollView
              style={styles.collapsibleScroll}
              nestedScrollEnabled
            >
              <Text style={styles.contentText}>{content}</Text>
            </ScrollView>
          </View>
        )}

        {hasContent && !expanded && (
          <Text style={styles.collapsedHintText}>Tool result hidden (tap to expand).</Text>
        )}

        {!hasContent && (
          <Text style={styles.collapsedHintText}>No tool output.</Text>
        )}
        {pinnedActions && onAction && onChangePinnedForRole && (
          <MessageActionsBar
            pinned={pinnedActions}
            onChangePinned={(next) => onChangePinnedForRole(role, next)}
            onAction={(action) => onAction(action, index, message)}
            availableActions={allowedActions}
          />
        )}
      </View>
    </View>
  );
};

const AssistantMessageBubble: React.FC<MessageBubbleProps> = ({
  index,
  message,
  pinnedActions,
  onAction,
  onChangePinnedForRole,
  allowedActions,
  isEditing,
  editingText,
  onChangeEditingText,
  onSubmitEdit,
  onCancelEdit,
}) => {
  const [reasoningExpanded, setReasoningExpanded] = useState(false);
  const content = selectDisplayContent(message);
  const reasoning = typeof (message.metadata as any)?.reasoning === 'string'
    ? (message.metadata as any).reasoning
    : undefined;
  const role = 'assistant';

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
          {reasoning && (
            <TouchableOpacity
              style={styles.collapseIconButton}
              onPress={() => setReasoningExpanded((prev) => !prev)}
            >
              <Icon
                name={reasoningExpanded ? 'chevron-up' : 'chevron-down'}
                size={14}
                color="#8E8E93"
              />
            </TouchableOpacity>
          )}
        </View>

        {reasoning && reasoningExpanded && (
          <View style={styles.collapsibleContainerReasoning}>
            <ScrollView
              style={styles.collapsibleScroll}
              nestedScrollEnabled
            >
              <Text style={styles.reasoningText}>{reasoning}</Text>
            </ScrollView>
          </View>
        )}

        {reasoning && !reasoningExpanded && (
          <Text style={styles.collapsedHintText}>Reasoning hidden (tap chevron to expand).</Text>
        )}

        {content ? (
          <MarkdownMessageContent
            text={content}
            variant="assistant"
          />
        ) : null}
        {pinnedActions && onAction && onChangePinnedForRole && (
          <MessageActionsBar
            pinned={pinnedActions}
            onChangePinned={(next) => onChangePinnedForRole(role, next)}
            onAction={(action) => onAction(action, index, message)}
            availableActions={allowedActions}
          />
        )}
      </View>
    </View>
  );
};

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  index,
  message,
  pinnedActions,
  onAction,
  onChangePinnedForRole,
  allowedActions,
  isEditing,
  editingText,
  onChangeEditingText,
  onSubmitEdit,
  onCancelEdit,
}) => {
  const role = message.role || 'unknown';

  if (role === 'user') {
    return (
      <UserMessageBubble
        index={index}
        message={message}
        pinnedActions={pinnedActions}
        onAction={onAction}
        onChangePinnedForRole={onChangePinnedForRole}
        allowedActions={allowedActions}
        isEditing={isEditing}
        editingText={editingText}
        onChangeEditingText={onChangeEditingText}
        onSubmitEdit={onSubmitEdit}
        onCancelEdit={onCancelEdit}
      />
    );
  }
  if (role === 'system') {
    return (
      <SystemMessageBubble
        index={index}
        message={message}
        pinnedActions={pinnedActions}
        onAction={onAction}
        onChangePinnedForRole={onChangePinnedForRole}
        allowedActions={allowedActions}
        isEditing={isEditing}
        editingText={editingText}
        onChangeEditingText={onChangeEditingText}
        onSubmitEdit={onSubmitEdit}
        onCancelEdit={onCancelEdit}
      />
    );
  }
  if (role === 'tool') {
    return (
      <ToolMessageBubble
        index={index}
        message={message}
        pinnedActions={pinnedActions}
        onAction={onAction}
        onChangePinnedForRole={onChangePinnedForRole}
        allowedActions={allowedActions}
      />
    );
  }
  if (role === 'assistant') {
    return (
      <AssistantMessageBubble
        index={index}
        message={message}
        pinnedActions={pinnedActions}
        onAction={onAction}
        onChangePinnedForRole={onChangePinnedForRole}
        allowedActions={allowedActions}
        isEditing={isEditing}
        editingText={editingText}
        onChangeEditingText={onChangeEditingText}
        onSubmitEdit={onSubmitEdit}
        onCancelEdit={onCancelEdit}
      />
    );
  }

  // Fallback for unexpected roles
  const content = selectDisplayContent(message);
  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.otherBubble]}>
        <Text style={styles.headerText}>{`[${index}] ${role}`}</Text>
        {content ? <Text style={styles.contentText}>{content}</Text> : null}
        {pinnedActions && onAction && onChangePinnedForRole && (
          <MessageActionsBar
            pinned={pinnedActions}
            onChangePinned={(next) => onChangePinnedForRole(role, next)}
            onAction={(action) => onAction(action, index, message)}
            availableActions={allowedActions}
          />
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  row: {
    marginBottom: 8,
  },
  bubble: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
  },
  userBubble: {
    backgroundColor: '#007AFF',
  },
  otherBubble: {
    backgroundColor: 'transparent',
  },
  toolSystemBubble: {
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 4,
  },
  headerText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  systemText: {
    fontSize: 13,
    color: '#000000',
    fontFamily: 'Courier',
    fontStyle: 'italic',
  },
  reasoningText: {
    fontSize: 12,
    color: '#8E8E93',
    fontStyle: 'italic',
    fontFamily: 'Courier',
  },
  contentText: {
    fontSize: 14,
    color: '#000000',
    fontFamily: 'Courier',
  },
  userContentText: {
    color: '#FFFFFF',
  },
  collapseIconButton: {
    paddingHorizontal: 4,
    paddingVertical: 2,
  },
  collapsibleContainerTool: {
    marginTop: 4,
    maxHeight: 220,
    borderRadius: 6,
    backgroundColor: 'rgba(142, 142, 147, 0.08)',
    overflow: 'hidden',
  },
  collapsibleContainerReasoning: {
    marginTop: 4,
    maxHeight: 160,
    borderRadius: 6,
    backgroundColor: 'rgba(142, 142, 147, 0.08)',
    overflow: 'hidden',
  },
  collapsibleScroll: {
    paddingHorizontal: 4,
    paddingVertical: 4,
  },
  collapsedHintText: {
    marginTop: 2,
    fontSize: 11,
    color: '#8E8E93',
    fontStyle: 'italic',
  },
  editInput: {
    marginTop: 4,
    minHeight: 60,
    maxHeight: 140,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 6,
    fontSize: 14,
    fontFamily: 'Courier',
    backgroundColor: '#FFFFFF',
  },
  editInputOnBlue: {
    backgroundColor: '#FFFFFF',
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
    backgroundColor: '#007AFF',
  },
  editButtonSecondary: {
    backgroundColor: '#E5E5EA',
  },
  editButtonTextPrimary: {
    color: '#FFFFFF',
    fontSize: 14,
    fontWeight: '600',
  },
  editButtonTextSecondary: {
    color: '#000000',
    fontSize: 14,
    fontWeight: '600',
  },
});

export default MessageBubble;
