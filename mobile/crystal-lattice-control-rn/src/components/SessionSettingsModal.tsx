import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Modal,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  TouchableWithoutFeedback,
  View,
} from 'react-native';
import type { ConnectionAdapter } from '../../App';
import {
  apiGetSessionOverrides,
  apiGetSessionUiElements,
  apiPatchSessionOverrides,
  type UiConfigElement,
} from '../api';
import { useTheme, type Theme } from '../theme';

export interface SessionSettingsModalProps {
  adapter: ConnectionAdapter | null;
  sessionId: string;
  visible: boolean;
  onRequestClose: () => void;
}

const SessionSettingsModal: React.FC<SessionSettingsModalProps> = ({
  adapter,
  sessionId,
  visible,
  onRequestClose,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elements, setElements] = useState<UiConfigElement[]>([]);
  const [overrides, setOverrides] = useState<Record<string, any>>({});
  const [pendingTextByKey, setPendingTextByKey] = useState<Record<string, string>>({});
  const [savingKey, setSavingKey] = useState<string | null>(null);

  useEffect(() => {
    if (!visible) {
      return;
    }
    if (!adapter) {
      setError('No active connection');
      setElements([]);
      setOverrides({});
      return;
    }
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [els, ovs] = await Promise.all([
          apiGetSessionUiElements(adapter, sessionId),
          apiGetSessionOverrides(adapter, sessionId),
        ]);
        if (cancelled) return;
        setElements(Array.isArray(els) ? els : []);
        setOverrides(ovs || {});
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
  }, [adapter, sessionId, visible]);

  const handleToggleCheckbox = async (key: string, next: boolean) => {
    if (!adapter) {
      Alert.alert('No connection', 'Connect to a server to change settings.');
      return;
    }
    setOverrides((prev) => ({ ...prev, [key]: next }));
    try {
      await apiPatchSessionOverrides(adapter, sessionId, { [key]: next });
    } catch (err: any) {
      console.log('Failed to update checkbox setting', err);
      const msg = err?.message || 'Failed to update setting.';
      Alert.alert('Error', msg);
      setOverrides((prev) => ({ ...prev, [key]: !next }));
    }
  };

  const handleSelectOption = async (key: string, value: string) => {
    if (!adapter) {
      Alert.alert('No connection', 'Connect to a server to change settings.');
      return;
    }
    setOverrides((prev) => ({ ...prev, [key]: value }));
    try {
      await apiPatchSessionOverrides(adapter, sessionId, { [key]: value });
    } catch (err: any) {
      console.log('Failed to update select setting', err);
      const msg = err?.message || 'Failed to update setting.';
      Alert.alert('Error', msg);
    }
  };

  const handleSaveText = async (key: string) => {
    if (!adapter) {
      Alert.alert('No connection', 'Connect to a server to change settings.');
      return;
    }
    const value = pendingTextByKey[key] ?? String(overrides[key] ?? '');
    setSavingKey(key);
    try {
      await apiPatchSessionOverrides(adapter, sessionId, { [key]: value });
      setOverrides((prev) => ({ ...prev, [key]: value }));
    } catch (err: any) {
      console.log('Failed to update text setting', err);
      const msg = err?.message || 'Failed to update setting.';
      Alert.alert('Error', msg);
    } finally {
      setSavingKey((current) => (current === key ? null : current));
    }
  };

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

  const renderElement = (el: UiConfigElement) => {
    if (!el || typeof el !== 'object') return null;
    if (typeof el.key !== 'string' || !el.key) return null;
    const key = el.key;
    const type = typeof el.type === 'string' ? el.type : undefined;
    const label = typeof el.label === 'string' && el.label ? el.label : key;
    const description = typeof el.description === 'string' ? el.description : '';
    const currentValue = overrides[key];

    if (type === 'checkbox') {
      const boolValue = Boolean(currentValue ?? false);
      return (
        <View key={key} style={styles.itemRow}>
          <View style={styles.itemTextColumn}>
            <Text style={styles.itemLabel}>{label}</Text>
            {description ? <Text style={styles.itemDescription}>{description}</Text> : null}
          </View>
          <Switch
            value={boolValue}
            onValueChange={(next) => handleToggleCheckbox(key, next)}
          />
        </View>
      );
    }

    if (type === 'select') {
      const options = normalizeOptions(el.options);
      if (!options.length) return null;
      const selected = typeof currentValue === 'string' ? currentValue : String(currentValue ?? '');
      return (
        <View key={key} style={styles.itemRow}>
          <View style={styles.itemTextColumn}>
            <Text style={styles.itemLabel}>{label}</Text>
            {description ? <Text style={styles.itemDescription}>{description}</Text> : null}
            <View style={styles.chipsRow}>
              {options.map((opt) => {
                const isSelected = opt.value === selected;
                return (
                  <TouchableOpacity
                    key={opt.value}
                    style={isSelected ? styles.chipSelected : styles.chip}
                    onPress={() => handleSelectOption(key, opt.value)}
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
    }

    const textValue =
      key in pendingTextByKey
        ? pendingTextByKey[key]
        : currentValue !== undefined && currentValue !== null
          ? String(currentValue)
          : '';

    return (
      <View key={key} style={styles.itemRow}>
        <View style={styles.itemTextColumn}>
          <Text style={styles.itemLabel}>{label}</Text>
          {description ? <Text style={styles.itemDescription}>{description}</Text> : null}
          <View style={styles.textRow}>
            <TextInput
              style={styles.textInput}
              value={textValue}
              onChangeText={(txt) =>
                setPendingTextByKey((prev) => ({ ...prev, [key]: txt }))
              }
              placeholder="Enter value"
              placeholderTextColor={theme.textSecondary}
            />
            <TouchableOpacity
              style={styles.saveButton}
              onPress={() => handleSaveText(key)}
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

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onRequestClose}
    >
      <TouchableWithoutFeedback onPress={onRequestClose}>
        <View style={styles.overlay}>
          <TouchableWithoutFeedback onPress={() => {}}>
            <View style={styles.content}>
              <Text style={styles.title}>Session settings</Text>
              {loading && (
                <View style={styles.loadingRow}>
                  <ActivityIndicator size="small" color={theme.primary} />
                  <Text style={styles.loadingText}>Loading settings...</Text>
                </View>
              )}
              {!loading && error && (
                <Text style={styles.errorText}>{error}</Text>
              )}
              {!loading && !error && elements.length === 0 && (
                <Text style={styles.helperText}>
                  No configurable settings are available for this session.
                </Text>
              )}
              {!loading && !error && elements.length > 0 && (
                <ScrollView style={styles.list}>{elements.map(renderElement)}</ScrollView>
              )}
              <View style={styles.footerRow}>
                <TouchableOpacity
                  style={styles.closeButton}
                  onPress={onRequestClose}
                >
                  <Text style={styles.closeButtonText}>Close</Text>
                </TouchableOpacity>
              </View>
            </View>
          </TouchableWithoutFeedback>
        </View>
      </TouchableWithoutFeedback>
    </Modal>
  );
};

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
    list: {
      maxHeight: 320,
      marginVertical: 8,
    },
    itemRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingVertical: 6,
      borderBottomWidth: StyleSheet.hairlineWidth,
      borderBottomColor: theme.border,
    },
    itemTextColumn: {
      flex: 1,
      marginRight: 8,
    },
    itemLabel: {
      fontSize: 14,
      fontWeight: '500',
      color: theme.text,
      marginBottom: 2,
    },
    itemDescription: {
      fontSize: 12,
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
      borderColor: theme.primary,
      marginRight: 6,
      marginBottom: 4,
      backgroundColor: theme.primary,
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
  });

export default SessionSettingsModal;
