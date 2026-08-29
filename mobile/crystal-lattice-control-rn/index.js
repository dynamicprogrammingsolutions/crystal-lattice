/**
 * @format
 */

import React from 'react';
import 'react-native-gesture-handler';
import { AppRegistry } from 'react-native';
import App from './App';
import { MobileSessionListHarness } from './src/testing/MobileSessionListHarness';
import { MobileTranscriptScrollHarness } from './src/testing/MobileTranscriptScrollHarness';
import { MobileTranscriptRangeNavigationHarness } from './src/testing/MobileTranscriptRangeNavigationHarness';
import { MobileNotificationBannerHarness } from './src/testing/MobileNotificationBannerHarness';
import { MobileSelectableCodeBlockHarness } from './src/testing/MobileSelectableCodeBlockHarness';
import { MobileOrderedListMarkdownHarness } from './src/testing/MobileOrderedListMarkdownHarness';
import { MobileNotificationUiEffectsHarness } from './src/testing/MobileNotificationUiEffectsHarness';
import { MobileConnectionsSettingsHarness } from './src/testing/MobileConnectionsSettingsHarness';
import { name as appName } from './app.json';

const RootComponent = props => {
  let Component = App;
  if (props?.clcTranscriptScrollHarness === '1') {
    Component = MobileTranscriptScrollHarness;
  } else if (props?.clcTranscriptRangeNavigationHarness === '1') {
    Component = MobileTranscriptRangeNavigationHarness;
  } else if (props?.clcSessionListHarness === '1') {
    Component = MobileSessionListHarness;
  } else if (props?.clcNotificationBannerHarness === '1') {
    Component = MobileNotificationBannerHarness;
  } else if (props?.clcSelectableCodeBlockHarness === '1') {
    Component = MobileSelectableCodeBlockHarness;
  } else if (props?.clcOrderedListMarkdownHarness === '1') {
    Component = MobileOrderedListMarkdownHarness;
  } else if (props?.clcNotificationUiEffectsHarness === '1') {
    Component = MobileNotificationUiEffectsHarness;
  } else if (props?.clcConnectionsSettingsHarness === '1') {
    Component = MobileConnectionsSettingsHarness;
  }
  return React.createElement(Component, props);
};

const MobileSessionListLargestPresetHarness = () =>
  React.createElement(MobileSessionListHarness, {
    clcDisplayPreset: 'largest',
  });

AppRegistry.registerComponent(appName, () => RootComponent);
AppRegistry.registerComponent(
  'MobileTranscriptScrollHarness',
  () => MobileTranscriptScrollHarness,
);
AppRegistry.registerComponent(
  'MobileTranscriptRangeNavigationHarness',
  () => MobileTranscriptRangeNavigationHarness,
);
AppRegistry.registerComponent(
  'MobileSessionListHarness',
  () => MobileSessionListHarness,
);
AppRegistry.registerComponent(
  'MobileSessionListLargestPresetHarness',
  () => MobileSessionListLargestPresetHarness,
);
AppRegistry.registerComponent(
  'MobileNotificationBannerHarness',
  () => MobileNotificationBannerHarness,
);
AppRegistry.registerComponent(
  'MobileSelectableCodeBlockHarness',
  () => MobileSelectableCodeBlockHarness,
);
AppRegistry.registerComponent(
  'MobileOrderedListMarkdownHarness',
  () => MobileOrderedListMarkdownHarness,
);
AppRegistry.registerComponent(
  'MobileNotificationUiEffectsHarness',
  () => MobileNotificationUiEffectsHarness,
);
AppRegistry.registerComponent(
  'MobileConnectionsSettingsHarness',
  () => MobileConnectionsSettingsHarness,
);
