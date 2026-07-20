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
    ThemeProvider: ({ children }: { children: any }) => React.createElement(React.Fragment, null, children),
    useTheme: () => theme,
    DropdownMenuSurface: ({ visible, children }: { visible: boolean; children: any }) =>
      visible ? React.createElement(React.Fragment, null, children) : null,
    SessionListFiltersPanel: ({
      schema,
      values,
      onChange,
      onReset,
      onShowAll,
    }) =>
      React.createElement(
        View,
        { testID: 'session-filters-panel' },
        (schema?.filters || [])
          .filter((filter) => filter.id !== schema?.mainSearch?.id)
          .map((filter) =>
            React.createElement(
              Pressable,
              {
                key: filter.id,
                testID: `session-filter-${filter.id}`,
                onPress: () => onChange(filter.id, values[filter.id]),
              },
              React.createElement(Text, null, filter.label),
            ),
          ),
        React.createElement(Pressable, {
          testID: 'session-filters-show-all',
          onPress: onShowAll,
        }),
        React.createElement(Pressable, {
          testID: 'session-filters-reset',
          onPress: onReset,
        }),
      ),

    ActionsMenuBar: () => null,
    ApplicationActionDialog: ({ visible }: { visible: boolean }) => (visible ? React.createElement(View, null) : null),
    ApplicationActionDialogLayout: () => React.createElement(React.Fragment, null),
    ApplicationActionForm,
    getLastActionsPopoverAnchorTag: () => null,
  };
});
