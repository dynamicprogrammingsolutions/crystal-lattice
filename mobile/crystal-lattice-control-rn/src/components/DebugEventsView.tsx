import React, { useMemo, useState } from 'react';
import {
  Platform,
  ScrollView,
  SectionList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import type { DebugTimelineEntry } from '../debugTimeline';
import type { Event } from '../eventsTypes';
import { useTheme, type Theme } from '../theme';

interface DebugEventsViewProps {
  events: Event[];
  notes?: DebugTimelineEntry[];
  onClose: () => void;
}

type DebugSectionItem =
  | { kind: 'note'; note: DebugTimelineEntry }
  | { kind: 'event'; event: Event };

const DebugEventsView: React.FC<DebugEventsViewProps> = ({ events, notes = [], onClose }) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [expandedById, setExpandedById] = useState<Record<string, boolean>>({});

  const toggleExpanded = (id: string) => {
    setExpandedById((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const sections = useMemo(
    () => [
      {
        title: 'Mobile timeline',
        data: notes
          .slice()
          .reverse()
          .map((note) => ({ kind: 'note' as const, note })),
      },
      {
        title: 'Streamed events',
        data: events.map((event) => ({ kind: 'event' as const, event })),
      },
    ],
    [events, notes],
  );

  const renderItem = ({ item }: { item: DebugSectionItem }) => {
    if (item.kind === 'note') {
      const note = item.note;
      const expanded = !!expandedById[note.id];
      return (
        <TouchableOpacity
          style={styles.noteRow}
          onPress={() => toggleExpanded(note.id)}
          activeOpacity={0.7}
        >
          <View style={styles.rowHeader}>
            <Text style={styles.rowHeaderText} numberOfLines={1}>
              {formatTimestamp(note.timestampMs)} · {note.scope} · {note.title}
            </Text>
            <Icon
              name={expanded ? 'chevron-up' : 'chevron-down'}
              size={16}
              color={theme.textSecondary}
            />
          </View>
          {note.detail ? <Text style={styles.rowSummaryText}>{note.detail}</Text> : null}
          {expanded && note.meta ? (
            <View style={styles.jsonContainer}>
              <ScrollView>
                <Text style={styles.jsonText}>{JSON.stringify(note.meta, null, 2)}</Text>
              </ScrollView>
            </View>
          ) : null}
        </TouchableOpacity>
      );
    }

    const event = item.event;
    const id = typeof event.event_id === 'string' ? event.event_id : '';
    const expanded = id ? !!expandedById[id] : false;
    const summary = buildSummary(event);

    return (
      <TouchableOpacity
        style={styles.eventRow}
        onPress={() => {
          if (id) {
            toggleExpanded(id);
          }
        }}
        activeOpacity={0.7}
      >
        <View style={styles.rowHeader}>
          <Text style={styles.rowHeaderText} numberOfLines={1}>
            #{id || '?'} · {event.type} · {event.session_id}
            {event.request_id ? ` · req=${event.request_id}` : ''}
          </Text>
          {id ? (
            <Icon
              name={expanded ? 'chevron-up' : 'chevron-down'}
              size={16}
              color={theme.textSecondary}
            />
          ) : null}
        </View>
        {summary ? <Text style={styles.rowSummaryText}>{summary}</Text> : null}
        {expanded && (
          <View style={styles.jsonContainer}>
            <ScrollView>
              <Text style={styles.jsonText}>{JSON.stringify(event, null, 2)}</Text>
            </ScrollView>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderSectionHeader = ({
    section,
  }: {
    section: { title: string; data: DebugSectionItem[] };
  }) => {
    if (section.data.length === 0) {
      return null;
    }

    return <Text style={styles.sectionTitle}>{section.title}</Text>;
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
        Tap a mobile timeline entry or streamed event to inspect its JSON payload.
      </Text>
      <SectionList
        sections={sections}
        keyExtractor={(item, index) =>
          item.kind === 'note'
            ? item.note.id
            : typeof item.event.event_id === 'string'
              ? item.event.event_id
              : `event-${index}`
        }
        renderItem={renderItem}
        renderSectionHeader={renderSectionHeader}
        style={styles.list}
        stickySectionHeadersEnabled={false}
      />
    </View>
  );
};

function formatTimestamp(timestampMs: number): string {
  return new Date(timestampMs).toISOString().slice(11, 19);
}

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
    sectionTitle: {
      fontSize: 12,
      fontWeight: '600',
      color: theme.textSecondary,
      marginTop: 10,
      marginBottom: 6,
      textTransform: 'uppercase',
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
    noteRow: {
      paddingVertical: 8,
      paddingHorizontal: 10,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: theme.border,
      marginBottom: 6,
      backgroundColor: theme.backgroundAlt,
    },
    rowHeader: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
    rowHeaderText: {
      flex: 1,
      fontSize: 12,
      color: theme.text,
      marginRight: 8,
    },
    rowSummaryText: {
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