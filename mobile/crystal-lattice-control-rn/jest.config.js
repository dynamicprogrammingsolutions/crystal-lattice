module.exports = {
  preset: 'react-native',
  setupFilesAfterEnv: ['./jest.setup.js'],
  testPathIgnorePatterns: ['/node_modules/', '/__integration__/'],
  transformIgnorePatterns: [
    'node_modules/(?!(@react-native|react-native|@react-native-community|@crystal-lattice/frontend-sdk|@crystal-lattice/frontend-sdk-react|react-native-url-polyfill)/)',
  ],
  moduleNameMapper: {
    '^react$': '<rootDir>/node_modules/react',
    '^react-native$': '<rootDir>/node_modules/react-native',
  },
};
