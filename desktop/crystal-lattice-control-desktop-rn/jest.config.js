module.exports = {
  preset: 'react-native',
  setupFiles: ['<rootDir>/jest.setup.js'],
  transformIgnorePatterns: [
    'node_modules/(?!(react-native|@react-native|react-native-vector-icons|react-native-markdown-display|react-native-syntax-highlighter|react-syntax-highlighter)/)',
  ],
  moduleNameMapper: {
    '^react$': '<rootDir>/node_modules/react',
  },
  testPathIgnorePatterns: ['/node_modules/', '<rootDir>/__integration__/'],
};
