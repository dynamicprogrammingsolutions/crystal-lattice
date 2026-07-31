import React, { useMemo, useState } from 'react';
import { StyleSheet, Text, TouchableOpacity, View } from 'react-native';

import {
  applicationActionKey,
  type ApplicationActionUiElement,
} from '@crystal-lattice/frontend-sdk';

import {
  ApplicationActionDialog,
  type ApplicationActionDialogFieldRenderers,
} from '../ApplicationActionDialog';
import { useTheme } from '../theme';
import { ActionsMenuBar } from './ActionsMenuBar';
import type { MenuIconRenderer } from './ActionsMenuContent';
import type { ActionDefinition } from './types';

interface ApplicationActionMenuDefinition extends ActionDefinition {
  element: ApplicationActionUiElement;
}

export interface ApplicationActionsMenuProps {
  actions: readonly ApplicationActionUiElement[];
  disabled?: boolean;
  loading?: boolean;
  isActive?: boolean;
  fieldRenderers?: ApplicationActionDialogFieldRenderers;
  renderIcon?: MenuIconRenderer;
  onExecuteAction: (
    element: ApplicationActionUiElement,
    dialogValues?: Record<string, any>,
  ) => void | Promise<void>;
}

export function ApplicationActionsMenu(
  props: ApplicationActionsMenuProps,
): React.JSX.Element | null {
  const theme = useTheme();
  const [activeElement, setActiveElement] =
    useState<ApplicationActionUiElement | null>(null);
  const definitions = useMemo<ApplicationActionMenuDefinition[]>(
    () =>
      props.actions.map((element) => ({
        key: applicationActionKey(element.plugin, element.id),
        label: element.label,
        iconName: typeof element.icon === 'string' ? element.icon : 'zap',
        element,
      })),
    [props.actions],
  );
  const byKey = useMemo(
    () =>
      Object.fromEntries(
        definitions.map((definition) => [definition.key, definition.element]),
      ) as Record<string, ApplicationActionUiElement>,
    [definitions],
  );
  if (definitions.length === 0) return null;

  return (
    <>
      <ActionsMenuBar<ApplicationActionMenuDefinition>
        title="Application actions"
        baseActions={definitions}
        availableActions={definitions.map((definition) => definition.key)}
        pinned={[]}
        onChangePinned={() => {}}
        onAction={(key) => {
          const element = byKey[String(key)];
          if (!element) return;
          const kind = element.dialog?.kind ?? 'none';
          if (kind === 'none') {
            void props.onExecuteAction(element);
          } else {
            setActiveElement(element);
          }
        }}
        isActionDisabled={() => props.disabled === true || props.loading === true}
        isActive={props.isActive}
        menuButtonTestID="application-actions-menu"
        renderIcon={props.renderIcon}
        getIconName={(definition) => definition.iconName ?? 'zap'}
        renderItem={({ action, disabled, onPressAction }) => (
          <TouchableOpacity
            style={styles.item}
            accessibilityRole="button"
            accessibilityLabel={action.label}
            accessibilityState={{ disabled }}
            testID={`application-action-${action.element.plugin}-${action.element.id}`}
            disabled={disabled}
            onPress={onPressAction}
          >
            {props.renderIcon ? (
              <View style={styles.icon}>
                {props.renderIcon({
                  name: action.iconName ?? 'zap',
                  size: 18,
                  color: disabled ? theme.textMuted : theme.primary,
                })}
              </View>
            ) : null}
            <Text style={[styles.label, { color: disabled ? theme.textMuted : theme.text }]}>
              {action.label}
            </Text>
          </TouchableOpacity>
        )}
      />
      <ApplicationActionDialog
        visible={activeElement !== null}
        dialog={activeElement?.dialog ?? null}
        titleFallback={activeElement?.label}
        fieldRenderers={props.fieldRenderers}
        onSubmit={(values) => {
          const element = activeElement;
          setActiveElement(null);
          if (element) void props.onExecuteAction(element, values);
        }}
        onCancel={() => setActiveElement(null)}
      />
    </>
  );
}

const styles = StyleSheet.create({
  item: {
    minHeight: 44,
    paddingHorizontal: 12,
    flexDirection: 'row',
    alignItems: 'center',
  },
  icon: {
    width: 34,
    alignItems: 'center',
  },
  label: {
    marginLeft: 8,
    flex: 1,
  },
});