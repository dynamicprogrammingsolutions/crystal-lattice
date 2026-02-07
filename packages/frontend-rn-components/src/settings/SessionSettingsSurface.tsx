import React, { useMemo } from 'react';
import { StyleSheet, TouchableWithoutFeedback, View } from 'react-native';

import { useTheme, type Theme } from '../theme';
import { SessionSettingsCard, type SessionSettingsCardProps } from './SessionSettingsCard';

export type SessionSettingsSurfaceProps = SessionSettingsCardProps;

export function SessionSettingsSurface(props: SessionSettingsSurfaceProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  return (
    <TouchableWithoutFeedback onPress={props.onRequestClose}>
      <View style={styles.overlay}>
        <TouchableWithoutFeedback onPress={() => {}}>
          <SessionSettingsCard {...props} />
        </TouchableWithoutFeedback>
      </View>
    </TouchableWithoutFeedback>
  );
}

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    overlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      justifyContent: 'center',
      alignItems: 'center',
    },
  });
