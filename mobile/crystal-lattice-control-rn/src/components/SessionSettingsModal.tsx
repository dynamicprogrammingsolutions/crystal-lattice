import React, { useCallback, useEffect, useMemo, useState } from 'react';
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
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import {
  buildConfigSchemaByKey,
  buildSessionSettingItems,
  SessionSettingsHost,
  useSessionSettingsController,
  type SessionSettingRenderCtx,
  type SessionSettingsRenderers,
} from '@crystal-lattice/frontend-sdk-react';
import Icon from 'react-native-vector-icons/Feather';

import OptionsPickerModal from './OptionsPickerModal';
import { useTheme, type Theme } from '../theme';

export interface SessionSettingsModalProps {
  backend: AgentBackend | null;
  cacheKey?: string;
  sessionId: string;
  visible: boolean;
  onRequestClose: () => void;
}

const SessionSettingsModal: React.FC<SessionSettingsModalProps> = ({
  backend,
  cacheKey = 'default',
  sessionId,
  visible,
  onRequestClose,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const [pendingTextByKey, setPendingTextByKey] = useState<Record<string, string>>({});
  const [dropdownState, setDropdownState] = useState<{
    key: string;
    label: string;
    options: { value: string; label: string }[];
    selected: string;
  } | null>(null);

  const controllerSessionId = visible ? sessionId : null;
  const { controller, state: settingsState } = useSessionSettingsController({
    backend,
    cacheKey,
    sessionId: controllerSessionId,
    enabled: visible,
  });
  const elements = settingsState?.elements ?? [];
  const schemaByKey = useMemo(
    () => buildConfigSchemaByKey(settingsState?.configSchema || []),
    [settingsState?.configSchema],
  );
  const savingKeys = settingsState?.savingKeys ?? [];
  const savingKeySet = useMemo(() => new Set(savingKeys), [savingKeys]);

  useEffect(() => {
    if (!visible) {
      setPendingTextByKey({});
      setDropdownState(null);
      return;
    }
    setPendingTextByKey({});
    setDropdownState(null);
  }, [sessionId, visible]);

  const items = useMemo(() => {
    return buildSessionSettingItems({
      elements,
      overrides: settingsState?.overrides || {},
      baseConfig: settingsState?.baseConfig || {},
      schemaByKey,
    });
  }, [elements, schemaByKey, settingsState?.baseConfig, settingsState?.overrides]);

  const itemByKey = useMemo(() => {
    const byKey: Record<string, (typeof items)[number]> = {};
    items.forEach((item) => {
      byKey[item.key] = item;
    });
    return byKey;
  }, [items]);

  useEffect(() => {
    const allowedKeys = new Set(items.map((item) => item.key));
    setPendingTextByKey((prev) => {
      const next: Record<string, string> = {};
      let changed = false;
      Object.entries(prev).forEach(([key, value]) => {
        if (allowedKeys.has(key)) {
          next[key] = value;
          return;
        }
        changed = true;
      });
      return changed ? next : prev;
    });
    setDropdownState((current) => {
      if (!current || allowedKeys.has(current.key)) {
        return current;
      }
      return null;
    });
  }, [items]);

  const handleToggleCheckbox = async (key: string, next: boolean) => {
    if (itemByKey[key]?.disabled) {
      return;
    }
    if (!controller) {
      Alert.alert('No connection', 'Connect to a server to change settings.');
      return;
    }
    try {
      await controller.patchOverride(key, next);
    } catch {
      // Controller state captures errors.
    }
  };

  const handleSelectOption = async (key: string, value: string) => {
    if (itemByKey[key]?.disabled) {
      return;
    }
    if (!controller) {
      Alert.alert('No connection', 'Connect to a server to change settings.');
      return;
    }
    try {
      await controller.patchOverride(key, value);
    } catch {
      // Controller state captures errors.
    }
  };

  const handleSaveText = async (key: string) => {
    if (itemByKey[key]?.disabled) {
      return;
    }
    if (!controller) {
      Alert.alert('No connection', 'Connect to a server to change settings.');
      return;
    }
    const currentEffective = itemByKey[key]?.effectiveValue;
    const value =
      pendingTextByKey[key] ??
      (currentEffective !== undefined && currentEffective !== null
        ? String(currentEffective)
        : '');
    try {
      await controller.patchOverride(key, value);
    } catch {
      // Controller state captures errors.
    }
  };

  const handleRevertToDefault = async (key: string) => {
    if (itemByKey[key]?.disabled) {
      return;
    }
    if (!controller) {
      Alert.alert('No connection', 'Connect to a server to change settings.');
      return;
    }
    setPendingTextByKey((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
    try {
      await controller.deleteOverride(key);
    } catch {
      // Controller state captures errors.
    }
  };

  if (!visible) {
    return null;
  }

  const normalizeOptions = (raw: any): { value: string; label: string }[] => {
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
        <View style={[styles.itemRow, item.disabled && styles.itemRowDisabled]}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <View style={styles.itemLabelChipColumn}>
                <Text style={[styles.itemLabel, item.disabled && styles.itemLabelDisabled]}>
                  {item.label}
                </Text>
                {item.tagLabel && (
                  <View
                    style={
                      item.tagLabel === 'config'
                        ? styles.tagConfig
                        : styles.tagDefault
                    }
                  >
                    <Text
                      style={
                        item.tagLabel === 'config'
                          ? styles.tagTextConfig
                          : styles.tagTextDefault
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
                  disabled={item.disabled}
                >
                  <Icon name="trash-2" size={14} color={theme.danger} />
                </TouchableOpacity>
              )}
            </View>
            {item.description ? (
              <Text style={[styles.itemDescription, item.disabled && styles.itemDescriptionDisabled]}>
                {item.description}
              </Text>
            ) : null}
            <View style={styles.textRow}>
              <TextInput
                style={[styles.textInput, item.disabled && styles.textInputDisabled]}
                value={textValue}
                editable={!item.disabled}
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
                style={[styles.saveButton, item.disabled && styles.saveButtonDisabled]}
                onPress={() => ctx.actions.saveText(key)}
                disabled={savingKeySet.has(key) || item.disabled}
              >
                {savingKeySet.has(key) ? (
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
    readonly: (ctx: SessionSettingRenderCtx) => {
      const { item } = ctx;
      const value =
        item.effectiveValue !== undefined && item.effectiveValue !== null
          ? String(item.effectiveValue)
          : '';

      return (
        <View style={[styles.itemRow, item.disabled && styles.itemRowDisabled]}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <View style={styles.itemLabelChipColumn}>
                <Text style={[styles.itemLabel, item.disabled && styles.itemLabelDisabled]}>
                  {item.label}
                </Text>
                {item.tagLabel && (
                  <View
                    style={
                      item.tagLabel === 'config'
                        ? styles.tagConfig
                        : styles.tagDefault
                    }
                  >
                    <Text
                      style={
                        item.tagLabel === 'config'
                          ? styles.tagTextConfig
                          : styles.tagTextDefault
                      }
                    >
                      {item.tagLabel}
                    </Text>
                  </View>
                )}
              </View>
            </View>
            {item.description ? (
              <Text style={[styles.itemDescription, item.disabled && styles.itemDescriptionDisabled]}>
                {item.description}
              </Text>
            ) : null}
            <View style={styles.readonlyValueBox}>
              <Text style={styles.readonlyValueText}>{value || 'Not set'}</Text>
            </View>
          </View>
        </View>
      );
    },
    checkbox: (ctx: SessionSettingRenderCtx) => {
      const { item } = ctx;
      const boolValue = Boolean(item.effectiveValue ?? false);
      return (
        <View style={[styles.itemRow, item.disabled && styles.itemRowDisabled]}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <View style={styles.itemLabelChipColumn}>
                <Text style={[styles.itemLabel, item.disabled && styles.itemLabelDisabled]}>
                  {item.label}
                </Text>
                {item.tagLabel && (
                  <View
                    style={
                      item.tagLabel === 'config'
                        ? styles.tagConfig
                        : styles.tagDefault
                    }
                  >
                    <Text
                      style={
                        item.tagLabel === 'config'
                          ? styles.tagTextConfig
                          : styles.tagTextDefault
                      }
                    >
                      {item.tagLabel}
                    </Text>
                  </View>
                )}
              </View>
            </View>
            {item.description ? (
              <Text style={[styles.itemDescription, item.disabled && styles.itemDescriptionDisabled]}>
                {item.description}
              </Text>
            ) : null}
          </View>
          <View style={styles.controlSwitchColumn}>
            <Switch
              value={boolValue}
              disabled={item.disabled}
              onValueChange={(next) => ctx.actions.toggleCheckbox(item.key, next)}
            />
            {item.hasOverride && (
              <TouchableOpacity
                style={styles.trashBeforeSwitch}
                onPress={() => ctx.actions.revertToDefault(item.key)}
                disabled={item.disabled}
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
        <View style={[styles.itemRow, item.disabled && styles.itemRowDisabled]}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <View style={styles.itemLabelChipColumn}>
                <Text style={[styles.itemLabel, item.disabled && styles.itemLabelDisabled]}>
                  {item.label}
                </Text>
                {item.tagLabel && (
                  <View
                    style={
                      item.tagLabel === 'config'
                        ? styles.tagConfig
                        : styles.tagDefault
                    }
                  >
                    <Text
                      style={
                        item.tagLabel === 'config'
                          ? styles.tagTextConfig
                          : styles.tagTextDefault
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
                  disabled={item.disabled}
                >
                  <Icon name="trash-2" size={14} color={theme.danger} />
                </TouchableOpacity>
              )}
            </View>
            {item.description ? (
              <Text style={[styles.itemDescription, item.disabled && styles.itemDescriptionDisabled]}>
                {item.description}
              </Text>
            ) : null}
            <View style={styles.chipsRow}>
              {options.map((opt) => {
                const isSelected = opt.value === selected;
                return (
                  <TouchableOpacity
                    key={opt.value}
                    style={[
                      isSelected ? styles.chipSelected : styles.chip,
                      item.disabled && styles.chipDisabled,
                    ]}
                    onPress={() => ctx.actions.selectOption(item.key, opt.value)}
                    disabled={item.disabled}
                  >
                    <Text
                      style={
                        item.disabled
                          ? styles.chipTextDisabled
                          : isSelected
                            ? styles.chipTextSelected
                            : styles.chipText
                      }
                    >
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
    dropdown: (ctx: SessionSettingRenderCtx) => {
      const { item } = ctx;
      const options = normalizeOptions((item.element as any).options);
      if (!options.length) {
        return null;
      }
      const selected =
        typeof item.effectiveValue === 'string'
          ? item.effectiveValue
          : String(item.effectiveValue ?? '');
      const selectedLabel =
        options.find((o) => o.value === selected)?.label ?? selected;
      return (
        <View style={[styles.itemRow, item.disabled && styles.itemRowDisabled]}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <View style={styles.itemLabelChipColumn}>
                <Text style={[styles.itemLabel, item.disabled && styles.itemLabelDisabled]}>
                  {item.label}
                </Text>
                {item.tagLabel && (
                  <View
                    style={
                      item.tagLabel === 'config'
                        ? styles.tagConfig
                        : styles.tagDefault
                    }
                  >
                    <Text
                      style={
                        item.tagLabel === 'config'
                          ? styles.tagTextConfig
                          : styles.tagTextDefault
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
                  disabled={item.disabled}
                >
                  <Icon name="trash-2" size={14} color={theme.danger} />
                </TouchableOpacity>
              )}
            </View>
            {item.description ? (
              <Text style={[styles.itemDescription, item.disabled && styles.itemDescriptionDisabled]}>
                {item.description}
              </Text>
            ) : null}
            <TouchableOpacity
              style={[styles.dropdownButton, item.disabled && styles.dropdownButtonDisabled]}
              disabled={item.disabled}
              onPress={() => {
                setDropdownState({
                  key: item.key,
                  label: item.label,
                  options,
                  selected,
                });
              }}
            >
              <Text style={styles.dropdownButtonLabel} numberOfLines={1}>
                {item.label}:
              </Text>
              <Text style={styles.dropdownButtonValue} numberOfLines={1}>
                {selectedLabel}
              </Text>
              <Icon name="chevron-down" size={14} color={theme.textSecondary} />
            </TouchableOpacity>
          </View>
        </View>
      );
    },
    text: renderTextLike,
    multiline: renderTextLike,
  };

  const error = !backend ? 'No active connection' : settingsState?.error ?? null;
  const statusText = error || settingsState?.statusMessage;
  const statusTone = error ? 'error' : settingsState?.statusTone ?? 'idle';
  const showSpinner = !error && statusTone === 'busy';
  const hasLoaded = settingsState?.lastLoadedAt != null;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onRequestClose}
    >
      <View style={styles.overlay}>
        <Pressable style={StyleSheet.absoluteFill} onPress={onRequestClose} />
        <View style={styles.content}>
          <Text style={styles.title}>Session settings</Text>
          <View style={styles.statusLine}>
            {showSpinner ? <ActivityIndicator size="small" color={theme.primary} /> : null}
            {statusText ? (
              <Text
                style={[
                  styles.statusText,
                  statusTone === 'error'
                    ? styles.statusTextError
                    : statusTone === 'success'
                      ? styles.statusTextSuccess
                      : null,
                ]}
                numberOfLines={1}
              >
                {statusText}
              </Text>
            ) : null}
          </View>
          {!error && hasLoaded && items.length === 0 && (
            <Text style={styles.helperText}>
              No configurable settings are available for this session.
            </Text>
          )}
          {!error && items.length > 0 && (
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
                renderFrame={({ children }) => <ScrollView style={styles.list}>{children}</ScrollView>}
              />
            </View>
          )}
          <View style={styles.footerRow}>
            <TouchableOpacity style={styles.closeButton} onPress={onRequestClose}>
              <Text style={styles.closeButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
      <OptionsPickerModal
        visible={!!dropdownState}
        options={dropdownState?.options ?? []}
        onSelect={(value) => {
          if (dropdownState) {
            handleSelectOption(dropdownState.key, value);
            setDropdownState(null);
          }
        }}
        onRequestClose={() => setDropdownState(null)}
      />
    </Modal>
  );
};

export default SessionSettingsModal;

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
    statusLine: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 8,
      minHeight: 20,
    },
    statusText: {
      marginLeft: 8,
      fontSize: 14,
      color: theme.textSecondary,
    },
    statusTextError: {
      color: theme.danger,
    },
    statusTextSuccess: {
      color: theme.primary,
    },
    helperText: {
      fontSize: 14,
      color: theme.textSecondary,
      marginBottom: 8,
    },
    body: {
      flexGrow: 0,
      flexShrink: 1,

    },
    list: {
      flexGrow: 0,
      flexShrink: 1,
      marginVertical: 8,
    },
    itemRow: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      paddingVertical: 6,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.border,
    },
    itemRowDisabled: {
      opacity: 0.65,
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
      fontSize: 14,
      fontWeight: '500',
      color: theme.text,
      marginBottom: 2,
      marginRight: 4,
    },
    itemLabelDisabled: {
      color: theme.textSecondary,
    },
    itemDescription: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    itemDescriptionDisabled: {
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
      fontSize: 10,
      color: theme.textSecondary,
    },
    tagTextDefault: {
      fontSize: 10,
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
    chipDisabled: {
      backgroundColor: theme.surfaceAlt,
      borderColor: theme.border,
    },
    chipText: {
      fontSize: 12,
      color: theme.text,
    },
    chipTextSelected: {
      fontSize: 12,
      color: theme.textOnPrimary,
    },
    chipTextDisabled: {
      fontSize: 12,
      color: theme.textSecondary,
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
      fontSize: 14,
      marginRight: 8,
    },
    textInputDisabled: {
      backgroundColor: theme.surfaceAlt,
      color: theme.textSecondary,
    },
    saveButton: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 8,
      backgroundColor: theme.primary,
    },
    saveButtonDisabled: {
      backgroundColor: theme.surfaceAlt,
    },
    saveButtonText: {
      color: theme.textOnPrimary,
      fontSize: 14,
      fontWeight: '600',
    },
    dropdownButtonDisabled: {
      backgroundColor: theme.surfaceAlt,
      borderColor: theme.border,
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
    },
    closeButton: {
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 8,
      backgroundColor: theme.surfaceAlt,
    },
    closeButtonText: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.text,
    },
    dropdownButton: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 8,
      paddingHorizontal: 10,
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      gap: 6,
      marginTop: 6,
    },
    dropdownButtonLabel: {
      fontSize: 14,
      color: theme.textSecondary,
    },
    dropdownButtonValue: {
      flex: 1,
      fontSize: 14,
      color: theme.text,
    },
    readonlyValueBox: {
      marginTop: 6,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      backgroundColor: theme.surfaceAlt,
    },
    readonlyValueText: {
      fontSize: 14,
      color: theme.text,
    },
  });
