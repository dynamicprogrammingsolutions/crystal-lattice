module.exports = {
  preset: 'react-native',
  transformIgnorePatterns: [
    'node_modules/(?!(@react-native|react-native|@react-native-community|@crystal-lattice/frontend-sdk|react-native-url-polyfill)/)',
  ],
};
