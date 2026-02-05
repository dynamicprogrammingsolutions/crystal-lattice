import { NativeEventEmitter, NativeModules, Platform } from 'react-native';

import type { ConnectionRecord } from '@crystal-lattice/frontend-sdk';

import type { MacOSSystemThemePayload } from '../theme/types';

export interface OpenConnectionEditorParams {
  mode: 'new' | 'edit';
  initialRecord?: ConnectionRecord;
}

export interface OpenAgentPickerParams {
  connectionId: string;
  connectionName?: string;
  agents: string[];
}

export interface DesktopWindowManagerModule {
  openConnectionEditor(params: OpenConnectionEditorParams): void;
  submitConnectionEditor(payload: { record: ConnectionRecord }): void;
  cancelConnectionEditor(): void;

  openAgentPicker(params: OpenAgentPickerParams): void;
  submitAgentPicker(payload: { connectionId: string; agentId: string }): void;
  cancelAgentPicker(): void;

  getSystemTheme?(): Promise<MacOSSystemThemePayload>;
}

export const DesktopWindowManager: DesktopWindowManagerModule | null =
  Platform.OS === 'macos' && NativeModules.DesktopWindowManager
    ? (NativeModules.DesktopWindowManager as DesktopWindowManagerModule)
    : null;

export const desktopWindowEvents = DesktopWindowManager
  ? new NativeEventEmitter(NativeModules.DesktopWindowManager)
  : null;
