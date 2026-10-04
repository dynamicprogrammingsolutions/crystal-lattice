import React, { useEffect, useMemo, useRef } from 'react';
import { StyleSheet, Text, View } from 'react-native';

import {
  type ApplicationActionDialogFieldRenderParams,
  type ApplicationActionDialogFieldRenderers,
  useTheme,
} from '@crystal-lattice/frontend-rn-components';
import {
  MacTextView,
  type MacTextViewHandle,
} from '@crystal-lattice/react-native-mac-text-view';

import { MacSelect } from '../native/MacSelect';

function DesktopMultilineActionField({
  params,
}: {
  params: ApplicationActionDialogFieldRenderParams;
}): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const inputRef = useRef<MacTextViewHandle | null>(null);

  useEffect(() => {
    if (!params.isFirstField) {
      return;
    }

    const timer = setTimeout(() => {
      inputRef.current?.focus();
    }, 0);

    return () => {
      clearTimeout(timer);
    };
  }, [params.isFirstField]);

  return (
    <View style={styles.inputGroup}>
      <Text style={styles.inputLabel}>{params.label}</Text>
      {params.description ? (
        <Text style={styles.inputDescription}>{params.description}</Text>
      ) : null}
      <MacTextView
        ref={inputRef}
        testID={`action-form-input-${params.name}`}
        style={styles.multilineInput}
        initialText={params.value}
        placeholder={params.placeholder}
        placeholderTextColor={theme.textSecondary}
        textColor={theme.text}
        submitOnEnter={false}
        onChangeText={params.onChange}
      />
    </View>
  );
}

export function useDesktopApplicationActionFieldRenderers(): ApplicationActionDialogFieldRenderers {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  return useMemo(
    () => ({
      select: (params: ApplicationActionDialogFieldRenderParams) => (
        <View style={styles.inputGroup}>
          <Text style={styles.inputLabel}>{params.label}</Text>
          {params.description ? (
            <Text style={styles.inputDescription}>{params.description}</Text>
          ) : null}
          <MacSelect
            style={styles.select}
            options={params.options}
            selectedValue={params.value}
            placeholder={params.placeholder || 'Select…'}
            onValueChange={params.onChange}
          />
        </View>
      ),
      multiline: (params: ApplicationActionDialogFieldRenderParams) => (
        <DesktopMultilineActionField params={params} />
      ),
    }),
    [styles],
  );
}

const createStyles = (theme: ReturnType<typeof useTheme>) =>
  StyleSheet.create({
    inputGroup: {
      marginBottom: 14,
    },
    inputLabel: {
      color: theme.text,
      fontSize: 12,
      fontWeight: '600',
      marginBottom: 5,
    },
    inputDescription: {
      color: theme.textSecondary,
      fontSize: 11,
      marginBottom: 5,
    },
    select: {
      minHeight: 28,
    },
    multilineInput: {
      height: 112,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      backgroundColor: theme.backgroundAlt,
    },
  });