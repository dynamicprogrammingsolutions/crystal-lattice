import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, StyleSheet, View } from 'react-native';

import {
  SessionSettingsCard,
  ThemeProvider,
  useTheme,
} from '@crystal-lattice/frontend-rn-components';
import type { ConfigSchemaEntry, UiSchemaElement } from '@crystal-lattice/frontend-sdk';

import { useDesktopTheme } from '../theme/useDesktopTheme';
import { DesktopWindowManager } from './desktopWindowManager';
import {
  clearActiveSessionSettingsWindow,
  useActiveSessionSettingsWindow,
} from './sessionSettingsCoordinator';

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
  const [schemaByKey, setSchemaByKey] = useState<Record<string, ConfigSchemaEntry>>({});
  const [pendingTextByKey, setPendingTextByKey] = useState<Record<string, string>>({});
  const [savingKey, setSavingKey] = useState<string | null>(null);

  const closeWindow = useCallback((id?: string) => {
    clearActiveSessionSettingsWindow(id);
    DesktopWindowManager?.closeSessionSettingsWindow();
  }, []);

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

        const configElements = (els || []).filter((el) => {
          if (!el || typeof el !== 'object') return false;
          const key = (el as any).key;
          if (typeof key !== 'string' || !key) return false;
          const uiType = (el as any).ui_type;
          if (uiType === 'config') return true;
          if (uiType === undefined || uiType === null || uiType === '') return true;
          return false;
        }) as UiSchemaElement[];

        setElements(configElements);
        setOverrides(ovs || {});
        const byKey: Record<string, ConfigSchemaEntry> = {};
        (schema || []).forEach((entry) => {
          if (!entry || typeof entry !== 'object') return;
          const key = (entry as any).key;
          if (typeof key === 'string' && key && !byKey[key]) {
            byKey[key] = entry;
          }
        });
        setSchemaByKey(byKey);
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
      const value = pendingTextByKey[key] ?? String(overrides[key] ?? '');
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
    [active, overrides, pendingTextByKey],
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

  if (!active) {
    return <View style={styles.root} />;
  }

  return (
    <View style={styles.root}>
      <SessionSettingsCard
        title="Session settings"
        loading={loading}
        error={error}
        elements={elements}
        overrides={overrides}
        baseConfig={baseConfig}
        schemaByKey={schemaByKey}
        pendingTextByKey={pendingTextByKey}
        savingKey={savingKey}
        onToggleCheckbox={handleToggleCheckbox}
        onSelectOption={handleSelectOption}
        onChangePendingText={(key, value) =>
          setPendingTextByKey((prev) => ({ ...prev, [key]: value }))
        }
        onSaveText={handleSaveText}
        onRevertToDefault={handleRevertToDefault}
        onRequestClose={() => closeWindow(active.state.id)}
      />
    </View>
  );
}

function createStyles(theme: ReturnType<typeof useTheme>) {
  return StyleSheet.create({
    root: {
      flex: 1,
      backgroundColor: theme.background,
      justifyContent: 'center',
      alignItems: 'center',
    },
  });
}
