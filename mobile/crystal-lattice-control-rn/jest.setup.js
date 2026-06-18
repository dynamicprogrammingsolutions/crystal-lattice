global.__fbBatchedBridgeConfig = global.__fbBatchedBridgeConfig || {
  remoteModuleConfig: [],
};

jest.mock('@react-native-documents/picker', () => {
  const types = {
    images: 'public.image',
    pdf: 'com.adobe.pdf',
    allFiles: 'public.item',
  };

  const errorCodes = {
    OPERATION_CANCELED: 'OPERATION_CANCELED',
    IN_PROGRESS: 'ASYNC_OP_IN_PROGRESS',
    UNABLE_TO_OPEN_FILE_TYPE: 'UNABLE_TO_OPEN_FILE_TYPE',
    NULL_PRESENTER: 'NULL_PRESENTER',
  };

  const canceled = Object.assign(new Error('Document picker canceled'), {
    code: errorCodes.OPERATION_CANCELED,
  });

  return {
    __esModule: true,
    types,
    errorCodes,
    isErrorWithCode: (err) => typeof err?.code === 'string',
    pick: jest.fn(async () => {
      throw canceled;
    }),
    keepLocalCopy: jest.fn(async () => [
      {
        status: 'error',
        sourceUri: 'content://mock',
        copyError: 'not implemented',
      },
    ]),
  };
});

jest.mock('react-native-image-picker', () => {
  return {
    __esModule: true,
    launchImageLibrary: jest.fn(async () => ({ didCancel: true })),
    launchCamera: jest.fn(async () => ({ didCancel: true })),
  };
});

jest.mock('react-native-share', () => ({
  __esModule: true,
  default: {
    open: jest.fn(async () => {}),
  },
  open: jest.fn(async () => {}),
}));

jest.mock('@react-native-camera-roll/camera-roll', () => ({
  __esModule: true,
  CameraRoll: {
    saveAsset: jest.fn(async () => {}),
  },
  iosRequestAddOnlyGalleryPermission: jest.fn(async () => 'granted'),
}));

jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock'),
);

jest.mock('@react-native-clipboard/clipboard', () => {
  return {
    __esModule: true,
    default: {
      setString: jest.fn(),
      getString: jest.fn(async () => ''),
    },
    setString: jest.fn(),
    getString: jest.fn(async () => ''),
  };
});

jest.mock('react-native-vector-icons/Feather', () => 'Icon');

jest.mock('react-native-gesture-handler', () => ({
  GestureHandlerRootView: ({ children }) => {
    const React = require('react');
    const { View } = require('react-native');
    return React.createElement(View, null, children);
  },
  gestureHandlerRootHOC: (Component) => Component,
}));

jest.mock('react-native-safe-area-context', () => {
  const React = require('react');
  const { View } = require('react-native');
  return {
    __esModule: true,
    SafeAreaProvider: ({ children }) => React.createElement(View, null, children),
    SafeAreaView: ({ children, ...props }) => React.createElement(View, props, children),
    useSafeAreaInsets: () => ({ top: 0, right: 0, bottom: 0, left: 0 }),
  };
});

jest.mock('@likashefqet/react-native-image-zoom', () => {
  const React = require('react');
  const { View } = require('react-native');
  return {
    ImageZoom: (props) => React.createElement(View, { ...props, testID: 'image-zoom' }),
  };
});

jest.mock('react-native-zeroconf', () => {
  return {
    __esModule: true,
    default: function Zeroconf() {
      return {
        scan: jest.fn(),
        stop: jest.fn(),
        on: jest.fn(),
        removeListener: jest.fn(),
        removeAllListeners: jest.fn(),
        getServices: jest.fn(() => []),
      };
    },
  };
});

jest.mock('react-native-gesture-handler', () => {
  const React = require('react');
  return {
    __esModule: true,
    GestureHandlerRootView: ({ children }) => React.createElement(React.Fragment, null, children),
    gestureHandlerRootHOC: (Component) => Component,
  };
});

jest.mock('react-native-share', () => ({
  __esModule: true,
  default: {
    open: jest.fn(async () => {}),
  },
  open: jest.fn(async () => {}),
}));

jest.mock('@react-native-camera-roll/camera-roll', () => ({
  __esModule: true,
  CameraRoll: {
    saveAsset: jest.fn(async () => {}),
  },
  iosRequestAddOnlyGalleryPermission: jest.fn(async () => 'granted'),
}));

jest.mock('@likashefqet/react-native-image-zoom', () => {
  const React = require('react');
  const { View } = require('react-native');
  return {
    __esModule: true,
    ImageZoom: (props) => React.createElement(View, { ...props, testID: 'image-zoom' }),
  };
});

jest.mock('@crystal-lattice/frontend-rn-components', () => {
  const React = require('react');
  const lightTheme = {
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

  return {
    __esModule: true,
    SESSION_ACTIONS: {},
    ThemeProvider: ({ children }) => React.createElement(React.Fragment, null, children),
    useTheme: () => lightTheme,
    SessionActionsBar: () => React.createElement(React.Fragment, null),
    ApplicationActionDialog: () => React.createElement(React.Fragment, null),
  };
});

jest.mock('react-native-markdown-display', () => {
  const React = require('react');
  return ({ children }) => React.createElement(React.Fragment, null, children);
});

jest.mock('react-native-enriched-markdown', () => {
  const React = require('react');
  return {
    __esModule: true,
    EnrichedMarkdownText: (props) => React.createElement('EnrichedMarkdownText', props),
  };
});

jest.mock('react-native-syntax-highlighter', () => 'SyntaxHighlighter');

jest.mock('react-syntax-highlighter/styles/hljs', () => ({}));

jest.mock('react-native-fs', () => {
  return {
    __esModule: true,
    default: {
      readFile: jest.fn(async () => ''),
    },
    readFile: jest.fn(async () => ''),
  };
});
