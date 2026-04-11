import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';

import { ThemeProvider, useTheme } from '@crystal-lattice/frontend-rn-components';
import {
  buildConfigSchemaByKey,
  buildSessionSettingItems,
  SessionSettingsHost,
  useSessionSettingsController,
  type SessionSettingItem,
  type SessionSettingRenderCtx,
  type SessionSettingsRenderers,
} from '@crystal-lattice/frontend-sdk-react';
import Icon from 'react-native-vector-icons/Feather';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { useActiveSessionSettingsWindow } from './sessionSettingsCoordinator';
import { clearActiveSessionSettingsWindow } from './sessionSettingsCoordinator';
import { DesktopWindowManager } from './desktopWindowManager';
import { MacCheckbox } from '../native/MacCheckbox';
import { MacSelect, type MacSelectOption } from '../native/MacSelect';

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

  const [pendingTextByKey, setPendingTextByKey] = useState<Record<string, string>>({});

  const backend = active?.state.backend ?? null;
  const sessionId = active?.state.sessionId ?? null;
  const cacheKey = active?.state.connectionId ?? 'default';
  const caps = backend?.getCapabilities?.();
  const supported = !caps || (caps.sessionUiSchema && caps.sessionConfigOverrides);
  const controllerSessionId = active && supported ? sessionId : null;
  const { controller, state: settingsState } = useSessionSettingsController({
    backend,
    cacheKey,
    sessionId: controllerSessionId,
    enabled: !!active,
  });
  const elements = settingsState?.elements ?? [];
  const schemaByKey = useMemo(
    () => buildConfigSchemaByKey(settingsState?.configSchema || []),
    [settingsState?.configSchema],
  );
  const savingKeys = settingsState?.savingKeys ?? [];
  const savingKeySet = useMemo(() => new Set(savingKeys), [savingKeys]);

  const items = useMemo(() => {
    return buildSessionSettingItems({
      elements,
      overrides: settingsState?.overrides || {},
      baseConfig: settingsState?.baseConfig || {},
      schemaByKey,
    });
  }, [elements, schemaByKey, settingsState?.baseConfig, settingsState?.overrides]);

  const itemByKey = useMemo(() => {
    const byKey: Record<string, SessionSettingItem> = {};
    items.forEach((item) => {
      byKey[item.key] = item;
    });
    return byKey;
  }, [items]);

  const closeWindow = useCallback(() => {
    if (active?.state.id) {
      clearActiveSessionSettingsWindow(active.state.id);
    }
    DesktopWindowManager?.closeReactWindow({ windowKey: 'sessionSettings' });
  }, [active]);

  useEffect(() => {
    if (!active) {
      setPendingTextByKey({});
      return;
    }
    setPendingTextByKey({});
  }, [active?.state.id]);

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
  }, [items]);

  const handleToggleCheckbox = useCallback(
    async (key: string, next: boolean) => {
      if (!active) {
        return;
      }

      if (!controller) {
        return;
      }

      try {
        await controller.patchOverride(key, next);
      } catch {
        // Controller state captures errors.
      }
    },
    [active, controller],
  );

  const handleSelectOption = useCallback(
    async (key: string, value: string) => {
      if (!active) {
        return;
      }

      if (!controller) {
        return;
      }

      try {
        await controller.patchOverride(key, value);
      } catch {
        // Controller state captures errors.
      }
    },
    [active, controller],
  );

  const handleSaveText = useCallback(
    async (key: string) => {
      if (!active) {
        return;
      }

      if (!controller) {
        return;
      }

      const hasPending = Object.prototype.hasOwnProperty.call(pendingTextByKey, key);
      const pending = hasPending ? pendingTextByKey[key] : undefined;
      const currentEffective = itemByKey[key]?.effectiveValue;
      const value =
        pending ??
        (currentEffective !== undefined && currentEffective !== null
          ? String(currentEffective)
          : '');

      try {
        await controller.patchOverride(key, value);
      } catch {
        // Controller state captures errors.
      }
    },
    [active, controller, itemByKey, pendingTextByKey],
  );

  const handleRevertToDefault = useCallback(
    async (key: string) => {
      if (!active) {
        return;
      }

      if (!controller) {
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
    },
    [active, controller],
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
                (state.pressed || savingKeySet.has(key)) && styles.saveButtonPressed,
              ]}
              onPress={() => actions.saveText(key)}
              disabled={savingKeySet.has(key)}
            >
              {savingKeySet.has(key) ? (
                <ActivityIndicator size="small" color={theme.textOnPrimary} />
              ) : (
                <Text style={styles.saveButtonText}>Save</Text>
              )}
            </Pressable>
          </View>
        </View>
      );
    };

    const normalizeOptions = (raw: any): MacSelectOption[] => {
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
        .filter((v) => v !== null) as MacSelectOption[];
    };

    return {
      fallback: renderTextLike,
      readonly: ({ item }) => {
        const value =
          item.effectiveValue !== undefined && item.effectiveValue !== null
            ? String(item.effectiveValue)
            : '';

        return (
          <View style={styles.itemRow}>
            <View style={styles.itemHeaderRow}>
              <View style={styles.itemTitleRow}>
                <Text style={styles.itemLabel}>{item.label}</Text>
                {renderTag(item.tagLabel)}
              </View>
            </View>
            {item.description ? <Text style={styles.itemDescription}>{item.description}</Text> : null}
            <View style={styles.readonlyValueBox}>
              <Text style={styles.readonlyValueText}>{value || 'Not set'}</Text>
            </View>
          </View>
        );
      },
      checkbox: ({ item, actions }) => {
        const boolValue = Boolean(item.effectiveValue ?? false);
        return (
          <View style={styles.itemRow}>
            <View style={styles.itemHeaderRow}>
              <View style={styles.itemTitleRow}>
                <MacCheckbox
                  style={styles.macCheckbox}
                  label={item.label}
                  value={boolValue}
                  onValueChange={(next) => actions.toggleCheckbox(item.key, next)}
                />
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

        const selectedValue =
          item.effectiveValue !== undefined && item.effectiveValue !== null ? String(item.effectiveValue) : '';

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
            <MacSelect
              style={styles.macSelect}
              options={options}
              selectedValue={selectedValue}
              placeholder="None"
              onValueChange={(value) => {
                // Treat the placeholder/empty value as "no selection".
                // If an override exists, clear it; otherwise leave state as-is.
                if (!value) {
                  if (item.hasOverride) {
                    actions.revertToDefault(item.key);
                  }
                  return;
                }
                actions.selectOption(item.key, value);
              }}
            />
          </View>
        );
      },
      text: renderTextLike,
      multiline: renderTextLike,
    } satisfies SessionSettingsRenderers;
  }, [pendingTextByKey, savingKeySet, styles, theme.textOnPrimary, theme.textSecondary]);

  if (!active) {
    return <View style={styles.root} />;
  }

  const error = !supported
    ? 'This backend does not support session settings.'
    : settingsState?.error ?? null;
  const statusText = error || settingsState?.statusMessage;
  const statusTone = error ? 'error' : settingsState?.statusTone ?? 'idle';
  const showSpinner = !error && statusTone === 'busy';
  const hasLoaded = settingsState?.lastLoadedAt != null;

  return (
    <View style={styles.root}>
      <View style={styles.headerRow}>
        <View style={styles.header}>
          <Text style={styles.title}>Session settings</Text>
          <Text style={styles.subtitle} numberOfLines={1}>
            Session: {active.state.sessionId}
          </Text>
        </View>

        <Pressable
          style={(state) => {
            const hovered = (state as any).hovered as boolean | undefined;
            return [
              styles.closeButton,
              (hovered || state.pressed) && styles.closeButtonHovered,
            ];
          }}
          onPress={closeWindow}
        >
          <Text style={styles.closeButtonText}>Close</Text>
        </Pressable>
      </View>

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

      {!error && hasLoaded && items.length === 0 ? (
        <Text style={styles.helperText}>No configurable settings are available.</Text>
      ) : null}

      {!error && items.length > 0 ? (
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
    headerRow: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: 12,
    },
    header: {
      gap: 4,
      flex: 1,
    },
    closeButton: {
      borderWidth,
      borderColor: theme.primary,
      backgroundColor: theme.primary,
      borderRadius: 10,
      paddingHorizontal: 12,
      paddingVertical: 7,
      alignItems: 'center',
      justifyContent: 'center',
    },
    closeButtonHovered: {
      opacity: 0.92,
    },
    closeButtonText: {
      fontSize: 12,
      fontWeight: '800',
      color: theme.textOnPrimary,
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
    statusLine: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
      minHeight: 18,
    },
    statusText: {
      fontSize: 12,
      color: theme.textSecondary,
    },
    statusTextError: {
      color: theme.danger,
    },
    statusTextSuccess: {
      color: theme.primary,
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
    macCheckbox: {
      flexGrow: 1,
      flexShrink: 1,
      minHeight: 20,
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
    macSelect: {
      minHeight: 26,
      minWidth: 240,
      maxWidth: 420,
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
    readonlyValueBox: {
      marginTop: 2,
      borderWidth,
      borderColor: theme.border,
      borderRadius: 10,
      paddingHorizontal: 10,
      paddingVertical: 8,
      backgroundColor: theme.surfaceAlt,
    },
    readonlyValueText: {
      fontSize: 12,
      color: theme.text,
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
