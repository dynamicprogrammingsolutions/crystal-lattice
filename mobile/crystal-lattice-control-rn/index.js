/**
 * @format
 */

import React from 'react';
import 'react-native-gesture-handler';
import { AppRegistry } from 'react-native';
import App from './App';
import { MobileSessionListHarness } from './src/testing/MobileSessionListHarness';
import { MobileTranscriptScrollHarness } from './src/testing/MobileTranscriptScrollHarness';
import { name as appName } from './app.json';

const RootComponent = props => {
  let Component = App;
  if (props?.clcTranscriptScrollHarness === '1') {
    Component = MobileTranscriptScrollHarness;
  } else if (props?.clcSessionListHarness === '1') {
    Component = MobileSessionListHarness;
  }
  return React.createElement(Component, props);
};

AppRegistry.registerComponent(appName, () => RootComponent);
AppRegistry.registerComponent(
  'MobileTranscriptScrollHarness',
  () => MobileTranscriptScrollHarness,
);
AppRegistry.registerComponent(
  'MobileSessionListHarness',
  () => MobileSessionListHarness,
);
