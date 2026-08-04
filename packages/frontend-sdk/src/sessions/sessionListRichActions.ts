import type { SessionSummary } from '../types/sessions';
import {
  resolveSessionListPath,
  type SessionListActionElement,
  type SessionListListRichUi,
  type SessionListRichActionPlacement,
  type SessionListRichUiBase,
  type SessionListRichUi,
  type SessionListToggleRichUi,
} from './sessionListContracts';
import type { SessionListOption } from './sessionListFilters';

export const SESSION_LIST_RICH_ACTION_KINDS = ['toggle', 'list'] as const;

export type SessionListRichActionKind =
  (typeof SESSION_LIST_RICH_ACTION_KINDS)[number];

export const DEFAULT_SESSION_LIST_RICH_ACTION_PLACEMENTS = ['actions_bar'] as const;

export interface SessionListRichToggleState {
  kind: 'toggle';
  value: unknown;
  active: boolean;
  tone: SessionListToggleRichUi['appearance']['active']['tone'];
}

export interface SessionListRichListState {
  kind: 'list';
  value: unknown;
  currentOption: SessionListOption | null;
  tone: SessionListOption['tone'] | undefined;
}

export type SessionListRichActionState =
  | SessionListRichToggleState
  | SessionListRichListState;

function typedEqual(left: unknown, right: unknown): boolean {
  return typeof left === typeof right && left === right;
}

function isToggleRichUi(
  richUi: SessionListRichUi | undefined,
): richUi is SessionListToggleRichUi {
  return (
    richUi?.kind === 'toggle' &&
    typeof (richUi as any).value_path === 'string' &&
    typeof (richUi as any).active_value !== 'undefined' &&
    typeof (richUi as any).appearance === 'object'
  );
}

function isListRichUi(
  richUi: SessionListRichUi | undefined,
): richUi is SessionListListRichUi {
  return (
    richUi?.kind === 'list' &&
    typeof (richUi as any).value_path === 'string' &&
    typeof (richUi as any).input_name === 'string' &&
    Array.isArray((richUi as any).options)
  );
}

export function resolveSessionListRichValue(
  summary: SessionSummary,
  richUi: SessionListRichUiBase,
): unknown {
  const resolved = resolveSessionListPath(summary, richUi.value_path);
  if (resolved.found) {
    return resolved.value;
  }
  return richUi.missing_value;
}

export function resolveSessionListRichActionState(
  element: SessionListActionElement,
  summary: SessionSummary,
): SessionListRichActionState | null {
  const richUi = element.rich_ui;
  if (isToggleRichUi(richUi)) {
    const value = resolveSessionListRichValue(summary, richUi);
    const active = typedEqual(value, richUi.active_value);
    return {
      kind: 'toggle',
      value,
      active,
      tone: active
        ? richUi.appearance.active.tone
        : richUi.appearance.inactive.tone,
    };
  }

  if (isListRichUi(richUi)) {
    const value = resolveSessionListRichValue(summary, richUi);
    const currentOption =
      richUi.options.find((option) => typedEqual(value, option.value)) ?? null;
    return {
      kind: 'list',
      value,
      currentOption,
      tone: currentOption?.tone,
    };
  }
  return null;
}

/**
 * Returns `null` when the value is already current. Callers close their rich
 * list in that case without invoking the ordinary application action.
 */
export function buildSessionListRichListDialogValues(
  richUi: SessionListListRichUi,
  currentValue: unknown,
  selectedValue: unknown,
): Record<string, string | boolean> | null {
  if (typedEqual(currentValue, selectedValue)) {
    return null;
  }
  const option = richUi.options.find((item) =>
    typedEqual(item.value, selectedValue),
  );
  if (!option) {
    return null;
  }
  return { [richUi.input_name]: option.value };
}

export function getDefaultPinnedSessionListActionKeys(
  elements: readonly SessionListActionElement[],
): string[] {
  return elements
    .filter((element) => element.rich_ui?.default_pinned === true)
    .map((element) => element.id);
}

export function getSessionListRichActionPlacements(
  element: SessionListActionElement,
): readonly string[] {
  const placements = element.rich_ui?.placements;
  return Array.isArray(placements) && placements.length > 0
    ? placements
    : DEFAULT_SESSION_LIST_RICH_ACTION_PLACEMENTS;
}

export function isSessionListRichActionPlacedAt(
  element: SessionListActionElement,
  placement: SessionListRichActionPlacement,
): boolean {
  return getSessionListRichActionPlacements(element).includes(placement);
}

/**
 * Header slots intentionally choose one action. Input order is declaration
 * order from the registry, so the first matching action wins deterministically.
 */
export function selectSessionListRichActionForPlacement(
  elements: readonly SessionListActionElement[],
  placement: Exclude<SessionListRichActionPlacement, 'actions_bar'>,
  supportedKinds: ReadonlySet<string> | readonly string[] = SESSION_LIST_RICH_ACTION_KINDS,
): SessionListActionElement | null {
  return (
    elements.find((element) => {
      const richUi = element.rich_ui;
      if (!richUi || !isSessionListRichActionPlacedAt(element, placement)) {
        return false;
      }
      return Array.isArray(supportedKinds)
        ? supportedKinds.includes(richUi.kind)
        : (supportedKinds as ReadonlySet<string>).has(richUi.kind);
    }) ?? null
  );
}

export function orderPinnedSessionListActionKeys(
  declaredKeys: readonly string[],
  pinnedKeys: readonly string[],
): string[] {
  const pinned = new Set(pinnedKeys);
  return declaredKeys.filter((key) => pinned.has(key));
}