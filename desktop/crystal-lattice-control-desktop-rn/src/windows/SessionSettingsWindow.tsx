import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';

import { ThemeProvider, useTheme } from '@crystal-lattice/frontend-rn-components';
import type { UiSchemaElement } from '@crystal-lattice/frontend-sdk';
import {
  buildConfigSchemaByKey,
  buildSessionSettingItems,
  filterConfigUiSchemaElements,
  SessionSettingsHost,
  type ConfigSchemaByKey,
  type SessionSettingItem,
  type SessionSettingRenderCtx,
  type SessionSettingsRenderers,
} from '@crystal-lattice/frontend-sdk-react';
import Icon from 'react-native-vector-icons/Feather';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { useActiveSessionSettingsWindow } from './sessionSettingsCoordinator';

export function SessionSettingsWindow(): React.JSX.Element {
  const systemTheme = useDesktopTheme();
  return (
    <ThemeProvider theme={systemTheme}>
      <SessionSettingsWindowInner />
    </ThemeProvider>
  );
}

function SessionSettingsWindowInner(): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const active = useActiveSessionSettingsWindow();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elements, setElements] = useState<UiSchemaElement[]>([]);
  const [overrides, setOverrides] = useState<Record<string, any>>({});
  const [baseConfig, setBaseConfig] = useState<Record<string, any>>({});
  const [schemaByKey, setSchemaByKey] = useState<ConfigSchemaByKey>({});
  const [pendingTextByKey, setPendingTextByKey] = useState<Record<string, string>>({});
  const [savingKey, setSavingKey] = useState<string | null>(null);

  const items = useMemo(() => {
    return buildSessionSettingItems({
      elements,
      overrides,
      baseConfig,
      schemaByKey,
    });
  }, [baseConfig, elements, overrides, schemaByKey]);

  const itemByKey = useMemo(() => {
    const byKey: Record<string, SessionSettingItem> = {};
    items.forEach((item) => {
      byKey[item.key] = item;
    });
    return byKey;
  }, [items]);

  useEffect(() => {
    if (!active) {
      setLoading(false);
      setError(null);
      setElements([]);
      setOverrides({});
      setBaseConfig({});
      setSchemaByKey({});
      setPendingTextByKey({});
      setSavingKey(null);
      return;
    }

    const backend = active.state.backend;
    const sessionId = active.state.sessionId;

    const caps = backend.getCapabilities?.();
    if (caps && (!caps.sessionUiSchema || !caps.sessionConfigOverrides)) {
      setLoading(false);
      setError('This backend does not support session settings.');
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

        if (cancelled) {
          return;
        }

        const configElements = filterConfigUiSchemaElements(els || []);
        setElements(configElements);
        setOverrides(ovs || {});
        setSchemaByKey(buildConfigSchemaByKey(schema || []));
        setBaseConfig(baseCfg || {});
        setPendingTextByKey({});
      } catch (err: any) {
        console.log('Failed to load session settings', err);
        const message = err?.message || 'Failed to load session settings.';
        if (!cancelled) {
          setError(message);
        }
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
  }, [active]);

  const handleToggleCheckbox = useCallback(
    async (key: string, next: boolean) => {
      if (!active) {
        return;
      }

      const backend = active.state.backend;
      const sessionId = active.state.sessionId;

      setOverrides((prev) => ({ ...prev, [key]: next }));
      try {
        await backend.patchSessionOverrides(sessionId, { [key]: next });
      } catch (err: any) {
        console.log('Failed to update checkbox setting', err);
        const message = err?.message || 'Failed to update setting.';
        Alert.alert('Error', message);
        setOverrides((prev) => ({ ...prev, [key]: !next }));
      }
    },
    [active],
  );

  const handleSelectOption = useCallback(
    async (key: string, value: string) => {
      if (!active) {
        return;
      }

      const backend = active.state.backend;
      const sessionId = active.state.sessionId;

      setOverrides((prev) => ({ ...prev, [key]: value }));
      try {
        await backend.patchSessionOverrides(sessionId, { [key]: value });
      } catch (err: any) {
        console.log('Failed to update select setting', err);
        const message = err?.message || 'Failed to update setting.';
        Alert.alert('Error', message);
      }
    },
    [active],
  );

  const handleSaveText = useCallback(
    async (key: string) => {
      if (!active) {
        return;
      }

      const backend = active.state.backend;
      const sessionId = active.state.sessionId;
      const hasPending = Object.prototype.hasOwnProperty.call(pendingTextByKey, key);
      const pending = hasPending ? pendingTextByKey[key] : undefined;
      const currentEffective = itemByKey[key]?.effectiveValue;
      const value =
        pending ??
        (currentEffective !== undefined && currentEffective !== null
          ? String(currentEffective)
          : '');

      setSavingKey(key);
      try {
        await backend.patchSessionOverrides(sessionId, { [key]: value });
        setOverrides((prev) => ({ ...prev, [key]: value }));
      } catch (err: any) {
        console.log('Failed to update text setting', err);
        const message = err?.message || 'Failed to update setting.';
        Alert.alert('Error', message);
      } finally {
        setSavingKey((current) => (current === key ? null : current));
      }
    },
    [active, itemByKey, pendingTextByKey],
  );

  const handleRevertToDefault = useCallback(
    async (key: string) => {
      if (!active) {
        return;
      }

      const backend = active.state.backend;
      const sessionId = active.state.sessionId;

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
        await backend.deleteSessionOverride(sessionId, key);
      } catch (err: any) {
        console.log('Failed to revert setting override', err);
        const message = err?.message || 'Failed to revert setting.';
        Alert.alert('Error', message);
        setOverrides(prevOverrides);
        setPendingTextByKey(prevPending);
      }
    },
    [active, overrides, pendingTextByKey],
  );

  const renderers: SessionSettingsRenderers = useMemo(() => {
    const renderTag = (tagLabel: 'config' | 'default' | null) => {
      if (!tagLabel) {
        return null;
      }
      const tagStyle = tagLabel === 'config' ? styles.tagConfig : styles.tagDefault;
      const tagTextStyle = tagLabel === 'config' ? styles.tagTextConfig : styles.tagTextDefault;
      return (
        <View style={tagStyle}>
          <Text style={tagTextStyle}>{tagLabel}</Text>
        </View>
      );
    };

    const renderReset = (ctx: SessionSettingRenderCtx) => {
      if (!ctx.item.hasOverride) {
        return null;
      }
      return (
        <Pressable
          onPress={() => ctx.actions.revertToDefault(ctx.item.key)}
          style={(state) => [styles.resetButton, state.pressed && styles.resetButtonPressed]}
        >
          <Icon name="rotate-ccw" size={14} color={theme.textSecondary} />
          <Text style={styles.resetButtonText}>Reset</Text>
        </Pressable>
      );
    };

    const renderTextLike = (ctx: SessionSettingRenderCtx) => {
      const { item, actions } = ctx;
      const key = item.key;
      const hasPending = Object.prototype.hasOwnProperty.call(pendingTextByKey, key);
      const pending = hasPending ? pendingTextByKey[key] : undefined;
      const textValue =
        pending ??
        (item.effectiveValue !== undefined && item.effectiveValue !== null
          ? String(item.effectiveValue)
          : '');

      const multiline = item.type === 'multiline';

      return (
        <View style={styles.itemRow}>
          <View style={styles.itemHeaderRow}>
            <View style={styles.itemTitleRow}>
              <Text style={styles.itemLabel}>{item.label}</Text>
              {renderTag(item.tagLabel)}
            </View>
            {renderReset(ctx)}
          </View>
          {item.description ? <Text style={styles.itemDescription}>{item.description}</Text> : null}
          <View style={styles.textRow}>
            <TextInput
              style={[styles.textInput, multiline && styles.textInputMultiline]}
              value={textValue}
              multiline={multiline}
              onChangeText={(txt) =>
                setPendingTextByKey((prev) => ({
                  ...prev,
                  [key]: txt,
                }))
              }
              placeholder="Enter value"
              placeholderTextColor={theme.textSecondary}
            />
            <Pressable
              style={(state) => [
                styles.saveButton,
                (state.pressed || savingKey === key) && styles.saveButtonPressed,
              ]}
              onPress={() => actions.saveText(key)}
              disabled={savingKey === key}
            >
              {savingKey === key ? (
                <ActivityIndicator size="small" color={theme.textOnPrimary} />
              ) : (
                <Text style={styles.saveButtonText}>Save</Text>
              )}
            </Pressable>
          </View>
        </View>
      );
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

    return {
      fallback: renderTextLike,
      checkbox: ({ item, actions }) => {
        const boolValue = Boolean(item.effectiveValue ?? false);
        return (
          <View style={styles.itemRow}>
            <View style={styles.itemHeaderRow}>
              <View style={styles.itemTitleRow}>
                <Text style={styles.itemLabel}>{item.label}</Text>
                {renderTag(item.tagLabel)}
              </View>
              <View style={styles.itemControlsRow}>
                {item.hasOverride ? (
                  <Pressable
                    onPress={() => actions.revertToDefault(item.key)}
                    style={(state) => [
                      styles.resetButton,
                      state.pressed && styles.resetButtonPressed,
                    ]}
                  >
                    <Icon name="rotate-ccw" size={14} color={theme.textSecondary} />
                    <Text style={styles.resetButtonText}>Reset</Text>
                  </Pressable>
                ) : null}
                <Switch value={boolValue} onValueChange={(next) => actions.toggleCheckbox(item.key, next)} />
              </View>
            </View>
            {item.description ? <Text style={styles.itemDescription}>{item.description}</Text> : null}
          </View>
        );
      },
      select: ({ item, actions, renderFallback }) => {
        const rawOptions = (item.element as any).options;
        const options = normalizeOptions(rawOptions);
        if (options.length === 0) {
          return <>{renderFallback()}</>;
        }

        const selected = item.effectiveValue !== undefined && item.effectiveValue !== null ? String(item.effectiveValue) : '';
        return (
          <View style={styles.itemRow}>
            <View style={styles.itemHeaderRow}>
              <View style={styles.itemTitleRow}>
                <Text style={styles.itemLabel}>{item.label}</Text>
                {renderTag(item.tagLabel)}
              </View>
              {item.hasOverride ? (
                <Pressable
                  onPress={() => actions.revertToDefault(item.key)}
                  style={(state) => [
                    styles.resetButton,
                    state.pressed && styles.resetButtonPressed,
                  ]}
                >
                  <Icon name="rotate-ccw" size={14} color={theme.textSecondary} />
                  <Text style={styles.resetButtonText}>Reset</Text>
                </Pressable>
              ) : null}
            </View>
            {item.description ? <Text style={styles.itemDescription}>{item.description}</Text> : null}
            <View style={styles.chipsRow}>
              {options.map((opt) => {
                const isSelected = selected === opt.value;
                return (
                  <Pressable
                    key={opt.value}
                    onPress={() => actions.selectOption(item.key, opt.value)}
                    style={(state) => [
                      styles.chip,
                      isSelected && styles.chipSelected,
                      (state.pressed || (state as any).hovered) && styles.chipPressed,
                    ]}
                  >
                    <Text style={isSelected ? styles.chipTextSelected : styles.chipText}>{opt.label}</Text>
                  </Pressable>
                );
              })}
            </View>
          </View>
        );
      },
      text: renderTextLike,
      multiline: renderTextLike,
    } satisfies SessionSettingsRenderers;
  }, [pendingTextByKey, savingKey, styles, theme.textOnPrimary, theme.textSecondary]);

  if (!active) {
    return <View style={styles.root} />;
  }

  return (
    <View style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.title}>Session settings</Text>
        <Text style={styles.subtitle} numberOfLines={1}>
          Session: {active.state.sessionId}
        </Text>
      </View>

      {loading ? (
        <View style={styles.loadingRow}>
          <ActivityIndicator size="small" color={theme.primary} />
          <Text style={styles.loadingText}>Loading settings…</Text>
        </View>
      ) : null}

      {!loading && error ? <Text style={styles.errorText}>{error}</Text> : null}

      {!loading && !error && items.length === 0 ? (
        <Text style={styles.helperText}>No configurable settings are available.</Text>
      ) : null}

      {!loading && !error && items.length > 0 ? (
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
            <View style={styles.listContainer}>
              <ScrollView style={styles.list} contentContainerStyle={styles.listContent}>
                {children}
              </ScrollView>
            </View>
          )}
        />
      ) : null}
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  const borderWidth = 1;
  return StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: theme.background,
      padding: 16,
      gap: 12,
    },
    header: {
      gap: 4,
    },
    title: {
      fontSize: 16,
      fontWeight: '800',
      color: theme.text,
    },
    subtitle: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    loadingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
    loadingText: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    errorText: {
      fontSize: 12,
      color: theme.danger,
    },
    helperText: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    listContainer: {
      flex: 1,
      borderWidth,
      borderColor: theme.border,
      borderRadius: 12,
      backgroundColor: theme.surface,
    },
    list: {
      flex: 1,
    },
    listContent: {
      padding: 12,
      gap: 12,
    },
    itemRow: {
      paddingBottom: 12,
      borderBottomWidth: borderWidth,
      borderBottomColor: theme.border,
      gap: 6,
    },
    itemHeaderRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 10,
    },
    itemTitleRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      flex: 1,
    },
    itemControlsRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 10,
    },
    itemLabel: {
      fontSize: 13,
      fontWeight: '700',
      color: theme.text,
      flexShrink: 1,
    },
    itemDescription: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    tagConfig: {
      paddingHorizontal: 6,
      paddingVertical: 2,
      borderRadius: 8,
      backgroundColor: theme.primaryMuted,
    },
    tagDefault: {
      paddingHorizontal: 6,
      paddingVertical: 2,
      borderRadius: 8,
      backgroundColor: theme.surfaceAlt,
    },
    tagTextConfig: {
      fontSize: 10,
      fontWeight: '700',
      color: theme.primary,
    },
    tagTextDefault: {
      fontSize: 10,
      fontWeight: '700',
      color: theme.textSecondary,
    },
    resetButton: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 6,
      paddingHorizontal: 8,
      paddingVertical: 6,
      borderRadius: 10,
      borderWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    resetButtonPressed: {
      backgroundColor: theme.surfaceAlt,
    },
    resetButtonText: {
      fontSize: 11,
      fontWeight: '700',
      color: theme.textSecondary,
    },
    chipsRow: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: 8,
    },
    chip: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 999,
      borderWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    chipPressed: {
      backgroundColor: theme.surfaceAlt,
    },
    chipSelected: {
      backgroundColor: theme.primary,
      borderColor: theme.primary,
    },
    chipText: {
      fontSize: 12,
      fontWeight: '700',
      color: theme.text,
    },
    chipTextSelected: {
      fontSize: 12,
      fontWeight: '800',
      color: theme.textOnPrimary,
    },
    textRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 10,
    },
    textInput: {
      flex: 1,
      borderWidth,
      borderColor: theme.border,
      borderRadius: 10,
      paddingHorizontal: 10,
      paddingVertical: 8,
      fontSize: 12,
      color: theme.text,
      backgroundColor: theme.background,
    },
    textInputMultiline: {
      minHeight: 72,
      textAlignVertical: 'top',
    },
    saveButton: {
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderRadius: 10,
      backgroundColor: theme.primary,
      minWidth: 80,
      alignItems: 'center',
    },
    saveButtonPressed: {
      opacity: 0.85,
    },
    saveButtonText: {
      fontSize: 12,
      fontWeight: '800',
      color: theme.textOnPrimary,
    },
  });
}
