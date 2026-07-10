/**
 * @format
 */

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

globalThis.CLC_FLATLIST_MANUAL_BOTTOM_FOLLOW_WINDOW_MS = 5000;

import { AppRegistry } from 'react-native';
import App from './App';
import { ProgressiveScrollHarness } from './src/testing/ProgressiveScrollHarness';
import { TranscriptScrollPersistenceHarness } from './src/testing/TranscriptScrollPersistenceHarness';
import { ConnectionEditorWindow } from './src/windows/ConnectionEditorWindow';
import { AgentPickerWindow } from './src/windows/AgentPickerWindow';
import { ActionsPopoverView } from './src/windows/ActionsPopoverView';
import { MessageLimitPopoverView } from './src/windows/MessageLimitPopoverView';
import { ApplicationActionDialogWindow } from './src/windows/ApplicationActionDialogWindow';
import { SessionSettingsWindow } from './src/windows/SessionSettingsWindow';
import { SessionPluginsWindow } from './src/windows/SessionPluginsWindow';
import { AttachmentMetadataWindow } from './src/windows/AttachmentMetadataWindow';
import { name as appName } from './app.json';

AppRegistry.registerComponent(appName, () => App);
AppRegistry.registerComponent('ProgressiveScrollHarness', () => ProgressiveScrollHarness);
AppRegistry.registerComponent('TranscriptScrollPersistenceHarness', () => TranscriptScrollPersistenceHarness);
AppRegistry.registerComponent('ConnectionEditorWindow', () => ConnectionEditorWindow);
AppRegistry.registerComponent('AgentPickerWindow', () => AgentPickerWindow);
AppRegistry.registerComponent('ActionsPopoverView', () => ActionsPopoverView);
AppRegistry.registerComponent('MessageLimitPopoverView', () => MessageLimitPopoverView);
AppRegistry.registerComponent('ApplicationActionDialogWindow', () => ApplicationActionDialogWindow);
AppRegistry.registerComponent('SessionSettingsWindow', () => SessionSettingsWindow);
AppRegistry.registerComponent('SessionPluginsWindow', () => SessionPluginsWindow);
AppRegistry.registerComponent('AttachmentMetadataWindow', () => AttachmentMetadataWindow);
