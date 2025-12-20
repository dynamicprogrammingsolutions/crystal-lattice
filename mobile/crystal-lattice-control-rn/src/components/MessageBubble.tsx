import React, { useState } from 'react';
import { ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import type { ApiMessage } from '../api';

export interface MessageBubbleProps {
  index: number;
  message: ApiMessage;
}

function selectDisplayContent(msg: ApiMessage): string {
  const metadata = msg.metadata || {};
  const display = (metadata as any).display;
  if (display && typeof display === 'object' && display.type === 'text') {
    const content = (display as any).content;
    if (typeof content === 'string' && content.trim()) {
      return content;
    }
  }

  if (typeof msg.content === 'string' && msg.content.trim()) {
    return msg.content;
  }

  return '';
}

const UserMessageBubble: React.FC<MessageBubbleProps> = ({ index, message }) => {
  const content = selectDisplayContent(message);

  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.userBubble]}>
        <Text style={styles.headerText}>{`[${index}] User`}</Text>
        {content ? <Text style={[styles.contentText, styles.userContentText]}>{content}</Text> : null}
      </View>
    </View>
  );
};

const SystemMessageBubble: React.FC<MessageBubbleProps> = ({ index, message }) => {
  const content = selectDisplayContent(message);

  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.otherBubble, styles.toolSystemBubble]}>
        <Text style={styles.headerText}>{`[${index}] System`}</Text>
        {content ? <Text style={styles.systemText}>{content}</Text> : null}
      </View>
    </View>
  );
};

const ToolMessageBubble: React.FC<MessageBubbleProps> = ({ index, message }) => {
  const [expanded, setExpanded] = useState(false);
  const content = selectDisplayContent(message);
  const hasContent = !!content;

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
      </View>
    </View>
  );
};

const AssistantMessageBubble: React.FC<MessageBubbleProps> = ({ index, message }) => {
  const [reasoningExpanded, setReasoningExpanded] = useState(false);
  const content = selectDisplayContent(message);
  const reasoning = typeof (message.metadata as any)?.reasoning === 'string'
    ? (message.metadata as any).reasoning
    : undefined;

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

        {content ? <Text style={styles.contentText}>{content}</Text> : null}

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
      </View>
    </View>
  );
};

export const MessageBubble: React.FC<MessageBubbleProps> = ({ index, message }) => {
  const role = message.role || 'unknown';

  if (role === 'user') {
    return <UserMessageBubble index={index} message={message} />;
  }
  if (role === 'system') {
    return <SystemMessageBubble index={index} message={message} />;
  }
  if (role === 'tool') {
    return <ToolMessageBubble index={index} message={message} />;
  }
  if (role === 'assistant') {
    return <AssistantMessageBubble index={index} message={message} />;
  }

  // Fallback for unexpected roles
  const content = selectDisplayContent(message);
  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.otherBubble]}>
        <Text style={styles.headerText}>{`[${index}] ${role}`}</Text>
        {content ? <Text style={styles.contentText}>{content}</Text> : null}
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
});

export default MessageBubble;
