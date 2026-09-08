import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import {
  buildConfigSchemaByKey,
  buildSessionSettingItems,
  filterConfigUiSchemaElements,
  SessionSettingsHost,
  type ConfigSchemaByKey,
  type SessionSettingRenderCtx,
  type SessionSettingsRenderers,
} from '@crystal-lattice/frontend-sdk-react';
import Icon from 'react-native-vector-icons/Feather';

import type { ConfigSchemaEntry, UiSchemaElement } from '../api';
import { useTheme, type Theme } from '../theme';

function normalizeOptions(raw: any): { value: string; label: string }[] {
  if (!Array.isArray(raw)) return [];
  return raw
    .map((opt) => {
      if (typeof opt === 'string') {
        return { value: opt, label: opt };
      }
      if (opt && typeof opt === 'object') {
        const value = typeof opt.value === 'string' ? opt.value : String(opt.value ?? '');
        const label = typeof opt.label === 'string' ? opt.label : value;
        return { value, label };
      }
      return null;
    })
    .filter((v) => v !== null) as { value: string; label: string }[];
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

export const AttachmentMetadataModal: React.FC<{
  visible: boolean;
  title: string;
  metadataUi: AttachmentMetadataUi | null;
  initialMetadata: Record<string, any>;
  onCancel: () => void;
  onSave: (metadata: Record<string, any>) => void;
}> = ({ visible, title, metadataUi, initialMetadata, onCancel, onSave }) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const [elements, setElements] = useState<UiSchemaElement[]>([]);
  const [schema, setSchema] = useState<ConfigSchemaEntry[]>([]);
  const [schemaByKey, setSchemaByKey] = useState<ConfigSchemaByKey>({});
  const [baseDefaults, setBaseDefaults] = useState<Record<string, any>>({});
  const [overrides, setOverrides] = useState<Record<string, any>>({});
  const [pendingTextByKey, setPendingTextByKey] = useState<Record<string, string>>({});
  const [savingKey, setSavingKey] = useState<string | null>(null);

  useEffect(() => {
    if (!visible) {
      return;
    }
    const rawElements = (metadataUi?.ui_schema ?? []) as UiSchemaElement[];
    const rawSchema = (metadataUi?.config_schema ?? []) as ConfigSchemaEntry[];

    const defaultsFromSchema = buildDefaultsFromSchema(rawSchema);
    const defaultsFromPlugin =
      metadataUi?.defaults && typeof metadataUi.defaults === 'object' ? metadataUi.defaults : {};
    const nextBaseDefaults = {
      ...defaultsFromSchema,
      ...defaultsFromPlugin,
    };

    setElements(filterConfigUiSchemaElements(rawElements || []));
    setSchema(rawSchema || []);
    setSchemaByKey(buildConfigSchemaByKey(rawSchema || []));
    setBaseDefaults(nextBaseDefaults);
    setOverrides(initialMetadata || {});
    setPendingTextByKey({});
    setSavingKey(null);
  }, [initialMetadata, metadataUi, visible]);

  const items = useMemo(() => {
    return buildSessionSettingItems({
      elements,
      overrides,
      baseConfig: baseDefaults,
      schemaByKey,
    });
  }, [baseDefaults, elements, overrides, schemaByKey]);

  const handleToggleCheckbox = async (key: string, next: boolean) => {
    setOverrides((prev) => ({ ...prev, [key]: next }));
  };

  const handleSelectOption = async (key: string, value: string) => {
    setOverrides((prev) => ({ ...prev, [key]: value }));
  };

  const handleSaveText = async (key: string) => {
    const value = pendingTextByKey[key] ?? String(overrides[key] ?? baseDefaults[key] ?? '');
    setSavingKey(key);
    try {
      setOverrides((prev) => ({ ...prev, [key]: value }));
      setPendingTextByKey((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    } finally {
      setSavingKey((current) => (current === key ? null : current));
    }
  };

  const handleRevertToDefault = async (key: string) => {
    setOverrides((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
    setPendingTextByKey((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
  };

  const renderTextLike = (ctx: SessionSettingRenderCtx) => {
    const { item } = ctx;
    const key = item.key;
    const hasPending = Object.prototype.hasOwnProperty.call(pendingTextByKey, key);
    const pending = hasPending ? pendingTextByKey[key] : undefined;

    const textValue =
      pending ??
      (item.effectiveValue !== undefined && item.effectiveValue !== null
        ? String(item.effectiveValue)
        : '');

    return (
      <View style={styles.itemRow}>
        <View style={styles.itemTextColumn}>
          <View style={styles.itemLabelRow}>
            <View style={styles.itemLabelChipColumn}>
              <Text style={styles.itemLabel}>{item.label}</Text>
              {item.tagLabel && (
                <View style={item.tagLabel === 'config' ? styles.tagConfig : styles.tagDefault}>
                  <Text
                    style={
                      item.tagLabel === 'config' ? styles.tagTextConfig : styles.tagTextDefault
                    }
                  >
                    {item.tagLabel}
                  </Text>
                </View>
              )}
            </View>
            {item.hasOverride && (
              <TouchableOpacity
                style={styles.trashRightOfLabel}
                onPress={() => ctx.actions.revertToDefault(key)}
              >
                <Icon name="trash-2" size={14} color={theme.danger} />
              </TouchableOpacity>
            )}
          </View>
          {item.description ? <Text style={styles.itemDescription}>{item.description}</Text> : null}
          <View style={styles.textRow}>
            <TextInput
              style={styles.textInput}
              value={textValue}
              onChangeText={(txt) =>
                setPendingTextByKey((prev) => ({
                  ...prev,
                  [key]: txt,
                }))
              }
              placeholder="Enter value"
              placeholderTextColor={theme.textSecondary}
            />
            <TouchableOpacity
              style={styles.saveButton}
              onPress={() => ctx.actions.saveText(key)}
              disabled={savingKey === key}
            >
              {savingKey === key ? (
                <ActivityIndicator size="small" color={theme.textOnPrimary} />
              ) : (
                <Text style={styles.saveButtonText}>Save</Text>
              )}
            </TouchableOpacity>
          </View>
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
              <View style={styles.itemLabelChipColumn}>
                <Text style={styles.itemLabel}>{item.label}</Text>
                {item.tagLabel && (
                  <View
                    style={item.tagLabel === 'config' ? styles.tagConfig : styles.tagDefault}
                  >
                    <Text
                      style={
                        item.tagLabel === 'config' ? styles.tagTextConfig : styles.tagTextDefault
                      }
                    >
                      {item.tagLabel}
                    </Text>
                  </View>
                )}
              </View>
            </View>
            {item.description ? <Text style={styles.itemDescription}>{item.description}</Text> : null}
          </View>
          <View style={styles.controlSwitchColumn}>
            <Switch value={boolValue} onValueChange={(next) => ctx.actions.toggleCheckbox(item.key, next)} />
            {item.hasOverride && (
              <TouchableOpacity
                style={styles.trashBeforeSwitch}
                onPress={() => ctx.actions.revertToDefault(item.key)}
              >
                <Icon name="trash-2" size={14} color={theme.danger} />
              </TouchableOpacity>
            )}
          </View>
        </View>
      );
    },
    select: (ctx: SessionSettingRenderCtx) => {
      const { item } = ctx;
      const options = normalizeOptions((item.element as any).options);
      if (!options.length) {
        return null;
      }

      const selected =
        typeof item.effectiveValue === 'string'
          ? item.effectiveValue
          : String(item.effectiveValue ?? '');

      return (
        <View style={styles.itemRow}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <View style={styles.itemLabelChipColumn}>
                <Text style={styles.itemLabel}>{item.label}</Text>
                {item.tagLabel && (
                  <View
                    style={item.tagLabel === 'config' ? styles.tagConfig : styles.tagDefault}
                  >
                    <Text
                      style={
                        item.tagLabel === 'config' ? styles.tagTextConfig : styles.tagTextDefault
                      }
                    >
                      {item.tagLabel}
                    </Text>
                  </View>
                )}
              </View>
              {item.hasOverride && (
                <TouchableOpacity
                  style={styles.trashRightOfLabel}
                  onPress={() => ctx.actions.revertToDefault(item.key)}
                >
                  <Icon name="trash-2" size={14} color={theme.danger} />
                </TouchableOpacity>
              )}
            </View>
            {item.description ? <Text style={styles.itemDescription}>{item.description}</Text> : null}
            <View style={styles.chipsRow}>
              {options.map((opt) => {
                const isSelected = opt.value === selected;
                return (
                  <TouchableOpacity
                    key={opt.value}
                    style={isSelected ? styles.chipSelected : styles.chip}
                    onPress={() => ctx.actions.selectOption(item.key, opt.value)}
                  >
                    <Text style={isSelected ? styles.chipTextSelected : styles.chipText}>
                      {opt.label}
                    </Text>
                  </TouchableOpacity>
                );
              })}
            </View>
          </View>
        </View>
      );
    },
    text: renderTextLike,
    multiline: renderTextLike,
  };

  if (!visible) {
    return null;
  }

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
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onCancel}>
      <View style={styles.overlay}>
        <Pressable style={StyleSheet.absoluteFill} onPress={onCancel} />
        <View style={styles.content}>
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
                  saveText: handleSaveText,
                  revertToDefault: handleRevertToDefault,
                }}
                renderers={renderers}
                renderFrame={({ children }) => (
                  <ScrollView style={styles.list}>{children}</ScrollView>
                )}
              />
            </View>
          )}
          <View style={styles.footerRow}>
            <TouchableOpacity style={styles.closeButton} onPress={onCancel}>
              <Text style={styles.closeButtonText}>Cancel</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.closeButton, styles.saveAllButton]}
              onPress={handleSaveAll}
            >
              <Text style={[styles.closeButtonText, styles.saveAllButtonText]}>Save</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </Modal>
  );
};

export function shouldPromptForAttachmentMetadata(options: {
  metadataUi: AttachmentMetadataUi | null;
}): boolean {
  const metadataUi = options.metadataUi;
  if (!metadataUi) return false;

  const schema = Array.isArray(metadataUi.config_schema) ? metadataUi.config_schema : [];
  const defaultsFromPlugin =
    metadataUi.defaults && typeof metadataUi.defaults === 'object' ? metadataUi.defaults : {};

  const defaultsFromSchema = buildDefaultsFromSchema(schema);
  const baseDefaults = {
    ...defaultsFromSchema,
    ...defaultsFromPlugin,
  };

  const requiredKeys = schema
    .map((entry) => {
      if (!entry || typeof entry !== 'object') return null;
      const key = (entry as any).key;
      const required = Boolean((entry as any).required);
      if (!required) return null;
      return typeof key === 'string' && key.length > 0 ? key : null;
    })
    .filter((key): key is string => typeof key === 'string');

  const missingRequiredDefaults = requiredKeys.some((key) =>
    isMissingRequiredValue(baseDefaults[key]),
  );
  if (missingRequiredDefaults) {
    return true;
  }

  const prompt = metadataUi.prompt;
  return prompt === 'always';
}

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

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    overlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      justifyContent: 'center',
      alignItems: 'center',
    },
    content: {
      width: '90%',
      maxHeight: '80%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      paddingHorizontal: 16,
      paddingVertical: 12,
    },
    title: {
      fontSize: 16,
      fontWeight: '600',
      color: theme.text,
      marginBottom: 8,
      textAlign: 'center',
    },
    helperText: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.textSecondary,
      marginBottom: 8,
    },
    body: {
      flexGrow: 0,
      flexShrink: 1,
      marginVertical: 8,
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
    },
    itemLabelRow: {
      flexDirection: 'row',
      alignItems: 'center',
      flexWrap: 'wrap',
      marginBottom: 2,
    },
    itemLabelChipColumn: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      alignItems: 'center',
      flex: 1,
    },
    itemLabel: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '500',
      color: theme.text,
      marginBottom: 2,
      marginRight: 4,
    },
    itemDescription: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
    },
    tagConfig: {
      marginLeft: 8,
      paddingHorizontal: 6,
      paddingVertical: 2,
      borderRadius: 10,
      backgroundColor: theme.surfaceAlt,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
    },
    tagDefault: {
      marginLeft: 8,
      paddingHorizontal: 6,
      paddingVertical: 2,
      borderRadius: 10,
      backgroundColor: theme.surfaceAlt,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
    },
    tagTextConfig: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textSecondary,
    },
    tagTextDefault: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textSecondary,
    },
    chipsRow: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      marginTop: 6,
    },
    chip: {
      paddingHorizontal: 10,
      paddingVertical: 4,
      borderRadius: 12,
      borderWidth: 1,
      borderColor: theme.border,
      marginRight: 6,
      marginBottom: 4,
      backgroundColor: theme.surfaceAlt,
    },
    chipSelected: {
      paddingHorizontal: 10,
      paddingVertical: 4,
      borderRadius: 12,
      borderWidth: 1,
      backgroundColor: theme.primary,
      borderColor: theme.primary,
      marginRight: 6,
      marginBottom: 4,
    },
    chipText: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.text,
    },
    chipTextSelected: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textOnPrimary,
    },
    textRow: {
      flexDirection: 'row',
      alignItems: 'center',
      marginTop: 6,
    },
    textInput: {
      flex: 1,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 8,
      paddingVertical: 4,
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      marginRight: 8,
    },
    saveButton: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 8,
      backgroundColor: theme.primary,
    },
    saveButtonText: {
      color: theme.textOnPrimary,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '600',
    },
    controlSwitchColumn: {
      marginLeft: 8,
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'flex-start',
    },
    trashBeforeSwitch: {
      paddingHorizontal: 4,
      paddingVertical: 2,
      marginRight: 4,
    },
    trashRightOfLabel: {
      paddingHorizontal: 4,
      paddingVertical: 2,
      marginLeft: 4,
    },
    footerRow: {
      marginTop: 8,
      flexDirection: 'row',
      justifyContent: 'flex-end',
      gap: 8,
    },
    closeButton: {
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 8,
      backgroundColor: theme.surfaceAlt,
    },
    closeButtonText: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '600',
      color: theme.text,
    },
    saveAllButton: {
      backgroundColor: theme.primary,
    },
    saveAllButtonText: {
      color: theme.textOnPrimary,
    },
  });
