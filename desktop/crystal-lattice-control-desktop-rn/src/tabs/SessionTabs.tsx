import React, { useMemo, useRef, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { DropdownMenuSurface, useTheme } from '@crystal-lattice/frontend-rn-components';

export interface DesktopSessionTab {
  tabId: string;
  connectionId: string;
  sessionId: string;
  title: string;
}

export interface SessionTabsProps {
  tabs: DesktopSessionTab[];
  activeTabId: string | null;
  connectionNameById: Record<string, string>;
  onSelectTab: (tabId: string) => void;
  onCloseTab: (tabId: string) => void;
}

export function SessionTabs({
  tabs,
  activeTabId,
  connectionNameById,
  onSelectTab,
  onCloseTab,
}: SessionTabsProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const menuAnchorRef = useRef<any>(null);
  const [menuVisible, setMenuVisible] = useState(false);

  return (
    <View style={styles.root}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.tabsContainer}
      >
        {tabs.map((tab) => {
          const active = tab.tabId === activeTabId;
          const connectionName = connectionNameById[tab.connectionId] ?? tab.connectionId;
          return (
            <Pressable
              key={tab.tabId}
              style={(state) => {
                const hovered = (state as any).hovered as boolean | undefined;
                return [
                  styles.tab,
                  active && styles.tabActive,
                  (hovered || state.pressed) && styles.tabHovered,
                ];
              }}
              onPress={() => onSelectTab(tab.tabId)}
            >
              <View style={styles.tabTextContainer}>
                <Text style={[styles.tabTitle, active && styles.tabTitleActive]} numberOfLines={1}>
                  {tab.title}
                </Text>
                <Text style={styles.tabMeta} numberOfLines={1}>
                  {connectionName}
                </Text>
              </View>
              <Pressable
                style={(state) => {
                  const hovered = (state as any).hovered as boolean | undefined;
                  return [
                    styles.closeButton,
                    (hovered || state.pressed) && styles.closeButtonHovered,
                  ];
                }}
                onPress={(event) => {
                  (event as any)?.stopPropagation?.();
                  onCloseTab(tab.tabId);
                }}
              >
                <Text style={styles.closeButtonText}>×</Text>
              </Pressable>
            </Pressable>
          );
        })}
      </ScrollView>

      <Pressable
        ref={menuAnchorRef}
        style={(state) => {
          const hovered = (state as any).hovered as boolean | undefined;
          return [styles.menuButton, (hovered || state.pressed) && styles.menuButtonHovered];
        }}
        onPress={() => setMenuVisible(true)}
      >
        <Text style={styles.menuButtonText}>⋯</Text>
      </Pressable>

      <DropdownMenuSurface
        visible={menuVisible}
        onRequestClose={() => setMenuVisible(false)}
        anchorRef={menuAnchorRef}
        offset={{ y: 6 }}
      >
        <View style={styles.menuContent}>
          <Pressable
            style={(state) => {
              const hovered = (state as any).hovered as boolean | undefined;
              return [styles.menuItem, (hovered || state.pressed) && styles.menuItemHovered];
            }}
            onPress={() => setMenuVisible(false)}
          >
            <Text style={styles.menuItemText}>Tab actions (placeholder)</Text>
          </Pressable>
        </View>
      </DropdownMenuSurface>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    root: {
      flexDirection: 'row',
      alignItems: 'stretch',
      gap: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.border,
      backgroundColor: theme.backgroundAlt,
    },
    tabsContainer: {
      alignItems: 'stretch',
      gap: 8,
      paddingRight: 8,
    },
    tab: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 10,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
      borderRadius: 12,
      paddingLeft: 10,
      paddingVertical: 8,
      backgroundColor: theme.surface,
      minWidth: 160,
      maxWidth: 220,
    },
    tabActive: {
      borderColor: theme.primary,
    },
    tabHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    tabTextContainer: {
      flex: 1,
      gap: 1,
    },
    tabTitle: {
      fontSize: 12,
      fontWeight: '700',
      color: theme.text,
    },
    tabTitleActive: {
      color: theme.primary,
    },
    tabMeta: {
      fontSize: 10,
      color: theme.textSecondary,
    },
    closeButton: {
      paddingHorizontal: 8,
      paddingVertical: 6,
      borderTopRightRadius: 12,
      borderBottomRightRadius: 12,
    },
    closeButtonHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    closeButtonText: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.textSecondary,
      lineHeight: 14,
    },
    menuButton: {
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: 10,
      borderRadius: 10,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    menuButtonHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    menuButtonText: {
      fontSize: 18,
      fontWeight: '600',
      color: theme.text,
      marginTop: -2,
    },
    menuContent: {
      paddingVertical: 4,
    },
    menuItem: {
      paddingHorizontal: 12,
      paddingVertical: 10,
    },
    menuItemHovered: {
      backgroundColor: theme.surfaceAlt,
    },
    menuItemText: {
      fontSize: 12,
      color: theme.text,
    },
  });
}
