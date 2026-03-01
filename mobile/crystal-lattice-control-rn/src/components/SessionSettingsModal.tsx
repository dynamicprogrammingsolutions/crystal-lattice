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
  TouchableWithoutFeedback,
  View,
} from 'react-native';
import type { AgentBackend, SessionSettingsRefreshResult } from '@crystal-lattice/frontend-sdk';
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

import type { UiSchemaElement } from '../api';
import { useTheme, type Theme } from '../theme';

export interface SessionSettingsModalProps {
  backend: AgentBackend | null;
  sessionId: string;
  visible: boolean;
  onRequestClose: () => void;
  /** Called after overrides are successfully updated with refreshed session data (from SDK). Parent can apply it to controller/state without refetching. */
  onOverridesSaved?: (data: SessionSettingsRefreshResult) => void;
}

const SessionSettingsModal: React.FC<SessionSettingsModalProps> = ({
  backend,
  sessionId,
  visible,
  onRequestClose,
  onOverridesSaved,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elements, setElements] = useState<UiSchemaElement[]>([]);
  const [overrides, setOverrides] = useState<Record<string, any>>({});
  const [baseConfig, setBaseConfig] = useState<Record<string, any>>({});
  const [schemaByKey, setSchemaByKey] = useState<ConfigSchemaByKey>({});
  const [pendingTextByKey, setPendingTextByKey] = useState<Record<string, string>>({});
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [dropdownState, setDropdownState] = useState<{
    key: string;
    label: string;
    options: { value: string; label: string }[];
    selected: string;
  } | null>(null);
  const [dropdownSearch, setDropdownSearch] = useState('');

  const applyRefreshResult = useCallback((result: SessionSettingsRefreshResult) => {
    setElements(filterConfigUiSchemaElements(result.uiSchemaElements));
    setOverrides(result.overrides as Record<string, any>);
    setSchemaByKey(buildConfigSchemaByKey(result.configSchema));
    setBaseConfig(result.baseConfig || {});
    setPendingTextByKey({});
  }, []);

  useEffect(() => {
    if (!visible) {
      return;
    }
    if (!backend) {
      setError('No active connection');
      setElements([]);
      setOverrides({});
      setBaseConfig({});
      setSchemaByKey({});
      return;
    }
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [els, ovs, schema, baseCfg] = await Promise.all([
          backend.getSessionUiSchema(sessionId),
          backend.getSessionOverrides(sessionId),
          backend.getSessionConfigSchema(sessionId),
          backend.getSessionBaseConfig(sessionId),
        ]);
        if (cancelled) return;
        setElements(filterConfigUiSchemaElements(els || []));
        setOverrides(ovs || {});
        setSchemaByKey(buildConfigSchemaByKey(schema || []));
        setBaseConfig(baseCfg || {});
        setPendingTextByKey({});
      } catch (err: any) {
        if (cancelled) return;
        console.log('Failed to load session settings', err);
        const msg = err?.message || 'Failed to load session settings.';
        setError(msg);
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [backend, sessionId, visible]);

  const handleToggleCheckbox = async (key: string, next: boolean) => {
    if (!backend) {
      Alert.alert('No connection', 'Connect to a server to change settings.');
      return;
    }
    setOverrides((prev) => ({ ...prev, [key]: next }));
    try {
      const result = await backend.patchSessionOverridesAndRefresh(sessionId, { [key]: next });
      applyRefreshResult(result);
      onOverridesSaved?.(result);
    } catch (err: any) {
      console.log('Failed to update checkbox setting', err);
      const msg = err?.message || 'Failed to update setting.';
      Alert.alert('Error', msg);
      setOverrides((prev) => ({ ...prev, [key]: !next }));
    }
  };

  const handleSelectOption = async (key: string, value: string) => {
    if (!backend) {
      Alert.alert('No connection', 'Connect to a server to change settings.');
      return;
    }
    setOverrides((prev) => ({ ...prev, [key]: value }));
    try {
      const result = await backend.patchSessionOverridesAndRefresh(sessionId, { [key]: value });
      applyRefreshResult(result);
      onOverridesSaved?.(result);
    } catch (err: any) {
      console.log('Failed to update select setting', err);
      const msg = err?.message || 'Failed to update setting.';
      Alert.alert('Error', msg);
    }
  };

  const handleSaveText = async (key: string) => {
    if (!backend) {
      Alert.alert('No connection', 'Connect to a server to change settings.');
      return;
    }
    const value = pendingTextByKey[key] ?? String(overrides[key] ?? '');
    setSavingKey(key);
    try {
      const result = await backend.patchSessionOverridesAndRefresh(sessionId, { [key]: value });
      applyRefreshResult(result);
      onOverridesSaved?.(result);
    } catch (err: any) {
      console.log('Failed to update text setting', err);
      const msg = err?.message || 'Failed to update setting.';
      Alert.alert('Error', msg);
    } finally {
      setSavingKey((current) => (current === key ? null : current));
    }
  };

  const handleRevertToDefault = async (key: string) => {
    if (!backend) {
      Alert.alert('No connection', 'Connect to a server to change settings.');
      return;
    }
    const prevOverrides = overrides;
    const prevPending = pendingTextByKey;
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
    try {
      const result = await backend.deleteSessionOverrideAndRefresh(sessionId, key);
      applyRefreshResult(result);
      onOverridesSaved?.(result);
    } catch (err: any) {
      console.log('Failed to revert setting override', err);
      const msg = err?.message || 'Failed to revert setting.';
      Alert.alert('Error', msg);
      setOverrides(prevOverrides);
      setPendingTextByKey(prevPending);
    }
  };

  if (!visible) {
    return null;
  }

  const items = buildSessionSettingItems({
    elements,
    overrides,
    baseConfig,
    schemaByKey,
  });

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
        <View style={styles.itemRow}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <View style={styles.itemLabelChipColumn}>
                <Text style={styles.itemLabel}>{item.label}</Text>
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
                >
                  <Icon name="trash-2" size={14} color={theme.danger} />
                </TouchableOpacity>
              )}
            </View>
            {item.description ? (
              <Text style={styles.itemDescription}>{item.description}</Text>
            ) : null}
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
              <Text style={styles.itemDescription}>{item.description}</Text>
            ) : null}
          </View>
          <View style={styles.controlSwitchColumn}>
            <Switch
              value={boolValue}
              onValueChange={(next) => ctx.actions.toggleCheckbox(item.key, next)}
            />
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
                >
                  <Icon name="trash-2" size={14} color={theme.danger} />
                </TouchableOpacity>
              )}
            </View>
            {item.description ? (
              <Text style={styles.itemDescription}>{item.description}</Text>
            ) : null}
            <View style={styles.chipsRow}>
              {options.map((opt) => {
                const isSelected = opt.value === selected;
                return (
                  <TouchableOpacity
                    key={opt.value}
                    style={isSelected ? styles.chipSelected : styles.chip}
                    onPress={() => ctx.actions.selectOption(item.key, opt.value)}
                  >
                    <Text
                      style={
                        isSelected ? styles.chipTextSelected : styles.chipText
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
        <View style={styles.itemRow}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <View style={styles.itemLabelChipColumn}>
                <Text style={styles.itemLabel}>{item.label}</Text>
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
                >
                  <Icon name="trash-2" size={14} color={theme.danger} />
                </TouchableOpacity>
              )}
            </View>
            {item.description ? (
              <Text style={styles.itemDescription}>{item.description}</Text>
            ) : null}
            <TouchableOpacity
              style={styles.dropdownButton}
              onPress={() => {
                setDropdownState({
                  key: item.key,
                  label: item.label,
                  options,
                  selected,
                });
                setDropdownSearch('');
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
          {loading && (
            <View style={styles.loadingRow}>
              <ActivityIndicator size="small" color={theme.primary} />
              <Text style={styles.loadingText}>Loading settings...</Text>
            </View>
          )}
          {!loading && error && <Text style={styles.errorText}>{error}</Text>}
          {!loading && !error && items.length === 0 && (
            <Text style={styles.helperText}>
              No configurable settings are available for this session.
            </Text>
          )}
          {!loading && !error && items.length > 0 && (
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
      {dropdownState && (
        <Modal
          visible
          transparent
          animationType="fade"
          onRequestClose={() => {
            setDropdownState(null);
            setDropdownSearch('');
          }}
        >
          <TouchableWithoutFeedback
            onPress={() => {
              setDropdownState(null);
              setDropdownSearch('');
            }}
          >
            <View style={styles.dropdownModalOverlay}>
              <TouchableWithoutFeedback onPress={() => {}}>
                <View style={styles.dropdownModalContent}>
                  <TextInput
                    style={styles.dropdownModalSearch}
                    placeholder="Search..."
                    placeholderTextColor={theme.textSecondary}
                    value={dropdownSearch}
                    onChangeText={setDropdownSearch}
                    autoCapitalize="none"
                    autoCorrect={false}
                  />
                  <ScrollView style={styles.dropdownModalList}>
                    {dropdownState.options
                      .filter((opt) => {
                        const q = dropdownSearch.trim().toLowerCase();
                        if (!q) return true;
                        const text = `${opt.label ?? ''} ${opt.value ?? ''}`.toLowerCase();
                        return text.includes(q);
                      })
                      .map((opt) => (
                        <TouchableOpacity
                          key={opt.value}
                          style={styles.dropdownModalItem}
                          onPress={() => {
                            handleSelectOption(dropdownState.key, opt.value);
                            setDropdownState(null);
                            setDropdownSearch('');
                          }}
                        >
                          <Text
                            style={styles.dropdownModalItemText}
                            numberOfLines={2}
                          >
                            {opt.label}
                          </Text>
                        </TouchableOpacity>
                      ))}
                  </ScrollView>
                  <TouchableOpacity
                    style={[styles.button, styles.secondaryButton, styles.dropdownModalButton]}
                    onPress={() => {
                      setDropdownState(null);
                      setDropdownSearch('');
                    }}
                  >
                    <Text style={styles.buttonTextSecondary}>Cancel</Text>
                  </TouchableOpacity>
                </View>
              </TouchableWithoutFeedback>
            </View>
          </TouchableWithoutFeedback>
        </Modal>
      )}
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
    loadingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 8,
    },
    loadingText: {
      marginLeft: 8,
      fontSize: 14,
      color: theme.textSecondary,
    },
    errorText: {
      fontSize: 14,
      color: theme.danger,
      marginBottom: 8,
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
    itemDescription: {
      fontSize: 12,
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
    chipText: {
      fontSize: 12,
      color: theme.text,
    },
    chipTextSelected: {
      fontSize: 12,
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
      fontSize: 14,
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
      fontSize: 14,
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
    dropdownModalOverlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      justifyContent: 'center',
      alignItems: 'center',
    },
    dropdownModalContent: {
      width: '85%',
      maxHeight: '70%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 16,
    },
    dropdownModalSearch: {
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      fontSize: 14,
      color: theme.text,
      backgroundColor: theme.surface,
      marginBottom: 8,
    },
    dropdownModalList: {
      maxHeight: 320,
      marginVertical: 8,
    },
    dropdownModalItem: {
      paddingVertical: 12,
      paddingHorizontal: 8,
      borderBottomWidth: 1,
      borderBottomColor: theme.border,
    },
    dropdownModalItemText: {
      fontSize: 14,
      color: theme.text,
    },
    dropdownModalButton: {
      marginTop: 8,
      alignSelf: 'flex-end',
    },
    button: {
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: 8,
    },
    secondaryButton: {
      backgroundColor: theme.surfaceAlt,
    },
    buttonTextSecondary: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.text,
    },
  });
