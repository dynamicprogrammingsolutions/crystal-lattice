import React, { useMemo } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import { useTheme } from '@crystal-lattice/frontend-rn-components';

export type DesktopLowerPanel = 'sessions' | 'history';

export function DesktopActivityRail({
  connectionsVisible,
  lowerPanel,
  onToggleConnections,
  onSelectLowerPanel,
}: {
  connectionsVisible: boolean;
  lowerPanel: DesktopLowerPanel;
  onToggleConnections: () => void;
  onSelectLowerPanel: (panel: DesktopLowerPanel) => void;
}): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const button = (
    key: string,
    icon: string,
    label: string,
    active: boolean,
    onPress: () => void,
  ) => (
    <Pressable
      key={key}
      testID={`desktop-activity-${key}`}
      accessibilityLabel={label}
      accessibilityState={{ selected: active }}
      style={state => [
        styles.button,
        active && styles.buttonActive,
        (((state as any).hovered as boolean | undefined) || state.pressed) &&
          styles.buttonHovered,
      ]}
      onPress={onPress}
    >
      <Icon
        name={icon}
        size={19}
        color={active ? theme.navIconActive : theme.navIconInactive}
      />
    </Pressable>
  );

  return (
    <View style={styles.root} testID="desktop-activity-rail">
      <View>
        {button(
          'connections',
          'server',
          connectionsVisible ? 'Hide Connections' : 'Show Connections',
          connectionsVisible,
          onToggleConnections,
        )}
      </View>
      <View style={styles.bottom}>
        {button(
          'sessions',
          'list',
          'Show Sessions panel',
          lowerPanel === 'sessions',
          () => onSelectLowerPanel('sessions'),
        )}
        {button(
          'history',
          'clock',
          'Show History panel',
          lowerPanel === 'history',
          () => onSelectLowerPanel('history'),
        )}
      </View>
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    root: {
      flex: 1,
      justifyContent: 'space-between',
      alignItems: 'stretch',
      paddingVertical: 8,
    },
    bottom: {
      gap: 4,
    },
    button: {
      height: 40,
      alignItems: 'center',
      justifyContent: 'center',
      borderLeftWidth: 2,
      borderLeftColor: 'transparent',
    },
    buttonActive: {
      borderLeftColor: theme.primary,
      backgroundColor: theme.surface,
    },
    buttonHovered: {
      backgroundColor: theme.surface,
    },
  });
}
