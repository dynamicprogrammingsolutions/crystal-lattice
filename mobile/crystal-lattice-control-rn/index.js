/**
 * @format
 */

import React from 'react';
import 'react-native-gesture-handler';
import { AppRegistry } from 'react-native';
import App from './App';
import { MobileTranscriptScrollHarness } from './src/testing/MobileTranscriptScrollHarness';
import { name as appName } from './app.json';

const RootComponent = props =>
  React.createElement(
    props?.clcTranscriptScrollHarness === '1'
      ? MobileTranscriptScrollHarness
      : App,
    props,
  );

AppRegistry.registerComponent(appName, () => RootComponent);
AppRegistry.registerComponent(
  'MobileTranscriptScrollHarness',
  () => MobileTranscriptScrollHarness,
);
