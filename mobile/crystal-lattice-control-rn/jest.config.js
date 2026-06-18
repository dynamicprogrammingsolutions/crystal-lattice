module.exports = {
  preset: 'react-native',
  setupFilesAfterEnv: ['./jest.setup.js'],
  modulePaths: ['<rootDir>/node_modules'],
  transformIgnorePatterns: [
    'node_modules/(?!(@react-native|react-native|@react-native-community|@crystal-lattice/frontend-sdk|@crystal-lattice/frontend-sdk-react|react-native-url-polyfill)/)',
  ],
};
