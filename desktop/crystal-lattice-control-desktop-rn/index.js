/**
 * @format
 */
/* global globalThis */

// globalThis.CLC_FLATLIST_MAX_TO_RENDER_PER_BATCH = 100
// Eagerly render every transcript row at or below this count.
// Set to 0 or remove this assignment to disable eager rendering.
globalThis.CLC_FLATLIST_EAGER_RENDER_THRESHOLD = 100;
//globalThis.CLC_TRANSCRIPT_LIST_IMPLEMENTATION = "scrollView"
globalThis.CLC_TRANSCRIPT_LIST_IMPLEMENTATION = "flatList"

// globalThis.CLC_TRANSCRIPT_LIST_IMPLEMENTATION = "progressiveScroll"
// globalThis.CLC_PROGRESSIVE_SCROLL_BACKING_LIST = "flatList"
// globalThis.CLC_PROGRESSIVE_SCROLL_EDGE_EPSILON_PX = 20
// globalThis.CLC_PROGRESSIVE_SCROLL_AUTO_LOAD = true;
// globalThis.CLC_PROGRESSIVE_SCROLL_EDGE_THRESHOLD_PX = 240
//
// globalThis.CLC_PROGRESSIVE_SCROLL_INITIAL_WINDOW_SIZE = 25;
// globalThis.CLC_PROGRESSIVE_SCROLL_PAGE_SIZE = 25;
// globalThis.CLC_PROGRESSIVE_SCROLL_MAX_WINDOW_SIZE = 50;

globalThis.CLC_TRANSCRIPT_RANGE_CONTROLS = true;
globalThis.CLC_TRANSCRIPT_RANGE_CONTROL_PAGE_SIZE = 50;

globalThis.CLC_FLATLIST_MANUAL_BOTTOM_CONVERGENCE_MAX_MS = 15000;
globalThis.CLC_FLATLIST_INITIAL_BOTTOM_CONVERGENCE_MAX_MS = 15000;
globalThis.CLC_FLATLIST_MAX_EDGE_CORRECTIONS = 60;
globalThis.CLC_FLATLIST_ITEM_ANCHOR_TIMEOUT_MS = 15000;
globalThis.CLC_FLATLIST_ITEM_ANCHOR_MAX_ATTEMPTS = 200;

// Lifecycle diagnostics are concise and off by default. Enable verbose mode
// only when frame-level observations/corrections are needed.
// globalThis.CLC_DEBUG_CHAT_SCROLL_COORDINATOR = true;
// globalThis.CLC_DEBUG_CHAT_SCROLL_COORDINATOR_VERBOSE = true;

if (globalThis.CLC_DEBUG_CHAT_SCROLL_COORDINATOR === true) {
  console.log(
    '[chatScrollBootstrap]',
    JSON.stringify({
      listImplementation: globalThis.CLC_TRANSCRIPT_LIST_IMPLEMENTATION,
      manualBottomConvergenceMaxMs:
        globalThis.CLC_FLATLIST_MANUAL_BOTTOM_CONVERGENCE_MAX_MS,
      initialBottomConvergenceMaxMs:
        globalThis.CLC_FLATLIST_INITIAL_BOTTOM_CONVERGENCE_MAX_MS,
      maxEdgeCorrections: globalThis.CLC_FLATLIST_MAX_EDGE_CORRECTIONS,
      itemAnchorTimeoutMs: globalThis.CLC_FLATLIST_ITEM_ANCHOR_TIMEOUT_MS,
      itemAnchorMaxAttempts: globalThis.CLC_FLATLIST_ITEM_ANCHOR_MAX_ATTEMPTS,
      verbose: globalThis.CLC_DEBUG_CHAT_SCROLL_COORDINATOR_VERBOSE,
    }),
  );
}

// Runtime requires guarantee that these flags are assigned before modules such
// as ChatPane capture their module-level configuration.
const { AppRegistry } = require('react-native');
const App = require('./App').default;
const { ProgressiveScrollHarness } = require('./src/testing/ProgressiveScrollHarness');
const {
  TranscriptScrollPersistenceHarness,
} = require('./src/testing/TranscriptScrollPersistenceHarness');
const {
  DesktopTranscriptRangeNavigationHarness,
} = require('./src/testing/DesktopTranscriptRangeNavigationHarness');
const {
  SessionFiltersPopoverHarness,
} = require('./src/testing/SessionFiltersPopoverHarness');
const {
  DesktopNotificationRailHarness,
} = require('./src/testing/DesktopNotificationRailHarness');
const {
  DesktopMarkdownGeometryHarness,
} = require('./src/testing/DesktopMarkdownGeometryHarness');
const {
  DesktopConnectionsPanelHarness,
} = require('./src/testing/DesktopConnectionsPanelHarness');
const {
  DesktopActionDisplayHarness,
} = require('./src/testing/DesktopActionDisplayHarness');
const {
  DesktopWorkspaceHarness,
} = require('./src/testing/DesktopWorkspaceHarness');
const {
  DesktopRichSessionUiHarness,
} = require('./src/testing/DesktopRichSessionUiHarness');
const {
  DesktopWebsiteVisualHarness,
} = require('./src/testing/DesktopWebsiteVisualHarness');
const { ConnectionEditorWindow } = require('./src/windows/ConnectionEditorWindow');
const { AgentPickerWindow } = require('./src/windows/AgentPickerWindow');
const { ActionsPopoverView } = require('./src/windows/ActionsPopoverView');
const { MessageLimitPopoverView } = require('./src/windows/MessageLimitPopoverView');
const {
  ApplicationActionDialogWindow,
} = require('./src/windows/ApplicationActionDialogWindow');
const { SessionSettingsWindow } = require('./src/windows/SessionSettingsWindow');
const { SessionPluginsWindow } = require('./src/windows/SessionPluginsWindow');
const { SessionSnapshotsWindow } = require('./src/windows/SessionSnapshotsWindow');
const { NotificationTestingWindow } = require('./src/windows/NotificationTestingWindow');
const { AttachmentMetadataWindow } = require('./src/windows/AttachmentMetadataWindow');
const { ServerSettingsWindow } = require('./src/windows/ServerSettingsWindow');
const { ActionDisplayWindow } = require('./src/windows/ActionDisplayWindow');
const { GlobalSettingsWindow } = require('./src/windows/GlobalSettingsWindow');
const { SessionNoteWindow } = require('./src/windows/SessionNoteWindow');
const { name: appName } = require('./app.json');

AppRegistry.registerComponent(appName, () => App);
AppRegistry.registerComponent('ProgressiveScrollHarness', () => ProgressiveScrollHarness);
AppRegistry.registerComponent('TranscriptScrollPersistenceHarness', () => TranscriptScrollPersistenceHarness);
AppRegistry.registerComponent('DesktopTranscriptRangeNavigationHarness', () => DesktopTranscriptRangeNavigationHarness);
AppRegistry.registerComponent('SessionFiltersPopoverHarness', () => SessionFiltersPopoverHarness);
AppRegistry.registerComponent('DesktopNotificationRailHarness', () => DesktopNotificationRailHarness);
AppRegistry.registerComponent('DesktopMarkdownGeometryHarness', () => DesktopMarkdownGeometryHarness);
AppRegistry.registerComponent('DesktopConnectionsPanelHarness', () => DesktopConnectionsPanelHarness);
AppRegistry.registerComponent('DesktopActionDisplayHarness', () => DesktopActionDisplayHarness);
AppRegistry.registerComponent('DesktopWorkspaceHarness', () => DesktopWorkspaceHarness);
AppRegistry.registerComponent('DesktopRichSessionUiHarness', () => DesktopRichSessionUiHarness);
AppRegistry.registerComponent('DesktopWebsiteVisualHarness', () => DesktopWebsiteVisualHarness);
AppRegistry.registerComponent('ConnectionEditorWindow', () => ConnectionEditorWindow);
AppRegistry.registerComponent('AgentPickerWindow', () => AgentPickerWindow);
AppRegistry.registerComponent('ActionsPopoverView', () => ActionsPopoverView);
AppRegistry.registerComponent('MessageLimitPopoverView', () => MessageLimitPopoverView);
AppRegistry.registerComponent('ApplicationActionDialogWindow', () => ApplicationActionDialogWindow);
AppRegistry.registerComponent('SessionSettingsWindow', () => SessionSettingsWindow);
AppRegistry.registerComponent('SessionPluginsWindow', () => SessionPluginsWindow);
AppRegistry.registerComponent('SessionSnapshotsWindow', () => SessionSnapshotsWindow);
AppRegistry.registerComponent('NotificationTestingWindow', () => NotificationTestingWindow);
AppRegistry.registerComponent('AttachmentMetadataWindow', () => AttachmentMetadataWindow);
AppRegistry.registerComponent('ServerSettingsWindow', () => ServerSettingsWindow);
AppRegistry.registerComponent('ActionDisplayWindow', () => ActionDisplayWindow);
AppRegistry.registerComponent('GlobalSettingsWindow', () => GlobalSettingsWindow);
AppRegistry.registerComponent('SessionNoteWindow', () => SessionNoteWindow);
