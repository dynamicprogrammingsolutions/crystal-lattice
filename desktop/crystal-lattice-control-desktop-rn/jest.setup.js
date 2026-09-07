global.__fbBatchedBridgeConfig = global.__fbBatchedBridgeConfig || {
  remoteModuleConfig: [],
};

jest.mock('@crystal-lattice/react-native-mac-text-view', () => {
  const React = require('react');
  const { TextInput } = require('react-native');

  const MacTextView = React.forwardRef((props, ref) => {
    React.useImperativeHandle(ref, () => ({
      setText: () => {},
      focus: () => {},
    }));
    return React.createElement(TextInput, {
      ...props,
      defaultValue: props.initialText,
    });
  });

  return {
    MacTextView,
  };
});

jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock'),
);

jest.mock('@crystal-lattice/frontend-sdk', () => ({
  ...jest.requireActual('@crystal-lattice/frontend-sdk'),
  CONNECTIONS_STORAGE_KEY: 'clc_connections_v1',
  loadConnections: async () => [],
  saveConnections: async () => {},
}));

jest.mock('@crystal-lattice/frontend-rn-components', () => {
  const React = require('react');
  const { Pressable, Text, TextInput, View } = require('react-native');
  let lastActionsPopoverAnchorTag = null;
  const {
    mergeSessionNotificationEvents,
    notificationExpectedRevision,
    selectSessionNotifications,
  } = jest.requireActual('@crystal-lattice/frontend-sdk');
  const markdownDisplayPreferences = jest.requireActual(
    '../../packages/frontend-rn-components/src/markdownDisplayPreferences',
  );
  const {
    DEFAULT_MARKDOWN_DISPLAY_PREFERENCES: defaultMarkdownDisplayPreferences,
    DISPLAY_TYPOGRAPHY_PRESETS,
    MARKDOWN_BASE_FONT_SIZES,
    MARKDOWN_BASE_FONT_SIZE_OPTIONS,
    MARKDOWN_HEADER_SIZE_OPTIONS,
    applyDisplayTypographyPreset,
    deriveMarkdownTypography,
    normalizeMarkdownBaseFontSize,
    normalizeMarkdownDisplayPreferences,
    normalizeMarkdownHeaderSize,
  } = markdownDisplayPreferences;
  const homeWorkspace = jest.requireActual(
    '../../packages/frontend-rn-components/src/homeWorkspace',
  );
  const reorderGeometry = jest.requireActual(
    '../../packages/frontend-rn-components/src/reorderGeometry',
  );
  const sessionRequestStatus = jest.requireActual(
    '../../packages/frontend-rn-components/src/sessionRequestStatus',
  );
  const theme = {
    typography:
      DISPLAY_TYPOGRAPHY_PRESETS[
        defaultMarkdownDisplayPreferences.baseFontSize
      ],
    background: '#fff',
    backgroundAlt: '#fff',
    surface: '#fff',
    surfaceAlt: '#eee',
    primary: '#007AFF',
    primaryMuted: 'rgba(0, 122, 255, 0.1)',
    border: '#ddd',
    divider: '#ddd',
    text: '#000',
    textSecondary: '#666',
    textMuted: '#666',
    textOnPrimary: '#fff',
    danger: '#f00',
    dangerMuted: 'rgba(255, 0, 0, 0.12)',
    success: '#0a0',
    successMuted: 'rgba(0, 170, 0, 0.12)',
    highlight: '#FFCC00',
    warning: '#FF9500',
    warningMuted: 'rgba(255, 149, 0, 0.12)',
    notification: '#007AFF',
    notificationMuted: 'rgba(0, 122, 255, 0.12)',
    message: '#0A84FF',
    bubbleUserBg: '#fff',
    bubbleSystemBorder: '#ddd',
    bubbleToolBg: '#fff',
    modalBackdrop: 'rgba(0,0,0,0.2)',
    inlineCodeBg: '#eee',
    codeBlockBg: '#000',
    navBarBg: '#fff',
    navBarBorder: '#ddd',
    navIconActive: '#007AFF',
    navIconInactive: '#666',
  };
  const MarkdownDisplayPreferencesContext = React.createContext({
    preferences: defaultMarkdownDisplayPreferences,
    setPreferences: () => {},
  });
  const ThemeContext = React.createContext(theme);

  const ApplicationActionForm = React.forwardRef(({ form }, ref) => {
    const inputs =
      form && form.kind === 'form' && Array.isArray(form.inputs)
        ? form.inputs
        : [];
    const initialValues = {};
    inputs.forEach(field => {
      if (!field?.name) return;
      initialValues[field.name] =
        field.default === undefined || field.default === null
          ? ''
          : String(field.default);
    });
    const [values, setValues] = React.useState(initialValues);
    const [error, setError] = React.useState(null);

    React.useImperativeHandle(ref, () => ({
      submit: () => {
        const result = {};
        for (const field of inputs) {
          if (!field?.name) continue;
          const raw = values[field.name] ?? '';
          const trimmed = raw.trim();
          if (!trimmed && field.required) {
            setError(`Field "${field.label || field.name}" is required.`);
            return null;
          }
          if (trimmed) {
            result[field.name] = trimmed;
          } else if (field.submit_empty === true) {
            result[field.name] = '';
          }
        }
        setError(null);
        return result;
      },
    }));

    return React.createElement(
      View,
      null,
      inputs.map(field => {
        if (!field?.name) return null;
        return React.createElement(
          View,
          { key: field.name },
          React.createElement(Text, null, field.label || field.name),
          React.createElement(TextInput, {
            value: values[field.name] ?? '',
            placeholder: field.placeholder || '',
            onChangeText: next =>
              setValues(prev => ({ ...prev, [field.name]: next })),
          }),
        );
      }),
      error ? React.createElement(Text, null, error) : null,
    );
  });

  const RichConfigDropdownControl = ({
    control,
    value,
    disabled,
    onPress,
    testID,
  }) =>
    React.createElement(
      Pressable,
      { testID, disabled, onPress },
      React.createElement(
        Text,
        null,
        `${control.richUi.label}: ${String(value ?? '')}`,
      ),
    );

  const RichConfigDropdownPanel = ({
    richUi,
    hasOverride,
    onSelect,
    onReset,
    testIDPrefix = 'rich-config-dropdown',
  }) => {
    const [query, setQuery] = React.useState('');
    const normalized = query.trim().toLowerCase();
    const declared = richUi.options.filter(
      option =>
        !normalized ||
        option.value.toLowerCase().includes(normalized) ||
        option.label.toLowerCase().includes(normalized),
    );
    const exact = richUi.options.some(option => option.value === query.trim());
    const customEnabled = richUi.custom_value?.enabled === true;
    const customPattern =
      customEnabled && richUi.custom_value.pattern
        ? new RegExp(richUi.custom_value.pattern)
        : null;
    const customValid =
      customEnabled &&
      !!query.trim() &&
      !exact &&
      (!customPattern || customPattern.test(query.trim()));
    return React.createElement(
      View,
      { testID: testIDPrefix },
      React.createElement(TextInput, {
        testID: `${testIDPrefix}-input`,
        value: query,
        onChangeText: setQuery,
      }),
      declared.map(option =>
        React.createElement(
          Pressable,
          {
            key: option.value,
            testID: `${testIDPrefix}-declared-${option.value}`,
            onPress: () => onSelect(option.value),
          },
          React.createElement(Text, null, option.label),
        ),
      ),
      customValid
        ? React.createElement(
            Pressable,
            {
              testID: `${testIDPrefix}-custom-${query.trim()}`,
              onPress: () => onSelect(query.trim()),
            },
            React.createElement(
              Text,
              null,
              richUi.custom_value.option_label.replace('{value}', query.trim()),
            ),
          )
        : null,
      hasOverride
        ? React.createElement(Pressable, {
            testID: `${testIDPrefix}-reset`,
            onPress: onReset,
          })
        : null,
    );
  };

  const RichConfigToggleControl = ({
    control,
    value,
    disabled,
    onPress,
    testID,
  }) =>
    React.createElement(
      Pressable,
      { testID, disabled, onPress },
      React.createElement(
        Text,
        null,
        `${control.richUi.label}: ${value === true ? 'On' : 'Off'}`,
      ),
    );

  const SessionListRichActionControl = ({
    element,
    onExecuteAction,
    onPresentRichList,
    testID,
  }) =>
    React.createElement(
      Pressable,
      {
        testID,
        onPress: () => {
          if (element.rich_ui?.kind === 'toggle') {
            onExecuteAction(element);
          } else {
            onPresentRichList(element);
          }
        },
      },
      React.createElement(Text, null, element.label),
    );

  const SessionListRichActionList = ({
    element,
    onExecuteAction,
    onRequestClose,
    testIDPrefix,
  }) =>
    React.createElement(
      View,
      { testID: testIDPrefix },
      (element.rich_ui?.options || []).map(option =>
        React.createElement(
          Pressable,
          {
            key: String(option.value),
            testID: `${testIDPrefix}-option-${String(option.value)}`,
            onPress: () => {
              onRequestClose();
              onExecuteAction({
                [element.rich_ui.input_name]: option.value,
              });
            },
          },
          React.createElement(Text, null, option.label),
        ),
      ),
    );

  return {
    ...homeWorkspace,
    ...reorderGeometry,
    ...sessionRequestStatus,
    ThemeProvider: ({
      theme: value,
      children,
    }: {
      theme: any,
      children: any,
    }) => React.createElement(ThemeContext.Provider, { value }, children),
    useTheme: () => React.useContext(ThemeContext),
    SessionRequestStatusIndicator: ({ status, variant = 'badge', testID }) => {
      if (!status) return null;
      const presentation =
        sessionRequestStatus.getSessionRequestStatusPresentation(status);
      return React.createElement(
        View,
        {
          testID,
          accessibilityLabel: `Request status: ${presentation.label}`,
          accessibilityValue: { text: presentation.label },
        },
        variant === 'dot'
          ? null
          : React.createElement(Text, null, presentation.label),
      );
    },
    DEFAULT_MARKDOWN_DISPLAY_PREFERENCES: defaultMarkdownDisplayPreferences,
    DISPLAY_TYPOGRAPHY_PRESETS,
    MARKDOWN_BASE_FONT_SIZES,
    MARKDOWN_BASE_FONT_SIZE_OPTIONS,
    MARKDOWN_HEADER_SIZE_OPTIONS,
    normalizeMarkdownBaseFontSize,
    normalizeMarkdownHeaderSize,
    normalizeMarkdownDisplayPreferences,
    deriveMarkdownTypography,
    applyDisplayTypographyPreset,
    MarkdownDisplayPreferencesProvider: ({ value, onChange, children }) => {
      const preferences = normalizeMarkdownDisplayPreferences(value);
      return React.createElement(
        MarkdownDisplayPreferencesContext.Provider,
        {
          value: {
            preferences,
            setPreferences: update => {
              const next =
                typeof update === 'function' ? update(preferences) : update;
              onChange?.(normalizeMarkdownDisplayPreferences(next));
            },
          },
        },
        children,
      );
    },
    useMarkdownDisplayPreferences: () =>
      React.useContext(MarkdownDisplayPreferencesContext),
    DropdownMenuSurface: ({
      visible,
      children,
    }: {
      visible: boolean,
      children: any,
    }) =>
      visible ? React.createElement(React.Fragment, null, children) : null,
    SessionListFiltersPanel: ({
      schema,
      values,
      onChange,
      onReset,
      onShowAll,
      onRequestClose,
    }) => {
      const renderOption = (filter, key, label, nextValue, option) =>
        React.createElement(
          Pressable,
          {
            key,
            testID: `session-filter-${filter.id}-option-${key}`,
            onPress: () => onChange(filter.id, nextValue),
          },
          option?.icon
            ? React.createElement(View, {
                testID: `session-filter-${filter.id}-option-${key}-icon`,
              })
            : null,
          React.createElement(Text, null, label),
        );
      const renderFilter = filter => {
        const value = values[filter.id];
        const controls = [];
        if (filter.type === 'boolean') {
          controls.push(renderOption(filter, 'any', 'Any', null));
          for (const nextValue of [true, false]) {
            const option = filter.options.find(
              candidate => candidate.value === nextValue,
            );
            controls.push(
              renderOption(
                filter,
                String(nextValue),
                option?.label || String(nextValue),
                nextValue,
                option,
              ),
            );
          }
        } else if (filter.type === 'select' && filter.multiple) {
          controls.push(renderOption(filter, 'any', 'Any', []));
          filter.options.forEach((option, index) => {
            const selected =
              Array.isArray(value) && value.some(item => item === option.value);
            const nextValue = selected
              ? value.filter(item => item !== option.value)
              : [...(Array.isArray(value) ? value : []), option.value];
            controls.push(
              renderOption(
                filter,
                String(index),
                option.label,
                nextValue,
                option,
              ),
            );
          });
        }
        return React.createElement(
          View,
          {
            key: filter.id,
            testID: `session-filter-${filter.id}`,
          },
          React.createElement(Text, null, filter.label),
          ...controls,
        );
      };
      return React.createElement(
        View,
        { testID: 'session-filters-panel' },
        (schema?.filters || [])
          .filter(filter => filter.id !== schema?.mainSearch?.id)
          .map(renderFilter),
        React.createElement(Pressable, {
          testID: 'session-filters-show-all',
          onPress: onShowAll,
        }),
        React.createElement(Pressable, {
          testID: 'session-filters-reset',
          onPress: onReset,
        }),
        onRequestClose
          ? React.createElement(Pressable, {
              testID: 'session-filters-close',
              onPress: onRequestClose,
            })
          : null,
      );
    },

    RichConfigDropdownControl,
    RichConfigDropdownPanel,
    RichConfigToggleControl,
    SessionListRichActionControl,
    SessionListRichActionList,
    ActionsMenuBar: ({
      baseActions = [],
      extraActions = [],
      menuButtonTestID,
      pinned = [],
      pinnedKeysForBar,
      renderPinnedAction,
      onAction,
    }) => {
      const actions = [...baseActions, ...extraActions];
      const barKeys = pinnedKeysForBar ?? pinned;
      return React.createElement(
        View,
        { testID: menuButtonTestID },
        actions
          .filter(action => barKeys.includes(action.key))
          .map(action => {
            const custom = renderPinnedAction?.({
              action,
              disabled: false,
              iconName: action.iconName ?? null,
              iconColor: '#007AFF',
              onPress: () => onAction?.(action.key),
            });
            if (custom !== undefined) {
              return React.createElement(
                React.Fragment,
                { key: action.key },
                custom,
              );
            }
            return React.createElement(
              Pressable,
              {
                key: action.key,
                testID: `action-menu-pinned-${String(action.key).replace(
                  /\u0000/g,
                  '-',
                )}`,
                onPress: () => onAction?.(action.key),
              },
              React.createElement(Text, null, action.label),
            );
          }),
        actions.map(action =>
          React.createElement(
            Pressable,
            {
              key: `menu:${action.key}`,
              testID: `action-menu-item-${String(action.key).replace(
                /\u0000/g,
                '-',
              )}`,
              onPress: () => onAction?.(action.key),
            },
            React.createElement(Text, null, action.label),
          ),
        ),
      );
    },
    NotificationBanner: ({
      display,
      onDismiss,
      onFollowupAction,
      disabledActionIds = [],
    }) =>
      React.createElement(
        View,
        { accessibilityRole: 'alert' },
        display?.title ? React.createElement(Text, null, display.title) : null,
        React.createElement(Text, null, display?.body || ''),
        (display?.actions || []).map(action =>
          React.createElement(
            Pressable,
            {
              key: action.id,
              disabled: disabledActionIds.includes(action.id),
              onPress: () =>
                action.kind === 'dismiss'
                  ? onDismiss?.()
                  : onFollowupAction?.(action),
            },
            React.createElement(Text, null, action.label),
          ),
        ),
        display?.dismissible !== false && onDismiss
          ? React.createElement(
              Pressable,
              { onPress: onDismiss },
              React.createElement(Text, null, 'Dismiss'),
            )
          : null,
      ),
    NotificationBannerHost: ({ items = [], onDismiss, onFollowupAction }) =>
      React.createElement(
        View,
        { testID: 'notification-banner-host' },
        items.map(item =>
          React.createElement(
            View,
            { key: item.envelope.id, accessibilityRole: 'alert' },
            item.connectionLabel
              ? React.createElement(Text, null, item.connectionLabel)
              : null,
            item.envelope.display.title
              ? React.createElement(Text, null, item.envelope.display.title)
              : null,
            React.createElement(Text, null, item.envelope.display.body),
            item.envelope.display.dismissible !== false && onDismiss
              ? React.createElement(
                  Pressable,
                  {
                    accessibilityLabel: 'Dismiss notification',
                    onPress: () => onDismiss(item),
                  },
                  React.createElement(Text, null, 'Dismiss'),
                )
              : null,
          ),
        ),
      ),
    SessionNotificationsHost: ({
      sessionSummary,
      events = [],
      onDismissNotification,
      onFollowupAction,
      renderInline,
      inlinePresentations = ['inline'],
    }) => {
      const [dismissedRevisions, setDismissedRevisions] = React.useState([]);
      const notifications = mergeSessionNotificationEvents(
        selectSessionNotifications(sessionSummary),
        events,
      ).filter(
        notification =>
          notification.status === 'pending' &&
          inlinePresentations.includes(
            notification.display.presentation || 'inline',
          ) &&
          !dismissedRevisions.includes(
            `${notification.id}:${notificationExpectedRevision(notification)}`,
          ),
      );
      return notifications.length > 0
        ? React.createElement(
            View,
            null,
            notifications.map(notification => {
              const dismiss = async () => {
                try {
                  await onDismissNotification?.(notification);
                  const revision = `${
                    notification.id
                  }:${notificationExpectedRevision(notification)}`;
                  setDismissedRevisions(current =>
                    current.includes(revision)
                      ? current
                      : [...current, revision],
                  );
                } catch {
                  // Keep the notification visible when its owner rejects dismissal.
                }
              };
              if (renderInline) {
                return React.createElement(
                  React.Fragment,
                  { key: notification.id },
                  renderInline({
                    notification,
                    onDismiss: () => {
                      void dismiss();
                    },
                    onFollowupAction: action =>
                      onFollowupAction?.(action, notification),
                  }),
                );
              }
              return React.createElement(
                View,
                { key: notification.id },
                React.createElement(Text, null, notification.display.body),
                React.createElement(Pressable, {
                  accessibilityLabel: 'Dismiss notification',
                  onPress: () => {
                    void dismiss();
                  },
                }),
              );
            }),
          )
        : null;
    },
    SessionListActionsBar: ({
      session,
      pluginActions,
      pinned,
      onExecuteAction,
    }) =>
      React.createElement(
        View,
        null,
        (pluginActions || [])
          .filter(
            action =>
              (pinned || []).includes(action.id) &&
              action.rich_ui?.placements?.includes('actions_bar'),
          )
          .map(action =>
            React.createElement(Pressable, {
              key: action.id,
              testID: `session-rich-action-${session.session_id}-${action.id}`,
              onPress: () => onExecuteAction(action),
            }),
          ),
      ),
    SessionListRichActionControl: ({
      element,
      session,
      testID,
      onExecuteAction,
      onPresentRichList,
    }) => {
      const richUi = element.rich_ui || {};
      const valuePath =
        typeof richUi.value_path === 'string'
          ? richUi.value_path.split('.')
          : [];
      const value = valuePath.reduce((current, key) => current?.[key], session);
      return React.createElement(Pressable, {
        testID,
        accessibilityState: {
          selected: value === richUi.active_value,
        },
        onPress: event =>
          richUi.kind === 'list'
            ? onPresentRichList(element, event?.nativeEvent?.target)
            : onExecuteAction(element),
      });
    },
    ApplicationActionDialog: ({ visible }: { visible: boolean }) =>
      visible ? React.createElement(View, null) : null,
    ApplicationActionDialogLayout: () =>
      React.createElement(React.Fragment, null),
    ApplicationActionForm,
    getLastActionsPopoverAnchorTag: () => lastActionsPopoverAnchorTag,
    setLastActionsPopoverAnchorTag: tag => {
      lastActionsPopoverAnchorTag = typeof tag === 'number' ? tag : null;
    },
  };
});
