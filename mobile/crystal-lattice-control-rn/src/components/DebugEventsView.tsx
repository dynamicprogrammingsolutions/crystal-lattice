import React, { useMemo, useState } from 'react';
import {
  FlatList,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import type { Event } from '../eventsTypes';
import { useTheme, type Theme } from '../theme';

interface DebugEventsViewProps {
  events: Event[];
  onClose: () => void;
}

const DebugEventsView: React.FC<DebugEventsViewProps> = ({ events, onClose }) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [expandedById, setExpandedById] = useState<Record<string, boolean>>({});

  const toggleExpanded = (id: string) => {
    setExpandedById((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const renderItem = ({ item }: { item: Event }) => {
    const id = typeof item.event_id === 'string' ? item.event_id : '';
    const expanded = id ? !!expandedById[id] : false;
    const summary = buildSummary(item);

    return (
      <TouchableOpacity
        style={styles.eventRow}
        onPress={() => {
          if (id) toggleExpanded(id);
        }}
        activeOpacity={0.7}
      >
        <View style={styles.eventHeaderRow}>
          <Text style={styles.eventHeaderText} numberOfLines={1}>
            #{id || '?'} · {item.type} · {item.session_id}
            {item.request_id ? ` · req=${item.request_id}` : ''}
          </Text>
          {id ? (
            <Icon
              name={expanded ? 'chevron-up' : 'chevron-down'}
              size={16}
              color={theme.textSecondary}
            />
          ) : null}
        </View>
        {summary ? <Text style={styles.eventSummaryText}>{summary}</Text> : null}
        {expanded && (
          <View style={styles.jsonContainer}>
            <ScrollView>
              <Text style={styles.jsonText}>{JSON.stringify(item, null, 2)}</Text>
            </ScrollView>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  return (
    <View style={styles.overlayContainer}>
      <View style={styles.headerRow}>
        <Text style={styles.title}>Debug events</Text>
        <TouchableOpacity style={styles.closeButton} onPress={onClose}>
          <Icon name="x" size={20} color={theme.text} />
        </TouchableOpacity>
      </View>
      <Text style={styles.subtitle}>
        Tap an event to expand and inspect its JSON payload.
      </Text>
      <FlatList
        data={events}
        keyExtractor={(item, index) =>
          typeof item.event_id === 'string' ? item.event_id : String(index)
        }
        renderItem={renderItem}
        style={styles.list}
      />
    </View>
  );
};

function buildSummary(ev: Event): string {
  switch (ev.type) {
    case 'final': {
      const messages = Array.isArray(ev.messages) ? ev.messages : [];
      const roles = messages.map((m) => m.role).join(', ');
      return `final – ${messages.length} messages [${roles}]`;
    }
    case 'message_appended': {
      const role = ev.role;
      const content = typeof ev.content === 'string' ? ev.content : '';
      const snippet = content.length > 40 ? `${content.slice(0, 37)}...` : content;
      return `message_appended – role=${role}, content="${snippet}"`;
    }
    case 'tool_results': {
      const messages = Array.isArray((ev as any).messages) ? (ev as any).messages : [];
      return `tool_results – ${messages.length} messages`;
    }
    case 'error': {
      const detail = typeof (ev as any).detail === 'string' ? (ev as any).detail : '';
      const snippet = detail.length > 60 ? `${detail.slice(0, 57)}...` : detail;
      return `error – ${snippet}`;
    }
    case 'checkpoint': {
      return 'checkpoint marker';
    }
    case 'tool_interceptor_prompt': {
      const e = ev as { tool_call_id?: string; phase?: string; prompt?: { title?: string } };
      const title =
        e.prompt && typeof e.prompt === 'object' && typeof e.prompt.title === 'string'
          ? e.prompt.title
          : '';
      const tid = typeof e.tool_call_id === 'string' ? e.tool_call_id : '';
      const phase = typeof e.phase === 'string' ? e.phase : '';
      return `tool_interceptor_prompt – phase=${phase}${tid ? ` id=${tid}` : ''}${title ? ` "${title}"` : ''}`;
    }
    default:
      return '';
  }
}

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    overlayContainer: {
      flex: 1,
      backgroundColor: theme.surface,
      paddingTop: 32,
      paddingHorizontal: 12,
    },
    headerRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 8,
    },
    title: {
      fontSize: 18,
      fontWeight: '600',
      color: theme.text,
    },
    subtitle: {
      fontSize: 12,
      color: theme.textSecondary,
      marginBottom: 8,
    },
    closeButton: {
      paddingHorizontal: 8,
      paddingVertical: 4,
    },
    list: {
      flex: 1,
    },
    eventRow: {
      paddingVertical: 8,
      paddingHorizontal: 10,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: theme.border,
      marginBottom: 6,
      backgroundColor: theme.surfaceAlt,
    },
    eventHeaderRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
    eventHeaderText: {
      flex: 1,
      fontSize: 12,
      color: theme.text,
      marginRight: 8,
    },
    eventSummaryText: {
      marginTop: 2,
      fontSize: 11,
      color: theme.textSecondary,
    },
    jsonContainer: {
      marginTop: 6,
      maxHeight: 220,
      borderRadius: 6,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.background,
      padding: 6,
    },
    jsonText: {
      fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
      fontSize: 11,
      color: theme.text,
    },
  });

export default DebugEventsView;
