import React, { useMemo, useRef, useState } from 'react';
import {
  ActionSheetIOS,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  findNodeHandle,
} from 'react-native';

import { DropdownMenuSurface, useTheme } from '@crystal-lattice/frontend-rn-components';

import type { TabStripStyle } from './tabStripStyle';

export interface DesktopSessionTab {
  tabId: string;
  connectionId: string;
  sessionId: string;
  title: string;
  subtitle?: string | null;
}

export interface SessionTabsProps {
  tabs: DesktopSessionTab[];
  activeTabId: string | null;
  styleVariant: TabStripStyle;
  connectionNameById: Record<string, string>;
  onSelectTab: (tabId: string) => void;
  onCloseTab: (tabId: string) => void;
}

export function SessionTabs({
  tabs,
  activeTabId,
  styleVariant,
  connectionNameById,
  onSelectTab,
  onCloseTab,
}: SessionTabsProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme, styleVariant), [theme, styleVariant]);

  const [hoveredTabId, setHoveredTabId] = useState<string | null>(null);

  const menuAnchorRef = useRef<any>(null);
  const [menuVisible, setMenuVisible] = useState(false);

  const openNativeMenu = () => {
    const options = ['Tab actions (placeholder)', 'Cancel'];
    const cancelButtonIndex = options.length - 1;

    let anchor: number | null = null;
    if (menuAnchorRef.current) {
      try {
        anchor = findNodeHandle(menuAnchorRef.current) as any;
      } catch {
        anchor = null;
      }
    }

    ActionSheetIOS.showActionSheetWithOptions(
      {
        options,
        cancelButtonIndex,
        anchor: anchor ?? undefined,
      },
      (_buttonIndex) => {
        // Placeholder.
      },
    );
  };

  return (
    <View style={styles.root}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.scrollView}
        contentContainerStyle={styles.tabsContainer}
      >
        {tabs.map((tab) => {
          const active = tab.tabId === activeTabId;
          const hovered = tab.tabId === hoveredTabId;
          const connectionName = connectionNameById[tab.connectionId] ?? tab.connectionId;
          const subtitleText =
            typeof tab.subtitle === 'string' && tab.subtitle.trim().length > 0
              ? tab.subtitle
              : null;
          const showClose =
            styleVariant === 'codeTabs' ? true : active || hovered;

          return (
            <Pressable
              key={tab.tabId}
              style={(state) => {
                const pressedOrHovered =
                  ((state as any).hovered as boolean | undefined) || state.pressed;
                return [
                  styles.tab,
                  active ? styles.tabActive : styles.tabInactive,
                  pressedOrHovered && styles.tabHovered,
                ];
              }}
              onPress={() => onSelectTab(tab.tabId)}
              onHoverIn={() => setHoveredTabId(tab.tabId)}
              onHoverOut={() => setHoveredTabId((prev) => (prev === tab.tabId ? null : prev))}
            >
              <View style={styles.tabTextContainer}>
                <Text style={[styles.tabTitle, active && styles.tabTitleActive]} numberOfLines={1}>
                  {tab.title}
                </Text>
                <Text style={styles.tabMeta} numberOfLines={1}>
                  {subtitleText ?? connectionName}
                </Text>
              </View>

              {showClose ? (
                <Pressable
                  style={(state) => {
                    const closeHovered = (state as any).hovered as boolean | undefined;
                    return [
                      styles.closeButton,
                      closeHovered && styles.closeButtonHovered,
                    ];
                  }}
                  onPress={(event) => {
                    (event as any)?.stopPropagation?.();
                    onCloseTab(tab.tabId);
                  }}
                >
                  <Text
                    style={[
                      styles.closeButtonText,
                      styleVariant === 'codeTabs' && !hovered && !active
                        ? styles.closeButtonTextDim
                        : null,
                    ]}
                  >
                    ×
                  </Text>
                </Pressable>
              ) : null}
            </Pressable>
          );
        })}
      </ScrollView>

      <View ref={menuAnchorRef} collapsable={false}>
        <Pressable
          style={(state) => {
            const hovered = (state as any).hovered as boolean | undefined;
            return [
              styles.menuButton,
              (hovered || state.pressed) && styles.menuButtonHovered,
            ];
          }}
          onPress={() => {
            if (Platform.OS === 'macos') {
              openNativeMenu();
              return;
            }
            setMenuVisible(true);
          }}
        >
          <Text style={styles.menuButtonText}>⋯</Text>
        </Pressable>
      </View>

      {Platform.OS !== 'macos' ? (
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
                return [
                  styles.menuItem,
                  (hovered || state.pressed) && styles.menuItemHovered,
                ];
              }}
              onPress={() => setMenuVisible(false)}
            >
              <Text style={styles.menuItemText}>Tab actions (placeholder)</Text>
            </Pressable>
          </View>
        </DropdownMenuSurface>
      ) : null}
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>, styleVariant: TabStripStyle) {
  const separatorWidth = 1;

  const toolbarTabs = styleVariant === 'toolbarTabs';
  const codeTabs = styleVariant === 'codeTabs';
  const underlineTabs = styleVariant === 'underlineTabs';
  const roundedPills = styleVariant === 'roundedPills';

  const codeLike = codeTabs || underlineTabs;

  const stripBackground = codeTabs ? theme.surfaceAlt : theme.backgroundAlt;
  const tabRadius = toolbarTabs ? 9 : roundedPills ? 12 : 0;
  const tabBackground =
    codeTabs
      ? theme.surfaceAlt
      : toolbarTabs
        ? stripBackground
        : underlineTabs
          ? stripBackground
          : theme.surface;
  const tabHoveredBackground =
    underlineTabs
      ? theme.surfaceAlt
      : toolbarTabs
        ? theme.surfaceAlt
        : codeTabs
          ? theme.surface
          : theme.surfaceAlt;

  return StyleSheet.create({
    root: {
      flexDirection: 'row',
      alignItems: 'stretch',
      gap: codeLike ? 0 : 8,
      paddingHorizontal: codeLike ? 0 : 10,
      paddingVertical: toolbarTabs ? 10 : codeLike ? 0 : 8,
      borderBottomWidth: separatorWidth,
      borderBottomColor: theme.border,
      backgroundColor: stripBackground,
      overflow: toolbarTabs ? 'visible' : 'hidden',
    },
    scrollView: {
      overflow: toolbarTabs ? 'visible' : 'hidden',
    },
    tabsContainer: {
      alignItems: 'stretch',
      gap: codeLike ? 0 : 8,
      paddingRight: codeLike ? 0 : 8,
      paddingVertical: toolbarTabs ? 6 : 0,
    },
    tab: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 10,
      position: 'relative',
      borderWidth: codeLike || underlineTabs ? 0 : separatorWidth,
      borderColor: toolbarTabs ? 'transparent' : theme.border,
      borderRightWidth: codeLike ? separatorWidth : 0,
      borderRightColor: codeLike ? theme.border : undefined,
      borderRadius: tabRadius,
      paddingLeft: codeLike ? 12 : 10,
      paddingRight: codeLike ? 34 : 32,
      paddingVertical: underlineTabs ? 8 : codeTabs ? 7 : 8,
      backgroundColor: tabBackground,
      minWidth: codeLike ? 140 : 160,
      maxWidth: codeLike ? 260 : 240,
    },
    tabInactive: {
      zIndex: 1,
      borderBottomWidth: underlineTabs ? 2 : undefined,
      borderBottomColor: underlineTabs ? 'transparent' : undefined,
    },
    tabActive: {
      zIndex: 10,
      backgroundColor: theme.surface,
      borderColor: toolbarTabs ? theme.border : roundedPills ? theme.primary : theme.border,
      borderBottomWidth: underlineTabs ? 2 : undefined,
      borderBottomColor: underlineTabs ? theme.primary : undefined,
      borderTopWidth: codeTabs ? 2 : undefined,
      borderTopColor: codeTabs ? theme.primary : undefined,
      shadowColor: toolbarTabs ? '#000' : undefined,
      shadowOpacity: toolbarTabs ? 0.18 : 0,
      shadowRadius: toolbarTabs ? 10 : 0,
      shadowOffset: toolbarTabs ? { width: 0, height: 4 } : { width: 0, height: 0 },
    },
    tabHovered: {
      backgroundColor: tabHoveredBackground,
    },
    tabTextContainer: {
      flex: 1,
      gap: 1,
    },
    tabTitle: {
      fontSize: 12,
      fontWeight: toolbarTabs ? '700' : '600',
      color: theme.text,
    },
    tabTitleActive: {
      color: theme.text,
    },
    tabMeta: {
      fontSize: 10,
      color: theme.textSecondary,
    },
    closeButton: {
      position: 'absolute',
      right: codeLike ? 10 : 8,
      top: 0,
      bottom: 0,
      alignItems: 'center',
      justifyContent: 'center',
      width: 22,
      borderRadius: 8,
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
    closeButtonTextDim: {
      color: theme.textSecondary,
      opacity: 0.55,
    },
    menuButton: {
      alignItems: 'center',
      justifyContent: 'center',
      paddingHorizontal: 10,
      borderRadius: codeLike ? 0 : 10,
      borderWidth: codeLike ? 0 : separatorWidth,
      borderLeftWidth: separatorWidth,
      borderLeftColor: theme.border,
      backgroundColor: codeLike ? stripBackground : theme.surface,
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
