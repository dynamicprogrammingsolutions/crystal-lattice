import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';

import { useTheme } from '@crystal-lattice/frontend-rn-components';
import {
  buildConfigSchemaByKey,
  buildSessionSettingItems,
  filterConfigUiSchemaElements,
  SessionSettingsHost,
  type ConfigSchemaByKey,
  type SessionSettingRenderCtx,
  type SessionSettingsRenderers,
} from '@crystal-lattice/frontend-sdk-react';
import type { ConfigSchemaEntry, UiSchemaElement } from '@crystal-lattice/frontend-sdk';

import { MacCheckbox } from '../native/MacCheckbox';
import { MacSelect, type MacSelectOption } from '../native/MacSelect';

function normalizeSelectOptions(raw: any): MacSelectOption[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .map((opt) => {
      if (typeof opt === 'string') {
        return { value: opt, label: opt };
      }
      if (opt && typeof opt === 'object') {
        const value = typeof (opt as any).value === 'string' ? (opt as any).value : String((opt as any).value ?? '');
        const label = typeof (opt as any).label === 'string' ? (opt as any).label : value;
        if (!value) return null;
        return { value, label };
      }
      return null;
    })
    .filter((v) => v !== null) as MacSelectOption[];
}

function buildDefaultsFromSchema(schema: ConfigSchemaEntry[]): Record<string, any> {
  const result: Record<string, any> = {};
  for (const entry of schema) {
    if (!entry || typeof entry !== 'object') continue;
    const key = (entry as any).key;
    if (typeof key !== 'string' || !key) continue;
    if ((entry as any).default === undefined) continue;
    result[key] = (entry as any).default;
  }
  return result;
}

function isMissingRequiredValue(value: any): boolean {
  if (value === undefined || value === null) return true;
  if (typeof value === 'string' && value.trim().length === 0) return true;
  return false;
}

export type AttachmentMetadataUi = {
  prompt?: 'always' | 'never' | 'if_missing_required';
  defaults?: Record<string, any>;
  config_schema?: ConfigSchemaEntry[];
  ui_schema?: UiSchemaElement[];
};

export function buildAttachmentMetadataDefaults(metadataUi: AttachmentMetadataUi | null): Record<string, any> {
  if (!metadataUi) return {};
  const schema = Array.isArray(metadataUi.config_schema) ? metadataUi.config_schema : [];
  const defaultsFromSchema = buildDefaultsFromSchema(schema);
  const defaultsFromPlugin =
    metadataUi.defaults && typeof metadataUi.defaults === 'object' ? metadataUi.defaults : {};
  return {
    ...defaultsFromSchema,
    ...defaultsFromPlugin,
  };
}

export function shouldPromptForAttachmentMetadata(options: {
  metadataUi: AttachmentMetadataUi | null;
}): boolean {
  const metadataUi = options.metadataUi;
  if (!metadataUi) return false;

  const schema = Array.isArray(metadataUi.config_schema) ? metadataUi.config_schema : [];
  const baseDefaults = buildAttachmentMetadataDefaults(metadataUi);

  const requiredKeys = schema
    .map((entry) => {
      if (!entry || typeof entry !== 'object') return null;
      const key = (entry as any).key;
      const required = Boolean((entry as any).required);
      if (!required) return null;
      return typeof key === 'string' && key.length > 0 ? key : null;
    })
    .filter((key): key is string => typeof key === 'string');

  const missingRequiredDefaults = requiredKeys.some((key) => isMissingRequiredValue(baseDefaults[key]));
  if (missingRequiredDefaults) {
    return true;
  }

  const prompt = metadataUi.prompt;
  return prompt === 'always';
}

export const AttachmentMetadataPopoverContent: React.FC<{
  title: string;
  metadataUi: AttachmentMetadataUi | null;
  initialMetadata: Record<string, any>;
  onCancel: () => void;
  onSave: (metadata: Record<string, any>) => void;
}> = ({ title, metadataUi, initialMetadata, onCancel, onSave }) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const [elements, setElements] = useState<UiSchemaElement[]>([]);
  const [schema, setSchema] = useState<ConfigSchemaEntry[]>([]);
  const [schemaByKey, setSchemaByKey] = useState<ConfigSchemaByKey>({});
  const [baseDefaults, setBaseDefaults] = useState<Record<string, any>>({});
  const [overrides, setOverrides] = useState<Record<string, any>>({});
  const firstInputRef = useRef<TextInput | null>(null);
  const inputRefsByKey = useRef<Record<string, TextInput | null>>({});

  useEffect(() => {
    const rawElements = (metadataUi?.ui_schema ?? []) as UiSchemaElement[];
    const rawSchema = (metadataUi?.config_schema ?? []) as ConfigSchemaEntry[];
    const defaults = buildAttachmentMetadataDefaults(metadataUi);

    setElements(filterConfigUiSchemaElements(rawElements || []));
    setSchema(rawSchema || []);
    setSchemaByKey(buildConfigSchemaByKey(rawSchema || []));
    setBaseDefaults(defaults);
    setOverrides(initialMetadata || {});
  }, [initialMetadata, metadataUi]);

  useEffect(() => {
    const handle = setTimeout(() => {
      firstInputRef.current?.focus();
    }, 50);
    return () => clearTimeout(handle);
  }, []);

  const items = useMemo(() => {
    return buildSessionSettingItems({
      elements,
      overrides,
      baseConfig: baseDefaults,
      schemaByKey,
    });
  }, [baseDefaults, elements, overrides, schemaByKey]);

  const orderedTextKeys = useMemo(() => {
    return items
      .filter((item) => item.type === 'text' || item.type === 'multiline' || item.type === 'fallback')
      .map((item) => item.key);
  }, [items]);

  const handleToggleCheckbox = async (key: string, next: boolean) => {
    setOverrides((prev) => ({ ...prev, [key]: next }));
  };

  const handleSelectOption = async (key: string, value: string) => {
    setOverrides((prev) => ({ ...prev, [key]: value }));
  };

  const focusTextKey = (key: string) => {
    const target = inputRefsByKey.current[key];
    target?.focus();
  };

  const handleTextKeyPress = (event: any, settingKey: string) => {
    const pressedKey = event?.nativeEvent?.key;
    const shiftKey = Boolean(event?.nativeEvent?.shiftKey);
    if (pressedKey === 'Escape') {
      onCancel();
      return;
    }
    if (pressedKey === 'Tab') {
      const idx = orderedTextKeys.indexOf(settingKey);
      if (idx >= 0) {
        const nextIdx = shiftKey ? idx - 1 : idx + 1;
        if (nextIdx >= 0 && nextIdx < orderedTextKeys.length) {
          focusTextKey(orderedTextKeys[nextIdx]);
        }
      }
      return;
    }
    if (pressedKey === 'Enter') {
      if (shiftKey) {
        return;
      }
      // Submit form on Enter.
      handleSaveAll();
    }
  };

  const renderTextLike = (ctx: SessionSettingRenderCtx) => {
    const { item } = ctx;
    const settingKey = item.key;
    const textValue =
      item.effectiveValue !== undefined && item.effectiveValue !== null ? String(item.effectiveValue) : '';

    return (
      <View style={styles.itemRow}>
        <View style={styles.itemTextColumn}>
          <View style={styles.itemLabelRow}>
            <View style={styles.itemLabelChipColumn}>
              <Text style={styles.itemLabel}>{item.label}</Text>
            </View>
          </View>
          {item.description ? <Text style={styles.itemDescription}>{item.description}</Text> : null}
          <TextInput
            ref={(ref) => {
              inputRefsByKey.current[settingKey] = ref;
              if (!firstInputRef.current) {
                firstInputRef.current = ref;
              }
            }}
            style={styles.textInput}
            value={textValue}
            onKeyPress={(event) => handleTextKeyPress(event, settingKey)}
            onChangeText={(txt) => setOverrides((prev) => ({ ...prev, [settingKey]: txt }))}
            placeholder="Enter value"
            placeholderTextColor={theme.textSecondary}
            autoCorrect={false}
            autoCapitalize="none"
            multiline={item.type === 'multiline'}
          />
        </View>
      </View>
    );
  };

  const renderers: SessionSettingsRenderers = {
    fallback: renderTextLike,
    checkbox: (ctx: SessionSettingRenderCtx) => {
      const { item } = ctx;
      const boolValue = Boolean(item.effectiveValue ?? false);
      return (
        <View style={styles.itemRow}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <Text style={styles.itemLabel}>{item.label}</Text>
            </View>
            {item.description ? <Text style={styles.itemDescription}>{item.description}</Text> : null}
          </View>
          <View style={styles.controlRightColumn}>
            <MacCheckbox
              label=""
              value={boolValue}
              onValueChange={(next) => ctx.actions.toggleCheckbox(item.key, next)}
            />
          </View>
        </View>
      );
    },
    select: (ctx: SessionSettingRenderCtx) => {
      const { item } = ctx;
      const schemaEntry = schemaByKey[item.key] as any;
      const options = normalizeSelectOptions(schemaEntry?.options ?? schemaEntry?.choices ?? []);
      const selected = typeof item.effectiveValue === 'string' ? item.effectiveValue : '';
      return (
        <View style={styles.itemRow}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <Text style={styles.itemLabel}>{item.label}</Text>
            </View>
            {item.description ? <Text style={styles.itemDescription}>{item.description}</Text> : null}
            <MacSelect
              options={options}
              selectedValue={selected}
              placeholder="Select…"
              enabled
              onValueChange={(value) => ctx.actions.selectOption(item.key, value)}
            />
          </View>
        </View>
      );
    },
    text: renderTextLike,
    multiline: renderTextLike,
  };

  const computeEffectiveMetadata = (): Record<string, any> => {
    return {
      ...baseDefaults,
      ...overrides,
    };
  };

  const requiredKeys = schema
    .map((entry) => (entry && typeof entry === 'object' ? (entry as any).key : null))
    .filter((key): key is string => typeof key === 'string' && key.length > 0)
    .filter((key) => Boolean((schemaByKey[key] as any)?.required));

  const handleSaveAll = () => {
    const effective = computeEffectiveMetadata();
    const missing = requiredKeys.filter((key) => isMissingRequiredValue(effective[key]));
    if (missing.length > 0) {
      Alert.alert('Missing required fields', `Please fill: ${missing.join(', ')}`);
      return;
    }
    onSave(effective);
  };

  return (
    <View style={styles.root}>
      <Text style={styles.title}>{title}</Text>
      {items.length === 0 ? (
        <Text style={styles.helperText}>No metadata fields are defined for this attachment.</Text>
      ) : (
        <View style={styles.body}>
          <SessionSettingsHost
            items={items}
            actions={{
              toggleCheckbox: handleToggleCheckbox,
              selectOption: handleSelectOption,
              saveText: () => {},
              revertToDefault: () => {},
            }}
            renderers={renderers}
            renderFrame={({ children }) => <ScrollView style={styles.list}>{children}</ScrollView>}
          />
        </View>
      )}
      <View style={styles.footerRow}>
        <TouchableOpacity style={styles.footerButton} onPress={onCancel}>
          <Text style={styles.footerButtonText}>Cancel</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.footerButton, styles.footerButtonPrimary]} onPress={handleSaveAll}>
          <Text style={[styles.footerButtonText, styles.footerButtonPrimaryText]}>Save</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const createStyles = (theme: ReturnType<typeof useTheme>) =>
  StyleSheet.create({
    root: {
      flex: 1,
      paddingHorizontal: 12,
      paddingVertical: 10,
    },
    title: {
      fontSize: 14,
      fontWeight: '700',
      color: theme.text,
      marginBottom: 8,
      textAlign: 'center',
    },
    helperText: {
      fontSize: 13,
      color: theme.textSecondary,
    },
    body: {
      flexGrow: 1,
      flexShrink: 1,
    },
    list: {
      flexGrow: 0,
      flexShrink: 1,
    },
    itemRow: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      paddingVertical: 6,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.border,
    },
    itemTextColumn: {
      flex: 1,
      marginRight: 8,
      minWidth: 0,
    },
    itemLabelRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 8,
      marginBottom: 2,
    },
    itemLabelChipColumn: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      alignItems: 'center',
      flex: 1,
      minWidth: 0,
    },
    itemLabel: {
      fontSize: 13,
      fontWeight: '600',
      color: theme.text,
      marginBottom: 2,
      marginRight: 4,
    },
    itemDescription: {
      fontSize: 12,
      color: theme.textSecondary,
      marginBottom: 6,
    },
    textInput: {
      flex: 1,
      minWidth: 0,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 6,
      fontSize: 13,
      backgroundColor: theme.surface,
      color: theme.text,
    },
    controlRightColumn: {
      justifyContent: 'center',
      alignItems: 'flex-end',
      paddingTop: 3,
    },
    footerRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      gap: 10,
      marginTop: 10,
    },
    footerButton: {
      flex: 1,
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderRadius: 10,
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surfaceAlt,
      alignItems: 'center',
    },
    footerButtonPrimary: {
      backgroundColor: theme.primary,
      borderColor: theme.primary,
    },
    footerButtonText: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.text,
    },
    footerButtonPrimaryText: {
      color: theme.textOnPrimary,
    },
  });
