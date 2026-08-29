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

jest.mock(
  '@react-native-async-storage/async-storage',
  () => require('@react-native-async-storage/async-storage/jest/async-storage-mock'),
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
  const {
    mergeSessionNotificationEvents,
    notificationExpectedRevision,
    selectSessionNotifications,
  } = jest.requireActual('@crystal-lattice/frontend-sdk');
  const theme = {
    typography: {
      fontSize: {
        tiny: 11,
        small: 12,
        secondary: 13,
        normal: 14,
        message: 15,
        large: 16,
        title: 18,
        screenTitle: 24,
        display: 28,
        code: 14,
      },
      lineHeight: {
        tiny: 15,
        small: 17,
        secondary: 18,
        normal: 20,
        message: 21,
        large: 22,
        title: 24,
        screenTitle: 30,
        display: 34,
        code: 19,
      },
    },
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
  const defaultMarkdownDisplayPreferences = {
    baseFontSize: 15,
    headerSize: 'normal',
  };
  const MarkdownDisplayPreferencesContext = React.createContext({
    preferences: defaultMarkdownDisplayPreferences,
    setPreferences: () => {},
  });
  const normalizeMarkdownBaseFontSize = (value) => {
    if (value === 13) return 14;
    if (value === 19) return 17;
    return [14, 15, 16, 17].includes(value) ? value : 15;
  };
  const normalizeMarkdownHeaderSize = (value) =>
    value === 'normal' || value === 'small' ? value : 'normal';
  const normalizeMarkdownDisplayPreferences = (value) => ({
    baseFontSize: normalizeMarkdownBaseFontSize(value?.baseFontSize),
    headerSize: normalizeMarkdownHeaderSize(value?.headerSize),
  });
  const deriveMarkdownTypography = (preferences) => {
    const normalized = normalizeMarkdownDisplayPreferences(preferences);
    const body = normalized.baseFontSize;
    const normal = {
      14: [20, 30, 36, 22, 27, 17, 22],
      15: [21, 32, 38, 24, 29, 18, 23],
      16: [23, 34, 41, 26, 32, 19, 24],
      17: [24, 36, 43, 27, 33, 20, 25],
    }[body];
    const bodyLineHeight = normal[0];
    if (normalized.headerSize === 'small') {
      return {
        body,
        bodyLineHeight,
        h1: body,
        h1LineHeight: bodyLineHeight,
        h2: body,
        h2LineHeight: bodyLineHeight,
        h3: body,
        h3LineHeight: bodyLineHeight,
        h4: body,
        h4LineHeight: bodyLineHeight,
        h5: body,
        h5LineHeight: bodyLineHeight,
        h6: body,
        h6LineHeight: bodyLineHeight,
      };
    }
    return {
      body,
      bodyLineHeight,
      h1: normal[1],
      h1LineHeight: normal[2],
      h2: normal[3],
      h2LineHeight: normal[4],
      h3: normal[5],
      h3LineHeight: normal[6],
      h4: body,
      h4LineHeight: bodyLineHeight,
      h5: body,
      h5LineHeight: bodyLineHeight,
      h6: body,
      h6LineHeight: bodyLineHeight,
    };
  };
  const ThemeContext = React.createContext(theme);
  const applyDisplayTypographyPreset = (baseTheme) => baseTheme;

  const ApplicationActionForm = React.forwardRef(({ form }, ref) => {
    const inputs = form && form.kind === 'form' && Array.isArray(form.inputs) ? form.inputs : [];
    const initialValues = {};
    inputs.forEach((field) => {
      if (!field?.name) return;
      initialValues[field.name] =
        field.default === undefined || field.default === null ? '' : String(field.default);
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
      inputs.map((field) => {
        if (!field?.name) return null;
        return React.createElement(
          View,
          { key: field.name },
          React.createElement(Text, null, field.label || field.name),
          React.createElement(TextInput, {
            value: values[field.name] ?? '',
            placeholder: field.placeholder || '',
            onChangeText: (next) => setValues((prev) => ({ ...prev, [field.name]: next })),
          }),
        );
      }),
      error ? React.createElement(Text, null, error) : null,
    );
  });

  return {
    ThemeProvider: ({ theme: value, children }: { theme: any; children: any }) =>
      React.createElement(ThemeContext.Provider, { value }, children),
    useTheme: () => React.useContext(ThemeContext),
    DEFAULT_MARKDOWN_DISPLAY_PREFERENCES: defaultMarkdownDisplayPreferences,
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
            setPreferences: (update) => {
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
    DropdownMenuSurface: ({ visible, children }: { visible: boolean; children: any }) =>
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
      const renderFilter = (filter) => {
        const value = values[filter.id];
        const controls = [];
        if (filter.type === 'boolean') {
          controls.push(renderOption(filter, 'any', 'Any', null));
          for (const nextValue of [true, false]) {
            const option = filter.options.find(
              (candidate) => candidate.value === nextValue,
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
              Array.isArray(value) &&
              value.some((item) => item === option.value);
            const nextValue = selected
              ? value.filter((item) => item !== option.value)
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
          .filter((filter) => filter.id !== schema?.mainSearch?.id)
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

    ActionsMenuBar: ({ baseActions = [], extraActions = [], menuButtonTestID }) =>
      React.createElement(
        View,
        { testID: menuButtonTestID },
        [...baseActions, ...extraActions].map((action) =>
          React.createElement(
            Text,
            { key: action.key, testID: `action-menu-item-${String(action.key).replace(/\u0000/g, '-')}` },
            action.label,
          ),
        ),
      ),
    NotificationBanner: ({ display, onDismiss, onFollowupAction, disabledActionIds = [] }) =>
      React.createElement(
        View,
        { accessibilityRole: 'alert' },
        display?.title ? React.createElement(Text, null, display.title) : null,
        React.createElement(Text, null, display?.body || ''),
        (display?.actions || []).map((action) =>
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
        items.map((item) =>
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
        (notification) =>
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
            notifications.map((notification) => {
              const dismiss = async () => {
                try {
                  await onDismissNotification?.(notification);
                  const revision =
                    `${notification.id}:${notificationExpectedRevision(notification)}`;
                  setDismissedRevisions((current) =>
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
                    onFollowupAction: (action) =>
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
    SessionListActionsBar: ({ session, pluginActions, pinned, onExecuteAction }) =>
      React.createElement(
        View,
        null,
        (pluginActions || [])
          .filter(
            (action) =>
              (pinned || []).includes(action.id) &&
              action.rich_ui?.placements?.includes('actions_bar'),
          )
          .map((action) =>
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
    }) => {
      const richUi = element.rich_ui || {};
      const valuePath =
        typeof richUi.value_path === 'string' ? richUi.value_path.split('.') : [];
      const value = valuePath.reduce((current, key) => current?.[key], session);
      return React.createElement(Pressable, {
        testID,
        accessibilityState: {
          selected: value === richUi.active_value,
        },
        onPress: () => onExecuteAction(element),
      });
    },
    ApplicationActionDialog: ({ visible }: { visible: boolean }) => (visible ? React.createElement(View, null) : null),
    ApplicationActionDialogLayout: () => React.createElement(React.Fragment, null),
    ApplicationActionForm,
    getLastActionsPopoverAnchorTag: () => null,
  };
});
