import React, { useMemo, useState } from 'react';
import { Platform, ScrollView, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import {
  useTheme,
  type Theme,
} from '@crystal-lattice/frontend-rn-components';
import {
  selectDisplayContent,
  selectSingleLineContent,
  type ApiMessage,
} from '@crystal-lattice/frontend-sdk';

import MarkdownMessageContent from './MarkdownMessageContent';

export interface DesktopMessageBubbleProps {
  index: number | null;
  message: ApiMessage;
  isStreaming?: boolean;
  renderMode?: 'markdown' | 'raw';
}

function formatHeader(options: {
  index: number | null;
  isStreaming: boolean;
  roleLabel: string;
}): string {
  const prefix = options.index == null ? '[stream]' : `[${options.index}]`;
  return `${prefix} ${options.roleLabel}${options.isStreaming ? ' • streaming' : ''}`;
}

const UserMessageBubble: React.FC<DesktopMessageBubbleProps> = ({
  index,
  message,
  isStreaming,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const content = selectDisplayContent(message);

  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.userBubble]}>
        <Text style={styles.headerText}>{formatHeader({ index, isStreaming: !!isStreaming, roleLabel: 'User' })}</Text>
        {content ? (
          <Text style={[styles.contentText, styles.userContentText]} selectable>
            {content}
          </Text>
        ) : null}
      </View>
    </View>
  );
};

const SystemMessageBubble: React.FC<DesktopMessageBubbleProps> = ({
  index,
  message,
  isStreaming,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const content = selectDisplayContent(message);

  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.otherBubble, styles.toolSystemBubble]}>
        <Text style={styles.headerText}>{formatHeader({ index, isStreaming: !!isStreaming, roleLabel: 'System' })}</Text>
        {content ? (
          <Text style={styles.systemText} selectable>
            {content}
          </Text>
        ) : null}
      </View>
    </View>
  );
};

const ToolMessageBubble: React.FC<DesktopMessageBubbleProps> = ({
  index,
  message,
  isStreaming,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [expanded, setExpanded] = useState(false);
  const content = selectDisplayContent(message);
  const singleLine = selectSingleLineContent(message);
  const hasContent = !!content;
  const toolName =
    typeof (message.metadata as any)?.tool_name === 'string'
      ? (message.metadata as any).tool_name
      : undefined;

  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.otherBubble, styles.toolSystemBubble]}>
        <View style={styles.headerRow}>
          <Text style={styles.headerText}>
            {formatHeader({ index, isStreaming: !!isStreaming, roleLabel: 'Tool' })}
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

        {hasContent && expanded && (
          <View style={styles.collapsibleContainerTool}>
            <ScrollView style={styles.collapsibleScroll} nestedScrollEnabled>
              <Text style={styles.contentText} selectable>
                {content}
              </Text>
            </ScrollView>
          </View>
        )}

        {hasContent && !expanded && (
          <Text style={styles.collapsedHintText} selectable>
            {singleLine || 'Tool result hidden (tap to expand).'}
          </Text>
        )}

        {!hasContent && (
          <Text style={styles.collapsedHintText} selectable>
            No tool output.
          </Text>
        )}
      </View>
    </View>
  );
};

const AssistantMessageBubble: React.FC<DesktopMessageBubbleProps> = ({
  index,
  message,
  isStreaming,
  renderMode,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [reasoningExpanded, setReasoningExpanded] = useState(false);
  const [toolCallsExpanded, setToolCallsExpanded] = useState(false);
  const content = selectDisplayContent(message);

  const reasoning =
    typeof (message.metadata as any)?.reasoning === 'string' ? (message.metadata as any).reasoning : undefined;
  const toolCalls = Array.isArray((message.metadata as any)?.tool_calls)
    ? (message.metadata as any).tool_calls
    : [];
  const toolCallNames = useMemo(() => {
    const names: string[] = [];
    for (const toolCall of toolCalls) {
      if (typeof toolCall === 'object' && toolCall !== null) {
        const func = (toolCall as any).function || {};
        const name =
          typeof func === 'object' &&
          func !== null &&
          typeof (func as any).name === 'string'
            ? (func as any).name
            : typeof (toolCall as any).type === 'string'
              ? (toolCall as any).type
              : 'tool';
        names.push(name);
      }
    }
    return names;
  }, [toolCalls]);
  const distinctToolCallNames = useMemo(() => Array.from(new Set(toolCallNames)), [toolCallNames]);

  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.otherBubble]}>
        <View style={styles.headerRow}>
          <Text style={styles.headerText}>
            {formatHeader({ index, isStreaming: !!isStreaming, roleLabel: 'Assistant' })}
          </Text>
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

        {reasoning && reasoningExpanded && (
          <View style={styles.collapsibleContainerReasoning}>
            <ScrollView style={styles.collapsibleScroll} nestedScrollEnabled>
              <Text style={styles.reasoningText} selectable>
                {reasoning}
              </Text>
            </ScrollView>
          </View>
        )}

        {reasoning && !reasoningExpanded && (
          <Text style={styles.collapsedHintText} selectable>
            Reasoning hidden (tap chevron to expand).
          </Text>
        )}

        {content ? (
          <MarkdownMessageContent
            text={content}
            renderMode={renderMode === 'raw' ? 'raw' : 'markdown'}
            variant="assistant"
          />
        ) : null}

        {toolCallNames.length > 0 && toolCallsExpanded && (
          <View style={styles.collapsibleContainerTool}>
            <ScrollView style={styles.collapsibleScroll} nestedScrollEnabled>
              {toolCalls.map((toolCall: any, idx: number) => {
                const func = toolCall.function || {};
                const toolName =
                  typeof func === 'object' && func !== null && typeof func.name === 'string'
                    ? func.name
                    : typeof toolCall.type === 'string'
                      ? toolCall.type
                      : 'tool';
                const callId = toolCall.id || toolCall.tool_call_id;

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
                    : typeof toolCall.arguments === 'string'
                      ? toolCall.arguments
                      : JSON.stringify(toolCall.arguments || {}, null, 2));

                return (
                  <View key={callId || idx} style={styles.toolCallItem}>
                    <Text style={styles.toolCallName}>{toolName}</Text>
                    <Text style={styles.toolCallArgs} selectable>
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
      </View>
    </View>
  );
};

export const DesktopMessageBubble: React.FC<DesktopMessageBubbleProps> = (props) => {
  const role = props.message.role || 'unknown';

  if (role === 'user') {
    return <UserMessageBubble {...props} />;
  }
  if (role === 'system') {
    return <SystemMessageBubble {...props} />;
  }
  if (role === 'tool') {
    return <ToolMessageBubble {...props} />;
  }
  if (role === 'assistant') {
    return <AssistantMessageBubble {...props} />;
  }

  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const content = selectDisplayContent(props.message);

  return (
    <View style={styles.row}>
      <View style={[styles.bubble, styles.otherBubble]}>
        <Text style={styles.headerText}>
          {formatHeader({ index: props.index, isStreaming: !!props.isStreaming, roleLabel: role })}
        </Text>
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
      fontSize: 12,
      color: theme.textSecondary,
    },
    systemText: {
      fontSize: 13,
      color: theme.text,
      fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
      fontStyle: 'italic',
    },
    reasoningText: {
      fontSize: 12,
      color: theme.textSecondary,
      fontStyle: 'italic',
      fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
    },
    toolCallItem: {
      marginBottom: 8,
    },
    toolCallName: {
      fontSize: 13,
      color: theme.text,
      fontWeight: '600',
      marginBottom: 2,
      fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
    },
    toolCallArgs: {
      fontSize: 11,
      color: theme.textSecondary,
      fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
      marginLeft: 8,
    },
    contentText: {
      fontSize: 14,
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
    collapsedHintText: {
      marginTop: 2,
      fontSize: 11,
      color: theme.textSecondary,
      fontStyle: 'italic',
    },
  });

export default DesktopMessageBubble;
