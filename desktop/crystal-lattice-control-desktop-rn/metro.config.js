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
const rnComponentsRoot = path.resolve(__dirname, '../../packages/frontend-rn-components');
const macTextViewRoot = path.resolve(__dirname, '../../packages/react-native-mac-text-view');

const config = {
  watchFolders: [sdkRoot, sdkReactRoot, rnComponentsRoot, macTextViewRoot],
  resolver: {
    unstable_enableSymlinks: true,
    extraNodeModules: {
      '@crystal-lattice/frontend-sdk': sdkRoot,
      '@crystal-lattice/frontend-sdk-react': sdkReactRoot,
      '@crystal-lattice/frontend-rn-components': rnComponentsRoot,
      '@crystal-lattice/react-native-mac-text-view': macTextViewRoot,
    },
    nodeModulesPaths: [
      path.resolve(__dirname, 'node_modules'),
      path.resolve(__dirname, '../../node_modules'),
    ],
  },
};

module.exports = mergeConfig(getDefaultConfig(__dirname), config);
