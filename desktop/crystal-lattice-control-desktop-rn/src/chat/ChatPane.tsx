import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react';
import {
  ActivityIndicator,
  Alert,
  Clipboard,
  Linking,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  findNodeHandle,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import {
  ActionsMenuBar,
  ChatActivityRow,
  ComposerEditContext,
  ApplicationActionDialog,
  getLastActionsPopoverAnchorTag,
  RichConfigDropdownControl,
  RichConfigDropdownPanel,
  RichConfigToggleControl,
  runComposedMessageSubmission,
  SessionListRichActionControl,
  SessionListRichActionList,
  SessionRequestStatusIndicator,
  LOCAL_NOTE_SESSION_ACTION_KEY,
  LOCAL_WATCHLIST_SESSION_ACTION_KEY,
  buildLocalSessionActionDefinitions,
  isLocalSessionActionKey,
  useTheme,
  type ActionDefinition,
  type ActionKey,
} from '@crystal-lattice/frontend-rn-components';
import type {
  ActionDisplayFollowupAction,
  ActionUiElement,
  ActionDisplayPayload,
  AgentBackend,
  ApiMessage,
  IndexedMessage,
  RunActionContext,
  SessionSummary,
  SessionRequestStatus,
} from '@crystal-lattice/frontend-sdk';
import {
  attachmentDraftStatusLabel,
  resolveAttachmentActionPluginId,
  deleteSessionAttachment,
  deriveSessionListPresentationFromGroups,
  emitDisplayPresentation,
  filterFooterElements,
  generateIdempotencyKey,
  getDefaultPinnedConfigRichUiKeys,
  groupSessionListFields,
  isSessionActionPlacedAt,
  isAttachmentDraftBlocking,
  mergeSessionScopedActionElements,
  normalizeSessionActionRichUiElements,
  normalizeActionDisplayForSurface,
  normalizeDisplayEnvelope,
  NotificationUiEffectObserver,
  observeSessionNotificationUiEffects,
  resolveConfigRichUiMenuStateLabel,
  resolveConfigRichToggleOption,
  resolveSessionListRichActionState,
  runApplicationAction,
  selectConfigRichUiControls,
  selectSessionAssetId,
  selectDisplayContent,
  selectTranscriptRangeRestoreAnchor,
  storeSessionAttachment,
  subscribeSessionRefreshInvalidations,
  type ComposerAttachmentUiElement as SharedComposerAttachmentUiElement,
  type ConfigRichDropdownUi,
  type ConfigRichToggleUi,
  type ConfigRichUiControl,
  type SessionActionRichUiElement,
  type AttachmentDraftStatus,
  type TranscriptViewportAnchorCandidate,
} from '@crystal-lattice/frontend-sdk';
import {
  useApplicationPlugins,
  buildConfigSchemaByKey,
  buildSessionSettingItems,
  useChatController,
  useHydrateControllerFromCache,
  usePersistentPinnedActions,
  usePluginActionDialog,
  useDisplayFollowupDialog,
  useSessionSettingsController,
  useSessionUiSchemaController,
  useSessionApplicationUiSchemaController,
  useSessionChatWorkspace,
  type PendingChatRequest,
} from '@crystal-lattice/frontend-sdk-react';
import {
  MacTextView,
  type MacTextViewHandle,
} from '@crystal-lattice/react-native-mac-text-view';

import type { MessagesCacheEntry } from '../cache/types';
import type { TabStripStyle } from '../tabs/tabStripStyle';
import { asyncStorageKeyValueStore } from '../storage/asyncStorageKeyValueStore';
import { desktopEventBus } from '../events/desktopEventBus';
import { truncateByChars } from '../utils/text';
import { DependencyFlatList } from '../ui/DependencyFlatList';
import { DependencyVirtualizedScroll } from '../ui/DependencyVirtualizedScroll';
import { PlaceholderFlatList } from '../ui/PlaceholderFlatList';
import { ProgressiveScrollList } from '../ui/ProgressiveScrollList';
import { ActionResultInlineCard } from '../ui/ActionResultInlineCard';
import { DesktopConnectionDisplayRail } from '../ui/DesktopGlobalDisplayLayer';
import { DesktopSessionNotificationRail } from '../ui/DesktopSessionNotificationRail';
import { DesktopWindowManager } from '../windows/desktopWindowManager';
import { setActiveAgentPickerWindow } from '../windows/agentPickerCoordinator';
import {
  closeDesktopPopover,
  openDesktopPopover,
} from '../windows/desktopPopoverCoordinator';
import { MessageLimitPopoverContent } from '../windows/MessageLimitPopoverContent';
import { setActiveSessionSettingsWindow } from '../windows/sessionSettingsCoordinator';
import { setActiveSessionPluginsWindow } from '../windows/sessionPluginsCoordinator';
import { setActiveSessionSnapshotsWindow } from '../windows/sessionSnapshotsCoordinator';
import { useMacOSApplicationActionDialog } from '../windows/useMacOSApplicationActionDialog';
import { pickMacAttachment } from '../native/MacAttachmentPicker';
import { SnapshotReadonlyBanner } from './SnapshotReadonlyBanner';
import { sendComposerMessageAtomically } from './sendComposerMessage';
import { useDesktopHumanTimeTelemetry } from '../humanTimeTelemetry/DesktopHumanTimeTelemetryProvider';
import {
  AppendAsPopoverContent,
  type AppendAsRole,
} from './AppendAsPopoverContent';
import {
  buildAttachmentMetadataDefaults,
  hasEditableAttachmentMetadataFields,
  shouldPromptForAttachmentMetadata,
  type AttachmentMetadataUi,
} from './AttachmentMetadataPopoverContent';
import {
  AttachmentThumbnailStrip,
  type AttachmentLike,
} from './AttachmentThumbnailStrip';
import { AttachmentUrlPopoverContent } from './AttachmentUrlPopoverContent';
import {
  ComposerAttachmentPlusPopoverContent,
  type ComposerAttachmentPlusRow,
} from './ComposerAttachmentPlusPopoverContent';
import {
  ComposerAttachmentsExpandedPanel,
  type ComposerAttachmentDraftRow,
} from './ComposerAttachmentsExpandedPanel';
import DesktopMessageBubble from './DesktopMessageBubble';
import {
  ALL_MESSAGE_ACTIONS,
  type MessageActionDefinition,
  type MessageActionKey,
} from './messageActions';
import {
  getTranscriptRangeControlPresentation,
  planTranscriptRangeControlAction,
  type TranscriptRangeControlAction,
  type TranscriptRangeControlButton,
} from './messageRangeControls';
import { PinnedMessageActionsProvider } from './PinnedMessageActionsContext';
import { useSessionStatusBarParts } from './useSessionStatusBarParts';
import { usePersistedChatDraft } from './usePersistedChatDraft';
import { useProactiveChatScrollPersistence } from './useProactiveChatScrollPersistence';
import { openAttachmentMetadataWindow } from '../windows/attachmentMetadataCoordinator';
import { useSynchronizedPersistentPinnedActions } from './useSynchronizedPersistentPinnedActions';

const DEFAULT_HISTORY_WINDOW = 50;
const PINNED_SESSION_ACTIONS_STORAGE_KEY_BASE =
  'clc_pinned_chat_session_actions_v1';
const PINNED_COMPOSER_ACTIONS_STORAGE_KEY_BASE =
  'clc_pinned_chat_composer_actions_v1';
const PINNED_MESSAGE_ACTIONS_STORAGE_KEY_BASE =
  'clc_pinned_message_actions_by_role_v1';

const TRANSCRIPT_LIST_IMPLEMENTATION = ((globalThis as any)
  .CLC_TRANSCRIPT_LIST_IMPLEMENTATION ?? 'flatList') as
  | 'scrollView'
  | 'flatList'
  | 'virtualizedScroll'
  | 'progressiveScroll';

type DesktopTranscriptRow =
  | { kind: 'stream' }
  | { kind: 'message'; item: IndexedMessage };

function readGlobalBoolean(name: string, fallback: boolean): boolean {
  const value = (globalThis as any)[name];
  if (value === true || value === 'true') {
    return true;
  }
  if (value === false || value === 'false') {
    return false;
  }
  return fallback;
}

function readOptionalGlobalBoolean(name: string): boolean | undefined {
  const value = (globalThis as any)[name];
  if (value === true || value === 'true') {
    return true;
  }
  if (value === false || value === 'false') {
    return false;
  }
  return undefined;
}

function readOptionalGlobalNumber(name: string): number | undefined {
  const value = Number((globalThis as any)[name]);
  return Number.isFinite(value) && value > 0 ? value : undefined;
}

function readOptionalGlobalString<T extends string>(
  name: string,
  allowed: ReadonlyArray<T>,
): T | undefined {
  const value = (globalThis as any)[name];
  return typeof value === 'string' && allowed.includes(value as T)
    ? (value as T)
    : undefined;
}

const FLATLIST_DISABLE_VIRTUALIZATION = readGlobalBoolean(
  'CLC_FLATLIST_DISABLE_VIRTUALIZATION',
  false,
);
const FLATLIST_EAGER_RENDER_THRESHOLD = readOptionalGlobalNumber(
  'CLC_FLATLIST_EAGER_RENDER_THRESHOLD',
);
const FLATLIST_INITIAL_NUM_TO_RENDER = readOptionalGlobalNumber(
  'CLC_FLATLIST_INITIAL_NUM_TO_RENDER',
);
const FLATLIST_MAX_TO_RENDER_PER_BATCH = readOptionalGlobalNumber(
  'CLC_FLATLIST_MAX_TO_RENDER_PER_BATCH',
);
const FLATLIST_UPDATE_CELLS_BATCHING_PERIOD = readOptionalGlobalNumber(
  'CLC_FLATLIST_UPDATE_CELLS_BATCHING_PERIOD',
);
const FLATLIST_WINDOW_SIZE = readOptionalGlobalNumber(
  'CLC_FLATLIST_WINDOW_SIZE',
);
const FLATLIST_REMOVE_CLIPPED_SUBVIEWS = readOptionalGlobalBoolean(
  'CLC_FLATLIST_REMOVE_CLIPPED_SUBVIEWS',
);
const FLATLIST_INVERTED = readGlobalBoolean('CLC_FLATLIST_INVERTED', true);
const FLATLIST_FORWARD_SCROLL_END_DRAG = readGlobalBoolean(
  'CLC_FLATLIST_FORWARD_SCROLL_END_DRAG',
  true,
);
const FLATLIST_FORWARD_MOMENTUM_SCROLL_END = readGlobalBoolean(
  'CLC_FLATLIST_FORWARD_MOMENTUM_SCROLL_END',
  true,
);
const FLATLIST_BOTTOM_SCROLL_THRESHOLD_PX =
  readOptionalGlobalNumber('CLC_FLATLIST_BOTTOM_SCROLL_THRESHOLD_PX') ?? 4;
const FLATLIST_BOTTOM_CONVERGENCE_STABLE_MS =
  readOptionalGlobalNumber('CLC_FLATLIST_BOTTOM_CONVERGENCE_STABLE_MS') ?? 200;
const FLATLIST_BOTTOM_CONVERGENCE_MAX_MS =
  readOptionalGlobalNumber('CLC_FLATLIST_BOTTOM_CONVERGENCE_MAX_MS') ?? 3000;
const FLATLIST_CONTENT_FOLLOW_LEASE_MS =
  readOptionalGlobalNumber('CLC_FLATLIST_CONTENT_FOLLOW_LEASE_MS') ??
  readOptionalGlobalNumber('CLC_FLATLIST_BOTTOM_FOLLOW_WINDOW_MS') ??
  1000;
const FLATLIST_MANUAL_BOTTOM_CONVERGENCE_MAX_MS =
  readOptionalGlobalNumber('CLC_FLATLIST_MANUAL_BOTTOM_CONVERGENCE_MAX_MS') ??
  readOptionalGlobalNumber('CLC_FLATLIST_MANUAL_BOTTOM_FOLLOW_WINDOW_MS') ??
  3000;
const FLATLIST_INITIAL_BOTTOM_CONVERGENCE_MAX_MS =
  readOptionalGlobalNumber('CLC_FLATLIST_INITIAL_BOTTOM_CONVERGENCE_MAX_MS') ??
  readOptionalGlobalNumber('CLC_FLATLIST_INITIAL_BOTTOM_FOLLOW_WINDOW_MS') ??
  5000;
const FLATLIST_MAX_EDGE_CORRECTIONS =
  readOptionalGlobalNumber('CLC_FLATLIST_MAX_EDGE_CORRECTIONS') ?? 12;
const FLATLIST_ITEM_ANCHOR_TIMEOUT_MS =
  readOptionalGlobalNumber('CLC_FLATLIST_ITEM_ANCHOR_TIMEOUT_MS') ?? 3000;
const FLATLIST_ITEM_ANCHOR_MAX_ATTEMPTS =
  readOptionalGlobalNumber('CLC_FLATLIST_ITEM_ANCHOR_MAX_ATTEMPTS') ?? 50;
const FLATLIST_BOTTOM_LOCK = readGlobalBoolean(
  'CLC_FLATLIST_BOTTOM_LOCK',
  true,
);
const PROGRESSIVE_SCROLL_INITIAL_WINDOW_SIZE =
  readOptionalGlobalNumber('CLC_PROGRESSIVE_SCROLL_INITIAL_WINDOW_SIZE') ?? 50;
const PROGRESSIVE_SCROLL_PAGE_SIZE =
  readOptionalGlobalNumber('CLC_PROGRESSIVE_SCROLL_PAGE_SIZE') ?? 50;
const PROGRESSIVE_SCROLL_MAX_WINDOW_SIZE =
  readOptionalGlobalNumber('CLC_PROGRESSIVE_SCROLL_MAX_WINDOW_SIZE') ?? 100;
const PROGRESSIVE_SCROLL_AUTO_LOAD = readGlobalBoolean(
  'CLC_PROGRESSIVE_SCROLL_AUTO_LOAD',
  false,
);
const PROGRESSIVE_SCROLL_EDGE_THRESHOLD_PX =
  readOptionalGlobalNumber('CLC_PROGRESSIVE_SCROLL_EDGE_THRESHOLD_PX') ?? 240;
const PROGRESSIVE_SCROLL_PREBUILD_ROWS = readGlobalBoolean(
  'CLC_PROGRESSIVE_SCROLL_PREBUILD_ROWS',
  true,
);
const PROGRESSIVE_SCROLL_ANCHOR_BEFORE_COUNT =
  readOptionalGlobalNumber('CLC_PROGRESSIVE_SCROLL_ANCHOR_BEFORE_COUNT') ?? 40;
const PROGRESSIVE_SCROLL_ANCHOR_AFTER_COUNT =
  readOptionalGlobalNumber('CLC_PROGRESSIVE_SCROLL_ANCHOR_AFTER_COUNT') ?? 59;
const PROGRESSIVE_SCROLL_ACTION_TIMEOUT_MS =
  readOptionalGlobalNumber('CLC_PROGRESSIVE_SCROLL_ACTION_TIMEOUT_MS') ?? 3000;
const PROGRESSIVE_SCROLL_EDGE_EPSILON_PX =
  readOptionalGlobalNumber('CLC_PROGRESSIVE_SCROLL_EDGE_EPSILON_PX') ?? 20;
const PROGRESSIVE_SCROLL_EDGE_STABLE_MS =
  readOptionalGlobalNumber('CLC_PROGRESSIVE_SCROLL_EDGE_STABLE_MS') ?? 200;
const PROGRESSIVE_SCROLL_BACKING_LIST =
  readOptionalGlobalString('CLC_PROGRESSIVE_SCROLL_BACKING_LIST', [
    'scrollView',
    'flatList',
  ] as const) ?? 'scrollView';
const PROGRESSIVE_SCROLL_GROW_ONLY = readGlobalBoolean(
  'CLC_PROGRESSIVE_SCROLL_GROW_ONLY',
  false,
);
const TRANSCRIPT_RANGE_CONTROLS = readGlobalBoolean(
  'CLC_TRANSCRIPT_RANGE_CONTROLS',
  false,
);
const TRANSCRIPT_RANGE_CONTROL_PAGE_SIZE =
  readOptionalGlobalNumber('CLC_TRANSCRIPT_RANGE_CONTROL_PAGE_SIZE') ??
  DEFAULT_HISTORY_WINDOW;
const TRANSCRIPT_RANGE_CONTROL_MAX_RANGE =
  readOptionalGlobalNumber('CLC_TRANSCRIPT_RANGE_CONTROL_MAX_RANGE') ??
  DEFAULT_HISTORY_WINDOW * 2;

const DEFAULT_PINNED_MESSAGE_ACTIONS_BY_ROLE: Record<
  string,
  MessageActionKey[]
> = {
  user: ['modify', 'copy'],
  assistant: ['modify', 'toggleMarkdown', 'copy'],
  system: ['modify', 'copy'],
  tool: ['copy'],
};

type ChatSessionActionKey =
  | 'reload'
  | 'agentSwitch'
  | 'messageLimit'
  | 'settings'
  | 'plugins'
  | 'snapshots'
  | typeof LOCAL_NOTE_SESSION_ACTION_KEY
  | typeof LOCAL_WATCHLIST_SESSION_ACTION_KEY;

type ChatComposerActionKey =
  | 'append'
  | 'appendAs'
  | 'resend'
  | 'softCancel'
  | 'cancel';

type ComposerAttachmentUiElement = SharedComposerAttachmentUiElement & {
  ui_type: 'composer_attachment';
  key?: string;
  plugin?: string;
  attachment_action_plugin?: string;
  attachment_type?: string;
  supported_file_types?: string[];
  supports_upload?: boolean;
  supports_url?: boolean;
  display_placement?: 'above' | 'below' | string;
  label?: string;
  icon?: string;
  metadata_ui?: AttachmentMetadataUi;
  [k: string]: any;
};

type ComposerRichConfigControl = {
  control: ConfigRichUiControl;
  effectiveValue: unknown;
  hasOverride: boolean;
  disabled: boolean;
};

type ComposerAttachmentDraft = {
  draftId: string;
  type: string;
  content: any;
  metadata?: Record<string, any> | null;
  previewUrl?: string | null;
  status: AttachmentDraftStatus;
  errorMessage?: string | null;
  schemaKey?: string;
  plugin?: string;
  placement: 'above' | 'below';
};

type AttachmentBackgroundOperation =
  | { kind: 'upload'; filename: string }
  | { kind: 'delete'; filename: string }
  | null;

type PluginActionContext =
  | { kind: 'session'; sessionSummary: SessionSummary | null }
  | {
      kind: 'message';
      index: number;
      message: ApiMessage;
      sessionSummary: SessionSummary | null;
    };

type ActionDisplayEntry = {
  key: string;
  display: ActionDisplayPayload;
  context: RunActionContext;
};

function createDisplayEntry(
  display: ActionDisplayPayload,
  context: RunActionContext,
): ActionDisplayEntry {
  const key =
    typeof display.display_id === 'string' && display.display_id
      ? display.display_id
      : `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  return { key, display, context };
}

function upsertInlineDisplay(
  current: ActionDisplayEntry[],
  nextEntry: ActionDisplayEntry,
): ActionDisplayEntry[] {
  const displayId = nextEntry.display.display_id;
  if (typeof displayId === 'string' && displayId) {
    const existingIndex = current.findIndex(
      entry => entry.display.display_id === displayId,
    );
    if (existingIndex >= 0) {
      const updated = current.slice();
      updated[existingIndex] = nextEntry;
      return updated;
    }
  }
  return [...current, nextEntry];
}

const BUILTIN_SESSION_ACTIONS: ActionDefinition[] = [
  { key: 'reload', label: 'Reload', iconName: 'refresh-ccw', order: 0 },
  {
    key: 'messageLimit',
    label: 'Message limit',
    iconName: 'sliders',
    order: 20,
  },
  { key: 'agentSwitch', label: 'Switch agent', iconName: 'user', order: 25 },
  { key: 'settings', label: 'Settings…', iconName: 'settings', order: 90 },
  { key: 'plugins', label: 'Plugins…', iconName: 'package', order: 91 },
  { key: 'snapshots', label: 'Snapshots…', iconName: 'camera', order: 92 },
];

const BUILTIN_COMPOSER_ACTIONS: ActionDefinition[] = [
  {
    key: 'append',
    label: 'Append',
    iconName: 'plus-circle',
    order: 100,
    testID: 'composer-action-append',
  },
  {
    key: 'appendAs',
    label: 'Append as…',
    iconName: 'layers',
    order: 110,
    testID: 'composer-action-append-as',
  },
  {
    key: 'resend',
    label: 'Resend',
    iconName: 'repeat',
    order: 120,
    testID: 'composer-action-resend',
  },
  {
    key: 'cancel',
    label: 'Cancel',
    iconName: 'x-circle',
    order: 130,
    testID: 'composer-action-cancel',
  },
  {
    key: 'softCancel',
    label: 'Soft cancel request',
    iconName: 'pause-circle',
    order: 125,
    testID: 'composer-action-soft-cancel',
  },
];

const DEFAULT_PINNED_SESSION_ACTION_KEYS: ActionKey[] = ['reload'];
const DEFAULT_PINNED_COMPOSER_ACTION_KEYS: ActionKey[] = [
  'append',
  'resend',
  'cancel',
];

export interface ChatPaneProps {
  isVisible: boolean;
  isActive: boolean;
  connectionId: string;
  connectionName: string;
  sessionId: string;
  sessionSummary?: SessionSummary | null;
  title: string;
  subtitle?: string;
  backend: AgentBackend | null;
  cachedEntry: MessagesCacheEntry | null;
  messagesCacheHydrated?: boolean;
  onOpenSessionTab?: (params: {
    connectionId: string;
    sessionId: string;
    title?: string;
    subtitle?: string | null;
  }) => void;
  onUpdateCache: (params: {
    connectionId: string;
    sessionId: string;
    messages: IndexedMessage[];
    cursorEventId?: string | null;
    activeRequestId?: string | null;
    rangeStartText?: string | null;
    rangeEndText?: string | null;
    composeText?: string;
    scrollAnchor?: unknown;
  }) => void;
  requestStatus?: SessionRequestStatus | null;
  onBeforeSessionMutation?: () => void;
  sessionNote?: string | null;
  localActionsEnabled?: boolean;
  sessionWatched?: boolean;
  onEditSessionNote?: () => void;
  onToggleSessionWatchlist?: () => void;
  styleVariant?: TabStripStyle;
}

export const ChatPane = React.memo(function ChatPane({
  isVisible,
  isActive,
  connectionId,
  connectionName,
  sessionId,
  sessionSummary,
  title,
  subtitle,
  backend,
  cachedEntry,
  messagesCacheHydrated = true,
  onOpenSessionTab,
  onUpdateCache,
  requestStatus = null,
  onBeforeSessionMutation,
  sessionNote = null,
  localActionsEnabled = true,
  sessionWatched = false,
  onEditSessionNote,
  onToggleSessionWatchlist,
  styleVariant = 'toolbarTabs',
}: ChatPaneProps): React.JSX.Element {
  const theme = useTheme();
  const {
    state: workspaceState,
    update: updateWorkspace,
    get: getWorkspace,
    runAction,
  } = useSessionChatWorkspace(connectionId, sessionId);
  const editingIndex = workspaceState.edit?.index ?? null;
  const runningHeaderActionIds = useMemo(() => new Set(
    Object.keys(workspaceState.actions)
      .map(key => JSON.parse(key) as [string, string, string, number | null])
      .filter(entry => entry[2] === sessionId && entry[3] == null)
      .map(entry => entry[1]),
  ), [sessionId, workspaceState.actions]);
  const sendInFlight = workspaceState.submitting;
  const setSendInFlight = useCallback((submitting: boolean) => {
    updateWorkspace(current => ({ ...current, submitting }));
  }, [updateWorkspace]);
  const {
    recordActivity: recordHumanTimeActivity,
    splitForComposedMessage: splitHumanTimeForComposedMessage,
  } = useDesktopHumanTimeTelemetry();
  const recordSessionActivity = useCallback(
    () => recordHumanTimeActivity(connectionId, sessionId),
    [connectionId, recordHumanTimeActivity, sessionId],
  );
  const splitSessionForComposedMessage = useCallback(
    () => splitHumanTimeForComposedMessage(connectionId, sessionId),
    [connectionId, sessionId, splitHumanTimeForComposedMessage],
  );
  const styles = useMemo(
    () => createStyles(theme, styleVariant),
    [theme, styleVariant],
  );
  const [paneHeight, setPaneHeight] = useState(0);
  const compactLayout = paneHeight > 0 && paneHeight < 650;
  const sessionBaseActions = useMemo(
    () => [
      ...BUILTIN_SESSION_ACTIONS,
      ...buildLocalSessionActionDefinitions({
        watched: sessionWatched,
        hasNote: !!sessionNote,
        includeNote: !!onEditSessionNote,
        includeWatchlist: !!onToggleSessionWatchlist,
      }),
    ],
    [onEditSessionNote, onToggleSessionWatchlist, sessionNote, sessionWatched],
  );

  const [messageViewModeByIndex, setMessageViewModeByIndex] = useState<
    Record<number, 'markdown' | 'raw'>
  >({});
  const [pinnedMessageActionsByRole, setPinnedMessageActionsByRole] = useState<
    Record<string, MessageActionKey[]>
  >({});

  const [loadError, setLoadError] = useState<string | null>(null);
  const [rangeStartText, setRangeStartText] = useState(
    cachedEntry?.rangeStartText ?? `-${DEFAULT_HISTORY_WINDOW}`,
  );
  const [rangeEndText, setRangeEndText] = useState(
    cachedEntry?.rangeEndText ?? '',
  );
  const didHydrateRangeFromCacheRef = useRef(false);
  const [lastReloadAt, setLastReloadAt] = useState<Date | null>(null);
  const [messageLimitVisible, setMessageLimitVisible] = useState(false);
  const [appendInFlight, setAppendInFlight] = useState(false);
  const [reloadInFlight, setReloadInFlight] = useState(false);
  const reloadInFlightRef = useRef(false);
  const [cancelInFlight, setCancelInFlight] = useState(false);
  const [softCancelInFlight, setSoftCancelInFlight] = useState(false);
  const [softCancelledRequestId, setSoftCancelledRequestId] = useState<
    string | null
  >(null);
  const [inlineActionDisplays, setInlineActionDisplays] = useState<
    ActionDisplayEntry[]
  >([]);
  const [activeDisplayActionId, setActiveDisplayActionId] = useState<
    string | null
  >(null);
  const [notificationEvents, setNotificationEvents] = useState<any[]>([]);
  const [attachmentBackgroundOperation, setAttachmentBackgroundOperation] =
    useState<AttachmentBackgroundOperation>(null);
  const [openingAgentPicker, setOpeningAgentPicker] = useState(false);
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(
    null,
  );
  const [activeRichConfigControl, setActiveRichConfigControl] =
    useState<ComposerRichConfigControl | null>(null);
  const [activeRichSessionAction, setActiveRichSessionAction] =
    useState<SessionActionRichUiElement | null>(null);
  const composerRef = useRef<MacTextViewHandle | null>(null);
  const attachmentPlusButtonRef = useRef<any>(null);
  const richConfigControlRefs = useRef<Record<string, any>>({});
  const attemptedInitialLoadRef = useRef(false);
  const pendingPersistTimerRef = useRef<ReturnType<typeof setTimeout> | null>(
    null,
  );
  const lastPersistKeyRef = useRef<string | null>(null);
  const rangeNavigationOperationRef = useRef(0);
  const [pendingRangeRestore, setPendingRangeRestore] = useState<{
    operationId: number;
    messageIndex: number;
    offsetFromViewportTop: number;
  } | null>(null);

  const cancelRangeNavigation = useCallback(() => {
    rangeNavigationOperationRef.current += 1;
    setPendingRangeRestore(null);
  }, []);

  useEffect(() => cancelRangeNavigation, [cancelRangeNavigation, sessionId]);

  const [composerHeight, setComposerHeight] = useState(34);
  const handleComposerHeightChange = useCallback((height: number) => {
    const next = Math.round(height);
    setComposerHeight(prev => {
      if (Math.abs(prev - next) < 1) {
        return prev;
      }
      return next;
    });
  }, []);

  // Debug logging removed; composer uses native MacTextView on macOS.

  const handleChatEvents = useCallback((events: any[]) => {
    const relevant = events.filter(event =>
      String(event.type).startsWith('session_notification_'),
    );
    if (relevant.length > 0) {
      setNotificationEvents(current => [...current, ...relevant].slice(-100));
    }
  }, []);

  // Sync the UI range state when the controller falls back to the default
  // range (e.g. an absolute range no longer selects messages after session
  // compaction). The persist effect then writes the default texts to the
  // messages cache automatically.
  const handleRangeFallback = useCallback((range: {
    start?: number;
    end?: number;
  }) => {
    setRangeStartText(range.start != null ? String(range.start) : '');
    setRangeEndText(range.end != null ? String(range.end) : '');
  }, []);

  const { controller: chatController, state: chatState } = useChatController({
    backend,
    sessionId,
    initialMessages: cachedEntry?.messages ?? [],
    initialEventsCursorId: cachedEntry?.cursorEventId ?? null,
    initialActiveRequestId: cachedEntry?.activeRequestId ?? null,
    eventsEnabled: isActive && backend != null,
    onRangeFallback: handleRangeFallback,
  });

  const pinnedSessionActionsStorageKey = useMemo(() => {
    return `${PINNED_SESSION_ACTIONS_STORAGE_KEY_BASE}:${connectionId}`;
  }, [connectionId]);

  const {
    pinned: pinnedSessionActionKeys,
    setPinned: setPinnedSessionActionKeys,
    hasStoredPreference: hasStoredSessionActionPreference,
  } = useSynchronizedPersistentPinnedActions<ActionKey>({
    store: asyncStorageKeyValueStore,
    key: pinnedSessionActionsStorageKey,
    initialPinned: DEFAULT_PINNED_SESSION_ACTION_KEYS,
  });

  const pinnedComposerActionsStorageKey = useMemo(() => {
    return `${PINNED_COMPOSER_ACTIONS_STORAGE_KEY_BASE}:${connectionId}`;
  }, [connectionId]);

  const {
    pinned: pinnedComposerActionKeys,
    setPinned: setPinnedComposerActionKeys,
    hasStoredPreference: hasStoredComposerActionPreference,
  } = usePersistentPinnedActions<ActionKey>({
    store: asyncStorageKeyValueStore,
    key: pinnedComposerActionsStorageKey,
    initialPinned: DEFAULT_PINNED_COMPOSER_ACTION_KEYS,
  });

  const pinnedMessageActionsStorageKey = useMemo(
    () => `${PINNED_MESSAGE_ACTIONS_STORAGE_KEY_BASE}:${connectionId}`,
    [connectionId],
  );

  useEffect(() => {
    const loadPinnedFromStorage = async () => {
      console.log(
        'Loading pinned message actions from storage with key',
        pinnedMessageActionsStorageKey,
      );
      try {
        const messageRaw = await asyncStorageKeyValueStore.get(
          pinnedMessageActionsStorageKey,
        );
        if (messageRaw) {
          try {
            const parsed = JSON.parse(messageRaw);
            if (parsed && typeof parsed === 'object') {
              const next: Record<string, MessageActionKey[]> = {};
              Object.entries(parsed).forEach(([role, value]) => {
                if (Array.isArray(value)) {
                  const filtered = (value as any[]).filter(
                    key => typeof key === 'string',
                  );
                  next[role] = filtered as MessageActionKey[];
                }
              });
              setPinnedMessageActionsByRole(next);
            }
          } catch (err) {
            console.log('Failed to parse stored pinned message actions', err);
          }
          return;
        }
      } catch (err) {
        console.log('Failed to load pinned message actions from storage', err);
      }
    };

    loadPinnedFromStorage();
  }, [connectionId, pinnedMessageActionsStorageKey]);

  useEffect(() => {
    const saveMessagePinned = async () => {
      console.log(
        'Saving pinned message actions to storage with key',
        pinnedMessageActionsStorageKey,
        pinnedMessageActionsByRole,
      );
      try {
        await asyncStorageKeyValueStore.set(
          pinnedMessageActionsStorageKey,
          JSON.stringify(pinnedMessageActionsByRole),
        );
      } catch (err) {
        console.log('Failed to save pinned message actions', err);
      }
    };
    saveMessagePinned();
  }, [pinnedMessageActionsByRole, pinnedMessageActionsStorageKey]);

  const { state: sessionUiSchemaState } = useSessionUiSchemaController({
    backend,
    cacheKey: connectionId,
    sessionId,
    enabled: !!(backend && isActive),
  });
  const { state: sessionAppUiSchemaState } =
    useSessionApplicationUiSchemaController({
      backend,
      cacheKey: connectionId,
      sessionId,
      enabled: !!(backend && isActive),
    });
  const { controller: sessionSettingsController, state: sessionSettingsState } =
    useSessionSettingsController({
      backend,
      cacheKey: connectionId,
      sessionId,
      enabled: !!(backend && isActive),
    });

  const { actionsById, sessionListFields } = useApplicationPlugins();

  const sessionListFieldGroups = useMemo(
    () => groupSessionListFields(sessionListFields || []),
    [sessionListFields],
  );

  const displayTitle = useMemo(() => {
    if (sessionSummary) {
      const presentation = deriveSessionListPresentationFromGroups(
        sessionSummary,
        sessionListFieldGroups,
      );
      return truncateByChars(
        presentation.title || sessionSummary.preview || sessionId,
        80,
      );
    }

    const titleSource =
      typeof title === 'string' && title.trim() ? title : sessionId;
    return truncateByChars(titleSource, 80);
  }, [sessionId, sessionListFieldGroups, sessionSummary, title]);

  const displaySubtitle = useMemo(() => {
    if (sessionSummary) {
      const presentation = deriveSessionListPresentationFromGroups(
        sessionSummary,
        sessionListFieldGroups,
      );
      const subtitleSource =
        presentation.subtitle ?? sessionSummary.preview ?? '';
      return truncateByChars(subtitleSource, 80);
    }

    const subtitleSource =
      typeof subtitle === 'string' && subtitle.trim() ? subtitle : '';
    return truncateByChars(subtitleSource, 80);
  }, [sessionListFieldGroups, sessionSummary, subtitle]);

  const uiSchemaElements = useMemo(
    () => sessionUiSchemaState?.elements ?? [],
    [sessionUiSchemaState?.elements],
  );

  // Session-scoped application UI elements (from /sessions/{id}/application/ui-schema)
  // These are config-aware and filter based on the session's agent config.
  // Used ONLY for session_action and message_action in the chat context.
  // Do NOT combine with global application UI elements from useApplicationPlugins().
  const sessionAppUiElements = useMemo(
    () => sessionAppUiSchemaState?.elements ?? [],
    [sessionAppUiSchemaState?.elements],
  );

  // Session-scoped actions for chat context (config-aware)
  const visibleSessionActions = useMemo(
    () =>
      mergeSessionScopedActionElements({
        applicationActions: sessionAppUiElements.filter(
          (el): el is ActionUiElement =>
            (el as any).ui_type === 'session_action',
        ),
        uiSchemaElements,
        uiType: 'session_action',
      }),
    [sessionAppUiElements, uiSchemaElements],
  );
  const visibleMessageActions = useMemo(
    () =>
      mergeSessionScopedActionElements({
        applicationActions: sessionAppUiElements.filter(
          (el): el is ActionUiElement =>
            (el as any).ui_type === 'message_action',
        ),
        uiSchemaElements,
        uiType: 'message_action',
      }),
    [sessionAppUiElements, uiSchemaElements],
  );
  const configSchemaByKey = useMemo(
    () => buildConfigSchemaByKey(sessionSettingsState?.configSchema ?? []),
    [sessionSettingsState?.configSchema],
  );
  const sessionSettingItems = useMemo(
    () =>
      buildSessionSettingItems({
        elements: sessionSettingsState?.elements ?? [],
        overrides: sessionSettingsState?.overrides ?? {},
        baseConfig: sessionSettingsState?.baseConfig ?? {},
        schemaByKey: configSchemaByKey,
      }),
    [
      configSchemaByKey,
      sessionSettingsState?.baseConfig,
      sessionSettingsState?.elements,
      sessionSettingsState?.overrides,
    ],
  );
  const sessionSettingItemByKey = useMemo(
    () => Object.fromEntries(sessionSettingItems.map(item => [item.key, item])),
    [sessionSettingItems],
  );
  const composerRichConfigControls = useMemo(() => {
    const selected = selectConfigRichUiControls(
      sessionSettingsState?.elements ?? [],
      'composer',
    );
    return selected.controls
      .filter(
        control =>
          control.richUi.kind === 'dropdown' ||
          control.richUi.kind === 'toggle',
      )
      .map(control => {
        const item = sessionSettingItemByKey[control.element.key];
        return {
          control,
          effectiveValue: item?.effectiveValue,
          hasOverride: item?.hasOverride ?? false,
          disabled: item?.disabled ?? false,
        } satisfies ComposerRichConfigControl;
      });
  }, [sessionSettingItemByKey, sessionSettingsState?.elements]);
  const composerRichConfigControlByActionKey = useMemo(
    () =>
      Object.fromEntries(
        composerRichConfigControls.map(entry => [
          `config:${entry.control.element.key}`,
          entry,
        ]),
      ),
    [composerRichConfigControls],
  );
  const normalizedSessionActions = useMemo(
    () => normalizeSessionActionRichUiElements(visibleSessionActions).elements,
    [visibleSessionActions],
  );
  const headerSessionActions = useMemo(
    () =>
      normalizedSessionActions.filter(
        element =>
          !element.rich_ui ||
          isSessionActionPlacedAt(element, 'session_header'),
      ),
    [normalizedSessionActions],
  );
  const composerSessionActions = useMemo(
    () =>
      normalizedSessionActions.filter(
        element =>
          !!element.rich_ui && isSessionActionPlacedAt(element, 'composer'),
      ),
    [normalizedSessionActions],
  );
  const composerSessionActionByActionKey = useMemo(
    () =>
      Object.fromEntries(
        composerSessionActions.map(element => [
          `session_action:${element.id}`,
          element,
        ]),
      ),
    [composerSessionActions],
  );
  const footerElements = useMemo(
    () => filterFooterElements(uiSchemaElements),
    [uiSchemaElements],
  );

  const composerAttachmentElements = useMemo(() => {
    return (uiSchemaElements || []).filter(
      (el): el is ComposerAttachmentUiElement =>
        el &&
        typeof el === 'object' &&
        (el as any).ui_type === 'composer_attachment' &&
        typeof (el as any).attachment_type === 'string',
    );
  }, [uiSchemaElements]);

  const composerAttachmentElementByActionKey = useMemo(() => {
    const map: Record<string, ComposerAttachmentUiElement> = {};
    composerAttachmentElements.forEach(el => {
      const attachmentType = String((el as any).attachment_type ?? '');
      if (!attachmentType) {
        return;
      }
      const key =
        typeof (el as any).key === 'string' && (el as any).key
          ? String((el as any).key)
          : `${String(
              (el as any).plugin ?? 'unknown',
            )}:attachment:${attachmentType}`;
      map[key] = el;
    });
    return map;
  }, [composerAttachmentElements]);

  const composerAttachmentPlusRows =
    useMemo((): ComposerAttachmentPlusRow[] => {
      const rows: ComposerAttachmentPlusRow[] = [];
      composerAttachmentElements.forEach(el => {
        const attachmentType = String((el as any).attachment_type ?? '');
        if (!attachmentType) {
          return;
        }
        const label =
          typeof (el as any).label === 'string' && (el as any).label
            ? String((el as any).label)
            : attachmentType;
        const baseKey =
          typeof (el as any).key === 'string' && (el as any).key
            ? String((el as any).key)
            : `${String(
                (el as any).plugin ?? 'unknown',
              )}:attachment:${attachmentType}`;

        const iconName =
          typeof (el as any).icon === 'string' && (el as any).icon
            ? String((el as any).icon)
            : 'paperclip';

        const supportsUpload = Boolean((el as any).supports_upload ?? true);
        if (supportsUpload) {
          rows.push({
            id: `${baseKey}:file`,
            label: `Select ${label}…`,
            iconName,
          });
        }

        const supportsUrl = Boolean((el as any).supports_url ?? true);
        if (supportsUrl) {
          rows.push({
            id: `${baseKey}:url`,
            label: `${label} URL…`,
            iconName: 'link',
          });
        }
      });

      return rows;
    }, [composerAttachmentElements]);

  const attachmentsAbove = workspaceState.attachmentDrafts.above as ComposerAttachmentDraft[];
  const attachmentsBelow = workspaceState.attachmentDrafts.below as ComposerAttachmentDraft[];
  const setAttachmentsAbove = useCallback((next: React.SetStateAction<ComposerAttachmentDraft[]>) => {
    updateWorkspace(current => ({
      ...current,
      attachmentDrafts: {
        ...current.attachmentDrafts,
        above: typeof next === 'function'
          ? next(current.attachmentDrafts.above as ComposerAttachmentDraft[])
          : next,
      },
    }));
  }, [updateWorkspace]);
  const setAttachmentsBelow = useCallback((next: React.SetStateAction<ComposerAttachmentDraft[]>) => {
    updateWorkspace(current => ({
      ...current,
      attachmentDrafts: {
        ...current.attachmentDrafts,
        below: typeof next === 'function'
          ? next(current.attachmentDrafts.below as ComposerAttachmentDraft[])
          : next,
      },
    }));
  }, [updateWorkspace]);
  const [attachmentsAboveExpanded, setAttachmentsAboveExpanded] =
    useState(false);
  const [attachmentsBelowExpanded, setAttachmentsBelowExpanded] =
    useState(false);

  const hasAttachments = attachmentsAbove.length + attachmentsBelow.length > 0;

  const richActionSession = useMemo<SessionSummary>(
    () =>
      sessionSummary ?? {
        session_id: sessionId,
        modified: 0,
        preview: '',
        metadata: {},
      },
    [sessionId, sessionSummary],
  );

  const pluginSessionActionDefs: ActionDefinition[] = useMemo(() => {
    if (!backend) {
      return [];
    }

    return headerSessionActions
      .map(el => {
        const richState = el.rich_ui
          ? resolveSessionListRichActionState(el as any, richActionSession)
          : null;
        return {
          key: el.id,
          label: el.label,
          iconName: (el as any).icon || 'zap',
          menuStateLabel:
            richState?.kind === 'toggle'
              ? richState.active
                ? 'On'
                : 'Off'
              : richState?.kind === 'list'
              ? richState.currentOption?.label
              : undefined,
          order: typeof el.order === 'number' ? el.order : undefined,
        };
      })
      .filter(def => typeof def.key === 'string' && def.key);
  }, [backend, headerSessionActions, richActionSession]);

  const composerPluginActionDefs: ActionDefinition[] = useMemo(
    () => [
      ...composerRichConfigControls.map(entry => {
        const richUi = entry.control.richUi as
          | ConfigRichDropdownUi
          | ConfigRichToggleUi;
        return {
          key: `config:${entry.control.element.key}`,
          label: entry.control.element.label || richUi.label,
          iconName: entry.control.element.icon || 'sliders',
          menuStateLabel: resolveConfigRichUiMenuStateLabel(
            richUi,
            entry.effectiveValue,
          ),
          order:
            typeof (entry.control.element as any).order === 'number'
              ? (entry.control.element as any).order
              : 10,
        };
      }),
      ...composerSessionActions.map(element => {
        const richState = resolveSessionListRichActionState(
          element as any,
          richActionSession,
        );
        return {
          key: `session_action:${element.id}`,
          label: element.label,
          iconName: (element as any).icon || 'zap',
          menuStateLabel:
            richState?.kind === 'toggle'
              ? richState.active
                ? 'On'
                : 'Off'
              : richState?.kind === 'list'
              ? richState.currentOption?.label
              : undefined,
          order: typeof element.order === 'number' ? element.order : undefined,
        };
      }),
    ],
    [composerRichConfigControls, composerSessionActions, richActionSession],
  );

  const defaultPinnedComposerUiActionKeys = useMemo(
    () => [
      ...getDefaultPinnedConfigRichUiKeys(
        composerRichConfigControls.map(entry => entry.control),
      ).map(key => `config:${key}`),
      ...composerSessionActions
        .filter(element => element.rich_ui?.default_pinned === true)
        .map(element => `session_action:${element.id}`),
    ],
    [composerRichConfigControls, composerSessionActions],
  );
  useEffect(() => {
    if (
      hasStoredComposerActionPreference ||
      defaultPinnedComposerUiActionKeys.length === 0
    ) {
      return;
    }
    setPinnedComposerActionKeys(current => [
      ...current,
      ...defaultPinnedComposerUiActionKeys.filter(
        key => !current.includes(key),
      ),
    ]);
  }, [
    defaultPinnedComposerUiActionKeys,
    hasStoredComposerActionPreference,
    setPinnedComposerActionKeys,
  ]);

  const defaultPinnedHeaderSessionActionKeys = useMemo(
    () =>
      headerSessionActions
        .filter(element => element.rich_ui?.default_pinned === true)
        .map(element => element.id),
    [headerSessionActions],
  );
  useEffect(() => {
    if (
      hasStoredSessionActionPreference ||
      defaultPinnedHeaderSessionActionKeys.length === 0
    ) {
      return;
    }
    setPinnedSessionActionKeys(current => [
      ...current,
      ...defaultPinnedHeaderSessionActionKeys.filter(
        key => !current.includes(key),
      ),
    ]);
  }, [
    defaultPinnedHeaderSessionActionKeys,
    hasStoredSessionActionPreference,
    setPinnedSessionActionKeys,
  ]);

  const pinnedComposerActionKeysForBar = pinnedComposerActionKeys;

  const pluginMessageActionDefs: MessageActionDefinition[] = useMemo(() => {
    if (!backend) {
      return [];
    }

    return (visibleMessageActions || [])
      .map(el => ({
        key: el.id,
        label: el.label,
        iconName: (el as any).icon || 'zap',
        defaultPinnedRoles: ['user', 'assistant', 'system', 'tool'],
        allowedRoles: ['user', 'assistant', 'system', 'tool'],
      }))
      .filter(def => typeof def.key === 'string' && def.key);
  }, [backend, visibleMessageActions]);

  const hydrateFromCache = useCallback(
    (
      controller: NonNullable<typeof chatController>,
      cache: {
        messages: IndexedMessage[];
        eventsCursorId: string | null;
        activeRequestId: string | null;
        updatedAtMs: number | null;
      },
    ) => {
      const snapshot = controller.getSnapshot();
      const hasInitialSnapshot =
        snapshot.eventsCursorId != null || snapshot.messages.length > 0;
      if (hasInitialSnapshot) {
        return;
      }
      controller.hydrateFromCache(cache);
    },
    [],
  );

  useHydrateControllerFromCache({
    controller: chatController,
    cache:
      cachedEntry != null
        ? {
            messages: cachedEntry.messages,
            eventsCursorId: cachedEntry.cursorEventId ?? null,
            activeRequestId: cachedEntry.activeRequestId ?? null,
            updatedAtMs: cachedEntry.lastLoadedAt ?? null,
          }
        : null,
    hydrate: hydrateFromCache,
  });

  useEffect(() => {
    if (didHydrateRangeFromCacheRef.current) {
      return;
    }

    const cachedStartText = cachedEntry?.rangeStartText ?? null;
    const cachedEndText = cachedEntry?.rangeEndText ?? null;
    if (cachedStartText == null && cachedEndText == null) {
      return;
    }

    const defaultStartText = `-${DEFAULT_HISTORY_WINDOW}`;
    const defaultEndText = '';
    const userChangedRange =
      rangeStartText !== defaultStartText || rangeEndText !== defaultEndText;
    if (userChangedRange) {
      didHydrateRangeFromCacheRef.current = true;
      return;
    }

    const nextStartText = cachedStartText ?? defaultStartText;
    const nextEndText = cachedEndText ?? defaultEndText;
    if (rangeStartText === nextStartText && rangeEndText === nextEndText) {
      didHydrateRangeFromCacheRef.current = true;
      return;
    }

    setRangeStartText(nextStartText);
    setRangeEndText(nextEndText);
    didHydrateRangeFromCacheRef.current = true;
  }, [
    cachedEntry?.rangeEndText,
    cachedEntry?.rangeStartText,
    rangeEndText,
    rangeStartText,
  ]);

  useEffect(() => {
    if (!chatController) {
      return;
    }

    chatController.setHistoryRangeFromRangeText({
      startText: rangeStartText,
      endText: rangeEndText,
    });
  }, [chatController, rangeEndText, rangeStartText]);

  useEffect(() => {
    attemptedInitialLoadRef.current = false;
    setLoadError(null);
  }, [chatController]);

  const loadInitialMessages = useCallback(async () => {
    if (!chatController) {
      return;
    }

    try {
      setLoadError(null);
      await chatController.loadMessagesFromRangeText({
        startText: rangeStartText,
        endText: rangeEndText,
      });
      const snapshot = chatController.getCacheSnapshot();
      setLastReloadAt(new Date(snapshot.updatedAtMs ?? Date.now()));
    } catch (err: any) {
      const message =
        typeof err?.message === 'string' && err.message
          ? err.message
          : 'Failed to load messages.';
      setLoadError(message);
      Alert.alert('Failed to load messages', message);
    }
  }, [chatController, rangeEndText, rangeStartText]);

  const refreshSelectedSnapshot = useCallback(async () => {
    if (!backend) {
      setSelectedSnapshotId(null);
      return;
    }
    try {
      const next = await backend.getSelectedSessionSnapshot(sessionId);
      setSelectedSnapshotId(next);
    } catch {
      setSelectedSnapshotId(null);
    }
  }, [backend, sessionId]);

  const handleClearSelectedSnapshot = useCallback(async () => {
    if (!backend) {
      return;
    }
    try {
      await backend.clearSelectedSessionSnapshot(sessionId);
      await refreshSelectedSnapshot();
    } catch (err: any) {
      const message =
        typeof err?.message === 'string' && err.message
          ? err.message
          : 'Failed to return to live session.';
      Alert.alert('Error', message);
    }
  }, [backend, refreshSelectedSnapshot, sessionId]);

  useEffect(() => {
    if (!backend) {
      setSelectedSnapshotId(null);
      return;
    }
    void refreshSelectedSnapshot();
  }, [backend, refreshSelectedSnapshot]);

  useEffect(() => {
    if (!chatController) {
      return;
    }
    chatController.setEventsListener(events => {
      handleChatEvents(events);
      let needsRefresh = false;
      for (const ev of events) {
        const type = (ev as any)?.type;
        if (
          type === 'session_snapshot_selected' ||
          type === 'session_snapshot_cleared' ||
          type === 'session_restored_from_snapshot'
        ) {
          needsRefresh = true;
          break;
        }
      }
      if (needsRefresh) {
        void refreshSelectedSnapshot();
      }
    });
    return () => {
      chatController.setEventsListener(null);
    };
  }, [chatController, handleChatEvents, refreshSelectedSnapshot]);

  const persistCacheSnapshot = useCallback(() => {
    if (!chatController) {
      return;
    }

    const snapshot = chatController.getCacheSnapshot();
    onUpdateCache({
      connectionId,
      sessionId,
      messages: snapshot.messages,
      cursorEventId: snapshot.eventsCursorId,
      activeRequestId: snapshot.activeRequestId,
      rangeStartText,
      rangeEndText,
    });
  }, [
    chatController,
    connectionId,
    onUpdateCache,
    rangeEndText,
    rangeStartText,
    sessionId,
  ]);

  useEffect(() => {
    if (!chatController) {
      return;
    }

    const snapshot = chatController.getCacheSnapshot();
    const messages = snapshot.messages;
    const firstIndex = messages[0]?.index ?? -1;
    const lastIndex = messages[messages.length - 1]?.index ?? -1;
    const nextKey = [
      messages.length,
      firstIndex,
      lastIndex,
      snapshot.eventsCursorId ?? '',
      snapshot.activeRequestId ?? '',
      rangeStartText,
      rangeEndText,
    ].join('|');

    if (nextKey === lastPersistKeyRef.current) {
      return;
    }
    lastPersistKeyRef.current = nextKey;

    if (pendingPersistTimerRef.current) {
      clearTimeout(pendingPersistTimerRef.current);
    }

    pendingPersistTimerRef.current = setTimeout(() => {
      pendingPersistTimerRef.current = null;
      persistCacheSnapshot();
    }, 250);
  }, [
    chatController,
    chatState?.activeRequestId,
    chatState?.eventsCursorId,
    chatState?.messages,
    persistCacheSnapshot,
    rangeEndText,
    rangeStartText,
  ]);

  useEffect(() => {
    return () => {
      if (pendingPersistTimerRef.current) {
        clearTimeout(pendingPersistTimerRef.current);
        pendingPersistTimerRef.current = null;
      }
      persistCacheSnapshot();
    };
  }, [persistCacheSnapshot]);

  useEffect(() => {
    if (!isActive) {
      return;
    }
    if (!chatController) {
      return;
    }
    if (chatState?.loading) {
      return;
    }

    const hasInitialSnapshot =
      chatState?.eventsCursorId != null ||
      (Array.isArray(chatState?.messages) && chatState.messages.length > 0);
    if (hasInitialSnapshot) {
      return;
    }

    if (attemptedInitialLoadRef.current) {
      return;
    }

    attemptedInitialLoadRef.current = true;
    loadInitialMessages().catch(() => {
      // errors are handled in `loadInitialMessages`
    });
  }, [
    chatController,
    chatState?.eventsCursorId,
    chatState?.loading,
    chatState?.messages,
    isActive,
    loadInitialMessages,
  ]);

  const messages: IndexedMessage[] = useMemo(() => {
    return chatState?.messages ?? cachedEntry?.messages ?? [];
  }, [chatState?.messages, cachedEntry?.messages]);

  useEffect(() => {
    if (!isVisible || !chatController) return;
    const snapshot = chatController.getSnapshot();
    if (snapshot.messages.length === 0 && snapshot.eventsCursorId == null) return;
    let cancelled = false;
    void chatController.recoverAfterResume().catch((error: Error) => {
      if (!cancelled) setLoadError(error.message);
    });
    return () => { cancelled = true; };
  }, [chatController, isVisible]);

  const messagesForCacheRef = useRef<IndexedMessage[]>(messages);
  useEffect(() => {
    messagesForCacheRef.current = messages;
  }, [messages]);

  const getMessagesForCache = useCallback(() => {
    return messagesForCacheRef.current ?? [];
  }, []);

  const {
    composeText,
    setComposeText,
    composeTextRef,
    handleChangeText: handleComposerChangeText,
    initialText: initialComposeText,
  } = usePersistedChatDraft({
    connectionId,
    sessionId,
    cachedComposeText: cachedEntry?.composeText,
    getMessagesForCache,
    onUpdateCache,
    composerRef: editingIndex == null ? composerRef : undefined,
  });

  useEffect(() => {
    composerRef.current?.setText(getWorkspace().edit?.text ?? composeTextRef.current);
    if (editingIndex != null) composerRef.current?.focus();
  }, [editingIndex, getWorkspace, composeTextRef]);

  const streamingRow = chatState?.streamingRow ?? null;
  const bottomContentRevisionRef = useRef(0);
  const bottomContentRevision = useMemo(() => {
    bottomContentRevisionRef.current += 1;
    return {
      sequence: bottomContentRevisionRef.current,
      messageCount: messages.length,
      lastMessageIndex:
        messages.length > 0 ? messages[messages.length - 1].index : null,
      streamingRequestId: streamingRow?.requestId ?? null,
      inlineDisplayCount: inlineActionDisplays.length,
    };
  }, [inlineActionDisplays, messages, streamingRow]);

  const transcriptScroll = useProactiveChatScrollPersistence({
    connectionId,
    sessionId,
    cachedScrollAnchor: cachedEntry?.scrollAnchor,
    getMessagesForCache,
    onUpdateCache,
    enabled: isActive,
    restoreReady: messagesCacheHydrated,
    bottomThresholdPx: FLATLIST_BOTTOM_SCROLL_THRESHOLD_PX,
    bottomConvergenceStableMs: FLATLIST_BOTTOM_CONVERGENCE_STABLE_MS,
    bottomConvergenceMaxMs: FLATLIST_BOTTOM_CONVERGENCE_MAX_MS,
    contentFollowLeaseMs: FLATLIST_CONTENT_FOLLOW_LEASE_MS,
    manualBottomConvergenceMaxMs: FLATLIST_MANUAL_BOTTOM_CONVERGENCE_MAX_MS,
    initialBottomConvergenceMaxMs: FLATLIST_INITIAL_BOTTOM_CONVERGENCE_MAX_MS,
    maxEdgeCorrections: FLATLIST_MAX_EDGE_CORRECTIONS,
    contentFollowEnabled:
      TRANSCRIPT_LIST_IMPLEMENTATION === 'progressiveScroll'
        ? false
        : FLATLIST_BOTTOM_LOCK,
    bottomContentRevision,
    messageAnchorBeforeCount: PROGRESSIVE_SCROLL_ANCHOR_BEFORE_COUNT,
    messageAnchorAfterCount: PROGRESSIVE_SCROLL_ANCHOR_AFTER_COUNT,
    messageViewportAnchorsEnabled:
      TRANSCRIPT_LIST_IMPLEMENTATION === 'progressiveScroll' ||
      TRANSCRIPT_LIST_IMPLEMENTATION === 'flatList',
    listEdgeMethodsEnabled:
      TRANSCRIPT_LIST_IMPLEMENTATION === 'progressiveScroll',
    onUserNavigationIntent: cancelRangeNavigation,
    onUserScrollActivity: recordSessionActivity,
  });

  useEffect(() => {
    if (
      !pendingRangeRestore ||
      rangeNavigationOperationRef.current !== pendingRangeRestore.operationId
    ) {
      return;
    }
    if (
      !messages.some(entry => entry.index === pendingRangeRestore.messageIndex)
    ) {
      return;
    }
    transcriptScroll.listRef.current?.scrollToItemAnchor?.({
      key: `msg-${pendingRangeRestore.messageIndex}`,
      offsetFromViewportTop: pendingRangeRestore.offsetFromViewportTop,
      animated: false,
    });
    setPendingRangeRestore(null);
  }, [messages, pendingRangeRestore, transcriptScroll.listRef]);

  const requestPersistTranscriptScroll = transcriptScroll.requestPersist;

  const prevIsVisibleRef = useRef(isVisible);
  useEffect(() => {
    const prev = prevIsVisibleRef.current;
    prevIsVisibleRef.current = isVisible;
    if (prev && !isVisible) {
      requestPersistTranscriptScroll('tabHidden', {
        force: true,
        immediate: true,
      });
    }
  }, [isVisible, requestPersistTranscriptScroll]);

  const {
    statusBarParts,
    ensureAgentDescriptorsLoaded,
    agentsLoading,
  } =
    useSessionStatusBarParts({
      backend,
      connectionId,
      sessionId,
      isActive,
      uiSchemaElements,
      messages,
      streamingRow,
      sessionSummary: sessionSummary ?? null,
    });

  const messagesCount = messages.length;
  const draftAttachments = [...attachmentsAbove, ...attachmentsBelow];
  const blockingAttachmentDraft =
    draftAttachments.find(draft => isAttachmentDraftBlocking(draft.status)) ??
    null;
  const unresolvedAttachmentDraft =
    draftAttachments.find(
      draft => draft.status !== 'ready' && draft.status !== 'local',
    ) ?? null;
  const attachmentActionInProgress =
    attachmentBackgroundOperation != null || blockingAttachmentDraft != null;
  const attachmentActionText =
    attachmentBackgroundOperation?.kind === 'upload'
      ? `Uploading ${attachmentBackgroundOperation.filename}...`
      : attachmentBackgroundOperation?.kind === 'delete'
      ? `Deleting ${attachmentBackgroundOperation.filename}...`
      : blockingAttachmentDraft
      ? `${attachmentDraftStatusLabel(
          blockingAttachmentDraft.status,
          blockingAttachmentDraft.errorMessage,
        )} ${
          blockingAttachmentDraft.content?.filename ??
          blockingAttachmentDraft.type
        }...`
      : '';

  const canSend =
    backend != null &&
    chatController != null &&
    isActive &&
    !sendInFlight &&
    !workspaceState.recovery &&
    !chatState?.activeRequestId &&
    !attachmentActionInProgress &&
    !unresolvedAttachmentDraft &&
    !selectedSnapshotId;

  const canSendNow =
    editingIndex != null
      ? backend != null && chatController != null && !selectedSnapshotId &&
        !workspaceState.modifying && !!workspaceState.edit?.text.trim()
      : canSend && (composeText.trim().length > 0 || hasAttachments);
  const requestInProgress = sendInFlight || workspaceState.modifying || Boolean(chatState?.activeRequestId);

  const buildMultipartContentPayload = useCallback(() => {
    const mapDraft = (d: ComposerAttachmentDraft) => ({
      type: d.type,
      content: d.content,
      metadata: d.metadata,
    });
    return [
      ...attachmentsAbove.map(mapDraft),
      ...attachmentsBelow.map(mapDraft),
    ];
  }, [attachmentsAbove, attachmentsBelow]);

  const clearComposerAttachments = useCallback(() => {
    setAttachmentsAbove([]);
    setAttachmentsBelow([]);
    setAttachmentsAboveExpanded(false);
    setAttachmentsBelowExpanded(false);
  }, []);

  const deleteStoredAttachmentAsset = useCallback(
    async (
      assetId: string,
      filename?: string,
      suppressAlert = false,
      pluginId?: string | null,
    ) => {
      if (!backend) {
        return false;
      }
      setAttachmentBackgroundOperation({
        kind: 'delete',
        filename: filename || 'attachment',
      });
      try {
        const resolvedPluginId =
          typeof pluginId === 'string' ? pluginId.trim() : '';
        if (!resolvedPluginId) {
          throw new Error(
            'The attachment action did not identify its owning plugin.',
          );
        }
        await deleteSessionAttachment({
          backend,
          sessionId,
          assetId,
          pluginId: resolvedPluginId,
        });
      } catch (err: any) {
        if (!suppressAlert) {
          const message = err?.message || 'Failed to delete attachment.';
          Alert.alert('Attachment error', message);
        }
        return false;
      } finally {
        setAttachmentBackgroundOperation(null);
      }
      return true;
    },
    [backend, sessionId],
  );

  const updateDraftMetadata = useCallback(
    (
      draftId: string,
      placement: 'above' | 'below',
      nextMetadata: Record<string, any>,
    ) => {
      const updater = (prev: ComposerAttachmentDraft[]) =>
        prev.map(d =>
          d.draftId === draftId ? { ...d, metadata: nextMetadata } : d,
        );
      if (placement === 'above') {
        setAttachmentsAbove(updater);
      } else {
        setAttachmentsBelow(updater);
      }
    },
    [],
  );

  const updateDraftState = useCallback(
    (
      draftId: string,
      placement: 'above' | 'below',
      updater: (draft: ComposerAttachmentDraft) => ComposerAttachmentDraft,
    ) => {
      const update = (prev: ComposerAttachmentDraft[]) =>
        prev.map(draft => (draft.draftId === draftId ? updater(draft) : draft));
      if (placement === 'above') {
        setAttachmentsAbove(update);
      } else {
        setAttachmentsBelow(update);
      }
    },
    [],
  );

  const openAttachmentMetadataEditorWindowForDraft = useCallback(
    (params: {
      draft: ComposerAttachmentDraft;
      element: ComposerAttachmentUiElement;
    }) => {
      const metadataUi = ((params.element as any).metadata_ui ??
        null) as AttachmentMetadataUi | null;
      if (!metadataUi) {
        Alert.alert(
          'No metadata',
          'This attachment type does not define metadata fields.',
        );
        return;
      }
      if (!hasEditableAttachmentMetadataFields(metadataUi)) {
        Alert.alert(
          'No metadata',
          'No metadata fields are defined for this attachment type.',
        );
        return;
      }

      const attachmentType = String(
        (params.element as any).attachment_type ?? params.draft.type,
      );
      const title =
        typeof (params.element as any).label === 'string' &&
        (params.element as any).label
          ? String((params.element as any).label)
          : attachmentType;

      openAttachmentMetadataWindow({
        id: `attachment-metadata:${connectionId}:${sessionId}:${params.draft.draftId}`,
        title: `${title} metadata`,
        attachmentType,
        attachmentContent: params.draft.content,
        metadataUi,
        initialMetadata: params.draft.metadata ?? {},
        onCancel: () => {},
        onSave: metadata => {
          updateDraftMetadata(
            params.draft.draftId,
            params.draft.placement,
            metadata,
          );
        },
      });
    },
    [connectionId, sessionId, updateDraftMetadata],
  );

  const findElementForDraft = useCallback(
    (draft: ComposerAttachmentDraft): ComposerAttachmentUiElement | null => {
      if (
        draft.schemaKey &&
        composerAttachmentElementByActionKey[draft.schemaKey]
      ) {
        return composerAttachmentElementByActionKey[draft.schemaKey];
      }

      const byType = composerAttachmentElements.find(
        el => String((el as any).attachment_type ?? '') === draft.type,
      );
      return byType ?? null;
    },
    [composerAttachmentElementByActionKey, composerAttachmentElements],
  );

  const addDraftAttachment = useCallback(
    (params: {
      element: ComposerAttachmentUiElement;
      content: any;
      placement: 'above' | 'below';
      metadata: Record<string, any>;
      previewUrl?: string | null;
      draftId?: string;
      status?: AttachmentDraftStatus;
      errorMessage?: string | null;
    }) => {
      const attachmentType = String(
        (params.element as any).attachment_type ?? '',
      );
      if (!attachmentType) {
        return null;
      }

      const actionKey =
        typeof (params.element as any).key === 'string' &&
        (params.element as any).key
          ? String((params.element as any).key)
          : `${String(
              (params.element as any).plugin ?? 'unknown',
            )}:attachment:${attachmentType}`;

      const draft: ComposerAttachmentDraft = {
        draftId:
          params.draftId ??
          `${Date.now()}-${Math.random().toString(36).slice(2)}`,
        type: attachmentType,
        content: params.content,
        metadata: params.metadata,
        previewUrl: params.previewUrl ?? null,
        status: params.status ?? 'ready',
        errorMessage: params.errorMessage ?? null,
        schemaKey: actionKey,
        plugin:
          typeof (params.element as any).plugin === 'string'
            ? (params.element as any).plugin
            : undefined,
        placement: params.placement,
      };

      const append = (prev: ComposerAttachmentDraft[]) => [...prev, draft];
      if (params.placement === 'above') {
        setAttachmentsAbove(append);
        return draft.draftId;
      }
      setAttachmentsBelow(append);
      return draft.draftId;
    },
    [],
  );

  const beginAddDraftAttachment = useCallback(
    (params: {
      element: ComposerAttachmentUiElement;
      content: any;
      placement: 'above' | 'below';
      previewUrl?: string | null;
      pendingAssetId?: string | null;
      draftId?: string | null;
    }) => {
      const metadataUi = ((params.element as any).metadata_ui ??
        null) as AttachmentMetadataUi | null;
      const defaults = buildAttachmentMetadataDefaults(metadataUi);

      if (
        shouldPromptForAttachmentMetadata({ metadataUi }) &&
        hasEditableAttachmentMetadataFields(metadataUi)
      ) {
        if (params.draftId) {
          updateDraftState(params.draftId, params.placement, draft => ({
            ...draft,
            status: 'stored',
            errorMessage: null,
          }));
        }
        const attachmentType = String(
          (params.element as any).attachment_type ?? '',
        );
        const title =
          typeof (params.element as any).label === 'string' &&
          (params.element as any).label
            ? String((params.element as any).label)
            : attachmentType;

        openAttachmentMetadataWindow({
          id: `attachment-metadata-new:${connectionId}:${sessionId}:${attachmentType}:${Date.now()}`,
          title: `${title} metadata`,
          attachmentType,
          attachmentContent: params.content,
          metadataUi,
          initialMetadata: defaults,
          onCancel: () => {
            if (params.pendingAssetId) {
              if (params.draftId) {
                updateDraftState(params.draftId, params.placement, draft => ({
                  ...draft,
                  status: 'deleting',
                  errorMessage: null,
                }));
              }
              deleteStoredAttachmentAsset(
                params.pendingAssetId,
                (params.content as any)?.filename,
                false,
                typeof (params.element as any).plugin === 'string'
                  ? String((params.element as any).plugin)
                  : undefined,
              )
                .then(deleted => {
                  if (deleted && params.draftId) {
                    const remove = (prev: ComposerAttachmentDraft[]) =>
                      prev.filter(draft => draft.draftId !== params.draftId);
                    if (params.placement === 'above') {
                      setAttachmentsAbove(remove);
                    } else {
                      setAttachmentsBelow(remove);
                    }
                  }
                })
                .catch(() => {});
            }
          },
          onSave: metadata => {
            if (params.draftId) {
              updateDraftState(params.draftId, params.placement, draft => ({
                ...draft,
                content: params.content,
                metadata,
                previewUrl: params.previewUrl ?? null,
                status: 'ready',
                errorMessage: null,
              }));
              return;
            }
            addDraftAttachment({
              element: params.element,
              placement: params.placement,
              content: params.content,
              metadata,
              previewUrl: params.previewUrl ?? null,
              status: 'ready',
            });
          },
        });
        return;
      }

      if (params.draftId) {
        updateDraftState(params.draftId, params.placement, draft => ({
          ...draft,
          content: params.content,
          metadata: defaults,
          previewUrl: params.previewUrl ?? null,
          status: 'ready',
          errorMessage: null,
        }));
        return;
      }

      addDraftAttachment({
        element: params.element,
        placement: params.placement,
        content: params.content,
        metadata: defaults,
        previewUrl: params.previewUrl ?? null,
        status: 'ready',
      });
    },
    [
      addDraftAttachment,
      connectionId,
      deleteStoredAttachmentAsset,
      sessionId,
      updateDraftState,
    ],
  );

  const storePickedAttachment = useCallback(
    async (params: {
      element: ComposerAttachmentUiElement;
      placement: 'above' | 'below';
      filename: string;
      mimeType: string;
      dataBase64: string;
    }) => {
      if (!backend) {
        throw new Error('Connect to a server before uploading attachments.');
      }
      const previewUrl =
        String((params.element as any).attachment_type ?? '') === 'image'
          ? `data:${params.mimeType};base64,${params.dataBase64}`
          : null;
      const draftId = addDraftAttachment({
        element: params.element,
        placement: params.placement,
        content: {
          filename: params.filename,
          mime_type: params.mimeType,
        },
        metadata: {},
        previewUrl,
        status: 'uploading_to_server',
      });
      if (!draftId) {
        throw new Error('Unable to create attachment draft.');
      }
      setAttachmentBackgroundOperation({
        kind: 'upload',
        filename: params.filename,
      });
      try {
        const resolvedPluginId = resolveAttachmentActionPluginId(
          params.element,
        );
        if (!resolvedPluginId) {
          throw new Error(
            'The attachment action did not identify its owning plugin.',
          );
        }
        const stored = await storeSessionAttachment({
          backend,
          sessionId,
          attachmentType: String((params.element as any).attachment_type ?? ''),
          filename: params.filename,
          mimeType: params.mimeType,
          dataBase64: params.dataBase64,
          pluginId: resolvedPluginId,
        });

        beginAddDraftAttachment({
          element: params.element,
          placement: params.placement,
          content: {
            asset_ref: stored.asset_ref,
            filename: stored.filename,
            mime_type: stored.mime_type,
          },
          previewUrl,
          pendingAssetId: stored.asset_ref.asset_id,
          draftId,
        });
      } catch (err: any) {
        updateDraftState(draftId, params.placement, draft => ({
          ...draft,
          status: 'failed',
          errorMessage:
            typeof err?.message === 'string' && err.message
              ? err.message
              : 'Upload failed',
        }));
        throw err;
      } finally {
        setAttachmentBackgroundOperation(null);
      }
    },
    [
      addDraftAttachment,
      backend,
      beginAddDraftAttachment,
      sessionId,
      updateDraftState,
    ],
  );

  const handleSend = useCallback(
    async (overrideText?: string) => {
      if (!canSendNow || !chatController || getWorkspace().edit ||
          getWorkspace().submitting || getWorkspace().recovery) {
        if (unresolvedAttachmentDraft) {
          Alert.alert(
            'Attachment not ready',
            'Resolve attachment upload issues before sending.',
          );
        }
        return;
      }

      const raw = overrideText ?? composeTextRef.current ?? composeText;
      const trimmed = String(raw ?? '').trim();
      const multipartContent = buildMultipartContentPayload();

      if (!trimmed && multipartContent.length === 0) {
        return;
      }

      const content = trimmed.length > 0 ? trimmed : '';
      const submission: PendingChatRequest = {
        kind: 'send_message',
        message: { role: 'user', content, multipartContent },
        idempotencyKey: generateIdempotencyKey(),
        requestedAtMs: Date.now(),
        errorMessage: '',
      };

      onBeforeSessionMutation?.();
      setSendInFlight(true);
      try {
        await runComposedMessageSubmission(
          splitSessionForComposedMessage,
          () =>
            sendComposerMessageAtomically(chatController, submission.message, submission.idempotencyKey),
        );
        setComposeText('');
        composerRef.current?.setText('');
        clearComposerAttachments();
        composerRef.current?.focus();
      } catch (err: any) {
        const message =
          typeof err?.message === 'string' && err.message
            ? err.message
            : 'Failed to send message.';
        updateWorkspace(current => ({
          ...current,
          recovery: { ...submission, errorMessage: message },
        }));
      } finally {
        setSendInFlight(false);
      }
    },
    [
      buildMultipartContentPayload,
      canSendNow,
      chatController,
      clearComposerAttachments,
      composeText,
      composeTextRef,
      getWorkspace,
      setComposeText,
      unresolvedAttachmentDraft,
      onBeforeSessionMutation,
      splitSessionForComposedMessage,
      setSendInFlight,
      updateWorkspace,
    ],
  );

  const canRunComposerActions =
    backend != null &&
    chatController != null &&
    isActive &&
    !selectedSnapshotId;

  const canOpenAttachmentPlus =
    canRunComposerActions &&
    editingIndex == null &&
    composerAttachmentPlusRows.length > 0 &&
    !attachmentActionInProgress;

  const appendMessageForRole = useCallback(
    async (role: AppendAsRole) => {
      if (getWorkspace().edit) return;
      const raw = composeTextRef.current || composeText;
      const content = String(raw ?? '').trim();
      const multipartContent = buildMultipartContentPayload();
      if (!content && multipartContent.length === 0) {
        return;
      }
      if (unresolvedAttachmentDraft) {
        Alert.alert(
          'Attachment not ready',
          'Resolve attachment upload issues before appending.',
        );
        return;
      }
      if (!canRunComposerActions) {
        Alert.alert('Offline', 'Connect to a server to append messages.');
        return;
      }
      if (appendInFlight || attachmentActionInProgress) {
        return;
      }

      onBeforeSessionMutation?.();
      setAppendInFlight(true);
      try {
        await runComposedMessageSubmission(
          splitSessionForComposedMessage,
          () =>
            chatController.appendMessage({
              role: role as any,
              content: content.length > 0 ? content : '',
              multipartContent,
            }),
        );
        composerRef.current?.focus();
      } catch (err: any) {
        const message = err?.message || 'Failed to append message.';
        Alert.alert('Failed to append', message);
      } finally {
        setAppendInFlight(false);
      }
    },
    [
      appendInFlight,
      attachmentActionInProgress,
      buildMultipartContentPayload,
      canRunComposerActions,
      chatController,
      composeText,
      composeTextRef,
      unresolvedAttachmentDraft,
      onBeforeSessionMutation,
      splitSessionForComposedMessage,
    ],
  );

  const handleAppend = useCallback(async () => {
    await appendMessageForRole('user');
  }, [appendMessageForRole]);

  const openAppendAsPopover = useCallback(() => {
    const raw = composeTextRef.current || composeText;
    const content = String(raw ?? '').trim();
    const multipartContent = buildMultipartContentPayload();
    if (!content && multipartContent.length === 0) {
      return;
    }
    if (unresolvedAttachmentDraft) {
      Alert.alert(
        'Attachment not ready',
        'Resolve attachment upload issues before appending.',
      );
      return;
    }
    if (!canRunComposerActions) {
      Alert.alert('Offline', 'Connect to a server to append messages.');
      return;
    }
    if (
      appendInFlight ||
      attachmentActionInProgress ||
      unresolvedAttachmentDraft
    ) {
      return;
    }

    if (Platform.OS !== 'macos') {
      Alert.alert('Append as', 'Choose a role for the appended message.', [
        { text: 'System', onPress: () => appendMessageForRole('system') },
        { text: 'Developer', onPress: () => appendMessageForRole('developer') },
        { text: 'User', onPress: () => appendMessageForRole('user') },
        { text: 'Assistant', onPress: () => appendMessageForRole('assistant') },
        { text: 'Cancel', style: 'cancel' },
      ]);
      return;
    }

    if (!DesktopWindowManager?.openMessageLimitPopover) {
      Alert.alert('Not supported', 'Append-as popover is not available.');
      return;
    }

    const id = `append-as:${connectionId}:${sessionId}`;
    openDesktopPopover({
      id,
      title: 'Append as',
      anchorTag: getLastActionsPopoverAnchorTag() ?? undefined,
      width: 360,
      height: 220,
      content: (
        <AppendAsPopoverContent
          popoverId={id}
          onSelectRole={role => {
            appendMessageForRole(role).catch(() => {});
          }}
        />
      ),
    });
  }, [
    appendMessageForRole,
    appendInFlight,
    attachmentActionInProgress,
    buildMultipartContentPayload,
    canRunComposerActions,
    composeText,
    composeTextRef,
    connectionId,
    sessionId,
    unresolvedAttachmentDraft,
  ]);

  const handleResend = useCallback(async () => {
    if (!canRunComposerActions) {
      Alert.alert('Offline', 'Connect to a server to resend.');
      return;
    }
    if (getWorkspace().submitting || getWorkspace().edit || getWorkspace().recovery || chatState?.activeRequestId) {
      return;
    }

    onBeforeSessionMutation?.();
    setSendInFlight(true);
    const submission: PendingChatRequest = {
      kind: 'send',
      idempotencyKey: generateIdempotencyKey(),
      requestedAtMs: Date.now(),
      errorMessage: '',
    };
    try {
      chatController.clearRequestState();
      await chatController.send({ idempotencyKey: submission.idempotencyKey });
      composerRef.current?.focus();
    } catch (err: any) {
      const message = err?.message || 'Failed to resend request.';
      updateWorkspace(current => ({ ...current, recovery: { ...submission, errorMessage: message } }));
    } finally {
      setSendInFlight(false);
    }
  }, [
    canRunComposerActions,
    chatController,
    chatState?.activeRequestId,
    onBeforeSessionMutation,
    sendInFlight,
    getWorkspace,
    setSendInFlight,
    updateWorkspace,
  ]);

  const handleRetryPendingRequest = useCallback(async () => {
    const pending = getWorkspace().recovery;
    if (!pending || !chatController || getWorkspace().submitting || getWorkspace().edit) return;
    setSendInFlight(true);
    try {
      chatController.clearRequestState();
      if (pending.kind === 'send_message') {
        await chatController.sendMessage({
          message: pending.message,
          idempotencyKey: pending.idempotencyKey,
          configOverrides: pending.configOverrides,
        });
        if (
          composeTextRef.current.trim() === pending.message.content &&
          JSON.stringify(buildMultipartContentPayload()) === JSON.stringify(pending.message.multipartContent ?? [])
        ) {
          setComposeText('');
          composerRef.current?.setText('');
          clearComposerAttachments();
        }
      } else {
        await chatController.send({ idempotencyKey: pending.idempotencyKey, configOverrides: pending.configOverrides });
      }
      updateWorkspace(current => ({ ...current, recovery: null }));
    } catch (error: any) {
      updateWorkspace(current => ({
        ...current,
        recovery: { ...pending, errorMessage: error?.message || 'Resend failed.' },
      }));
    } finally {
      setSendInFlight(false);
    }
  }, [buildMultipartContentPayload, chatController, clearComposerAttachments, composeTextRef, getWorkspace, setComposeText, setSendInFlight, updateWorkspace]);

  const handleCancel = useCallback(async () => {
    if (!canRunComposerActions) {
      return;
    }
    if (cancelInFlight) {
      return;
    }
    if (!chatState?.activeRequestId) {
      return;
    }

    setCancelInFlight(true);
    try {
      await chatController.cancelActiveRequest();
    } catch (err: any) {
      const message = err?.message || 'Failed to cancel request';
      Alert.alert('Failed to cancel', message);
    } finally {
      setCancelInFlight(false);
    }
  }, [
    canRunComposerActions,
    cancelInFlight,
    chatController,
    chatState?.activeRequestId,
  ]);

  const handleSoftCancel = useCallback(async () => {
    if (!canRunComposerActions) {
      return;
    }
    const activeRequestId = chatState?.activeRequestId;
    if (
      softCancelInFlight ||
      !activeRequestId ||
      softCancelledRequestId === activeRequestId
    ) {
      return;
    }

    setSoftCancelInFlight(true);
    try {
      await chatController.softCancelActiveRequest();
      setSoftCancelledRequestId(activeRequestId);
    } catch (err: any) {
      const message = err?.message || 'Failed to soft cancel request';
      Alert.alert('Failed to soft cancel', message);
    } finally {
      setSoftCancelInFlight(false);
    }
  }, [
    canRunComposerActions,
    chatController,
    chatState?.activeRequestId,
    softCancelInFlight,
    softCancelledRequestId,
  ]);

  const openAttachmentUrlPopover = useCallback(
    (params: { element: ComposerAttachmentUiElement; anchorTag?: number }) => {
      const attachmentType = String(
        (params.element as any).attachment_type ?? '',
      );
      const attachmentTitle =
        typeof (params.element as any).label === 'string' &&
        (params.element as any).label
          ? String((params.element as any).label)
          : attachmentType;

      const popoverId = `attachment-url:${connectionId}:${sessionId}:${attachmentType}`;
      openDesktopPopover({
        id: popoverId,
        title: 'Attach URL',
        anchorTag:
          params.anchorTag ?? getLastActionsPopoverAnchorTag() ?? undefined,
        width: 520,
        height: 200,
        content: (
          <AttachmentUrlPopoverContent
            title={attachmentTitle}
            onCancel={() => closeDesktopPopover(popoverId)}
            onAttach={url => {
              beginAddDraftAttachment({
                element: params.element,
                placement:
                  (params.element as any).display_placement === 'above'
                    ? 'above'
                    : 'below',
                content: {
                  url,
                },
              });
              closeDesktopPopover(popoverId);
            }}
          />
        ),
      });
    },
    [beginAddDraftAttachment, connectionId, sessionId],
  );

  const pickAttachmentFile = useCallback(
    async (params: { element: ComposerAttachmentUiElement }) => {
      const supported = Array.isArray(
        (params.element as any).supported_file_types,
      )
        ? ((params.element as any).supported_file_types as any[]).filter(
            v => typeof v === 'string',
          )
        : [];
      const allowedExtensions = supported.map(v => String(v));

      const picked = await pickMacAttachment({
        allowedExtensions,
        maxBytes: 15 * 1024 * 1024,
      });

      if (!picked) {
        return;
      }

      await storePickedAttachment({
        element: params.element,
        placement:
          (params.element as any).display_placement === 'above'
            ? 'above'
            : 'below',
        filename: picked.filename,
        mimeType: picked.mime_type,
        dataBase64: picked.data_base64,
      });
    },
    [storePickedAttachment],
  );

  const getAttachmentPlusAnchorTag = useCallback((): number | undefined => {
    const tag = attachmentPlusButtonRef.current
      ? (findNodeHandle(attachmentPlusButtonRef.current) as any)
      : null;
    return typeof tag === 'number' ? tag : undefined;
  }, []);

  const openComposerAttachmentPlusPopover = useCallback(() => {
    if (composerAttachmentPlusRows.length === 0) {
      return;
    }

    const anchorTag = getAttachmentPlusAnchorTag();
    const popoverId = `composer-attachments-plus:${connectionId}:${sessionId}`;

    openDesktopPopover({
      id: popoverId,
      title: 'Add attachment',
      anchorTag,
      width: 360,
      height: Math.min(200, 50 + composerAttachmentPlusRows.length * 52),
      content: (
        <ComposerAttachmentPlusPopoverContent
          rows={composerAttachmentPlusRows}
          onSelectRow={rowId => {
            closeDesktopPopover(popoverId);

            const method = rowId.endsWith(':url')
              ? 'url'
              : rowId.endsWith(':file')
              ? 'file'
              : null;
            if (!method) {
              return;
            }
            const baseKey = rowId.slice(0, -(method.length + 1));
            const element = composerAttachmentElementByActionKey[baseKey];
            if (!element) {
              return;
            }

            if (method === 'file') {
              pickAttachmentFile({ element }).catch((err: any) => {
                const message = err?.message || 'Failed to pick file.';
                Alert.alert('Failed to attach', message);
              });
              return;
            }

            openAttachmentUrlPopover({ element, anchorTag });
          }}
          onCancel={() => {
            closeDesktopPopover(popoverId);
          }}
        />
      ),
    });
  }, [
    composerAttachmentElementByActionKey,
    composerAttachmentPlusRows,
    connectionId,
    getAttachmentPlusAnchorTag,
    openAttachmentUrlPopover,
    pickAttachmentFile,
    sessionId,
  ]);

  const handleComposerAction = useCallback(
    (key: ActionKey) => {
      const action = key as ChatComposerActionKey;
      if (action === 'append') {
        handleAppend().catch(() => {});
        return;
      }
      if (action === 'appendAs') {
        openAppendAsPopover();
        return;
      }
      if (action === 'resend') {
        handleResend().catch(() => {});
        return;
      }
      if (action === 'cancel') {
        handleCancel().catch(() => {});
        return;
      }
      if (action === 'softCancel') {
        handleSoftCancel().catch(() => {});
        return;
      }
    },
    [
      handleAppend,
      handleCancel,
      handleResend,
      handleSoftCancel,
      openAppendAsPopover,
    ],
  );

  const buildAttachmentStripRows = useCallback(
    (drafts: ComposerAttachmentDraft[]): AttachmentLike[] => {
      return drafts.map(d => ({
        id: d.draftId,
        type: d.type,
        content: d.content,
        metadata: d.metadata,
        previewUrl: d.previewUrl,
        status: d.status,
        errorMessage: d.errorMessage,
      }));
    },
    [],
  );

  const buildManageRows = useCallback(
    (drafts: ComposerAttachmentDraft[]): ComposerAttachmentDraftRow[] => {
      return drafts.map(d => ({
        draftId: d.draftId,
        type: d.type,
        content: d.content,
        title:
          typeof d.metadata?.title === 'string' ? d.metadata?.title : undefined,
        status: d.status,
        errorMessage: d.errorMessage,
      }));
    },
    [],
  );

  const handleMoveDraft = useCallback(
    (
      placement: 'above' | 'below',
      draftId: string,
      direction: 'up' | 'down',
    ) => {
      const update = (prev: ComposerAttachmentDraft[]) => {
        const idx = prev.findIndex(d => d.draftId === draftId);
        if (idx === -1) return prev;
        const nextIdx = direction === 'up' ? idx - 1 : idx + 1;
        if (nextIdx < 0 || nextIdx >= prev.length) return prev;
        const next = [...prev];
        const [item] = next.splice(idx, 1);
        next.splice(nextIdx, 0, item);
        return next;
      };

      if (placement === 'above') {
        setAttachmentsAbove(update);
      } else {
        setAttachmentsBelow(update);
      }
    },
    [],
  );

  const handleDeleteDraft = useCallback(
    async (placement: 'above' | 'below', draftId: string) => {
      const list = placement === 'above' ? attachmentsAbove : attachmentsBelow;
      const draft = list.find(d => d.draftId === draftId);
      if (!draft) {
        return;
      }
      const update = (prev: ComposerAttachmentDraft[]) => {
        const next = prev.filter(d => d.draftId !== draftId);
        if (next.length === 0) {
          if (placement === 'above') {
            setAttachmentsAboveExpanded(false);
          } else {
            setAttachmentsBelowExpanded(false);
          }
        }
        return next;
      };

      const assetId = selectSessionAssetId(draft?.content);
      if (!assetId) {
        if (placement === 'above') {
          setAttachmentsAbove(update);
        } else {
          setAttachmentsBelow(update);
        }
        return;
      }

      const previousStatus = draft.status;
      updateDraftState(draftId, placement, current => ({
        ...current,
        status: 'deleting',
        errorMessage: null,
      }));
      const deleted = await deleteStoredAttachmentAsset(
        assetId,
        draft?.content?.filename,
        false,
        draft?.plugin,
      );
      if (deleted) {
        if (placement === 'above') {
          setAttachmentsAbove(update);
        } else {
          setAttachmentsBelow(update);
        }
        return;
      }

      updateDraftState(draftId, placement, current => ({
        ...current,
        status: previousStatus,
      }));
    },
    [
      attachmentsAbove,
      attachmentsBelow,
      deleteStoredAttachmentAsset,
      updateDraftState,
    ],
  );

  const handleEditDraftMetadata = useCallback(
    (placement: 'above' | 'below', draftId: string, _anchorTag?: number) => {
      const list = placement === 'above' ? attachmentsAbove : attachmentsBelow;
      const draft = list.find(d => d.draftId === draftId);
      if (!draft) return;
      const element = findElementForDraft(draft);
      if (!element) {
        Alert.alert(
          'Not supported',
          'Attachment metadata schema was not found.',
        );
        return;
      }
      openAttachmentMetadataEditorWindowForDraft({ draft, element });
    },
    [
      attachmentsAbove,
      attachmentsBelow,
      findElementForDraft,
      openAttachmentMetadataEditorWindowForDraft,
    ],
  );

  const canRunHeaderActions =
    backend != null && chatController != null && isActive;

  const handleReload = useCallback(async () => {
    if (!canRunHeaderActions) {
      return false;
    }
    // Guard with a ref so the callback identity (and therefore the
    // session-refresh invalidation subscription) stays stable across
    // reload attempts; the `reloadInFlight` state only drives the UI.
    if (reloadInFlightRef.current) {
      return false;
    }

    reloadInFlightRef.current = true;
    setReloadInFlight(true);
    try {
      setLoadError(null);
      chatController.clearRequestState();
      await chatController.loadMessagesFromRangeText({
        startText: rangeStartText,
        endText: rangeEndText,
      });
      const snapshot = chatController.getCacheSnapshot();
      setLastReloadAt(new Date(snapshot.updatedAtMs ?? Date.now()));
      return true;
    } catch (err: any) {
      const message =
        typeof err?.message === 'string' && err.message
          ? err.message
          : 'Failed to reload messages.';
      setLoadError(message);
      Alert.alert('Failed to reload', message);
      return false;
    } finally {
      reloadInFlightRef.current = false;
      setReloadInFlight(false);
    }
  }, [canRunHeaderActions, chatController, rangeEndText, rangeStartText]);

  const notificationUiEffectObserver = useMemo(
    () => (backend ? new NotificationUiEffectObserver(backend) : null),
    [backend],
  );
  useEffect(() => {
    if (!backend) return;
    return subscribeSessionRefreshInvalidations(
      backend,
      sessionId,
      handleReload,
    );
  }, [backend, handleReload, sessionId]);

  useEffect(() => {
    if (!notificationUiEffectObserver) return;
    observeSessionNotificationUiEffects(
      notificationUiEffectObserver,
      sessionSummary ?? null,
      notificationEvents,
    );
  }, [notificationEvents, notificationUiEffectObserver, sessionSummary]);

  const presentActionDisplay = useCallback(
    (display: ActionDisplayPayload, context: RunActionContext) => {
      if ((display.presentation ?? 'modal') === 'modal' && backend) {
        emitDisplayPresentation(
          backend,
          normalizeDisplayEnvelope({
            source: 'action_response',
            ownershipScope: 'session',
            connectionId,
            sessionId,
            display,
          }),
        );
        return;
      }
      const nextEntry = createDisplayEntry(
        { ...display, presentation: 'inline' },
        context,
      );
      setInlineActionDisplays(current =>
        upsertInlineDisplay(current, nextEntry),
      );
    },
    [backend, connectionId, sessionId],
  );

  const executePluginAction = useCallback(
    async (element: ActionUiElement, context: RunActionContext) => {
      if (!backend) {
        Alert.alert('Offline', 'Connect to a server to run actions.');
        return;
      }

      await runAction(
        JSON.stringify([element.plugin, element.id, context.sessionId, context.messageContext?.index]),
        `Running ${element.label}…`,
        async () => {
        const { ok, effects, display, errorMessage } =
          await runApplicationAction({
            backend,
            element,
            actionsById,
            context,
            effects: {
              currentSessionId: sessionId,
              navigateOnCreatedSession: true,
              reloadSessionsListOnMutations: true,
            },
          });

        if (!ok) {
          Alert.alert(
            'Action error',
            errorMessage || 'Failed to execute action',
          );
          return;
        }

        if (effects.some(effect => effect.type === 'reloadSessionsList')) {
          desktopEventBus.publish('sessionsReloadRequested', {
            connectionId,
            reason: `action:${element.id}`,
          });
        }

        if (effects.some(effect => effect.type === 'reloadSession')) {
          await handleReload();
        }

        const navigateEffect = effects.find(
          effect => effect.type === 'navigateToSession',
        );
        if (navigateEffect && onOpenSessionTab) {
          onOpenSessionTab({
            connectionId,
            sessionId: navigateEffect.sessionId,
            title: navigateEffect.sessionId,
          });
        }
        const normalizedDisplay = normalizeActionDisplayForSurface({
          display,
          surface: 'session_action',
          host: 'desktop',
        });
        if (normalizedDisplay) {
          presentActionDisplay(normalizedDisplay, context);
        }
        },
      );
    },
    [
      actionsById,
      backend,
      connectionId,
      handleReload,
      onOpenSessionTab,
      presentActionDisplay,
      runAction,
      sessionId,
    ],
  );

  const executeRichSessionAction = useCallback(
    (
      element: SessionActionRichUiElement,
      dialogValues?: Record<string, string | boolean>,
    ) =>
      executePluginAction(element, {
        sessionId,
        connectionId,
        sessionSummary: richActionSession,
        dialogValues,
      }),
    [connectionId, executePluginAction, richActionSession, sessionId],
  );

  const openRichConfigDropdown = useCallback(
    (entry: ComposerRichConfigControl, anchorTag?: number) => {
      if (
        entry.control.richUi.kind !== 'dropdown' ||
        !sessionSettingsController
      ) {
        return;
      }
      const richUi = entry.control.richUi as ConfigRichDropdownUi;
      const id = `rich-config:${connectionId}:${sessionId}:${entry.control.element.key}`;
      setActiveRichConfigControl(entry);
      openDesktopPopover({
        id,
        title: richUi.label,
        accessibilityId: `rich-config-dropdown-${entry.control.element.key}`,
        anchorTag: anchorTag ?? getLastActionsPopoverAnchorTag() ?? undefined,
        width: 420,
        height: Math.min(
          520,
          168 + richUi.options.length * 44 + (entry.hasOverride ? 44 : 0),
        ),
        onRequestClose: () => setActiveRichConfigControl(null),
        content: (
          <RichConfigDropdownPanel
            richUi={richUi}
            selectedValue={
              entry.effectiveValue == null ? '' : String(entry.effectiveValue)
            }
            hasOverride={entry.hasOverride}
            testIDPrefix={`rich-config-dropdown-${entry.control.element.key}`}
            onSelect={value => {
              sessionSettingsController
                .patchOverride(entry.control.element.key, value)
                .finally(() => {
                  setActiveRichConfigControl(null);
                  closeDesktopPopover(id);
                });
            }}
            onReset={() => {
              sessionSettingsController
                .deleteOverride(entry.control.element.key)
                .finally(() => {
                  setActiveRichConfigControl(null);
                  closeDesktopPopover(id);
                });
            }}
            onRequestClose={() => {
              setActiveRichConfigControl(null);
              closeDesktopPopover(id);
            }}
            renderIcon={({ name, size, color }) => (
              <Icon name={name} size={size} color={color} />
            )}
          />
        ),
      });
    },
    [connectionId, sessionId, sessionSettingsController],
  );

  const openRichSessionActionList = useCallback(
    (element: SessionActionRichUiElement, anchorTag?: number) => {
      if (element.rich_ui?.kind !== 'list') {
        return;
      }
      const id = `rich-session-action:${connectionId}:${sessionId}:${element.id}`;
      const optionCount = Array.isArray((element.rich_ui as any).options)
        ? (element.rich_ui as any).options.length
        : 0;
      setActiveRichSessionAction(element);
      openDesktopPopover({
        id,
        title: element.label,
        accessibilityId: `session-rich-list-${element.id}`,
        anchorTag: anchorTag ?? getLastActionsPopoverAnchorTag() ?? undefined,
        width: 380,
        height: Math.min(460, 70 + optionCount * 46),
        onRequestClose: () => setActiveRichSessionAction(null),
        content: (
          <SessionListRichActionList
            element={element as any}
            session={richActionSession}
            testIDPrefix={`session-rich-list-${element.id}`}
            onExecuteAction={values => {
              executeRichSessionAction(element, values).catch(() => {});
            }}
            onRequestClose={() => {
              setActiveRichSessionAction(null);
              closeDesktopPopover(id);
            }}
            renderIcon={({ name, size, color }) => (
              <Icon name={name} size={size} color={color} />
            )}
          />
        ),
      });
    },
    [connectionId, executeRichSessionAction, richActionSession, sessionId],
  );

  const renderPinnedHeaderSessionAction = useCallback(
    (params: any) => {
      const element = headerSessionActions.find(
        candidate => candidate.id === params.action.key,
      );
      if (!element?.rich_ui) {
        return undefined;
      }
      return (
        <SessionListRichActionControl
          element={element as any}
          session={richActionSession}
          placement="session_header"
          disabled={params.disabled}
          onExecuteAction={(selected, values) => {
            executeRichSessionAction(selected as any, values).catch(() => {});
          }}
          onPresentRichList={(selected, anchorTag) =>
            openRichSessionActionList(selected as any, anchorTag)
          }
          renderIcon={({ name, size, color }) => (
            <Icon name={name} size={size} color={color} />
          )}
          testID={`session-rich-action-${element.id}-session-header`}
        />
      );
    },
    [
      executeRichSessionAction,
      headerSessionActions,
      openRichSessionActionList,
      richActionSession,
    ],
  );

  const renderPinnedComposerSessionAction = useCallback(
    (params: any) => {
      const configEntry =
        composerRichConfigControlByActionKey[params.action.key];
      if (configEntry?.control.richUi.kind === 'dropdown') {
        const key = configEntry.control.element.key;
        return (
          <RichConfigDropdownControl
            buttonRef={ref => {
              richConfigControlRefs.current[key] = ref;
            }}
            control={configEntry.control}
            value={configEntry.effectiveValue}
            disabled={params.disabled}
            placement="composer"
            maxValueCharacters={24}
            renderIcon={({ name, size, color }) => (
              <Icon name={name} size={size} color={color} />
            )}
            testID={`composer-rich-config-${key}`}
            onPress={() => {
              const node = richConfigControlRefs.current[key];
              const tag = node ? (findNodeHandle(node) as any) : null;
              openRichConfigDropdown(
                configEntry,
                typeof tag === 'number' ? tag : undefined,
              );
            }}
          />
        );
      }
      if (configEntry?.control.richUi.kind === 'toggle') {
        const option = resolveConfigRichToggleOption(
          configEntry.control.richUi as ConfigRichToggleUi,
          configEntry.effectiveValue,
        );
        return (
          <RichConfigToggleControl
            control={configEntry.control}
            value={configEntry.effectiveValue}
            disabled={params.disabled}
            placement="composer"
            renderIcon={({ name, size, color }) => (
              <Icon name={name} size={size} color={color} />
            )}
            testID={`composer-rich-config-${configEntry.control.element.key}`}
            onPress={() => {
              void sessionSettingsController?.patchOverride(
                configEntry.control.element.key,
                !option.value,
              );
            }}
          />
        );
      }

      const element = composerSessionActionByActionKey[params.action.key];
      if (!element?.rich_ui) {
        return undefined;
      }
      return (
        <SessionListRichActionControl
          element={element as any}
          session={richActionSession}
          placement="composer"
          disabled={params.disabled}
          onExecuteAction={(selected, values) => {
            executeRichSessionAction(selected as any, values).catch(() => {});
          }}
          onPresentRichList={(selected, anchorTag) =>
            openRichSessionActionList(selected as any, anchorTag)
          }
          renderIcon={({ name, size, color }) => (
            <Icon name={name} size={size} color={color} />
          )}
          testID={`session-rich-action-${element.id}-composer`}
        />
      );
    },
    [
      composerRichConfigControlByActionKey,
      composerSessionActionByActionKey,
      executeRichSessionAction,
      openRichConfigDropdown,
      openRichSessionActionList,
      richActionSession,
      sessionSettingsController,
    ],
  );

  const displayFollowupDialog = useDisplayFollowupDialog<ActionDisplayEntry>(
    async (element, { action, source: entry, formValues }, dialogValues) => {
      setActiveDisplayActionId(action.id);
      try {
        await executePluginAction(element, {
          ...entry.context,
          formValues,
          dialogValues,
        });
      } finally {
        setActiveDisplayActionId(null);
      }
    },
  );
  const displayFollowupPrefill = useMemo(() => {
    const context = displayFollowupDialog.context?.source.context;
    return {
      session: context?.sessionSummary,
      message: context?.messageContext
        ? { index: context.messageContext.index, ...context.messageContext.message }
        : undefined,
    };
  }, [displayFollowupDialog.context]);
  useMacOSApplicationActionDialog({
    ownerId: `chat-display-followup:${connectionId}:${sessionId}`,
    activeElement: displayFollowupDialog.activeElement,
    prefillContext: displayFollowupPrefill,
    onCancel: displayFollowupDialog.handleCancel,
    onSubmit: displayFollowupDialog.handleSubmit,
  });

  const handleDisplayFollowupAction = useCallback(
    async (
      entry: ActionDisplayEntry,
      action: ActionDisplayFollowupAction,
      formValues?: Record<string, any>,
    ) => {
      if (action.kind === 'open_url') {
        try {
          await Linking.openURL(action.url);
        } catch (err: any) {
          Alert.alert(
            'Open link failed',
            err?.message || 'Unable to open the link.',
          );
        }
        return;
      }
      if (action.kind === 'copy_text') {
        Clipboard.setString(action.text);
        Alert.alert('Copied', 'Copied to clipboard.');
        return;
      }
      if (action.kind === 'run_action') {
        displayFollowupDialog.openForAction(action, entry.display, entry, formValues);
      }
    },
    [displayFollowupDialog.openForAction],
  );

  const applyMessageLimitAndReload = useCallback(
    async (params: {
      startText: string;
      endText: string;
      rangeNavigationOperationId?: number;
    }) => {
      if (params.rangeNavigationOperationId == null) {
        cancelRangeNavigation();
      } else if (
        rangeNavigationOperationRef.current !==
        params.rangeNavigationOperationId
      ) {
        return null;
      }
      setRangeStartText(params.startText);
      setRangeEndText(params.endText);

      if (!chatController || !backend) {
        return;
      }
      try {
        setLoadError(null);
        chatController.clearRequestState();
        await chatController.loadMessagesFromRangeText({
          startText: params.startText,
          endText: params.endText,
        });
        if (
          params.rangeNavigationOperationId != null &&
          rangeNavigationOperationRef.current !==
            params.rangeNavigationOperationId
        ) {
          return null;
        }
        const snapshot = chatController.getCacheSnapshot();
        setLastReloadAt(new Date(snapshot.updatedAtMs ?? Date.now()));
        return snapshot;
      } catch (err: any) {
        const message = err?.message || 'Failed to reload messages.';
        setLoadError(message);
        Alert.alert('Failed to reload', message);
      }
    },
    [backend, cancelRangeNavigation, chatController],
  );

  const firstLoadedMessageIndex =
    messages.length > 0 ? messages[0].index : null;
  const lastLoadedMessageIndex =
    messages.length > 0 ? messages[messages.length - 1].index : null;
  const transcriptRangeControlPresentation = useMemo(
    () =>
      TRANSCRIPT_RANGE_CONTROLS
        ? getTranscriptRangeControlPresentation({
            startText: rangeStartText,
            endText: rangeEndText,
            firstLoadedIndex: firstLoadedMessageIndex,
            lastLoadedIndex: lastLoadedMessageIndex,
            loadedCount: messages.length,
            pageSize: TRANSCRIPT_RANGE_CONTROL_PAGE_SIZE,
            maxRangeSize: TRANSCRIPT_RANGE_CONTROL_MAX_RANGE,
          })
        : null,
    [
      firstLoadedMessageIndex,
      lastLoadedMessageIndex,
      messages.length,
      rangeEndText,
      rangeStartText,
    ],
  );
  const handleTranscriptRangeAction = useCallback(
    async (action: TranscriptRangeControlAction) => {
      if (!TRANSCRIPT_RANGE_CONTROLS || reloadInFlight || chatState?.loading) {
        return;
      }
      const plan = planTranscriptRangeControlAction(
        {
          startText: rangeStartText,
          endText: rangeEndText,
          firstLoadedIndex: firstLoadedMessageIndex,
          lastLoadedIndex: lastLoadedMessageIndex,
          loadedCount: messages.length,
          pageSize: TRANSCRIPT_RANGE_CONTROL_PAGE_SIZE,
          maxRangeSize: TRANSCRIPT_RANGE_CONTROL_MAX_RANGE,
        },
        action,
      );
      if (!plan) {
        return;
      }
      if (action !== 'expandAbove' && action !== 'expandBelow') {
        await applyMessageLimitAndReload({
          startText: plan.startText,
          endText: plan.endText,
        });
        return;
      }
      const operationId = rangeNavigationOperationRef.current + 1;
      rangeNavigationOperationRef.current = operationId;
      setPendingRangeRestore(null);
      transcriptScroll.listRef.current?.cancelItemAnchor?.();
      const previousState = chatController?.getSnapshot() ?? null;
      const previousMessages = previousState?.messages ?? messages;
      const messageByIndex = new Map(
        previousMessages.map(entry => [entry.index, entry.message] as const),
      );
      const measuredAnchors =
        (await transcriptScroll.listRef.current?.getVisibleMessageAnchors?.()) ??
        [];
      if (rangeNavigationOperationRef.current !== operationId) {
        return;
      }
      const candidates: TranscriptViewportAnchorCandidate[] = measuredAnchors
        .map((measured: { key: string; offsetFromViewportTop: number }) => {
          const match = /^msg-(-?\d+)$/.exec(measured.key);
          const messageIndex = match ? Number(match[1]) : Number.NaN;
          const message = messageByIndex.get(messageIndex);
          return message && Number.isFinite(messageIndex)
            ? {
                messageIndex,
                offsetFromViewportTop: measured.offsetFromViewportTop,
                message,
              }
            : null;
        })
        .filter(
          (
            candidate: TranscriptViewportAnchorCandidate | null,
          ): candidate is TranscriptViewportAnchorCandidate =>
            candidate != null,
        );
      if ((globalThis as any).CLC_DEBUG_TRANSCRIPT_RANGE_NAVIGATION === true) {
        console.log('[transcriptRangeNavigation] captured', {
          action,
          operationId,
          candidates: candidates.map(candidate => ({
            messageIndex: candidate.messageIndex,
            offsetFromViewportTop: candidate.offsetFromViewportTop,
          })),
        });
      }
      transcriptScroll.suppressNextBottomContentFollow();
      const completed = await applyMessageLimitAndReload({
        startText: plan.startText,
        endText: plan.endText,
        rangeNavigationOperationId: operationId,
      });
      if (
        !completed ||
        !chatController ||
        rangeNavigationOperationRef.current !== operationId
      ) {
        if (!completed) {
          transcriptScroll.clearBottomContentFollowSuppression();
        }
        return;
      }
      const completedState = chatController.getSnapshot();
      const anchor = selectTranscriptRangeRestoreAnchor({
        candidates,
        completedMessages: completedState.messages,
        previousContext: {
          cursorEventId: previousState?.listCursorEventId ?? null,
          snapshotId: previousState?.snapshotId ?? null,
        },
        completedContext: {
          cursorEventId: completedState.listCursorEventId,
          snapshotId: completedState.snapshotId,
        },
      });
      if ((globalThis as any).CLC_DEBUG_TRANSCRIPT_RANGE_NAVIGATION === true) {
        console.log('[transcriptRangeNavigation] selected', {
          action,
          operationId,
          anchor,
        });
      }
      if (rangeNavigationOperationRef.current !== operationId) {
        return;
      }
      if (!anchor) {
        if (action === 'expandAbove') {
          transcriptScroll.scrollToBottom(false);
          return;
        }
        const firstCompletedIndex = completedState.messages[0]?.index;
        if (firstCompletedIndex != null) {
          setPendingRangeRestore({
            operationId,
            messageIndex: firstCompletedIndex,
            offsetFromViewportTop: 0,
          });
        }
        return;
      }
      setPendingRangeRestore({
        operationId,
        messageIndex: anchor.messageIndex,
        offsetFromViewportTop: anchor.offsetFromViewportTop,
      });
    },
    [
      applyMessageLimitAndReload,
      chatState?.loading,
      chatController,
      firstLoadedMessageIndex,
      lastLoadedMessageIndex,
      messages.length,
      rangeEndText,
      rangeStartText,
      reloadInFlight,
      transcriptScroll.listRef,
      transcriptScroll.clearBottomContentFollowSuppression,
      transcriptScroll.scrollToBottom,
      transcriptScroll.suppressNextBottomContentFollow,
    ],
  );

  const openMessageLimitPopover = useCallback(() => {
    if (Platform.OS !== 'macos') {
      setMessageLimitVisible(true);
      return;
    }
    if (!DesktopWindowManager?.openMessageLimitPopover) {
      Alert.alert('Not supported', 'Message limit popover is not available.');
      return;
    }

    const id = `message-limit:${connectionId}:${sessionId}`;
    openDesktopPopover({
      id,
      title: 'Message range',
      anchorTag: getLastActionsPopoverAnchorTag() ?? undefined,
      width: 420,
      height: 260,
      content: (
        <MessageLimitPopoverContent
          popoverId={id}
          startText={rangeStartText}
          endText={rangeEndText}
          lastReloadAtMs={lastReloadAt?.getTime() ?? null}
          onCancel={() => {}}
          onApply={params => {
            applyMessageLimitAndReload(params).catch(() => {});
          }}
        />
      ),
    });
  }, [
    applyMessageLimitAndReload,
    connectionId,
    lastReloadAt,
    rangeEndText,
    rangeStartText,
    sessionId,
  ]);

  const openAgentPickerForSwitch = useCallback(async () => {
    if (!backend) {
      return;
    }
    if (openingAgentPicker) {
      return;
    }

    setOpeningAgentPicker(true);
    try {
      const agentDescriptors = await ensureAgentDescriptorsLoaded();
      const agents = agentDescriptors.map(descriptor => descriptor.id);

      let initialAgentId: string | undefined;
      try {
        const current = await backend.getSessionAgent(sessionId);
        const trimmed = typeof current === 'string' ? current.trim() : '';
        if (trimmed) {
          initialAgentId = trimmed;
        }
      } catch {
        // Ignore; agent picker will fall back to first agent.
      }

      setActiveAgentPickerWindow({
        id: `switch-session-agent:${connectionId}:${sessionId}`,
        connectionId,
        backend,
      });
      DesktopWindowManager?.openAgentPicker({
        mode: 'switchSessionAgent',
        title: 'Switch Agent',
        primaryButtonLabel: 'Switch',
        sessionId,
        connectionId,
        connectionName,
        initialAgentId,
        agents,
        agentDescriptors,
      });
    } catch (err: any) {
      Alert.alert('Error', err?.message || 'Failed to load agents');
    } finally {
      setOpeningAgentPicker(false);
    }
  }, [
    backend,
    connectionId,
    connectionName,
    ensureAgentDescriptorsLoaded,
    openingAgentPicker,
    sessionId,
  ]);

  const {
    activeElement: activePluginDialogElement,
    context: activePluginDialogContext,
    openForElement: openPluginDialogForElement,
    handleSubmit: handleSubmitPluginDialog,
    handleCancel: handleCancelPluginDialog,
  } = usePluginActionDialog<PluginActionContext>(
    useCallback(
      async (
        element: ActionUiElement,
        context: PluginActionContext,
        dialogValues: Record<string, any> | undefined,
      ) => {
        const isMessage = context.kind === 'message';
        await executePluginAction(element, {
          sessionId,
          sessionSummary: context.sessionSummary ?? undefined,
          messageContext: isMessage
            ? { index: context.index, message: context.message }
            : undefined,
          dialogValues,
        });
      },
      [executePluginAction, sessionId],
    ),
  );

  const pluginDialogPrefillContext = useMemo(() => {
    const ctx = activePluginDialogContext;
    const message =
      ctx && ctx.kind === 'message'
        ? { index: ctx.index, ...(ctx.message as any) }
        : undefined;
    return {
      session: ctx?.sessionSummary ?? undefined,
      message,
    };
  }, [activePluginDialogContext]);

  useMacOSApplicationActionDialog({
    ownerId: `chat-pane:${connectionId}:${sessionId}`,
    activeElement: activePluginDialogElement,
    prefillContext: pluginDialogPrefillContext,
    onCancel: handleCancelPluginDialog,
    onSubmit: handleSubmitPluginDialog,
  });

  const handleSessionAction = useCallback(
    (key: ActionKey) => {
      const action = key as ChatSessionActionKey;
      if (action === LOCAL_NOTE_SESSION_ACTION_KEY && onEditSessionNote) {
        onEditSessionNote();
        return;
      }
      if (
        action === LOCAL_WATCHLIST_SESSION_ACTION_KEY &&
        onToggleSessionWatchlist
      ) {
        onToggleSessionWatchlist();
        return;
      }
      if (action === 'reload') {
        handleReload().catch(() => {});
        return;
      }
      if (action === 'agentSwitch') {
        openAgentPickerForSwitch().catch(() => {});
        return;
      }
      if (action === 'messageLimit') {
        openMessageLimitPopover();
        return;
      }
      if (action === 'settings') {
        if (!backend) {
          return;
        }
        const caps = backend.getCapabilities?.();
        if (caps && (!caps.sessionUiSchema || !caps.sessionConfigOverrides)) {
          Alert.alert(
            'Not supported',
            'This backend does not support session settings.',
          );
          return;
        }
        setActiveSessionSettingsWindow({
          state: {
            id: `session-settings:${connectionId}:${sessionId}`,
            connectionId,
            connectionName,
            sessionId,
            backend,
          },
        });
        DesktopWindowManager?.openReactWindow({
          windowKey: 'sessionSettings',
          moduleName: 'SessionSettingsWindow',
          title: 'Session settings',
          width: 560,
          height: 640,
          initialProps: {},
        });
        return;
      }

      if (action === 'plugins') {
        if (!backend) {
          return;
        }

        const caps = backend.getCapabilities?.();
        if (caps && !caps.sessionPlugins) {
          Alert.alert(
            'Not supported',
            'This backend does not support session plugins.',
          );
          return;
        }

        setActiveSessionPluginsWindow({
          state: {
            id: `session-plugins:${connectionId}:${sessionId}`,
            connectionId,
            connectionName,
            sessionId,
            backend,
          },
        });

        DesktopWindowManager?.openReactWindow({
          windowKey: 'sessionPlugins',
          moduleName: 'SessionPluginsWindow',
          title: 'Session plugins',
          width: 560,
          height: 640,
          initialProps: {},
        });
        return;
      }

      if (action === 'snapshots') {
        if (!backend) {
          return;
        }

        setActiveSessionSnapshotsWindow({
          state: {
            id: `session-snapshots:${connectionId}:${sessionId}`,
            connectionId,
            connectionName,
            sessionId,
            backend,
          },
        });

        DesktopWindowManager?.openReactWindow({
          windowKey: 'sessionSnapshots',
          moduleName: 'SessionSnapshotsWindow',
          title: 'Snapshots',
          width: 560,
          height: 640,
          initialProps: {},
        });
        return;
      }

      const pluginEl = headerSessionActions.find(el => el.id === key);
      if (pluginEl) {
        if (pluginEl.rich_ui?.kind === 'toggle') {
          executeRichSessionAction(pluginEl).catch(() => {});
        } else if (pluginEl.rich_ui?.kind === 'list') {
          openRichSessionActionList(pluginEl);
        } else {
          openPluginDialogForElement(pluginEl, {
            kind: 'session',
            sessionSummary: sessionSummary ?? null,
          });
        }
      }
    },
    [
      backend,
      connectionId,
      connectionName,
      executeRichSessionAction,
      handleReload,
      headerSessionActions,
      openPluginDialogForElement,
      openAgentPickerForSwitch,
      openMessageLimitPopover,
      openRichSessionActionList,
      onEditSessionNote,
      onToggleSessionWatchlist,
      sessionId,
      sessionSummary,
    ],
  );

  const handleComposerActionWithPlugins = useCallback(
    (key: ActionKey) => {
      const richConfig = composerRichConfigControlByActionKey[key];
      if (richConfig) {
        if (richConfig.control.richUi.kind === 'toggle') {
          const option = resolveConfigRichToggleOption(
            richConfig.control.richUi as ConfigRichToggleUi,
            richConfig.effectiveValue,
          );
          void sessionSettingsController?.patchOverride(
            richConfig.control.element.key,
            !option.value,
          );
        } else {
          openRichConfigDropdown(richConfig);
        }
        return;
      }

      const richSessionAction = composerSessionActionByActionKey[key];
      if (richSessionAction) {
        if (richSessionAction.rich_ui?.kind === 'toggle') {
          executeRichSessionAction(richSessionAction).catch(() => {});
        } else if (richSessionAction.rich_ui?.kind === 'list') {
          openRichSessionActionList(richSessionAction);
        } else {
          openPluginDialogForElement(richSessionAction, {
            kind: 'session',
            sessionSummary: sessionSummary ?? null,
          });
        }
        return;
      }

      handleComposerAction(key);
    },
    [
      composerRichConfigControlByActionKey,
      composerSessionActionByActionKey,
      executeRichSessionAction,
      handleComposerAction,
      openPluginDialogForElement,
      openRichConfigDropdown,
      openRichSessionActionList,
      sessionSettingsController,
      sessionSummary,
    ],
  );

  const getPinnedActionsForRole = useCallback(
    (role: string): MessageActionKey[] => {
      const existing = pinnedMessageActionsByRole[role];
      if (Array.isArray(existing)) {
        return existing;
      }
      return DEFAULT_PINNED_MESSAGE_ACTIONS_BY_ROLE[role] ?? [];
    },
    [pinnedMessageActionsByRole],
  );

  const setPinnedActionsForRole = useCallback(
    (role: string, pinned: MessageActionKey[]) => {
      setPinnedMessageActionsByRole(prev => ({ ...prev, [role]: pinned }));
    },
    [],
  );

  const pinnedMessageActionsContextValue = useMemo(
    () => ({
      isActive,
      getPinnedForRole: getPinnedActionsForRole,
      setPinnedForRole: setPinnedActionsForRole,
    }),
    [getPinnedActionsForRole, isActive, setPinnedActionsForRole],
  );

  const handleStartEditMessage = useCallback(
    (index: number, message: { role?: string; content?: unknown }) => {
      const role = message.role || 'unknown';
      if (role === 'tool') {
        return;
      }
      const content =
        typeof message.content === 'string' ? message.content : '';
      if (getWorkspace().modifying || selectedSnapshotId) return;
      updateWorkspace(current => ({ ...current, edit: { index, text: content } }));
      composerRef.current?.setText(content);
      composerRef.current?.focus();
    },
    [getWorkspace, selectedSnapshotId, updateWorkspace],
  );

  const handleSubmitEditMessage = useCallback(
    async (index: number, newText: string) => {
      const trimmed = newText.trim();
      if (!trimmed) {
        Alert.alert('Invalid content', 'Message content cannot be empty.');
        return;
      }

      if (!chatController || !backend) {
        Alert.alert('Offline', 'Connect to a server to modify messages.');
        return;
      }

      const edit = getWorkspace().edit;
      if (!edit || edit.index !== index || getWorkspace().modifying) return;
      updateWorkspace(current => ({ ...current, modifying: true }));
      try {
        onBeforeSessionMutation?.();
        await chatController.modifyMessage(index, trimmed);
        await chatController.loadMessages();
        updateWorkspace(current => ({ ...current, edit: null }));
        composerRef.current?.setText(composeTextRef.current);
      } catch (err: any) {
        const message = err?.message || 'Failed to modify message.';
        Alert.alert('Error', message);
      } finally {
        updateWorkspace(current => ({ ...current, modifying: false }));
      }
    },
    [backend, chatController, composeTextRef, getWorkspace, onBeforeSessionMutation, updateWorkspace],
  );

  const handleCancelEditMessage = useCallback(() => {
    if (getWorkspace().modifying) return;
    updateWorkspace(current => ({ ...current, edit: null }));
    composerRef.current?.setText(composeTextRef.current);
  }, [composeTextRef, getWorkspace, updateWorkspace]);

  const handleMessageAction = useCallback(
    async (action: MessageActionKey, index: number, message: any) => {
      if (action === 'modify') {
        handleStartEditMessage(index, message);
        return;
      }

      if (action === 'toggleMarkdown') {
        if ((message?.role || 'unknown') !== 'assistant') {
          return;
        }
        setMessageViewModeByIndex(prev => {
          const current = prev[index] ?? 'markdown';
          const next = current === 'markdown' ? 'raw' : 'markdown';
          return { ...prev, [index]: next };
        });
        return;
      }

      if (action === 'copy') {
        const content = selectDisplayContent(message);
        if (!content) {
          Alert.alert('Nothing to copy', 'This message has no text content.');
          return;
        }
        try {
          Clipboard.setString(content);
          Alert.alert('Copied', 'Message content copied to clipboard.');
        } catch {
          Alert.alert('Copy failed', 'Clipboard is not available.');
        }

        return;
      }

      const pluginEl = visibleMessageActions.find(el => el.id === action);
      if (pluginEl) {
        openPluginDialogForElement(pluginEl, {
          kind: 'message',
          index,
          message: message as ApiMessage,
          sessionSummary: sessionSummary ?? null,
        });
      }
    },
    [
      handleStartEditMessage,
      openPluginDialogForElement,
      sessionSummary,
      visibleMessageActions,
    ],
  );

  const sessionDisplayRail = useMemo(() => {
    return (
      <View testID="desktop-session-display-rail">
        <DesktopSessionNotificationRail
          backend={backend}
          connectionId={connectionId}
          sessionId={sessionId}
          sessionSummary={sessionSummary ?? null}
          events={notificationEvents}
          enabled={isVisible}
          activeActionId={activeDisplayActionId}
          onFollowupAction={(action, notification) =>
            handleDisplayFollowupAction(
              createDisplayEntry(notification.display, {
                connectionId,
                sessionId,
                sessionSummary: sessionSummary ?? undefined,
              }),
              action,
            )
          }
        />
        {inlineActionDisplays.map(entry => (
          <ActionResultInlineCard
            key={entry.key}
            display={entry.display}
            activeActionId={activeDisplayActionId}
            onDismiss={() =>
              setInlineActionDisplays(current =>
                current.filter(item => item.key !== entry.key),
              )
            }
            onFollowupAction={(action, formValues) =>
              handleDisplayFollowupAction(entry, action, formValues)
            }
          />
        ))}
      </View>
    );
  }, [
    activeDisplayActionId,
    backend,
    handleDisplayFollowupAction,
    inlineActionDisplays,
    notificationEvents,
    connectionId,
    isVisible,
    sessionId,
    sessionSummary,
  ]);

  const streamingFooter = useMemo(() => {
    const hasStreaming = !!(
      streamingRow &&
      (streamingRow.content || streamingRow.reasoning)
    );
    if (!hasStreaming) {
      return null;
    }
    return (
      <View>
        <DesktopMessageBubble
          index={
            messages.length > 0 ? messages[messages.length - 1].index + 1 : 0
          }
          message={{
            role: 'assistant',
            content: streamingRow?.content,
            metadata: {
              ...(streamingRow?.metadata || {}),
              reasoning: streamingRow?.reasoning,
            },
          }}
          renderMode="markdown"
          footerElements={footerElements}
        />
      </View>
    );
  }, [footerElements, messages, streamingRow]);

  const transcriptRows = useMemo<DesktopTranscriptRow[]>(() => {
    const rows: DesktopTranscriptRow[] = [];
    for (const message of messages) {
      rows.push({ kind: 'message', item: message });
    }
    const hasStreaming = !!(
      streamingRow &&
      (streamingRow.content || streamingRow.reasoning)
    );
    if (hasStreaming) {
      rows.push({ kind: 'stream' });
    }
    return rows;
  }, [messages, streamingRow]);

  const renderMessageItem = useCallback(
    ({ item: msg }: { item: IndexedMessage; index: number }) => {
      const role = msg.message.role || 'unknown';
      const allowedActions = ALL_MESSAGE_ACTIONS.filter(def =>
        def.allowedRoles.includes(role),
      ).map(def => def.key as MessageActionKey);
      const defaultModeForRole: 'markdown' | 'raw' =
        role === 'assistant' ? 'markdown' : 'raw';
      const renderMode =
        messageViewModeByIndex[msg.index] ?? defaultModeForRole;

      return (
        <View
          accessible
          accessibilityLabel={`Transcript message ${msg.index}`}
          testID={`transcript-message-${msg.index}`}
        >
          <DesktopMessageBubble
            index={msg.index}
            message={msg.message}
            allowedActions={allowedActions}
            onAction={(action, index, message) =>
              handleMessageAction(action, index, message)
            }
            renderMode={renderMode}
            footerElements={footerElements}
            pluginActionDefs={pluginMessageActionDefs}
          />
        </View>
      );
    },
    [
      footerElements,
      handleCancelEditMessage,
      handleMessageAction,
      handleSubmitEditMessage,
      messageViewModeByIndex,
      pluginMessageActionDefs,
    ],
  );

  const getTranscriptRowKey = useCallback((row: DesktopTranscriptRow) => {
    if (row.kind === 'stream') {
      return 'row-stream';
    }
    return `msg-${row.item.index}`;
  }, []);

  const getTranscriptRowDependencies = useCallback(
    (row: DesktopTranscriptRow) => {
      if (row.kind === 'stream') {
        return [
          streamingRow,
          inlineActionDisplays,
          activeDisplayActionId,
          footerElements,
          messages.length > 0 ? messages[messages.length - 1].index : null,
        ];
      }

      const msg = row.item;
      const role = msg.message.role || 'unknown';
      const defaultModeForRole: 'markdown' | 'raw' =
        role === 'assistant' ? 'markdown' : 'raw';
      const renderMode =
        messageViewModeByIndex[msg.index] ?? defaultModeForRole;
      return [
        renderMode,
        footerElements,
      ];
    },
    [
      activeDisplayActionId,
      footerElements,
      inlineActionDisplays,
      messageViewModeByIndex,
      messages,
      streamingRow,
    ],
  );

  const renderTranscriptRow = useCallback(
    ({ item: row, index }: { item: DesktopTranscriptRow; index: number }) => {
      if (row.kind === 'stream') {
        return streamingFooter;
      }
      return renderMessageItem({ item: row.item, index });
    },
    [renderMessageItem, streamingFooter],
  );

  const rangeControlsDisabled = reloadInFlight || (chatState?.loading ?? false);
  const renderTranscriptRangeButton = useCallback(
    (button: TranscriptRangeControlButton, secondary = false) => (
      <Pressable
        key={button.id}
        accessibilityRole="button"
        accessibilityLabel={button.title}
        disabled={rangeControlsDisabled}
        style={({ pressed }) => [
          styles.transcriptRangeControlButton,
          secondary && styles.transcriptRangeControlButtonSecondary,
          rangeControlsDisabled && styles.transcriptRangeControlButtonDisabled,
          pressed &&
            !rangeControlsDisabled &&
            styles.transcriptRangeControlButtonPressed,
        ]}
        onPress={() => {
          void handleTranscriptRangeAction(button.id);
        }}
      >
        <Text style={styles.transcriptRangeControlText}>{button.title}</Text>
      </Pressable>
    ),
    [handleTranscriptRangeAction, rangeControlsDisabled, styles],
  );
  const transcriptRangeTopControls =
    transcriptRangeControlPresentation &&
    transcriptRangeControlPresentation.topButtons.length > 0 ? (
      <View style={styles.transcriptRangeControlRow}>
        {transcriptRangeControlPresentation.topButtons.map(button =>
          renderTranscriptRangeButton(button, button.id === 'showAll'),
        )}
      </View>
    ) : null;
  const transcriptRangeBottomControls =
    transcriptRangeControlPresentation &&
    transcriptRangeControlPresentation.bottomButtons.length > 0 ? (
      <View
        style={[
          styles.transcriptRangeControlRow,
          styles.transcriptRangeControlRowBottom,
        ]}
      >
        {transcriptRangeControlPresentation.bottomButtons.map(button =>
          renderTranscriptRangeButton(button, button.id === 'showLast'),
        )}
      </View>
    ) : null;
  const scrollViewTranscriptFooter =
    streamingFooter || transcriptRangeBottomControls ? (
      <View>
        {streamingFooter}
        {transcriptRangeBottomControls}
      </View>
    ) : null;

  return (
    <View
      style={styles.root}
      onLayout={event => setPaneHeight(event.nativeEvent.layout.height)}
    >
      <View
        testID="chat-header"
        accessible
        accessibilityRole="summary"
        accessibilityLabel="Session"
        collapsable={false}
        style={[styles.header, compactLayout && styles.compactHeader]}
      >
        <View style={styles.headerLeft}>
          <Text
            style={styles.title}
            numberOfLines={compactLayout ? 1 : 2}
            selectable
            testID="chat-header-title"
          >
            {displayTitle}
          </Text>
          <View style={[styles.metaRow, compactLayout && styles.compactMetaRow]}>
            <Text style={styles.metaText} numberOfLines={1}>
              {connectionName}
            </Text>
            <Text style={styles.metaDot}>•</Text>
            <Text
              style={styles.metaText}
              numberOfLines={1}
              selectable
              testID="chat-header-session-id"
            >
              {sessionId}
            </Text>
            <Text style={styles.metaDot}>•</Text>
            <View
              style={[
                styles.statusDot,
                { backgroundColor: backend ? theme.success : theme.textMuted },
              ]}
            />
            <Text style={styles.metaText} numberOfLines={1}>
              {backend ? 'Online' : 'Offline'}
            </Text>
            {requestStatus ? <Text style={styles.metaDot}>•</Text> : null}
            <SessionRequestStatusIndicator
              status={requestStatus}
              variant="inline"
              testID={`chat-request-status-${connectionId}-${sessionId}`}
            />
          </View>
          <Text
            style={styles.subtitle}
            numberOfLines={compactLayout ? 1 : 2}
            selectable
            testID="chat-header-subtitle"
          >
            {displaySubtitle}
          </Text>
        </View>

        <View style={styles.headerRight}>
          <ActionsMenuBar<ActionDefinition>
            title="Session actions"
            variant="dropdown"
            menuButtonTestID="session-actions-menu"
            isActive={isActive}
            renderIcon={({ name, size, color }) => (
              <Icon name={name} size={size} color={color} />
            )}
            baseActions={sessionBaseActions}
            extraActions={pluginSessionActionDefs}
            pinned={pinnedSessionActionKeys}
            onChangePinned={next => setPinnedSessionActionKeys(next)}
            onAction={handleSessionAction}
            renderPinnedAction={renderPinnedHeaderSessionAction}
            isActionDisabled={key => {
              if (isLocalSessionActionKey(String(key))) {
                return !localActionsEnabled;
              }
              if (runningHeaderActionIds.has(String(key))) return true;
              if (!canRunHeaderActions) {
                return true;
              }
              if (key === 'reload') {
                return reloadInFlight || (chatState?.loading ?? false);
              }
              if (key === 'agentSwitch') {
                return openingAgentPicker || agentsLoading;
              }
              if (key === 'settings') {
                const caps = backend.getCapabilities?.();
                if (
                  caps &&
                  (!caps.sessionUiSchema || !caps.sessionConfigOverrides)
                ) {
                  return true;
                }
                return false;
              }
              if (key === 'plugins') {
                const caps = backend.getCapabilities?.();
                if (caps && !caps.sessionPlugins) {
                  return true;
                }
                return false;
              }
              if (key === 'snapshots') {
                return !backend;
              }
              return false;
            }}
          />
        </View>
      </View>

      <ScrollView
        testID="chat-notification-rail"
        style={[
          styles.notificationRail,
          { maxHeight: compactLayout ? paneHeight * 0.12 : 180 },
        ]}
      >
        <DesktopConnectionDisplayRail />
        {sessionDisplayRail}
      </ScrollView>
      <ChatActivityRow
        recovery={workspaceState.recovery && !sendInFlight ? {
          onResend: () => { void handleRetryPendingRequest(); },
          onCancel: () => updateWorkspace(current => ({ ...current, recovery: null })),
          disabled: !backend || workspaceState.edit != null,
        } : null}
        activities={[
        ...(workspaceState.modifying ? [`Saving message [${editingIndex}]…`] : []),
        ...(sendInFlight ? ['Sending…'] : chatState?.activeRequestId ? ['Generating response…'] : []),
        ...Object.values(workspaceState.actions),
        ...(chatState?.loading && !workspaceState.modifying ? ['Loading messages…'] : []),
        ...(attachmentActionInProgress ? [attachmentActionText] : []),
      ]} />

      <View style={[styles.body, compactLayout && styles.compactBody]}>
        <View style={styles.statusRow}>
          <Text style={styles.hintSecondary}>Messages: {messagesCount}</Text>
          <Text style={styles.hintSecondary}>
            Streaming: {chatController?.isEventStreaming() ? 'on' : 'off'}
          </Text>
        </View>

        {loadError ? (
          <View style={styles.errorRow}>
            <Text style={styles.errorText} numberOfLines={2}>
              {loadError}
            </Text>
            <Pressable
              style={({ pressed }) => [
                styles.retryButton,
                pressed && styles.retryButtonPressed,
              ]}
              onPress={() => {
                attemptedInitialLoadRef.current = true;
                loadInitialMessages().catch(() => {
                  // errors are handled in `loadInitialMessages`
                });
              }}
            >
              <Text style={styles.retryButtonText}>Retry</Text>
            </Pressable>
          </View>
        ) : null}

        {selectedSnapshotId ? (
          <SnapshotReadonlyBanner
            snapshotId={selectedSnapshotId}
            onClear={handleClearSelectedSnapshot}
            disabled={!backend}
          />
        ) : null}

        <View
          testID="chat-transcript-viewport"
          accessible
          accessibilityRole="summary"
          accessibilityLabel="Messages"
          collapsable={false}
          style={[
            styles.transcriptFrame,
            paneHeight > 0 && { minHeight: paneHeight * 0.30 },
          ]}
        >
          <PinnedMessageActionsProvider
            value={pinnedMessageActionsContextValue}
          >
            {TRANSCRIPT_LIST_IMPLEMENTATION === 'flatList' ? (
              <DependencyFlatList
                testID="transcript-scroll-list"
                listRef={transcriptScroll.listRef}
                style={styles.transcript}
                contentContainerStyle={styles.transcriptContent}
                data={transcriptRows}
                inverted={FLATLIST_INVERTED}
                keyExtractor={getTranscriptRowKey}
                getItemDependencies={getTranscriptRowDependencies}
                scrollEventThrottle={16}
                disableVirtualization={FLATLIST_DISABLE_VIRTUALIZATION}
                eagerRenderThreshold={FLATLIST_EAGER_RENDER_THRESHOLD}
                eagerRenderEligibilityCount={messages.length}
                itemAnchorTimeoutMs={FLATLIST_ITEM_ANCHOR_TIMEOUT_MS}
                itemAnchorMaxAttempts={FLATLIST_ITEM_ANCHOR_MAX_ATTEMPTS}
                onScrollActionDiagnostic={
                  transcriptScroll.onListScrollDiagnostic
                }
                initialNumToRender={FLATLIST_INITIAL_NUM_TO_RENDER}
                maxToRenderPerBatch={FLATLIST_MAX_TO_RENDER_PER_BATCH}
                updateCellsBatchingPeriod={
                  FLATLIST_UPDATE_CELLS_BATCHING_PERIOD
                }
                windowSize={FLATLIST_WINDOW_SIZE}
                removeClippedSubviews={FLATLIST_REMOVE_CLIPPED_SUBVIEWS}
                onLayout={transcriptScroll.onLayout}
                onContentSizeChange={transcriptScroll.onContentSizeChange}
                onScroll={transcriptScroll.onScroll}
                onScrollBeginDrag={transcriptScroll.onScrollBeginDrag}
                onMomentumScrollBegin={transcriptScroll.onMomentumScrollBegin}
                onScrollEndDrag={
                  FLATLIST_FORWARD_SCROLL_END_DRAG
                    ? transcriptScroll.onScrollEndDrag
                    : undefined
                }
                onMomentumScrollEnd={
                  FLATLIST_FORWARD_MOMENTUM_SCROLL_END
                    ? transcriptScroll.onMomentumScrollEnd
                    : undefined
                }
                renderItem={renderTranscriptRow}
                ListHeaderComponent={transcriptRangeTopControls}
                ListFooterComponent={transcriptRangeBottomControls}
                ListEmptyComponent={
                  !chatState?.loading ? (
                    <Text style={styles.hintSecondary}>No messages.</Text>
                  ) : null
                }
              />
            ) : TRANSCRIPT_LIST_IMPLEMENTATION === 'virtualizedScroll' ? (
              <DependencyVirtualizedScroll
                listRef={transcriptScroll.listRef}
                style={styles.transcript}
                contentContainerStyle={styles.transcriptContent}
                data={transcriptRows}
                inverted={FLATLIST_INVERTED}
                keyExtractor={getTranscriptRowKey}
                getItemDependencies={getTranscriptRowDependencies}
                scrollEventThrottle={16}
                disableVirtualization={FLATLIST_DISABLE_VIRTUALIZATION}
                initialNumToRender={FLATLIST_INITIAL_NUM_TO_RENDER}
                maxToRenderPerBatch={FLATLIST_MAX_TO_RENDER_PER_BATCH}
                updateCellsBatchingPeriod={
                  FLATLIST_UPDATE_CELLS_BATCHING_PERIOD
                }
                windowSize={FLATLIST_WINDOW_SIZE}
                removeClippedSubviews={FLATLIST_REMOVE_CLIPPED_SUBVIEWS}
                onLayout={transcriptScroll.onLayout}
                onContentSizeChange={transcriptScroll.onContentSizeChange}
                onScroll={transcriptScroll.onScroll}
                onScrollBeginDrag={transcriptScroll.onScrollBeginDrag}
                onMomentumScrollBegin={transcriptScroll.onMomentumScrollBegin}
                onScrollEndDrag={
                  FLATLIST_FORWARD_SCROLL_END_DRAG
                    ? transcriptScroll.onScrollEndDrag
                    : undefined
                }
                onMomentumScrollEnd={
                  FLATLIST_FORWARD_MOMENTUM_SCROLL_END
                    ? transcriptScroll.onMomentumScrollEnd
                    : undefined
                }
                renderItem={renderTranscriptRow}
                ListHeaderComponent={transcriptRangeTopControls}
                ListFooterComponent={transcriptRangeBottomControls}
                ListEmptyComponent={
                  !chatState?.loading ? (
                    <Text style={styles.hintSecondary}>No messages.</Text>
                  ) : null
                }
              />
            ) : TRANSCRIPT_LIST_IMPLEMENTATION === 'progressiveScroll' ? (
              <ProgressiveScrollList
                testID="transcript-scroll-list"
                listRef={transcriptScroll.listRef}
                style={styles.transcript}
                contentContainerStyle={styles.transcriptContent}
                data={transcriptRows}
                keyExtractor={getTranscriptRowKey}
                getItemDependencies={getTranscriptRowDependencies}
                initialWindowSize={PROGRESSIVE_SCROLL_INITIAL_WINDOW_SIZE}
                pageSize={PROGRESSIVE_SCROLL_PAGE_SIZE}
                maxWindowSize={PROGRESSIVE_SCROLL_MAX_WINDOW_SIZE}
                autoLoadEdges={PROGRESSIVE_SCROLL_AUTO_LOAD}
                edgeThresholdPx={PROGRESSIVE_SCROLL_EDGE_THRESHOLD_PX}
                prebuildRows={PROGRESSIVE_SCROLL_PREBUILD_ROWS}
                backingList={PROGRESSIVE_SCROLL_BACKING_LIST}
                growOnly={PROGRESSIVE_SCROLL_GROW_ONLY}
                defaultAnchorBeforeCount={
                  PROGRESSIVE_SCROLL_ANCHOR_BEFORE_COUNT
                }
                defaultAnchorAfterCount={PROGRESSIVE_SCROLL_ANCHOR_AFTER_COUNT}
                scrollActionTimeoutMs={PROGRESSIVE_SCROLL_ACTION_TIMEOUT_MS}
                edgeScrollEpsilonPx={PROGRESSIVE_SCROLL_EDGE_EPSILON_PX}
                edgeScrollStableMs={PROGRESSIVE_SCROLL_EDGE_STABLE_MS}
                scrollEventThrottle={16}
                onLayout={transcriptScroll.onLayout}
                onContentSizeChange={transcriptScroll.onContentSizeChange}
                onScroll={transcriptScroll.onScroll}
                onScrollBeginDrag={transcriptScroll.onScrollBeginDrag}
                onMomentumScrollBegin={transcriptScroll.onMomentumScrollBegin}
                onScrollEndDrag={transcriptScroll.onScrollEndDrag}
                onMomentumScrollEnd={transcriptScroll.onMomentumScrollEnd}
                renderItem={renderTranscriptRow}
                ListHeaderComponent={transcriptRangeTopControls}
                ListFooterComponent={transcriptRangeBottomControls}
                ListEmptyComponent={
                  !chatState?.loading ? (
                    <Text style={styles.hintSecondary}>No messages.</Text>
                  ) : null
                }
              />
            ) : (
              <PlaceholderFlatList
                testID="transcript-scroll-list"
                listRef={transcriptScroll.listRef}
                style={styles.transcript}
                contentContainerStyle={styles.transcriptContent}
                data={messages}
                keyExtractor={item => String(item.index)}
                showsVerticalScrollIndicator
                getItemDependencies={item => {
                  const role = item.message.role || 'unknown';
                  const defaultModeForRole: 'markdown' | 'raw' =
                    role === 'assistant' ? 'markdown' : 'raw';
                  const renderMode =
                    messageViewModeByIndex[item.index] ?? defaultModeForRole;
                  return [
                    renderMode,
                    footerElements,
                  ];
                }}
                scrollEventThrottle={16}
                onLayout={transcriptScroll.onLayout}
                onContentSizeChange={transcriptScroll.onContentSizeChange}
                onScroll={transcriptScroll.onScroll}
                onScrollBeginDrag={transcriptScroll.onScrollBeginDrag}
                onMomentumScrollBegin={transcriptScroll.onMomentumScrollBegin}
                onScrollEndDrag={transcriptScroll.onScrollEndDrag}
                onMomentumScrollEnd={transcriptScroll.onMomentumScrollEnd}
                renderItem={renderMessageItem}
                ListHeaderComponent={transcriptRangeTopControls}
                ListEmptyComponent={
                  !chatState?.loading ? (
                    <Text style={styles.hintSecondary}>No messages.</Text>
                  ) : null
                }
                ListFooterComponent={scrollViewTranscriptFooter}
              />
            )}
          </PinnedMessageActionsProvider>

          {transcriptScroll.canScrollToTop ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Scroll to top"
              style={({ pressed }) => [
                styles.transcriptScrollButton,
                styles.transcriptScrollButtonTop,
                pressed && styles.transcriptScrollButtonPressed,
              ]}
              onPress={() => transcriptScroll.scrollToTop(true)}
            >
              <Icon name="arrow-up" size={18} color={theme.text} />
            </Pressable>
          ) : null}

          {transcriptScroll.canScrollToBottom ? (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Scroll to bottom"
              style={({ pressed }) => [
                styles.transcriptScrollButton,
                styles.transcriptScrollButtonBottom,
                pressed && styles.transcriptScrollButtonPressed,
              ]}
              onPress={() => transcriptScroll.scrollToBottom(true)}
            >
              <Icon name="arrow-down" size={18} color={theme.text} />
            </Pressable>
          ) : null}
        </View>

        <View
          testID="chat-composer"
          accessible
          accessibilityRole="summary"
          accessibilityLabel="Message composer"
          collapsable={false}
          style={styles.composerArea}
        >
          {editingIndex != null && !compactLayout && <ComposerEditContext
            index={editingIndex}
            submitting={workspaceState.modifying}
            onCancel={handleCancelEditMessage}
          />}
          <View style={styles.composerHeaderRow}>
            {editingIndex != null && compactLayout && <ComposerEditContext
              index={editingIndex}
              submitting={workspaceState.modifying}
              onCancel={handleCancelEditMessage}
              style={styles.compactEditContext}
            />}
            <View style={[
              styles.composerHeaderRight,
              editingIndex != null && compactLayout && styles.compactEditActions,
            ]}>
              <ActionsMenuBar<ActionDefinition>
                title="Composer actions"
                variant="dropdown"
                style={styles.composerActionsBar}
                pinnedRows={compactLayout ? 1 : 2}
                secondPinnedRowPlacement="below"
                isActive={isActive}
                renderIcon={({ name, size, color }) => (
                  <Icon name={name} size={size} color={color} />
                )}
                baseActions={BUILTIN_COMPOSER_ACTIONS}
                extraActions={composerPluginActionDefs}
                pinned={pinnedComposerActionKeys}
                pinnedKeysForBar={pinnedComposerActionKeysForBar}
                maxPinnedActionsForBar={editingIndex != null && compactLayout ? 0 : undefined}
                onChangePinned={next => setPinnedComposerActionKeys(next)}
                onAction={handleComposerActionWithPlugins}
                renderPinnedAction={renderPinnedComposerSessionAction}
                isActionDisabled={key => {
                  if (!canRunComposerActions) {
                    return true;
                  }
                  if (editingIndex != null && (
                    key === 'append' || key === 'appendAs' || key === 'resend' ||
                    composerAttachmentElementByActionKey[String(key)]
                  )) return true;
                  if (key === 'append' || key === 'appendAs') {
                    if (appendInFlight || attachmentActionInProgress) {
                      return true;
                    }
                    return !composeText.trim() && !hasAttachments;
                  }
                  if (key === 'resend') {
                    return sendInFlight || !!workspaceState.recovery || !!chatState?.activeRequestId;
                  }
                  if (key === 'cancel') {
                    return cancelInFlight || !chatState?.activeRequestId;
                  }
                  if (key === 'softCancel') {
                    return (
                      softCancelInFlight ||
                      !chatState?.activeRequestId ||
                      softCancelledRequestId === chatState.activeRequestId
                    );
                  }
                  const richConfig =
                    composerRichConfigControlByActionKey[String(key)];
                  if (richConfig) {
                    return richConfig.control.element.disabled === true;
                  }
                  const sessionAction =
                    composerSessionActionByActionKey[String(key)];
                  if (sessionAction) {
                    return sessionAction.disabled === true || runningHeaderActionIds.has(sessionAction.id);
                  }
                  const attachment =
                    composerAttachmentElementByActionKey[String(key)];
                  if (attachment) {
                    return (
                      attachment.disabled === true || attachmentActionInProgress
                    );
                  }
                  return false;
                }}
              />
            </View>
          </View>

          {editingIndex == null && attachmentsAbove.length > 0 ? (
            attachmentsAboveExpanded ? (
              <View style={styles.attachmentsExpandedContainer}>
                <View style={styles.attachmentsExpandedChevronRow}>
                  <Pressable
                    style={({ pressed }) => [
                      styles.attachmentsChevronButton,
                      pressed && styles.attachmentsChevronButtonPressed,
                    ]}
                    onPress={() => setAttachmentsAboveExpanded(false)}
                  >
                    <Icon
                      name="chevron-up"
                      size={16}
                      color={theme.textSecondary}
                    />
                  </Pressable>
                </View>
                <ComposerAttachmentsExpandedPanel
                  attachments={buildManageRows(attachmentsAbove)}
                  disabled={
                    editingIndex != null || !canRunComposerActions || attachmentActionInProgress
                  }
                  onMove={(draftId, direction) =>
                    handleMoveDraft('above', draftId, direction)
                  }
                  onEditMetadata={(draftId, anchorTag) =>
                    handleEditDraftMetadata('above', draftId, anchorTag)
                  }
                  onDelete={draftId => handleDeleteDraft('above', draftId)}
                />
              </View>
            ) : (
              <AttachmentThumbnailStrip
                attachments={buildAttachmentStripRows(attachmentsAbove)}
                disabled={editingIndex != null || !canRunComposerActions || attachmentActionInProgress}
                expanded={false}
                onToggleExpanded={() => setAttachmentsAboveExpanded(true)}
              />
            )
          ) : null}

          <View style={styles.composerRow}>
            {composerAttachmentPlusRows.length > 0 ? (
              <View ref={attachmentPlusButtonRef} collapsable={false}>
                <Pressable
                  testID="composer-attachment-plus"
                  accessibilityRole="button"
                  accessibilityLabel="Add attachment"
                  accessibilityState={{ disabled: !canOpenAttachmentPlus }}
                  style={({ pressed }) => [
                    styles.attachmentPlusButton,
                    !canOpenAttachmentPlus &&
                      styles.attachmentPlusButtonDisabled,
                    pressed &&
                      canOpenAttachmentPlus &&
                      styles.attachmentPlusButtonPressed,
                  ]}
                  disabled={!canOpenAttachmentPlus}
                  onPress={() => {
                    openComposerAttachmentPlusPopover();
                  }}
                >
                  <Icon
                    name="plus"
                    size={16}
                    color={
                      canOpenAttachmentPlus
                        ? theme.textSecondary
                        : theme.textMuted
                    }
                  />
                </Pressable>
              </View>
            ) : null}
            <View
              style={[
                styles.composerInputFrame,
                { height: Math.min(composerHeight, compactLayout ? 48 : 120) },
                !backend && styles.composerInputDisabled,
              ]}
            >
              <MacTextView
                testID="message-composer-input"
                accessibilityLabel="Message composer"
                ref={composerRef}
                style={styles.composerInput}
                initialText={workspaceState.edit?.text ?? initialComposeText}
                placeholder={
                  backend ? 'Type a message…' : 'Offline (read-only)'
                }
                placeholderTextColor={theme.textMuted}
                textColor={theme.text}
                fontSize={13}
                editable={backend != null && !sendInFlight && !workspaceState.modifying}
                autoGrow
                minHeight={34}
                maxHeight={compactLayout ? 48 : 120}
                onHeightChange={handleComposerHeightChange}
                onChangeText={text => {
                  recordSessionActivity();
                  if (editingIndex != null) {
                    updateWorkspace(current => current.edit
                      ? { ...current, edit: { ...current.edit, text } }
                      : current);
                  } else {
                    handleComposerChangeText(text);
                  }
                }}
                onSubmit={text => {
                  (editingIndex != null
                    ? handleSubmitEditMessage(editingIndex, text)
                    : handleSend(text)).catch(() => {
                    // errors are handled in `handleSend`
                  });
                }}
              />
            </View>
            <Pressable
              testID="composer-send"
              accessibilityRole="button"
              accessibilityLabel={`${editingIndex != null ? 'Save edit' : 'Send message'}${requestInProgress ? ', in progress' : ''}`}
              accessibilityValue={{ text: requestInProgress ? 'In progress' : 'Ready' }}
              accessibilityState={{
                disabled: !canSendNow,
                busy: requestInProgress,
              }}
              style={({ pressed }) => [
                styles.sendButton,
                !canSendNow && styles.sendButtonDisabled,
                pressed && canSendNow && styles.sendButtonPressed,
              ]}
              disabled={!canSendNow}
              onPress={() => {
                (editingIndex != null
                  ? handleSubmitEditMessage(editingIndex, getWorkspace().edit?.text ?? '')
                  : handleSend(composeTextRef.current)).catch(() => {
                  // errors are handled in `handleSend`
                });
              }}
            >
              {requestInProgress ? (
                <View
                  testID="composer-send-progress"
                  accessible
                  accessibilityRole="progressbar"
                  accessibilityLabel={workspaceState.modifying ? 'Saving edit' : 'Request in progress'}
                >
                  <ActivityIndicator size="small" color={theme.textOnPrimary} />
                </View>
              ) : null}
              <Text style={styles.sendButtonText}>{editingIndex != null ? 'Save edit' : 'Send'}</Text>
            </Pressable>
          </View>

          {editingIndex == null && attachmentsBelow.length > 0 ? (
            attachmentsBelowExpanded ? (
              <View style={styles.attachmentsExpandedContainer}>
                <View style={styles.attachmentsExpandedChevronRow}>
                  <Pressable
                    style={({ pressed }) => [
                      styles.attachmentsChevronButton,
                      pressed && styles.attachmentsChevronButtonPressed,
                    ]}
                    onPress={() => setAttachmentsBelowExpanded(false)}
                  >
                    <Icon
                      name="chevron-up"
                      size={16}
                      color={theme.textSecondary}
                    />
                  </Pressable>
                </View>
                <ComposerAttachmentsExpandedPanel
                  attachments={buildManageRows(attachmentsBelow)}
                  disabled={
                    editingIndex != null || !canRunComposerActions || attachmentActionInProgress
                  }
                  onMove={(draftId, direction) =>
                    handleMoveDraft('below', draftId, direction)
                  }
                  onEditMetadata={(draftId, anchorTag) =>
                    handleEditDraftMetadata('below', draftId, anchorTag)
                  }
                  onDelete={draftId => handleDeleteDraft('below', draftId)}
                />
              </View>
            ) : (
              <AttachmentThumbnailStrip
                attachments={buildAttachmentStripRows(attachmentsBelow)}
                disabled={editingIndex != null || !canRunComposerActions || attachmentActionInProgress}
                expanded={false}
                onToggleExpanded={() => setAttachmentsBelowExpanded(true)}
              />
            )
          ) : null}
        </View>

        {statusBarParts.length > 0 ? (
          <View style={styles.sessionStatusBarContainer}>
            <Text
              style={styles.sessionStatusBarText}
              numberOfLines={1}
              ellipsizeMode="tail"
              selectable
              testID="chat-session-status-footer"
            >
              {statusBarParts.join('   ')}
            </Text>
          </View>
        ) : null}
      </View>

      {Platform.OS !== 'macos' && messageLimitVisible && (
        <Modal
          visible={messageLimitVisible}
          transparent
          animationType="fade"
          onRequestClose={() => setMessageLimitVisible(false)}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Message range</Text>
              <Text style={styles.modalSubtitle}>
                Python-style range (start:end). Example: -
                {DEFAULT_HISTORY_WINDOW}: for last {DEFAULT_HISTORY_WINDOW}{' '}
                messages. Leave blank for all messages.
              </Text>
              <View style={styles.rangeRow}>
                <View style={styles.rangeInputContainer}>
                  <Text style={styles.rangeLabel}>Start</Text>
                  <TextInput
                    style={styles.modalInput}
                    value={rangeStartText}
                    onChangeText={setRangeStartText}
                    placeholder={`e.g. -${DEFAULT_HISTORY_WINDOW}`}
                  />
                </View>
                <View style={styles.rangeInputContainer}>
                  <Text style={styles.rangeLabel}>End</Text>
                  <TextInput
                    style={styles.modalInput}
                    value={rangeEndText}
                    onChangeText={setRangeEndText}
                    placeholder="optional"
                  />
                </View>
              </View>
              <View style={styles.modalButtonsRow}>
                <Pressable
                  style={({ pressed }) => [
                    styles.modalButton,
                    styles.modalButtonSecondary,
                    pressed && styles.modalButtonPressed,
                  ]}
                  onPress={() => setMessageLimitVisible(false)}
                >
                  <Text style={styles.modalButtonSecondaryText}>Cancel</Text>
                </Pressable>
                <Pressable
                  style={({ pressed }) => [
                    styles.modalButton,
                    styles.modalButtonPrimary,
                    pressed && styles.modalButtonPressed,
                  ]}
                  onPress={() => {
                    setMessageLimitVisible(false);
                    applyMessageLimitAndReload({
                      startText: rangeStartText,
                      endText: rangeEndText,
                    }).catch(() => {});
                  }}
                >
                  <Text style={styles.modalButtonPrimaryText}>Apply</Text>
                </Pressable>
              </View>
              {lastReloadAt && (
                <Text style={styles.modalHelperText}>
                  Last reload at {lastReloadAt.toLocaleTimeString()}
                </Text>
              )}
            </View>
          </View>
        </Modal>
      )}

      {Platform.OS === 'macos' ? null : (
        <ApplicationActionDialog
          visible={!!activePluginDialogElement}
          dialog={(activePluginDialogElement as any)?.dialog}
          titleFallback={activePluginDialogElement?.label}
          prefillContext={pluginDialogPrefillContext}
          onSubmit={values => handleSubmitPluginDialog(values)}
          onCancel={handleCancelPluginDialog}
        />
      )}
    </View>
  );
});

function createStyles(
  theme: ReturnType<typeof useTheme>,
  styleVariant: TabStripStyle,
) {
  const codeLike =
    styleVariant === 'codeTabs' || styleVariant === 'underlineTabs';
  const radius = styleVariant === 'roundedPills' ? 12 : 10;
  const separatorWidth = 1;

  return StyleSheet.create({
    root: {
      flex: 1,
      borderWidth: codeLike ? 0 : separatorWidth,
      borderColor: codeLike ? 'transparent' : theme.border,
      borderRadius: codeLike ? 0 : radius,
      backgroundColor: theme.surface,
      overflow: codeLike ? 'visible' : 'hidden',
    },
    header: {
      flexDirection: 'row',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      paddingHorizontal: 12,
      paddingVertical: 10,
      borderBottomWidth: separatorWidth,
      borderBottomColor: theme.border,
      gap: 10,
      backgroundColor: theme.surface,
    },
    headerLeft: {
      flex: 1,
      gap: 4,
    },
    compactHeader: {
      paddingVertical: 6,
    },
    compactMetaRow: {
      flexWrap: 'nowrap',
      overflow: 'hidden',
    },
    notificationRail: {
      flexGrow: 0,
      flexShrink: 0,
    },
    headerRight: {
      paddingTop: Platform.OS === 'macos' ? 2 : 0,
    },
    title: {
      fontSize: theme.typography.fontSize.normal,
      lineHeight: theme.typography.lineHeight.normal,
      fontWeight: '700',
      color: theme.text,
      flexShrink: 1,
    },
    subtitle: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
      flexShrink: 1,
    },
    metaRow: {
      flexDirection: 'row',
      alignItems: 'center',
      flexWrap: 'wrap',
      gap: 6,
    },
    metaText: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textMuted,
      fontWeight: '600',
    },
    metaDot: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textMuted,
      marginTop: -1,
    },
    statusDot: {
      width: 7,
      height: 7,
      borderRadius: 999,
      marginTop: 1,
    },
    modalOverlay: {
      flex: 1,
      alignItems: 'center',
      justifyContent: 'center',
      padding: 20,
      backgroundColor: theme.modalBackdrop,
    },
    modalContent: {
      width: 360,
      maxWidth: '100%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      borderWidth: 1,
      borderColor: theme.border,
      padding: 16,
      gap: 10,
    },
    modalTitle: {
      fontSize: 16,
      fontWeight: '800',
      color: theme.text,
    },
    modalSubtitle: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
    },
    rangeRow: {
      flexDirection: 'row',
      gap: 12,
    },
    rangeInputContainer: {
      flex: 1,
      gap: 6,
    },
    rangeLabel: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      fontWeight: '700',
      color: theme.textSecondary,
    },
    modalInput: {
      borderWidth: 1,
      borderColor: theme.border,
      backgroundColor: theme.surfaceAlt,
      borderRadius: 10,
      paddingHorizontal: 10,
      paddingVertical: 8,
      color: theme.text,
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
    },
    modalButtonsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      gap: 10,
      marginTop: 2,
    },
    modalButton: {
      borderRadius: 10,
      paddingVertical: 10,
      paddingHorizontal: 14,
      borderWidth: 1,
    },
    modalButtonSecondary: {
      borderColor: theme.border,
      backgroundColor: theme.surfaceAlt,
    },
    modalButtonPrimary: {
      borderColor: theme.primary,
      backgroundColor: theme.primary,
    },
    modalButtonPressed: {
      opacity: 0.85,
    },
    modalButtonSecondaryText: {
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      fontWeight: '700',
      color: theme.text,
    },
    modalButtonPrimaryText: {
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      fontWeight: '800',
      color: theme.textOnPrimary,
    },
    modalHelperText: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textMuted,
    },
    body: {
      flex: 1,
      minHeight: 0,
      padding: 12,
      gap: 10,
    },
    compactBody: {
      padding: 8,
      gap: 6,
    },
    statusRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      gap: 12,
    },
    loadingRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
    errorRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      gap: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      borderRadius: 10,
      backgroundColor: theme.dangerMuted,
      borderWidth: separatorWidth,
      borderColor: theme.border,
    },
    errorText: {
      flex: 1,
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.text,
    },
    retryButton: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 8,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    retryButtonPressed: {
      opacity: 0.8,
    },
    retryButtonText: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      fontWeight: '600',
      color: theme.primary,
    },
    transcriptFrame: {
      flex: 1,
      position: 'relative',
    },
    transcript: {
      flex: 1,
    },
    transcriptContent: {
      paddingBottom: 12,
    },
    transcriptRangeControlRow: {
      flexDirection: 'row',
      justifyContent: 'center',
      alignItems: 'center',
      flexWrap: 'wrap',
      gap: 8,
      paddingBottom: 8,
    },
    transcriptRangeControlRowBottom: {
      paddingTop: 8,
      paddingBottom: 0,
    },
    transcriptRangeControlButton: {
      minHeight: 30,
      borderRadius: 8,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      paddingHorizontal: 10,
      paddingVertical: 6,
      alignItems: 'center',
      justifyContent: 'center',
    },
    transcriptRangeControlButtonSecondary: {
      backgroundColor: theme.surfaceAlt,
    },
    transcriptRangeControlButtonPressed: {
      opacity: 0.8,
    },
    transcriptRangeControlButtonDisabled: {
      opacity: 0.45,
    },
    transcriptRangeControlText: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      fontWeight: '700',
      color: theme.primary,
    },
    transcriptScrollButton: {
      position: 'absolute',
      right: 14,
      width: 38,
      height: 38,
      borderRadius: 19,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      alignItems: 'center',
      justifyContent: 'center',
      opacity: 0.95,
    },
    transcriptScrollButtonTop: {
      top: 14,
    },
    transcriptScrollButtonBottom: {
      bottom: 14,
    },
    transcriptScrollButtonPressed: {
      opacity: 0.75,
    },
    composerArea: {
      gap: 8,
      paddingTop: 10,
      borderTopWidth: separatorWidth,
      borderTopColor: theme.border,
    },
    sessionStatusBarContainer: {
      borderTopWidth: separatorWidth,
      borderTopColor: theme.border,
      paddingTop: 8,
    },
    sessionStatusBarText: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      color: theme.textSecondary,
      fontFamily: Platform.OS === 'macos' ? 'Menlo' : 'Courier',
    },
    composerHeaderRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
    composerHeaderLeft: {
      flex: 1,
    },
    composerHeaderRight: {
      flex: 1,
      minWidth: 0,
      alignItems: 'stretch',
      paddingTop: Platform.OS === 'macos' ? 2 : 0,
    },
    compactEditContext: {
      flex: 1,
    },
    compactEditActions: {
      flex: 0,
      width: 44,
    },
    composerActionsBar: {
      width: '100%',
    },
    composerRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
    attachmentPlusButton: {
      width: 32,
      height: 32,
      borderRadius: 10,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      alignItems: 'center',
      justifyContent: 'center',
      marginBottom: 1,
    },
    attachmentPlusButtonPressed: {
      opacity: 0.85,
    },
    attachmentPlusButtonDisabled: {
      opacity: 0.5,
    },
    composerInputFrame: {
      flex: 1,
      minHeight: 34,
      borderRadius: 10,
      paddingHorizontal: 10,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
      overflow: 'hidden',
    },
    composerInput: {
      flex: 1,
      flexShrink: 1,
    },
    composerInputDisabled: {
      opacity: 0.7,
    },
    sendButton: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 6,
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderRadius: 10,
      borderWidth: separatorWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    sendButtonPressed: {
      opacity: 0.85,
    },
    sendButtonDisabled: {
      opacity: 0.5,
    },
    attachmentsExpandedContainer: {
      marginBottom: 4,
    },
    attachmentsExpandedChevronRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      paddingHorizontal: 10,
      marginBottom: 4,
    },
    attachmentsChevronButton: {
      width: 28,
      height: 28,
      borderRadius: 14,
      alignItems: 'center',
      justifyContent: 'center',
      borderWidth: separatorWidth,
      borderColor: theme.border,
      backgroundColor: theme.surface,
    },
    attachmentsChevronButtonPressed: {
      opacity: 0.85,
    },
    sendButtonText: {
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      fontWeight: '700',
      color: theme.primary,
    },
    messageRow: {
      borderWidth: separatorWidth,
      borderColor: theme.border,
      borderRadius: 10,
      paddingHorizontal: 10,
      paddingVertical: 8,
      gap: 6,
    },
    messageRowAssistant: {
      backgroundColor: theme.bubbleToolBg,
    },
    messageMeta: {
      fontSize: theme.typography.fontSize.tiny,
      lineHeight: theme.typography.lineHeight.tiny,
      fontWeight: '600',
      color: theme.textSecondary,
    },
    messageText: {
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      color: theme.text,
    },
    hint: {
      fontSize: theme.typography.fontSize.secondary,
      lineHeight: theme.typography.lineHeight.secondary,
      color: theme.text,
    },
    hintSecondary: {
      fontSize: theme.typography.fontSize.small,
      lineHeight: theme.typography.lineHeight.small,
      color: theme.textSecondary,
    },
  });
}

export { createStyles as createChatPaneStyles };
