import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import type {
  ActionDisplayPayload,
  ActionUiElement,
  AgentBackend,
  ConfigCustomValue,
  RichDropdownOption,
} from "@crystal-lattice/frontend-sdk";
import {
  getSessionSettingsActionAnchor,
  runApplicationAction,
} from "@crystal-lattice/frontend-sdk";
import {
  buildConfigSchemaByKey,
  buildSessionSettingItems,
  SessionSettingsHost,
  usePluginActionDialog,
  useDisplayFollowupDialog,
  useSessionSettingsController,
  type SessionSettingRenderCtx,
  type SessionSettingsRenderers,
} from "@crystal-lattice/frontend-sdk-react";
import { ApplicationActionDialog } from "@crystal-lattice/frontend-rn-components";
import Icon from "react-native-vector-icons/Feather";

import { acquireActionClientValues } from "../actionClientInputs";
import OptionsPickerModal from "./OptionsPickerModal";
import PanelModalFrame from "./PanelModalFrame";
import ActionResultModal from "./ActionResultModal";
import { useMobileApplicationActionDialogFieldRenderers } from "./applicationActionDialogRenderers";
import { useTheme, type Theme } from "../theme";

export interface SessionSettingsModalProps {
  backend: AgentBackend | null;
  cacheKey?: string;
  sessionId: string;
  visible: boolean;
  onRequestClose: () => void;
  acquireClientValues?: (
    element: ActionUiElement
  ) => Promise<Record<string, unknown> | null>;
}

const SessionSettingsModal: React.FC<SessionSettingsModalProps> = ({
  backend,
  cacheKey = "default",
  sessionId,
  visible,
  onRequestClose,
  acquireClientValues = acquireActionClientValues,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const actionDialogFieldRenderers =
    useMobileApplicationActionDialogFieldRenderers();
  const [activeActionId, setActiveActionId] = useState<string | null>(null);
  const [actionDisplay, setActionDisplay] =
    useState<ActionDisplayPayload | null>(null);

  const [pendingTextByKey, setPendingTextByKey] = useState<
    Record<string, string>
  >({});
  const [dropdownState, setDropdownState] = useState<{
    key: string;
    label: string;
    options: RichDropdownOption[];
    selected: string;
    placeholder?: string;
    customValue?: ConfigCustomValue;
  } | null>(null);

  const controllerSessionId = visible ? sessionId : null;
  const { controller, state: settingsState } = useSessionSettingsController({
    backend,
    cacheKey,
    sessionId: controllerSessionId,
    enabled: visible,
  });
  const elements = settingsState?.elements ?? [];
  const settingsActions = settingsState?.actions ?? [];
  const schemaByKey = useMemo(
    () => buildConfigSchemaByKey(settingsState?.configSchema || []),
    [settingsState?.configSchema]
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
  }, [
    elements,
    schemaByKey,
    settingsState?.baseConfig,
    settingsState?.overrides,
  ]);

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
      Alert.alert("No connection", "Connect to a server to change settings.");
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
      Alert.alert("No connection", "Connect to a server to change settings.");
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
      Alert.alert("No connection", "Connect to a server to change settings.");
      return;
    }
    const currentEffective = itemByKey[key]?.effectiveValue;
    const value =
      pendingTextByKey[key] ??
      (currentEffective !== undefined && currentEffective !== null
        ? String(currentEffective)
        : "");
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
      Alert.alert("No connection", "Connect to a server to change settings.");
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

  const executeSettingsAction = useCallback(
    async (
      element: ActionUiElement,
      dialogValues: Record<string, any> | undefined,
      formValues?: Record<string, any>
    ) => {
      if (!backend) {
        Alert.alert("No connection", "Connect to a server to run actions.");
        return;
      }
      setActiveActionId(element.id);
      try {
        const clientValues = await acquireClientValues(element);
        if (clientValues === null) {
          return;
        }
        const result = await runApplicationAction({
          backend,
          element,
          actionsById: {},
          context: {
            sessionId,
            dialogValues,
            formValues,
            clientValues,
          },
          effects: {
            currentSessionId: sessionId,
          },
        });
        if (!result.ok) {
          Alert.alert(
            "Action error",
            result.errorMessage || "Failed to execute action."
          );
          return;
        }
        if (result.display) {
          setActionDisplay(result.display);
        }
        controller?.invalidate();
        await controller?.load();
      } catch (error: any) {
        Alert.alert(
          "Action error",
          error?.message || "Failed to execute action."
        );
      } finally {
        setActiveActionId(null);
      }
    },
    [acquireClientValues, backend, controller, sessionId]
  );
  const displayFollowupDialog = useDisplayFollowupDialog<null>(
    async (element, { formValues }, values) => {
      await executeSettingsAction(element, values, formValues);
    }
  );

  const {
    activeElement: activeDialogElement,
    openForElement: openAction,
    handleSubmit: submitActionDialog,
    handleCancel: cancelActionDialog,
  } = usePluginActionDialog<{ sessionId: string }>(
    async (element, _context, values) => {
      await executeSettingsAction(element, values);
    }
  );

  const anchoredActionsByKey = useMemo(() => {
    const result: Record<string, ActionUiElement[]> = {};
    settingsActions.forEach((action) => {
      const anchor = getSessionSettingsActionAnchor(action);
      if (!anchor.key || !itemByKey[anchor.key]) {
        return;
      }
      result[anchor.key] = [...(result[anchor.key] ?? []), action];
    });
    Object.values(result).forEach((actions) =>
      actions.sort((left, right) => (left.order ?? 0) - (right.order ?? 0))
    );
    return result;
  }, [itemByKey, settingsActions]);

  const fallbackActions = useMemo(
    () =>
      settingsActions
        .filter((action) => {
          const anchor = getSessionSettingsActionAnchor(action);
          return !anchor.key || !itemByKey[anchor.key];
        })
        .sort((left, right) => (left.order ?? 0) - (right.order ?? 0)),
    [itemByKey, settingsActions]
  );

  const renderSettingsAction = (action: ActionUiElement) => (
    <TouchableOpacity
      key={`${action.plugin}:${action.id}`}
      accessibilityRole="button"
      testID={`session-settings-action-${action.id}`}
      style={styles.settingsActionButton}
      disabled={activeActionId !== null}
      onPress={() => openAction(action, { sessionId })}
    >
      <Icon
        name={action.icon || "zap"}
        size={15}
        color={theme.primary}
      />
      <Text style={styles.settingsActionLabel}>{action.label}</Text>
      {activeActionId === action.id ? (
        <ActivityIndicator size="small" color={theme.primary} />
      ) : null}
    </TouchableOpacity>
  );

  if (!visible) {
    return null;
  }

  const normalizeOptions = (raw: any): RichDropdownOption[] => {
    if (!Array.isArray(raw)) return [];
    return raw
      .map((opt) => {
        if (typeof opt === "string") {
          return { value: opt, label: opt };
        }
        if (opt && typeof opt === "object") {
          const value =
            typeof opt.value === "string" ? opt.value : String(opt.value ?? "");
          const label = typeof opt.label === "string" ? opt.label : value;
          return {
            value,
            label,
            ...(typeof opt.icon === "string" ? { icon: opt.icon } : {}),
            ...(typeof opt.tone === "string" ? { tone: opt.tone } : {}),
          };
        }
        return null;
      })
      .filter((v) => v !== null) as RichDropdownOption[];
  };

  const renderTextLike = (ctx: SessionSettingRenderCtx) => {
    const { item } = ctx;
    const key = item.key;
    const hasPending = Object.prototype.hasOwnProperty.call(
      pendingTextByKey,
      key
    );
    const pending = hasPending ? pendingTextByKey[key] : undefined;

    const textValue =
      pending ??
      (item.effectiveValue !== undefined && item.effectiveValue !== null
        ? String(item.effectiveValue)
        : "");

    return (
      <View style={[styles.itemRow, item.disabled && styles.itemRowDisabled]}>
        <View style={styles.itemTextColumn}>
          <View style={styles.itemLabelRow}>
            <View style={styles.itemLabelChipColumn}>
              <Text
                style={[
                  styles.itemLabel,
                  item.disabled && styles.itemLabelDisabled,
                ]}
              >
                {item.label}
              </Text>
              {item.tagLabel && (
                <View
                  style={
                    item.tagLabel === "config"
                      ? styles.tagConfig
                      : styles.tagDefault
                  }
                >
                  <Text
                    style={
                      item.tagLabel === "config"
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
            <Text
              style={[
                styles.itemDescription,
                item.disabled && styles.itemDescriptionDisabled,
              ]}
            >
              {item.description}
            </Text>
          ) : null}
          <View style={styles.textRow}>
            <TextInput
              style={[
                styles.textInput,
                item.disabled && styles.textInputDisabled,
              ]}
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
              style={[
                styles.saveButton,
                item.disabled && styles.saveButtonDisabled,
              ]}
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
          : "";

      return (
        <View style={[styles.itemRow, item.disabled && styles.itemRowDisabled]}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <View style={styles.itemLabelChipColumn}>
                <Text
                  style={[
                    styles.itemLabel,
                    item.disabled && styles.itemLabelDisabled,
                  ]}
                >
                  {item.label}
                </Text>
                {item.tagLabel && (
                  <View
                    style={
                      item.tagLabel === "config"
                        ? styles.tagConfig
                        : styles.tagDefault
                    }
                  >
                    <Text
                      style={
                        item.tagLabel === "config"
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
              <Text
                style={[
                  styles.itemDescription,
                  item.disabled && styles.itemDescriptionDisabled,
                ]}
              >
                {item.description}
              </Text>
            ) : null}
            <View style={styles.readonlyValueBox}>
              <Text style={styles.readonlyValueText}>{value || "Not set"}</Text>
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
                <Text
                  style={[
                    styles.itemLabel,
                    item.disabled && styles.itemLabelDisabled,
                  ]}
                >
                  {item.label}
                </Text>
                {item.tagLabel && (
                  <View
                    style={
                      item.tagLabel === "config"
                        ? styles.tagConfig
                        : styles.tagDefault
                    }
                  >
                    <Text
                      style={
                        item.tagLabel === "config"
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
              <Text
                style={[
                  styles.itemDescription,
                  item.disabled && styles.itemDescriptionDisabled,
                ]}
              >
                {item.description}
              </Text>
            ) : null}
          </View>
          <View style={styles.controlSwitchColumn}>
            <Switch
              testID={`session-setting-checkbox-${item.key}`}
              value={boolValue}
              disabled={item.disabled}
              onValueChange={(next) =>
                ctx.actions.toggleCheckbox(item.key, next)
              }
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
      const customValue =
        (item.element as any).custom_value &&
        typeof (item.element as any).custom_value === "object"
          ? ((item.element as any).custom_value as ConfigCustomValue)
          : undefined;
      if (!options.length && customValue?.enabled !== true) {
        return null;
      }

      const selected =
        typeof item.effectiveValue === "string"
          ? item.effectiveValue
          : String(item.effectiveValue ?? "");

      return (
        <View style={[styles.itemRow, item.disabled && styles.itemRowDisabled]}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <View style={styles.itemLabelChipColumn}>
                <Text
                  style={[
                    styles.itemLabel,
                    item.disabled && styles.itemLabelDisabled,
                  ]}
                >
                  {item.label}
                </Text>
                {item.tagLabel && (
                  <View
                    style={
                      item.tagLabel === "config"
                        ? styles.tagConfig
                        : styles.tagDefault
                    }
                  >
                    <Text
                      style={
                        item.tagLabel === "config"
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
              <Text
                style={[
                  styles.itemDescription,
                  item.disabled && styles.itemDescriptionDisabled,
                ]}
              >
                {item.description}
              </Text>
            ) : null}
            <View style={styles.chipsRow}>
              {options.map((opt) => {
                const isSelected = opt.value === selected;
                return (
                  <TouchableOpacity
                    key={opt.value}
                    testID={`session-setting-select-${item.key}-${opt.value}`}
                    accessibilityRole="button"
                    accessibilityState={{ selected: isSelected }}
                    style={[
                      isSelected ? styles.chipSelected : styles.chip,
                      item.disabled && styles.chipDisabled,
                    ]}
                    onPress={() =>
                      ctx.actions.selectOption(item.key, opt.value)
                    }
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
      const customValue =
        (item.element as any).custom_value &&
        typeof (item.element as any).custom_value === "object"
          ? ((item.element as any).custom_value as ConfigCustomValue)
          : undefined;
      if (!options.length && customValue?.enabled !== true) {
        return null;
      }
      const selected =
        typeof item.effectiveValue === "string"
          ? item.effectiveValue
          : String(item.effectiveValue ?? "");
      const selectedLabel =
        options.find((o) => o.value === selected)?.label ?? selected;
      return (
        <View style={[styles.itemRow, item.disabled && styles.itemRowDisabled]}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <View style={styles.itemLabelChipColumn}>
                <Text
                  style={[
                    styles.itemLabel,
                    item.disabled && styles.itemLabelDisabled,
                  ]}
                >
                  {item.label}
                </Text>
                {item.tagLabel && (
                  <View
                    style={
                      item.tagLabel === "config"
                        ? styles.tagConfig
                        : styles.tagDefault
                    }
                  >
                    <Text
                      style={
                        item.tagLabel === "config"
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
              <Text
                style={[
                  styles.itemDescription,
                  item.disabled && styles.itemDescriptionDisabled,
                ]}
              >
                {item.description}
              </Text>
            ) : null}
            <TouchableOpacity
              style={[
                styles.dropdownButton,
                item.disabled && styles.dropdownButtonDisabled,
              ]}
              disabled={item.disabled}
              onPress={() => {
                setDropdownState({
                  key: item.key,
                  label: item.label,
                  options,
                  selected,
                  placeholder:
                    typeof (item.element as any).placeholder === "string"
                      ? (item.element as any).placeholder
                      : undefined,
                  customValue,
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
    directory: (ctx: SessionSettingRenderCtx) => {
      const { item } = ctx;
      const options = normalizeOptions((item.element as any).options);
      if (!options.length) {
        return null;
      }
      const selected =
        typeof item.effectiveValue === "string"
          ? item.effectiveValue
          : String(item.effectiveValue ?? "");
      const selectedLabel =
        options.find((option) => option.value === selected)?.label ??
        "Unavailable directory";
      return (
        <View style={[styles.itemRow, item.disabled && styles.itemRowDisabled]}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <View style={styles.itemLabelChipColumn}>
                <Text
                  style={[
                    styles.itemLabel,
                    item.disabled && styles.itemLabelDisabled,
                  ]}
                >
                  {item.label}
                </Text>
                {item.tagLabel && (
                  <View
                    style={
                      item.tagLabel === "config"
                        ? styles.tagConfig
                        : styles.tagDefault
                    }
                  >
                    <Text
                      style={
                        item.tagLabel === "config"
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
              <Text
                style={[
                  styles.itemDescription,
                  item.disabled && styles.itemDescriptionDisabled,
                ]}
              >
                {item.description}
              </Text>
            ) : null}
            <TouchableOpacity
              testID={`session-setting-directory-${item.key}`}
              style={[
                styles.dropdownButton,
                item.disabled && styles.dropdownButtonDisabled,
              ]}
              disabled={item.disabled}
              onPress={() => {
                setDropdownState({
                  key: item.key,
                  label: item.label,
                  options,
                  selected,
                  placeholder:
                    typeof (item.element as any).placeholder === "string"
                      ? (item.element as any).placeholder
                      : "Select a workspace directory",
                });
              }}
            >
              <Icon name="folder" size={14} color={theme.textSecondary} />
              <Text style={styles.dropdownButtonValue} numberOfLines={1}>
                {selectedLabel}
              </Text>
              <Icon name="chevron-down" size={14} color={theme.textSecondary} />
            </TouchableOpacity>
          </View>
        </View>
      );
    },
    workspace: (ctx: SessionSettingRenderCtx) => {
      const { item } = ctx;
      const rawOptions = Array.isArray((item.element as any).options)
        ? (item.element as any).options
        : [];
      const options = rawOptions
        .filter(
          (option: any) =>
            option &&
            typeof option === "object" &&
            typeof option.value === "string" &&
            option.available !== false
        )
        .map((option: any) => {
          const source =
            option.source === "private"
              ? "Private"
              : option.source === "files"
              ? "Files"
              : "Shared";
          return {
            value: option.value,
            label: `${source} · ${String(option.label || option.value)}`,
            icon:
              option.source === "private"
                ? "lock"
                : option.source === "files"
                ? "hard-drive"
                : "users",
          };
        });
      const selected =
        typeof item.effectiveValue === "string"
          ? item.effectiveValue
          : String(item.effectiveValue ?? "");
      const selectedRaw = rawOptions.find(
        (option: any) => option?.value === selected
      );
      const selectedSource =
        selectedRaw?.source === "private"
          ? "Private"
          : selectedRaw?.source === "files"
          ? "Files"
          : "Shared";
      const selectedLabel = selectedRaw
        ? `${
            selectedRaw.available === false ? "Unavailable" : selectedSource
          } · ${selectedRaw.label || selectedRaw.value}`
        : "Unavailable workspace";
      return (
        <View style={[styles.itemRow, item.disabled && styles.itemRowDisabled]}>
          <View style={styles.itemTextColumn}>
            <View style={styles.itemLabelRow}>
              <View style={styles.itemLabelChipColumn}>
                <Text
                  style={[
                    styles.itemLabel,
                    item.disabled && styles.itemLabelDisabled,
                  ]}
                >
                  {item.label}
                </Text>
              </View>
            </View>
            {item.description ? (
              <Text style={styles.itemDescription}>{item.description}</Text>
            ) : null}
            <TouchableOpacity
              testID={`session-setting-workspace-${item.key}`}
              style={[
                styles.dropdownButton,
                item.disabled && styles.dropdownButtonDisabled,
              ]}
              disabled={item.disabled}
              onPress={() =>
                setDropdownState({
                  key: item.key,
                  label: item.label,
                  options,
                  selected,
                  placeholder: "Choose a working directory",
                })
              }
            >
              <Icon name="folder" size={14} color={theme.textSecondary} />
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

  const error = !backend
    ? "No active connection"
    : settingsState?.error ?? null;
  const statusText = error || settingsState?.statusMessage;
  const statusTone = error ? "error" : settingsState?.statusTone ?? "idle";
  const showSpinner = !error && statusTone === "busy";
  const hasLoaded = settingsState?.lastLoadedAt != null;

  return (
    <>
      <PanelModalFrame
        visible={visible}
        testID="session-settings-modal"
        title="Session settings"
        titleTestID="session-settings-title"
        onRequestClose={onRequestClose}
        statusText={statusText}
        statusTone={statusTone}
        showSpinner={showSpinner}
        scroll={!error && (items.length > 0 || fallbackActions.length > 0)}
        scrollTestID="session-settings-scroll"
        overlayChildren={
          <OptionsPickerModal
            visible={!!dropdownState}
            options={dropdownState?.options ?? []}
            selectedValue={dropdownState?.selected ?? ""}
            placeholder={dropdownState?.placeholder}
            customValue={dropdownState?.customValue}
            useModal={false}
            onSelect={(value) => {
              if (dropdownState) {
                handleSelectOption(dropdownState.key, value);
                setDropdownState(null);
              }
            }}
            onRequestClose={() => setDropdownState(null)}
          />
        }
      >
        {!error &&
          hasLoaded &&
          items.length === 0 &&
          fallbackActions.length === 0 && (
            <Text style={styles.helperText}>
              No configurable settings are available for this session.
            </Text>
          )}
        {!error && items.length > 0 && (
          <SessionSettingsHost
            items={items}
            actions={{
              toggleCheckbox: handleToggleCheckbox,
              selectOption: handleSelectOption,
              saveText: handleSaveText,
              revertToDefault: handleRevertToDefault,
            }}
            renderers={renderers}
            renderAfterItem={({ item }) => {
              const actions = anchoredActionsByKey[item.key] ?? [];
              return actions.length > 0 ? (
                <View style={styles.settingsActionGroup}>
                  {actions.map(renderSettingsAction)}
                </View>
              ) : null;
            }}
          />
        )}
        {!error && fallbackActions.length > 0 ? (
          <View style={styles.settingsActionsSection}>
            <Text style={styles.settingsActionsTitle}>Actions</Text>
            {fallbackActions.map(renderSettingsAction)}
          </View>
        ) : null}
      </PanelModalFrame>
      <ApplicationActionDialog
        visible={!!activeDialogElement}
        dialog={(activeDialogElement as any)?.dialog || null}
        titleFallback={activeDialogElement?.label}
        prefillContext={{ session: { session_id: sessionId } }}
        fieldRenderers={actionDialogFieldRenderers}
        onSubmit={submitActionDialog}
        onCancel={cancelActionDialog}
      />
      <ActionResultModal
        testID="session-settings-action-result"
        visible={!!actionDisplay}
        display={actionDisplay}
        onRequestClose={() => setActionDisplay(null)}
        fieldRenderers={actionDialogFieldRenderers}
        onOverlayRequestClose={displayFollowupDialog.handleCancel}
        onFollowupAction={(action, formValues) => {
          if (action.kind === "run_action" && actionDisplay) {
            displayFollowupDialog.openForAction(action, actionDisplay, null, formValues);
          }
        }}
        overlayChildren={displayFollowupDialog.activeElement ? (
          <ApplicationActionDialog
            presentationMode="overlay"
            visible
            dialog={displayFollowupDialog.activeElement.dialog}
            titleFallback={displayFollowupDialog.activeElement.label}
            fieldRenderers={actionDialogFieldRenderers}
            onSubmit={displayFollowupDialog.handleSubmit}
            onCancel={displayFollowupDialog.handleCancel}
          />
        ) : null}
      />
    </>
  );
};

export default SessionSettingsModal;

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    helperText: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.textSecondary,
      marginBottom: 8,
    },
    settingsActionGroup: {
      marginTop: 4,
      marginBottom: 8,
    },
    settingsActionsSection: {
      marginTop: 14,
    },
    settingsActionsTitle: {
      color: theme.text,
      fontSize: theme.typography.fontSize.normal,
      fontWeight: "600",
      marginBottom: 6,
    },
    settingsActionButton: {
      minHeight: 38,
      borderWidth: StyleSheet.hairlineWidth,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      marginBottom: 6,
      backgroundColor: theme.surfaceAlt,
      flexDirection: "row",
      alignItems: "center",
    },
    settingsActionLabel: {
      flex: 1,
      marginLeft: 8,
      color: theme.primary,
      fontSize: theme.typography.fontSize.small,
      fontWeight: "600",
    },
    itemRow: {
      flexDirection: "row",
      alignItems: "flex-start",
      justifyContent: "space-between",
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
      flexDirection: "row",
      alignItems: "center",
      flexWrap: "wrap",
      marginBottom: 2,
    },
    itemLabelChipColumn: {
      flexDirection: "row",
      flexWrap: "wrap",
      alignItems: "center",
      flex: 1,
    },
    itemLabel: {
      flexShrink: 1,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: "500",
      color: theme.text,
      marginBottom: 2,
      marginRight: 4,
    },
    itemLabelDisabled: {
      color: theme.textSecondary,
    },
    itemDescription: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
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
      flexDirection: "row",
      flexWrap: "wrap",
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
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.text,
    },
    chipTextSelected: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textOnPrimary,
    },
    chipTextDisabled: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
    },
    textRow: {
      flexDirection: "row",
      alignItems: "center",
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
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: "600",
    },
    dropdownButtonDisabled: {
      backgroundColor: theme.surfaceAlt,
      borderColor: theme.border,
    },
    controlSwitchColumn: {
      marginLeft: 8,
      flexDirection: "row",
      alignItems: "center",
      justifyContent: "flex-start",
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
    dropdownButton: {
      flexDirection: "row",
      alignItems: "center",
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
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.textSecondary,
    },
    dropdownButtonValue: {
      flex: 1,
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
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
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      color: theme.text,
    },
  });
