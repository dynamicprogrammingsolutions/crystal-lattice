import React, { useEffect, useState } from 'react';
import { Alert, Modal } from 'react-native';
import type { AgentBackend } from '@crystal-lattice/frontend-sdk';
import { SessionSettingsSurface } from '@crystal-lattice/frontend-rn-components';
import {
  type ConfigSchemaEntry,
  type UiSchemaElement,
} from '../api';

export interface SessionSettingsModalProps {
  backend: AgentBackend | null;
  sessionId: string;
  visible: boolean;
  onRequestClose: () => void;
}

const SessionSettingsModal: React.FC<SessionSettingsModalProps> = ({
  backend,
  sessionId,
  visible,
  onRequestClose,
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [elements, setElements] = useState<UiSchemaElement[]>([]);
  const [overrides, setOverrides] = useState<Record<string, any>>({});
  const [baseConfig, setBaseConfig] = useState<Record<string, any>>({});
  const [schemaByKey, setSchemaByKey] = useState<Record<string, ConfigSchemaEntry>>({});
  const [pendingTextByKey, setPendingTextByKey] = useState<Record<string, string>>({});
  const [savingKey, setSavingKey] = useState<string | null>(null);

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
        // Filter to config-style elements: ui_type == "config" or missing,
        // and with a non-empty key.
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
          const k = (entry as any).key;
          if (typeof k === 'string' && k && !byKey[k]) {
            byKey[k] = entry;
          }
        });
        setSchemaByKey(byKey);
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
      await backend.patchSessionOverrides(sessionId, { [key]: next });
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
      await backend.patchSessionOverrides(sessionId, { [key]: value });
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
      await backend.patchSessionOverrides(sessionId, { [key]: value });
      setOverrides((prev) => ({ ...prev, [key]: value }));
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
    // Optimistically update local state, then revert on failure.
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
      const msg = err?.message || 'Failed to revert setting.';
      Alert.alert('Error', msg);
      // Revert optimistic update on failure.
      setOverrides(prevOverrides);
      setPendingTextByKey(prevPending);
    }
  };

  if (!visible) {
    return null;
  }

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onRequestClose}
    >
      <SessionSettingsSurface
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
        onRequestClose={onRequestClose}
      />
    </Modal>
  );
};

export default SessionSettingsModal;
