/**
 * @format
 */

import React from "react";
import "react-native-gesture-handler";
import { AppRegistry } from "react-native";
import App from "./App";
import { MobileSessionListHarness } from "./src/testing/MobileSessionListHarness";
import { MobileTranscriptScrollHarness } from "./src/testing/MobileTranscriptScrollHarness";
import { MobileTranscriptRangeNavigationHarness } from "./src/testing/MobileTranscriptRangeNavigationHarness";
import { MobileNotificationBannerHarness } from "./src/testing/MobileNotificationBannerHarness";
import { MobileSelectableCodeBlockHarness } from "./src/testing/MobileSelectableCodeBlockHarness";
import { MobileOrderedListMarkdownHarness } from "./src/testing/MobileOrderedListMarkdownHarness";
import { MobileNotificationUiEffectsHarness } from "./src/testing/MobileNotificationUiEffectsHarness";
import { MobileConnectionsSettingsHarness } from "./src/testing/MobileConnectionsSettingsHarness";
import { MobileActionFormsHarness } from "./src/testing/MobileActionFormsHarness";
import { MobileHomeHarness } from "./src/testing/MobileHomeHarness";
import { MobileWebsiteVisualHarness } from "./src/testing/MobileWebsiteVisualHarness";
import { MobileRichSessionUiHarness } from "./src/testing/MobileRichSessionUiHarness";
import { EmbeddedPythonRuntimeDiagnosticsScreen } from "./src/embeddedRuntime/EmbeddedPythonRuntimeDiagnosticsScreen";
import { EmbeddedPythonWebFetchDiagnosticsScreen } from "./src/embeddedRuntime/EmbeddedPythonWebFetchDiagnosticsScreen";
import { EmbeddedProviderMatrixDiagnosticsScreen } from "./src/embeddedRuntime/EmbeddedProviderMatrixDiagnosticsScreen";
import { name as appName } from "./app.json";

const RootComponent = (props) => {
  let Component = App;
  if (props?.clcTranscriptScrollHarness === "1") {
    Component = MobileTranscriptScrollHarness;
  } else if (props?.clcTranscriptRangeNavigationHarness === "1") {
    Component = MobileTranscriptRangeNavigationHarness;
  } else if (props?.clcSessionListHarness === "1") {
    Component = MobileSessionListHarness;
  } else if (props?.clcNotificationBannerHarness === "1") {
    Component = MobileNotificationBannerHarness;
  } else if (props?.clcSelectableCodeBlockHarness === "1") {
    Component = MobileSelectableCodeBlockHarness;
  } else if (props?.clcOrderedListMarkdownHarness === "1") {
    Component = MobileOrderedListMarkdownHarness;
  } else if (props?.clcNotificationUiEffectsHarness === "1") {
    Component = MobileNotificationUiEffectsHarness;
  } else if (props?.clcWebsiteVisualHarness === "1") {
    Component = MobileWebsiteVisualHarness;
  } else if (props?.clcConnectionsSettingsHarness === "1") {
    Component = MobileConnectionsSettingsHarness;
  } else if (props?.clcActionFormsHarness === "1") {
    Component = MobileActionFormsHarness;
  } else if (props?.clcHomeHarness === "1") {
    Component = MobileHomeHarness;
  } else if (props?.clcRichSessionUiHarness === "1") {
    Component = MobileRichSessionUiHarness;
  } else if (props?.clcEmbeddedPythonRuntimeHarness === "1") {
    Component = EmbeddedPythonRuntimeDiagnosticsScreen;
  }
  return React.createElement(Component, props);
};

const MobileSessionListLargestPresetHarness = () =>
  React.createElement(MobileSessionListHarness, {
    clcDisplayPreset: "largest",
  });

AppRegistry.registerComponent(appName, () => RootComponent);
AppRegistry.registerComponent(
  "MobileTranscriptScrollHarness",
  () => MobileTranscriptScrollHarness
);
AppRegistry.registerComponent(
  "MobileTranscriptRangeNavigationHarness",
  () => MobileTranscriptRangeNavigationHarness
);
AppRegistry.registerComponent(
  "MobileSessionListHarness",
  () => MobileSessionListHarness
);
AppRegistry.registerComponent(
  "MobileSessionListLargestPresetHarness",
  () => MobileSessionListLargestPresetHarness
);
AppRegistry.registerComponent(
  "MobileNotificationBannerHarness",
  () => MobileNotificationBannerHarness
);
AppRegistry.registerComponent(
  "MobileSelectableCodeBlockHarness",
  () => MobileSelectableCodeBlockHarness
);
AppRegistry.registerComponent(
  "MobileOrderedListMarkdownHarness",
  () => MobileOrderedListMarkdownHarness
);
AppRegistry.registerComponent(
  "MobileNotificationUiEffectsHarness",
  () => MobileNotificationUiEffectsHarness
);
AppRegistry.registerComponent(
  "MobileWebsiteVisualHarness",
  () => MobileWebsiteVisualHarness
);
AppRegistry.registerComponent(
  "MobileConnectionsSettingsHarness",
  () => MobileConnectionsSettingsHarness
);
AppRegistry.registerComponent("MobileActionFormsHarness", () => MobileActionFormsHarness);
AppRegistry.registerComponent("MobileHomeHarness", () => MobileHomeHarness);
AppRegistry.registerComponent(
  "MobileRichSessionUiHarness",
  () => MobileRichSessionUiHarness
);
AppRegistry.registerComponent(
  "EmbeddedPythonRuntimeDiagnostics",
  () => EmbeddedPythonRuntimeDiagnosticsScreen
);
AppRegistry.registerComponent(
  "EmbeddedPythonWebFetchDiagnostics",
  () => EmbeddedPythonWebFetchDiagnosticsScreen
);
AppRegistry.registerComponent(
  "EmbeddedProviderMatrixDiagnostics",
  () => EmbeddedProviderMatrixDiagnosticsScreen
);
