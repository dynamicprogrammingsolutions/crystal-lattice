module.exports = {
  preset: 'react-native',
  setupFiles: ['<rootDir>/jest.setup.js'],
  transformIgnorePatterns: [
    'node_modules/(?!(react-native|@react-native|react-native-vector-icons|react-native-markdown-display|react-syntax-highlighter)/)',
  ],
  moduleNameMapper: {
    '^react$': '<rootDir>/node_modules/react',
    '^react-native$': '<rootDir>/node_modules/react-native',
  },
  testPathIgnorePatterns: [
    '/node_modules/',
    '<rootDir>/__integration__/',
    '<rootDir>/__native__/',
  ],
};
