/**
 * @format
 */

import { AppRegistry } from 'react-native';
import App from './App';
import { ConnectionEditorWindow } from './src/windows/ConnectionEditorWindow';
import { AgentPickerWindow } from './src/windows/AgentPickerWindow';
import { ActionsPopoverView } from './src/windows/ActionsPopoverView';
import { ApplicationActionDialogWindow } from './src/windows/ApplicationActionDialogWindow';
import { name as appName } from './app.json';

AppRegistry.registerComponent(appName, () => App);
AppRegistry.registerComponent('ConnectionEditorWindow', () => ConnectionEditorWindow);
AppRegistry.registerComponent('AgentPickerWindow', () => AgentPickerWindow);
AppRegistry.registerComponent('ActionsPopoverView', () => ActionsPopoverView);
AppRegistry.registerComponent('ApplicationActionDialogWindow', () => ApplicationActionDialogWindow);
