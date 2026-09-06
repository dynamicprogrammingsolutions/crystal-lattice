import React, { useCallback, useMemo } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import {
  SESSION_LIST_RICH_ACTION_KINDS,
  buildSessionListRichListDialogValues,
  isSessionListRichActionPlacedAt,
  resolveSessionListActionPresentation,
  resolveSessionListRichActionState,
  type SessionListActionElement,
  type SessionListListRichUi,
  type SessionListRichActionPlacement,
  type SessionSummary,
  type ChatRichUiPlacement,
} from '@crystal-lattice/frontend-sdk';

import { useTheme } from '../theme';
import {
  ALL_SESSION_ACTIONS,
  type SessionActionDefinition,
} from '../sessionActions';
import { ActionsMenuBar } from './ActionsMenuBar';
import type { MenuIconRenderer } from './ActionsMenuContent';
import { resolveSemanticToneColor } from './semanticTone';
import type { ActionDefinition, ActionKey } from './types';

const SUPPORTED_RICH_KINDS = new Set<string>(SESSION_LIST_RICH_ACTION_KINDS);

export interface SessionListPluginActionDefinition extends ActionDefinition {
  element: SessionListActionElement;
}

export interface SessionListActionsBarProps {
  session: SessionSummary;
  pluginActions: readonly SessionListActionElement[];
  baseActions?: readonly SessionActionDefinition[];
  availableActions?: readonly ActionKey[];
  pinned: readonly ActionKey[];
  pinnedKeysForBar?: readonly ActionKey[];
  onChangePinned: (nextPinned: ActionKey[]) => void;
  onBaseAction: (key: ActionKey) => void;
  onExecuteAction: (
    element: SessionListActionElement,
    dialogValues?: Record<string, string | boolean>,
  ) => void;
  onFallbackAction: (element: SessionListActionElement) => void;
  onPresentRichList: (element: SessionListActionElement) => void;
  title?: string;
  variant?: 'modal' | 'dropdown';
  menuButtonTestID?: string;
  isActionDisabled?: (key: ActionKey) => boolean;
  isActive?: boolean;
  pinnedRows?: 1 | 2;
  secondPinnedRowPlacement?: 'above' | 'below';
  renderIcon?: MenuIconRenderer;
  renderPinIcon?: (params: {
    pinned: boolean;
    size: number;
    color: string;
  }) => React.ReactNode;
  renderCloseIcon?: (params: {
    size: number;
    color: string;
    renderIcon?: MenuIconRenderer;
  }) => React.ReactNode;
  modalContentStyle?: any;
}

export interface SessionListRichActionListProps {
  element: SessionListActionElement;
  session: SessionSummary;
  onExecuteAction: (dialogValues: Record<string, string | boolean>) => void;
  onRequestClose: () => void;
  renderIcon?: MenuIconRenderer;
  testIDPrefix?: string;
}

export interface SessionListRichActionControlProps {
  element: SessionListActionElement;
  session: SessionSummary;
  placement: SessionListRichActionPlacement | ChatRichUiPlacement;
  disabled?: boolean;
  onExecuteAction: (
    element: SessionListActionElement,
    dialogValues?: Record<string, string | boolean>,
  ) => void;
  onPresentRichList: (element: SessionListActionElement) => void;
  renderIcon?: MenuIconRenderer;
  testID?: string;
}

/**
 * Compact rich presentation used for both an actions-bar pin and a
 * plugin-declared session-row header slot. Ordinary fallback remains in the
 * action menu; a slot is only rendered for a supported rich presentation.
 */
export function SessionListRichActionControl(
  props: SessionListRichActionControlProps,
): React.JSX.Element | null {
  const theme = useTheme();
  const presentation = resolveSessionListActionPresentation(
    props.element,
    SUPPORTED_RICH_KINDS,
  );
  const state = resolveSessionListRichActionState(props.element, props.session);
  if (presentation.mode !== 'rich' || !state) {
    return null;
  }

  const color = resolveSemanticToneColor(theme, state.tone);
  const testID =
    props.testID ??
    `session-rich-action-${props.session.session_id}-${props.element.id}-${props.placement}`;
  const isHeader =
    props.placement === 'header_leading' ||
    props.placement === 'header_trailing' ||
    props.placement === 'session_header';
  const iconName =
    state.kind === 'list' && state.currentOption?.icon
      ? state.currentOption.icon
      : typeof props.element.icon === 'string'
        ? props.element.icon
        : null;
  const trigger = (event?: unknown) => {
    (event as any)?.stopPropagation?.();
    if (state.kind === 'toggle') {
      props.onExecuteAction(props.element);
      return;
    }
    props.onPresentRichList(props.element);
  };

  if (state.kind === 'toggle') {
    return (
      <TouchableOpacity
        style={[styles.richButton, isHeader && styles.headerRichButton]}
        testID={testID}
        accessibilityRole="button"
        accessibilityLabel={`${props.element.label}: ${state.active ? 'On' : 'Off'}`}
        accessibilityState={{
          disabled: props.disabled,
          selected: state.active,
        }}
        disabled={props.disabled}
        onPress={trigger}
      >
        {iconName && props.renderIcon ? (
          props.renderIcon({ name: iconName, size: isHeader ? 18 : 16, color })
        ) : (
          <Text
            style={[
              styles.pinnedFallback,
              {
                color,
                fontSize: theme.typography.fontSize.normal,
                lineHeight: theme.typography.lineHeight.normal,
              },
            ]}
          >
            ●
          </Text>
        )}
      </TouchableOpacity>
    );
  }

  return (
    <TouchableOpacity
      style={[styles.richListButton, isHeader && styles.headerRichListButton]}
      testID={testID}
      accessibilityRole="button"
      accessibilityLabel={`${props.element.label}: ${state.currentOption?.label ?? 'Unknown'}`}
      accessibilityState={{ disabled: props.disabled }}
      disabled={props.disabled}
      onPress={trigger}
    >
      {iconName && props.renderIcon
        ? props.renderIcon({ name: iconName, size: isHeader ? 16 : 14, color })
        : null}
      <Text
        numberOfLines={1}
        style={[
          styles.pinnedListText,
          {
            color,
            fontSize: theme.typography.fontSize.small,
            lineHeight: theme.typography.lineHeight.small,
          },
        ]}
      >
        {state.currentOption?.label ?? props.element.label}
      </Text>
    </TouchableOpacity>
  );
}

function buildPluginActionDefinitions(
  actions: readonly SessionListActionElement[],
): SessionListPluginActionDefinition[] {
  return actions.map((element) => ({
    key: element.id,
    label: element.label,
    iconName: typeof element.icon === 'string' ? element.icon : 'zap',
    element,
  }));
}

export function SessionListActionsBar(
  props: SessionListActionsBarProps,
): React.JSX.Element {
  const pluginDefinitions = useMemo(
    () => buildPluginActionDefinitions(props.pluginActions),
    [props.pluginActions],
  );
  const pluginByKey = useMemo(
    () =>
      Object.fromEntries(
        pluginDefinitions.map((definition) => [
          definition.key,
          definition.element,
        ]),
      ) as Record<string, SessionListActionElement>,
    [pluginDefinitions],
  );
  const actionBarPinnedKeys = useMemo(() => {
    const requested = props.pinnedKeysForBar ?? props.pinned;
    return requested.filter((key) => {
      const element = pluginByKey[key];
      return (
        !element || isSessionListRichActionPlacedAt(element, 'actions_bar')
      );
    });
  }, [pluginByKey, props.pinned, props.pinnedKeysForBar]);

  const handleAction = useCallback(
    (key: ActionKey) => {
      const element = pluginByKey[key];
      if (!element) {
        props.onBaseAction(key);
        return;
      }

      const presentation = resolveSessionListActionPresentation(
        element,
        SUPPORTED_RICH_KINDS,
      );
      if (presentation.mode !== 'rich') {
        props.onFallbackAction(element);
        return;
      }

      const state = resolveSessionListRichActionState(element, props.session);
      if (!state) {
        props.onFallbackAction(element);
        return;
      }
      if (state.kind === 'toggle') {
        props.onExecuteAction(element);
        return;
      }
      props.onPresentRichList(element);
    },
    [pluginByKey, props],
  );

  const renderPinnedAction = useCallback(
    (params: {
      action: ActionDefinition;
      disabled: boolean;
      iconName: string | null;
      onPress: () => void;
    }) => {
      const element = pluginByKey[params.action.key];
      if (!element) {
        return undefined;
      }
      if (!isSessionListRichActionPlacedAt(element, 'actions_bar')) {
        return undefined;
      }
      const presentation = resolveSessionListActionPresentation(
        element,
        SUPPORTED_RICH_KINDS,
      );
      if (presentation.mode !== 'rich') {
        return undefined;
      }
      return (
        <SessionListRichActionControl
          element={element}
          session={props.session}
          placement="actions_bar"
          disabled={params.disabled}
          onExecuteAction={props.onExecuteAction}
          onPresentRichList={props.onPresentRichList}
          renderIcon={props.renderIcon}
          testID={`session-rich-action-${props.session.session_id}-${element.id}`}
        />
      );
    },
    [pluginByKey, props],
  );

  return (
    <ActionsMenuBar<ActionDefinition>
      title={props.title ?? 'Session actions'}
      variant={props.variant ?? 'modal'}
      baseActions={props.baseActions ?? ALL_SESSION_ACTIONS}
      extraActions={pluginDefinitions}
      availableActions={props.availableActions}
      pinned={props.pinned}
      pinnedKeysForBar={actionBarPinnedKeys}
      onChangePinned={props.onChangePinned}
      onAction={handleAction}
      isActionDisabled={props.isActionDisabled}
      isActive={props.isActive}
      pinnedRows={props.pinnedRows}
      secondPinnedRowPlacement={props.secondPinnedRowPlacement}
      menuButtonTestID={props.menuButtonTestID}
      renderIcon={props.renderIcon}
      renderPinIcon={props.renderPinIcon}
      renderCloseIcon={props.renderCloseIcon}
      renderPinnedAction={renderPinnedAction}
      modalContentStyle={props.modalContentStyle}
    />
  );
}

export function SessionListRichActionList(
  props: SessionListRichActionListProps,
): React.JSX.Element | null {
  const theme = useTheme();
  const richUi = props.element.rich_ui;
  const state = resolveSessionListRichActionState(props.element, props.session);
  if (!richUi || richUi.kind !== 'list' || !state || state.kind !== 'list') {
    return null;
  }

  const listUi = richUi as SessionListListRichUi;
  const prefix = props.testIDPrefix ?? `session-rich-list-${props.element.id}`;
  return (
    <View style={styles.listRoot} testID={prefix}>
      <View style={[styles.listHeader, { borderBottomColor: theme.border }]}>
        <Text
          style={[styles.listTitle, { color: theme.text }]}
          numberOfLines={1}
        >
          {props.element.label}
        </Text>
        <Pressable
          testID={`${prefix}-close`}
          accessibilityRole="button"
          accessibilityLabel={`Close ${props.element.label}`}
          onPress={props.onRequestClose}
        >
          <Text style={[styles.closeText, { color: theme.primary }]}>×</Text>
        </Pressable>
      </View>
      <ScrollView keyboardShouldPersistTaps="handled">
        {listUi.options.map((option) => {
          const selected =
            state.currentOption != null &&
            typeof state.currentOption.value === typeof option.value &&
            state.currentOption.value === option.value;
          const color = resolveSemanticToneColor(theme, option.tone);
          return (
            <Pressable
              key={`${typeof option.value}:${String(option.value)}`}
              testID={`${prefix}-option-${String(option.value)}`}
              accessibilityRole="button"
              accessibilityLabel={`${option.label}${selected ? ' selected' : ''}`}
              accessibilityState={{ selected }}
              style={[
                styles.listOption,
                selected && { backgroundColor: theme.surfaceAlt },
              ]}
              onPress={() => {
                props.onRequestClose();
                const dialogValues = buildSessionListRichListDialogValues(
                  listUi,
                  state.value,
                  option.value,
                );
                if (!dialogValues) {
                  return;
                }
                props.onExecuteAction(dialogValues);
              }}
            >
              {option.icon && props.renderIcon
                ? props.renderIcon({ name: option.icon, size: 16, color })
                : null}
              <Text style={[styles.listOptionText, { color }]}>
                {option.label}
              </Text>
              {selected ? (
                <Text style={[styles.selectedMark, { color: theme.primary }]}>
                  ✓
                </Text>
              ) : null}
            </Pressable>
          );
        })}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  richButton: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    marginLeft: 4,
  },
  headerRichButton: {
    minWidth: 32,
    minHeight: 32,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 0,
  },
  pinnedFallback: {
    fontWeight: '800',
  },
  richListButton: {
    flexDirection: 'row',
    alignItems: 'center',
    maxWidth: 118,
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    marginLeft: 4,
  },
  headerRichListButton: {
    marginLeft: 0,
  },
  pinnedListText: {
    fontWeight: '700',
    flexShrink: 1,
  },
  listRoot: {
    flex: 1,
    minWidth: 260,
  },
  listHeader: {
    minHeight: 44,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  listTitle: {
    flex: 1,
    fontWeight: '800',
    fontSize: 15,
  },
  closeText: {
    fontSize: 22,
    fontWeight: '700',
    paddingHorizontal: 6,
  },
  listOption: {
    minHeight: 46,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  listOptionText: {
    flex: 1,
    fontSize: 15,
    fontWeight: '600',
  },
  selectedMark: {
    fontSize: 16,
    fontWeight: '800',
  },
});
