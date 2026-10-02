import { NativeEventEmitter, NativeModules, Platform } from 'react-native';

import type {
  AgentDescriptor,
  ConnectionRecord,
} from '@crystal-lattice/frontend-sdk';

import type { MacOSSystemThemePayload } from '../theme/types';

export interface OpenConnectionEditorParams {
  mode: 'new' | 'edit';
  initialRecord?: ConnectionRecord;
}

export interface OpenAgentPickerParams {
  connectionId: string;
  connectionName?: string;
  agents: string[];
  agentDescriptors?: AgentDescriptor[];
  mode?: 'createSession' | 'switchSessionAgent';
  sessionId?: string;
  title?: string;
  primaryButtonLabel?: string;
  initialAgentId?: string;
}

export interface ToggleActionsPopoverParams {
  anchorTag: number;
  width?: number;
  height?: number;
}

export interface OpenMessageLimitPopoverParams {
  popoverId?: string;
  anchorTag?: number;
  width?: number;
  height?: number;
}

export interface OpenApplicationActionDialogWindowParams {
  title?: string;
}

export interface OpenApplicationActionDialogPopoverParams {
  anchorTag?: number;
  width?: number;
  height?: number;
}

export interface OpenSessionSettingsWindowParams {
  title?: string;
}

export interface OpenReactWindowParams {
  windowKey: string;
  moduleName: string;
  title?: string;
  width?: number;
  height?: number;
  initialProps?: Record<string, any>;
}

export interface CloseReactWindowParams {
  windowKey: string;
}

export interface SetDesktopGlobalSettingParams {
  key:
    | 'baseFontSize'
    | 'headerSize'
    | 'recentSessionsWindow'
    | 'sessionDoubleClickAction'
    | 'sessionsFollowActiveTabEnabled'
    | 'switchConnectionWithActiveTabEnabled'
    | 'timeTrackingEnabled'
    | 'timeTrackingPluginId'
    | 'timeTrackingInactivitySeconds';
  value: string | number | boolean;
}

export interface DesktopWindowManagerModule {
  openConnectionEditor(params: OpenConnectionEditorParams): void;
  submitConnectionEditor(payload: { record: ConnectionRecord }): void;
  cancelConnectionEditor(): void;

  openAgentPicker(params: OpenAgentPickerParams): void;
  submitAgentPicker(payload: {
    connectionId: string;
    agentId: string;
    mode?: 'createSession' | 'switchSessionAgent';
    sessionId?: string;
  }): void;
  cancelAgentPicker(): void;

  toggleActionsPopover(params: ToggleActionsPopoverParams): void;
  closeActionsPopover(): void;

  openMessageLimitPopover(params?: OpenMessageLimitPopoverParams): void;
  closeMessageLimitPopover(): void;

  openApplicationActionDialogWindow(
    params?: OpenApplicationActionDialogWindowParams,
  ): void;
  closeApplicationActionDialogWindow(): void;

  openApplicationActionDialogPopover(
    params?: OpenApplicationActionDialogPopoverParams,
  ): void;
  closeApplicationActionDialogPopover(): void;

  openSessionSettingsWindow(params?: OpenSessionSettingsWindowParams): void;
  closeSessionSettingsWindow(): void;

  openReactWindow(params: OpenReactWindowParams): void;
  closeReactWindow(params: CloseReactWindowParams): void;
  getDesktopGlobalSettings?(): Promise<Record<string, unknown>>;
  setDesktopGlobalSetting?(params: SetDesktopGlobalSettingParams): void;

  getSystemTheme?(): Promise<MacOSSystemThemePayload>;
  recordProgressiveScrollHarnessState?(state: Record<string, unknown>): void;
  recordMarkdownGeometryHarnessState?(state: Record<string, unknown>): void;
  recordConnectionsPanelHarnessState?(state: Record<string, unknown>): void;
  recordDesktopWorkspaceHarnessState?(state: Record<string, unknown>): void;
  readProgressiveScrollHarnessCommand?(): Promise<Record<
    string,
    unknown
  > | null>;
}

export const DesktopWindowManager: DesktopWindowManagerModule | null =
  Platform.OS === 'macos' && NativeModules.DesktopWindowManager
    ? (NativeModules.DesktopWindowManager as DesktopWindowManagerModule)
    : null;

export const desktopWindowEvents = DesktopWindowManager
  ? new NativeEventEmitter(NativeModules.DesktopWindowManager)
  : null;
