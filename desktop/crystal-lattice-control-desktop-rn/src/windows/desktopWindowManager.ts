import { NativeEventEmitter, NativeModules, Platform } from 'react-native';

import type { ConnectionRecord } from '@crystal-lattice/frontend-sdk';

export interface OpenConnectionEditorParams {
  mode: 'new' | 'edit';
  initialRecord?: ConnectionRecord;
}

export interface DesktopWindowManagerModule {
  openConnectionEditor(params: OpenConnectionEditorParams): void;
  submitConnectionEditor(payload: { record: ConnectionRecord }): void;
  cancelConnectionEditor(): void;
}

export const DesktopWindowManager: DesktopWindowManagerModule | null =
  Platform.OS === 'macos' && NativeModules.DesktopWindowManager
    ? (NativeModules.DesktopWindowManager as DesktopWindowManagerModule)
    : null;

export const desktopWindowEvents = DesktopWindowManager
  ? new NativeEventEmitter(NativeModules.DesktopWindowManager)
  : null;
