import React from 'react';
import ReactTestRenderer from 'react-test-renderer';
import { Text, TextInput, TouchableOpacity } from 'react-native';

const mockLightTheme = {
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
  background: '#F2F2F7',
  backgroundAlt: '#FFFFFF',
  surface: '#FFFFFF',
  surfaceAlt: '#F2F2F7',
  primary: '#007AFF',
  primaryMuted: 'rgba(0, 122, 255, 0.1)',
  border: '#E5E5EA',
  divider: '#E5E5EA',
  text: '#000000',
  textSecondary: '#8E8E93',
  textMuted: '#8E8E93',
  textOnPrimary: '#FFFFFF',
  danger: '#FF3B30',
  success: '#34C759',
  bubbleUserBg: 'rgba(0, 122, 255, 0.12)',
  bubbleSystemBorder: '#E5E5EA',
  bubbleToolBg: 'rgba(142, 142, 147, 0.08)',
  modalBackdrop: 'rgba(0, 0, 0, 0.3)',
  inlineCodeBg: 'rgba(142, 142, 147, 0.16)',
  codeBlockBg: '#FFFFFF',
  navBarBg: '#FFFFFF',
  navBarBorder: '#E5E5EA',
  navIconActive: '#007AFF',
  navIconInactive: '#8E8E93',
};

jest.mock('../src/theme', () => ({
  __esModule: true,
  lightTheme: mockLightTheme,
  ThemeProvider: ({ children }: any) => <>{children}</>,
  useTheme: () => mockLightTheme,
}));

jest.mock('@crystal-lattice/frontend-sdk', () => ({
  __esModule: true,
  extractByPath: (root: any, path: string) => {
    return path.split('.').reduce((current, part) => {
      if (!current || typeof current !== 'object') return undefined;
      return current[part];
    }, root);
  },
  normalizeSelectOptions: (raw: any) => {
    if (!Array.isArray(raw)) return [];
    return raw
      .map((option) => {
        if (typeof option === 'string') return { value: option, label: option };
        if (option && typeof option === 'object') {
          const value =
            typeof option.value === 'string'
              ? option.value
              : option.value !== undefined && option.value !== null
                ? String(option.value)
                : '';
          if (!value) return null;
          return {
            value,
            label: typeof option.label === 'string' ? option.label : value,
          };
        }
        return null;
      })
      .filter(Boolean);
  },
}));

import {
  ApplicationActionDialog,
  ApplicationActionForm,
  type ApplicationActionFormHandle,
} from '../../../packages/frontend-rn-components/src/ApplicationActionDialog';
import { useMobileApplicationActionDialogFieldRenderers } from '../src/components/applicationActionDialogRenderers';

function DialogHarness({
  dialog,
  onSubmit,
}: {
  dialog: any;
  onSubmit: (values: Record<string, any>) => void;
}) {
  const fieldRenderers = useMobileApplicationActionDialogFieldRenderers();
  return (
    <ApplicationActionDialog
      visible
      dialog={dialog}
      fieldRenderers={fieldRenderers}
      onSubmit={onSubmit}
      onCancel={jest.fn()}
    />
  );
}

function findButtonByText(renderer: ReactTestRenderer.ReactTestRenderer, label: string) {
  return renderer.root.findAllByType(TouchableOpacity).find((button) => {
    return button.findAllByType(Text).some((text) => text.props.children === label);
  });
}

const SELECT_DIALOG = {
  kind: 'form',
  title: 'MCP Login',
  inputs: [
    {
      name: 'server_name',
      type: 'select',
      label: 'MCP server',
      options: [{ value: 'figma', label: 'Figma' }],
      required: true,
    },
  ],
};

test('action dialog submits selected chip values as strings', () => {
  const onSubmit = jest.fn();
  let renderer: ReactTestRenderer.ReactTestRenderer;

  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <DialogHarness dialog={SELECT_DIALOG} onSubmit={onSubmit} />,
    );
  });

  const chip = renderer!.root.findByProps({ testID: 'action-dialog-select-server_name-figma' });
  ReactTestRenderer.act(() => {
    chip.props.onPress();
  });

  const okButton = findButtonByText(renderer!, 'OK');
  expect(okButton).toBeTruthy();
  ReactTestRenderer.act(() => {
    okButton!.props.onPress();
  });

  expect(onSubmit).toHaveBeenCalledWith({ server_name: 'figma' });
});

test('action dialog validates required select fields', () => {
  const onSubmit = jest.fn();
  let renderer: ReactTestRenderer.ReactTestRenderer;

  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <DialogHarness dialog={SELECT_DIALOG} onSubmit={onSubmit} />,
    );
  });

  const okButton = findButtonByText(renderer!, 'OK');
  ReactTestRenderer.act(() => {
    okButton!.props.onPress();
  });

  expect(onSubmit).not.toHaveBeenCalled();
  expect(
    renderer!.root.findAllByType(Text).some((text) => {
      return text.props.children === 'Field "MCP server" is required.';
    }),
  ).toBe(true);
});

test('application action form submits embedded form values', () => {
  const ref = React.createRef<ApplicationActionFormHandle>();
  let renderer: ReactTestRenderer.ReactTestRenderer;

  ReactTestRenderer.act(() => {
    renderer = ReactTestRenderer.create(
      <ApplicationActionForm
        ref={ref}
        form={{
          kind: 'form',
          inputs: [
            {
              name: 'callback_url',
              type: 'multiline',
              label: 'Callback URL',
              required: true,
            },
            {
              name: 'note',
              type: 'string',
              label: 'Note',
              submit_empty: true,
            },
          ],
        }}
      />,
    );
  });

  const inputs = renderer!.root.findAllByType(TextInput);
  ReactTestRenderer.act(() => {
    inputs[0].props.onChangeText('http://127.0.0.1:41793/callback?code=abc&state=xyz');
  });

  let submitted: Record<string, any> | null = null;
  ReactTestRenderer.act(() => {
    submitted = ref.current!.submit();
  });

  expect(submitted).toEqual({
    callback_url: 'http://127.0.0.1:41793/callback?code=abc&state=xyz',
    note: '',
  });
});