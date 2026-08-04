/**
 * @format
 */

import React from 'react';
import 'react-native-gesture-handler';
import { AppRegistry } from 'react-native';
import App from './App';
import { MobileSessionListHarness } from './src/testing/MobileSessionListHarness';
import { MobileTranscriptScrollHarness } from './src/testing/MobileTranscriptScrollHarness';
import { MobileNotificationBannerHarness } from './src/testing/MobileNotificationBannerHarness';
import { MobileSelectableCodeBlockHarness } from './src/testing/MobileSelectableCodeBlockHarness';
import { name as appName } from './app.json';

const RootComponent = props => {
  let Component = App;
  if (props?.clcTranscriptScrollHarness === '1') {
    Component = MobileTranscriptScrollHarness;
  } else if (props?.clcSessionListHarness === '1') {
    Component = MobileSessionListHarness;
  } else if (props?.clcNotificationBannerHarness === '1') {
    Component = MobileNotificationBannerHarness;
  } else if (props?.clcSelectableCodeBlockHarness === '1') {
    Component = MobileSelectableCodeBlockHarness;
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
AppRegistry.registerComponent(
  'MobileNotificationBannerHarness',
  () => MobileNotificationBannerHarness,
);
AppRegistry.registerComponent(
  'MobileSelectableCodeBlockHarness',
  () => MobileSelectableCodeBlockHarness,
);
