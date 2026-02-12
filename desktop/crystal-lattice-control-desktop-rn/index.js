/**
 * @format
 */

import { AppRegistry } from 'react-native';
import App from './App';
import { ConnectionEditorWindow } from './src/windows/ConnectionEditorWindow';
import { name as appName } from './app.json';

AppRegistry.registerComponent(appName, () => App);
AppRegistry.registerComponent('ConnectionEditorWindow', () => ConnectionEditorWindow);
