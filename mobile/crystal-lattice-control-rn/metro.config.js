const path = require('path');
const { getDefaultConfig, mergeConfig } = require('@react-native/metro-config');

/**
 * Metro configuration
 * https://reactnative.dev/docs/metro
 *
 * @type {import('@react-native/metro-config').MetroConfig}
 */
const sdkRoot = path.resolve(__dirname, '../../packages/frontend-sdk');
const sdkReactRoot = path.resolve(__dirname, '../../packages/frontend-sdk-react');

const config = {
  watchFolders: [sdkRoot, sdkReactRoot],
  resolver: {
    unstable_enableSymlinks: true,
    extraNodeModules: {
      '@crystal-lattice/frontend-sdk': sdkRoot,
      '@crystal-lattice/frontend-sdk-react': sdkReactRoot,
    },
    nodeModulesPaths: [
      path.resolve(__dirname, 'node_modules'),
      path.resolve(__dirname, '../../node_modules'),
    ],
  },
};

module.exports = mergeConfig(getDefaultConfig(__dirname), config);
