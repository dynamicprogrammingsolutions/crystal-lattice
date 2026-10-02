import type { ReactNode } from 'react';

import type { ConfigSchemaEntry, UiSchemaElement } from '@crystal-lattice/frontend-sdk';

export type SessionSettingSource = 'override' | 'config' | 'ui_default' | 'schema_default' | 'none';

export type SessionSettingTagLabel = 'config' | 'default' | null;

export type ConfigSchemaByKey = Record<string, ConfigSchemaEntry>;

export interface SessionSettingItem {
  key: string;
  type: string;
  element: UiSchemaElement;

  label: string;
  description: string;
  disabled: boolean;

  hasOverride: boolean;
  effectiveValue: unknown;

  source: SessionSettingSource;
  tagLabel: SessionSettingTagLabel;

  overrideValue?: unknown;
  baseValue?: unknown;
  schemaDefaultValue?: unknown;
}

export interface SessionSettingsActions {
  toggleCheckbox: (key: string, next: boolean) => void | Promise<void>;
  selectOption: (key: string, value: string) => void | Promise<void>;
  saveText: (key: string) => void | Promise<void>;
  revertToDefault: (key: string) => void | Promise<void>;
}

export interface SessionSettingRenderCtx {
  item: SessionSettingItem;
  actions: SessionSettingsActions;
  renderFallback: () => ReactNode;
}

export type SessionSettingRenderer = (ctx: SessionSettingRenderCtx) => ReactNode;

export type SessionSettingsRenderers = {
  fallback: SessionSettingRenderer;
} & Partial<Record<string, SessionSettingRenderer>>;

export type SessionSettingsFrameRenderer = (ctx: {
  items: SessionSettingItem[];
  children: ReactNode;
}) => ReactNode;

export type SessionSettingsAfterItemRenderer = (ctx: {
  item: SessionSettingItem;
}) => ReactNode;
