import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
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

export const MessageBubble: React.FC<MessageBubbleProps> = ({ index, message }) => {
  const role = message.role || 'unknown';
  const roleLabel = role.charAt(0).toUpperCase() + role.slice(1);
  const isUser = role === 'user';
  const isToolOrSystem = role === 'tool' || role === 'system';

  const content = selectDisplayContent(message);
  const reasoning = typeof (message.metadata as any)?.reasoning === 'string'
    ? (message.metadata as any).reasoning
    : undefined;

  return (
    <View style={styles.row}>
      <View
        style={[
          styles.bubble,
          isUser && styles.userBubble,
          !isUser && styles.otherBubble,
          isToolOrSystem && styles.toolSystemBubble,
        ]}
      >
        <Text style={styles.headerText}>{`[${index}] ${roleLabel}`}</Text>
        {reasoning && (
          <Text style={styles.reasoningText}>
            thinking: {reasoning}
          </Text>
        )}
        {content ? <Text style={[styles.contentText, isUser && styles.userContentText]}>{content}</Text> : null}
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
  headerText: {
    fontSize: 12,
    color: '#8E8E93',
    marginBottom: 4,
  },
  reasoningText: {
    fontSize: 12,
    color: '#8E8E93',
    fontStyle: 'italic',
    marginBottom: 4,
  },
  contentText: {
    fontSize: 14,
    color: '#000000',
  },
  userContentText: {
    color: '#FFFFFF',
  },
});

export default MessageBubble;
