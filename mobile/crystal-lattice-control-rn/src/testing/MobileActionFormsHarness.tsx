import React, { useMemo, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import {
  ApplicationActionDialog,
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  MarkdownDisplayPreferencesProvider,
  applyDisplayTypographyPreset,
} from '@crystal-lattice/frontend-rn-components';
import { useDisplayFollowupDialog } from '@crystal-lattice/frontend-sdk-react';
import type { ActionDialog, ActionDisplayPayload } from '@crystal-lattice/frontend-sdk';

import {
  buildLayoutDisplay,
  MANY_FIELD_DIALOG,
  THREE_FIELD_DIALOG,
} from '../../../../test/fixture/actionFormLayouts';
import ActionResultModal from '../components/ActionResultModal';
import { useMobileApplicationActionDialogFieldRenderers } from '../components/applicationActionDialogRenderers';
import { lightTheme, ThemeProvider } from '../theme';

export function MobileActionFormsHarness(): React.JSX.Element {
  const [largeText, setLargeText] = useState(false);
  const [enrichedMarkdown, setEnrichedMarkdown] = useState(false);
  const theme = useMemo(
    () => applyDisplayTypographyPreset(lightTheme, largeText ? 17 : 14),
    [largeText],
  );
  return (
    <ThemeProvider theme={theme}>
      <MarkdownDisplayPreferencesProvider
        value={{
          ...DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
          baseFontSize: largeText ? 17 : 14,
          markdownRenderer: enrichedMarkdown
            ? 'react-native-enriched-markdown'
            : 'react-native-markdown-display',
        }}
      >
        <SafeAreaProvider>
          <ActionFormsHarnessContent
            onToggleLargeText={() => setLargeText((current) => !current)}
            onToggleRenderer={() => setEnrichedMarkdown((current) => !current)}
          />
        </SafeAreaProvider>
      </MarkdownDisplayPreferencesProvider>
    </ThemeProvider>
  );
}

function ActionFormsHarnessContent({
  onToggleLargeText,
  onToggleRenderer,
}: {
  onToggleLargeText: () => void;
  onToggleRenderer: () => void;
}): React.JSX.Element {
  const [dialog, setDialog] = useState<ActionDialog | null>(null);
  const [display, setDisplay] = useState<ActionDisplayPayload | null>(null);
  const [submitted, setSubmitted] = useState('');
  const [orientation, setOrientation] = useState('');
  const fieldRenderers = useMobileApplicationActionDialogFieldRenderers();
  const followup = useDisplayFollowupDialog<null>(async (_element, { formValues }, values) => {
    setSubmitted(JSON.stringify(values ?? formValues ?? {}));
  });
  const buttons = [
    [
      'confirm',
      'Confirmation',
      () =>
        setDialog({
          kind: 'confirm',
          title: 'Confirm fixture action',
          message: 'A short confirmation.',
        }),
    ],
    ['three', 'Three fields', () => setDialog(THREE_FIELD_DIALOG)],
    ['many', 'Many fields', () => setDialog(MANY_FIELD_DIALOG)],
    ['report', 'Report', () => setDisplay(buildLayoutDisplay())],
    ['small-form', 'Small embedded form', () => setDisplay(buildLayoutDisplay(2))],
    ['oversized-form', 'Oversized embedded form', () => setDisplay(buildLayoutDisplay(20))],
    ['large-text', 'Toggle large text', onToggleLargeText],
    ['renderer', 'Toggle markdown renderer', onToggleRenderer],
  ] as const;

  return (
    <View
      style={styles.root}
      testID="action-forms-harness-ready"
      onLayout={({ nativeEvent: { layout } }) =>
        setOrientation(layout.width > layout.height ? 'landscape' : 'portrait')
      }
    >
      <Text testID="action-forms-orientation">{orientation}</Text>
      <View style={styles.buttons}>
        {buttons.map(([id, label, onPress]) => (
          <TouchableOpacity
            key={id}
            testID={`action-forms-open-${id}`}
            accessibilityRole="button"
            style={styles.button}
            onPress={onPress}
          >
            <Text>{label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <Text testID="action-forms-submitted">{submitted}</Text>
      <ApplicationActionDialog
        visible={!!dialog}
        dialog={dialog}
        fieldRenderers={fieldRenderers}
        onCancel={() => setDialog(null)}
        onSubmit={(values) => {
          setSubmitted(JSON.stringify(values));
          setDialog(null);
        }}
      />
      <ActionResultModal
        visible={!!display}
        display={display}
        testID="action-forms-result"
        fieldRenderers={fieldRenderers}
        onRequestClose={() => setDisplay(null)}
        onOverlayRequestClose={followup.handleCancel}
        onFollowupAction={(action, formValues) => {
          if (display && action.kind === 'run_action') {
            followup.openForAction(action, display, null, formValues);
          }
        }}
        overlayChildren={
          followup.activeElement ? (
            <ApplicationActionDialog
              visible
              presentationMode="overlay"
              dialog={followup.activeElement.dialog}
              fieldRenderers={fieldRenderers}
              onSubmit={followup.handleSubmit}
              onCancel={followup.handleCancel}
            />
          ) : null
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    paddingTop: 60,
    paddingHorizontal: 12,
    backgroundColor: '#FFFFFF',
  },
  buttons: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  button: { padding: 12, backgroundColor: '#E5E5EA', borderRadius: 8 },
});
