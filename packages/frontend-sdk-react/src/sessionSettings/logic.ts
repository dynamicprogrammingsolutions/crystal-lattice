import type { ConfigSchemaEntry, UiSchemaElement } from '@crystal-lattice/frontend-sdk';

import type {
  ConfigSchemaByKey,
  SessionSettingItem,
  SessionSettingSource,
  SessionSettingTagLabel,
} from './types';

function hasOwn(obj: unknown, key: string): boolean {
  return Object.prototype.hasOwnProperty.call(obj, key);
}

function looseEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (a == null || b == null) return a === b;
  if (typeof a === 'object' && typeof b === 'object') {
    try {
      return JSON.stringify(a) === JSON.stringify(b);
    } catch {
      return false;
    }
  }
  return false;
}

export function filterConfigUiSchemaElements(elements: UiSchemaElement[]): UiSchemaElement[] {
  return (Array.isArray(elements) ? elements : []).filter((element) => {
    if (!element || typeof element !== 'object') {
      return false;
    }

    const key = (element as any).key;
    if (typeof key !== 'string' || !key) {
      return false;
    }

    const uiType = (element as any).ui_type;
    if (uiType === 'config') {
      return true;
    }

    return uiType === undefined || uiType === null || uiType === '';
  }) as UiSchemaElement[];
}

export function buildConfigSchemaByKey(schema: ConfigSchemaEntry[]): ConfigSchemaByKey {
  const byKey: ConfigSchemaByKey = {};
  (Array.isArray(schema) ? schema : []).forEach((entry) => {
    if (!entry || typeof entry !== 'object') {
      return;
    }

    const key = (entry as any).key;
    if (typeof key !== 'string' || !key || byKey[key]) {
      return;
    }

    byKey[key] = entry;
  });
  return byKey;
}

function resolveValue(params: {
  key: string;
  overrides: Record<string, unknown>;
  baseConfig: Record<string, unknown>;
  schemaByKey: ConfigSchemaByKey;
  element?: UiSchemaElement | null;
}): {
  hasOverride: boolean;
  overrideValue: unknown;
  baseHasValue: boolean;
  baseValue: unknown;
  schemaDefaultValue: unknown;
  source: SessionSettingSource;
  tagLabel: SessionSettingTagLabel;
  effectiveValue: unknown;
} {
  const { key, overrides, baseConfig, schemaByKey, element } = params;

  const hasOverride = hasOwn(overrides, key);
  const overrideValue = hasOverride ? overrides[key] : undefined;

  const baseHasValue = hasOwn(baseConfig, key);
  const baseValue = baseHasValue ? baseConfig[key] : undefined;

  const schemaEntry = schemaByKey[key];
  const schemaHasDefault =
    schemaEntry && hasOwn(schemaEntry, 'default') && (schemaEntry as any).default !== undefined;
  const schemaDefaultValue = schemaHasDefault ? (schemaEntry as any).default : undefined;

  const elementHasDefault =
    element && hasOwn(element, 'default') && (element as any).default !== undefined;
  const elementDefaultValue = elementHasDefault ? (element as any).default : undefined;

  if (hasOverride) {
    return {
      hasOverride,
      overrideValue,
      baseHasValue,
      baseValue,
      schemaDefaultValue,
      source: 'override',
      tagLabel: null,
      effectiveValue: overrideValue,
    };
  }

  if (baseHasValue) {
    // When base config value equals schema or element default, show "default" for consistency.
    const matchesSchemaDefault =
      schemaHasDefault && looseEqual(baseValue, schemaDefaultValue);
    const matchesElementDefault =
      elementHasDefault && looseEqual(baseValue, elementDefaultValue);
    const tagLabel: SessionSettingTagLabel =
      matchesSchemaDefault || matchesElementDefault ? 'default' : 'config';

    return {
      hasOverride,
      overrideValue,
      baseHasValue,
      baseValue,
      schemaDefaultValue,
      source: 'config',
      tagLabel,
      effectiveValue: baseValue,
    };
  }

  if (schemaHasDefault) {
    return {
      hasOverride,
      overrideValue,
      baseHasValue,
      baseValue,
      schemaDefaultValue,
      source: 'schema_default',
      tagLabel: 'default',
      effectiveValue: schemaDefaultValue,
    };
  }

  if (elementHasDefault) {
    return {
      hasOverride,
      overrideValue,
      baseHasValue,
      baseValue,
      schemaDefaultValue,
      source: 'schema_default',
      tagLabel: 'default',
      effectiveValue: elementDefaultValue,
    };
  }

  return {
    hasOverride,
    overrideValue,
    baseHasValue,
    baseValue,
    schemaDefaultValue,
    source: 'none',
    tagLabel: null,
    effectiveValue: undefined,
  };
}

export function buildSessionSettingItems(params: {
  elements: UiSchemaElement[];
  overrides: Record<string, unknown>;
  baseConfig: Record<string, unknown>;
  schemaByKey: ConfigSchemaByKey;
}): SessionSettingItem[] {
  const { elements, overrides, baseConfig, schemaByKey } = params;
  const safeElements = Array.isArray(elements) ? elements : [];

  return safeElements
    .map((element) => {
      if (!element || typeof element !== 'object') {
        return null;
      }

      const key = (element as any).key;
      if (typeof key !== 'string' || !key) {
        return null;
      }

      const type =
        typeof (element as any).type === 'string' && (element as any).type
          ? ((element as any).type as string)
          : 'text';
      const label =
        typeof (element as any).label === 'string' && (element as any).label
          ? ((element as any).label as string)
          : key;
      const description =
        typeof (element as any).description === 'string' ? ((element as any).description as string) : '';

      const resolved = resolveValue({
        key,
        overrides,
        baseConfig,
        schemaByKey,
        element,
      });
      return {
        key,
        type,
        element,
        label,
        description,
        hasOverride: resolved.hasOverride,
        effectiveValue: resolved.effectiveValue,
        source: resolved.source,
        tagLabel: resolved.tagLabel,
        overrideValue: resolved.hasOverride ? resolved.overrideValue : undefined,
        baseValue: resolved.baseHasValue ? resolved.baseValue : undefined,
        schemaDefaultValue: resolved.schemaDefaultValue,
      } satisfies SessionSettingItem;
    })
    .filter((value) => value !== null) as SessionSettingItem[];
}
