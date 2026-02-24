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

jest.mock('react-native-zeroconf', () => {
  return {
    __esModule: true,
    default: function Zeroconf() {
      return {
        scan: jest.fn(),
        stop: jest.fn(),
        on: jest.fn(),
        removeListener: jest.fn(),
        getServices: jest.fn(() => []),
      };
    },
  };
});

jest.mock('@crystal-lattice/frontend-rn-components', () => {
  const React = require('react');
  return {
    __esModule: true,
    SESSION_ACTIONS: {},
    SessionActionsBar: () => React.createElement(React.Fragment, null),
    ApplicationActionDialog: () => React.createElement(React.Fragment, null),
  };
});

jest.mock('react-native-markdown-display', () => {
  const React = require('react');
  return ({ children }) => React.createElement(React.Fragment, null, children);
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
