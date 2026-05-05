import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  AppState,
  Alert,
  Keyboard,
  KeyboardAvoidingView,
  Linking,
  Modal,
  Platform,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  TouchableWithoutFeedback,
  View,
} from 'react-native';
import type { FlatList as FlatListType } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Clipboard from '@react-native-clipboard/clipboard';
import type { AgentBackend, ChatController as FrontendChatController } from '@crystal-lattice/frontend-sdk';
import {
  attachmentDraftStatusLabel,
  deleteSessionAttachment,
  deriveChatStatusBarParts,
  deriveSessionListPresentationFromGroups,
  filterFooterElements,
  filterStatusBarElements,
  groupSessionListFields,
  isAttachmentDraftBlocking,
  mergeSessionScopedActionElements,
  runApplicationAction,
  selectSessionAssetId,
  selectLastAssistantMessage,
  storeSessionAttachment,
  generateIdempotencyKey,
  type RunActionContext,
  type AttachmentDraftStatus,
} from '@crystal-lattice/frontend-sdk';
import {
  ApplicationActionDialog,
  ActionsMenuBar,
  SessionActionsBar,
  SESSION_ACTIONS,
  type ActionDefinition,
  type SessionActionKey,
} from '@crystal-lattice/frontend-rn-components';
import { useChatController, useAgentsController } from '@crystal-lattice/frontend-sdk-react';
import {
  useHydrateControllerFromCache,
  useSessionSettingsController,
  useSessionUiSchemaController,
  useSessionApplicationUiSchemaController,
} from '@crystal-lattice/frontend-sdk-react';
import {
  type ApiMessage,
  type IndexedMessage,
  type ActionDisplayFollowupAction,
  type ActionUiElement,
  type ActionDisplayPayload,
  type UiSchemaElement,
  type SessionSummary,
} from './api';
import MessageBubble from './components/MessageBubble';
import { DependencyFlatList } from './components/DependencyFlatList';
import DebugEventsView from './components/DebugEventsView';
import {
  describePendingRequestRecovery,
  shouldClearPendingRequestRecovery,
  type PendingRequestRecovery,
} from './chatRecovery';
import OptionsPickerModal from './components/OptionsPickerModal';
import SessionSettingsModal from './components/SessionSettingsModal';
import SessionPluginsModal from './components/SessionPluginsModal';
import AgentSwitchModal from './components/AgentSwitchModal';
import ActionResultModal from './components/ActionResultModal';
import ActionResultInlineCard from './components/ActionResultInlineCard';
import type { DebugTimelineEntry } from './debugTimeline';
import { ALL_MESSAGE_ACTIONS, type MessageActionKey } from './messageActions';
import { selectDisplayContent } from './messageUtils';
import { pickAssetAsDataUrl } from './attachmentPicking';
import { AttachmentThumbnailStrip, type AttachmentLike } from './components/AttachmentThumbnailStrip';
import { ComposerAttachmentsManageModal } from './components/ComposerAttachmentsManageModal';
import {
  AttachmentMetadataModal,
  buildAttachmentMetadataDefaults,
  shouldPromptForAttachmentMetadata,
  type AttachmentMetadataUi,
} from './components/AttachmentMetadataModal';
import {
  createChatScrollAnchor,
  isChatScrollAnchor,
  PINNED_TO_BOTTOM_THRESHOLD_PX,
  type ChatScrollAnchor,
} from './chatScroll';
import { useTheme, type Theme } from './theme';
import { useApplicationPlugins } from './ApplicationPluginsContext';
import { usePersistentPinnedActions } from './usePersistentPinnedActions';
import { usePluginActionDialog } from './usePluginActionDialog';
import type { Event } from './eventsTypes';

interface SessionChatScreenProps {
  backend: AgentBackend | null;
  connectionId: string | null;
  isActive: boolean;
  sessionId: string;
  sessionSummary: SessionSummary | null;
  cachedMessages: IndexedMessage[] | null;
  lastLoadedAt: number | null;
  cachedEventsCursorId: string | null;
  cachedActiveRequestId: string | null;
  onUpdateCache: (
    messages: IndexedMessage[],
    eventsCursorId: string | null,
    activeRequestId: string | null,
  ) => void;
  onBack: () => void;
  onNavigateToSession?: (sessionId: string) => void;
  initialComposeText: string;
  initialScrollAnchor: ChatScrollAnchor | null;
  onSaveComposeText: (composeText: string) => void;
  onSaveScrollAnchor: (scrollAnchor: ChatScrollAnchor) => void;
  debugTimeline: DebugTimelineEntry[];
  onAppendDebugTimelineEntry: (
    entry: Omit<DebugTimelineEntry, 'id' | 'timestampMs'> & {
      detail?: string | null;
      meta?: Record<string, any> | null;
    },
  ) => void;
}

const STORAGE_KEY_SESSION_ACTIONS = 'clc_pinned_session_actions_v1';
const STORAGE_KEY_COMPOSER_ACTIONS = 'clc_pinned_composer_actions_v1';
const STORAGE_KEY_MESSAGE_ACTIONS = 'clc_pinned_message_actions_by_role_v1';

type PluginActionContext =
  | { kind: 'session'; sessionSummary: SessionSummary | null }
  | { kind: 'message'; index: number; message: ApiMessage; sessionSummary: SessionSummary | null };

type AppendAsRole = 'system' | 'developer' | 'user' | 'assistant';

type TranscriptRow =
  | { kind: 'status' }
  | { kind: 'stream' }
  | IndexedMessage;

type AttachmentDraftSide = 'above' | 'below';

type ComposerActionOptions = Array<{ value: string; label: string } | string>;

type ComposerActionUiElementBase = UiSchemaElement & {
  key?: string;
  attachment_type: string;
  label?: string;
  title?: string;
  icon?: string;
  options?: ComposerActionOptions;
  attachment_action_plugin?: string;
};

type ComposerAttachmentUiElement = ComposerActionUiElementBase & {
  ui_type: 'composer_attachment';
  supported_file_types?: string[];
  supports_upload?: boolean;
  display_placement: AttachmentDraftSide;
  metadata_ui?: AttachmentMetadataUi;
};

type ModelPickerUiElement = ComposerActionUiElementBase & {
  ui_type: 'model_picker';
  display_placement: 'left';
};

type MultipartPartDraft = {
  draftId: string;
  type: string;
  content: any;
  metadata?: any;
  previewUrl?: string | null;
  status: AttachmentDraftStatus;
  errorMessage?: string | null;
  attachmentKey: string;
  pluginId?: string | null;
  title: string;
  iconName: string | null;
  metadataUi: AttachmentMetadataUi | null;
};

type AttachmentBackgroundOperation =
  | { kind: 'upload'; filename: string }
  | { kind: 'delete'; filename: string }
  | null;

type ActionDisplayEntry = {
  key: string;
  display: ActionDisplayPayload;
  context: RunActionContext;
};

type SessionSnapshotSummary = {
  snapshot_id: string;
  session_id: string;
  created_at: string;
  reason: string;
};

function createDisplayEntry(display: ActionDisplayPayload, context: RunActionContext): ActionDisplayEntry {
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
    const existingIndex = current.findIndex((entry) => entry.display.display_id === displayId);
    if (existingIndex >= 0) {
      const updated = current.slice();
      updated[existingIndex] = nextEntry;
      return updated;
    }
  }
  return [...current, nextEntry];
}

function resolveAttachmentActionPluginId(element: ComposerAttachmentUiElement): string | null {
  const actionPlugin = (element as any).attachment_action_plugin;
  if (typeof actionPlugin === 'string' && actionPlugin.trim()) {
    return actionPlugin.trim();
  }
  const plugin = (element as any).plugin;
  if (typeof plugin === 'string' && plugin.trim()) {
    return plugin.trim();
  }
  return null;
}

const TRANSCRIPT_STATUS_ROW: TranscriptRow = { kind: 'status' };
const TRANSCRIPT_STREAM_ROW: TranscriptRow = { kind: 'stream' };

const SessionChatScreen: React.FC<SessionChatScreenProps> = ({
  backend,
  connectionId,
  isActive,
  sessionId,
  sessionSummary,
  cachedMessages,
  lastLoadedAt,
  cachedEventsCursorId,
  cachedActiveRequestId,
  onUpdateCache,
  onBack,
  onNavigateToSession,
  initialComposeText,
  initialScrollAnchor,
  onSaveComposeText,
  onSaveScrollAnchor,
  debugTimeline,
  onAppendDebugTimelineEntry,
}) => {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const [isAppActive, setIsAppActive] = useState(() => AppState.currentState === 'active');
  const [sendInProgress, setSendInProgress] = useState(false);
  const [composeText, setComposeText] = useState(initialComposeText ?? '');
  const [attachmentsAbove, setAttachmentsAbove] = useState<MultipartPartDraft[]>([]);
  const [attachmentsBelow, setAttachmentsBelow] = useState<MultipartPartDraft[]>([]);
  const [attachmentsManageVisible, setAttachmentsManageVisible] = useState(false);
  const [attachmentsManageSide, setAttachmentsManageSide] = useState<AttachmentDraftSide | null>(
    null,
  );
  const [attachmentMetadataVisible, setAttachmentMetadataVisible] = useState(false);
  const [attachmentMetadataTitle, setAttachmentMetadataTitle] = useState('');
  const [attachmentMetadataUi, setAttachmentMetadataUi] = useState<AttachmentMetadataUi | null>(
    null,
  );
  const [attachmentMetadataInitial, setAttachmentMetadataInitial] = useState<Record<string, any>>(
    {},
  );
  const [attachmentMetadataContext, setAttachmentMetadataContext] = useState<
    | {
        kind: 'new';
        element: ComposerAttachmentUiElement;
        side: AttachmentDraftSide;
        draftId?: string | null;
        content: any;
        previewUrl?: string | null;
        pendingAssetId?: string | null;
        pluginId?: string | null;
      }
    | { kind: 'edit'; side: AttachmentDraftSide; draftId: string }
    | null
  >(null);
  const [attachmentPickInProgress, setAttachmentPickInProgress] = useState(false);
  const [attachmentBackgroundOperation, setAttachmentBackgroundOperation] =
    useState<AttachmentBackgroundOperation>(null);
  const [imageAttachVisible, setImageAttachVisible] = useState(false);
  const [imageAttachElement, setImageAttachElement] = useState<ComposerAttachmentUiElement | null>(
    null,
  );
  const [imageUrlText, setImageUrlText] = useState('');
  const [rangeStartText, setRangeStartText] = useState('');
  const [rangeEndText, setRangeEndText] = useState('');
  const [lastReloadAt, setLastReloadAt] = useState<Date | null>(null);
  const [messageLimitVisible, setMessageLimitVisible] = useState(false);
  const [appendAsVisible, setAppendAsVisible] = useState(false);
  const [appendAsRole, setAppendAsRole] = useState<AppendAsRole>('user');
  const [deleteRangeVisible, setDeleteRangeVisible] = useState(false);
  const [deleteRangeStartText, setDeleteRangeStartText] = useState('');
  const [deleteRangeEndText, setDeleteRangeEndText] = useState('');
  const defaultPinnedSessionActions: SessionActionKey[] = Object.values(SESSION_ACTIONS)
    .filter((def) => def.defaultPinned)
    .map((def) => def.key);

  const scopedSessionActionsStorageKey = useMemo(
    () => `${STORAGE_KEY_SESSION_ACTIONS}:${connectionId ?? 'default'}`,
    [connectionId],
  );

  const scopedComposerActionsStorageKey = useMemo(
    () => `${STORAGE_KEY_COMPOSER_ACTIONS}:${connectionId ?? 'default'}`,
    [connectionId],
  );

  const { pinned: pinnedSessionActions, setPinned: setPinnedSessionActions } =
    usePersistentPinnedActions<SessionActionKey>(
      scopedSessionActionsStorageKey,
      defaultPinnedSessionActions,
      { migrateFromKeys: [STORAGE_KEY_SESSION_ACTIONS] },
    );

  const { pinned: pinnedComposerActions, setPinned: setPinnedComposerActions } =
    usePersistentPinnedActions<string>(
      scopedComposerActionsStorageKey,
      ['resend', 'cancel'],
      { migrateFromKeys: [STORAGE_KEY_COMPOSER_ACTIONS] },
    );
  const { controller: agentsController, state: agentsState } = useAgentsController({
    backend,
    cacheKey: connectionId ?? 'default',
    enabled: !!(backend && isActive),
  });
  const availableAgents = agentsState?.agents ?? [];
  const agentsLoading = agentsState?.loading ?? false;
  const [agentSwitchInProgress, setAgentSwitchInProgress] = useState(false);
  const [sessionAgentId, setSessionAgentId] = useState<string | null>(null);
  const [agentModalVisible, setAgentModalVisible] = useState(false);
  const [pinnedMessageActionsByRole, setPinnedMessageActionsByRole] = useState<
    Record<string, MessageActionKey[]>
  >({});
  const [messageViewModeByIndex, setMessageViewModeByIndex] = useState<
    Record<number, 'markdown' | 'raw'>
  >({});
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingText, setEditingText] = useState('');
  const [debugVisible, setDebugVisible] = useState(false);
  const [debugEvents, setDebugEvents] = useState<Event[]>([]);
  const [pendingRequestRecovery, setPendingRequestRecovery] =
    useState<PendingRequestRecovery | null>(null);
  const [resumeRecoveryInProgress, setResumeRecoveryInProgress] = useState(false);
  const [settingsVisible, setSettingsVisible] = useState(false);
  const [snapshotsVisible, setSnapshotsVisible] = useState(false);
  const [snapshotsLoading, setSnapshotsLoading] = useState(false);
  const [snapshotItems, setSnapshotItems] = useState<SessionSnapshotSummary[]>([]);
  const [selectedSnapshotId, setSelectedSnapshotId] = useState<string | null>(null);
  const [actionResultDisplay, setActionResultDisplay] = useState<ActionDisplayEntry | null>(null);
  const [inlineActionDisplays, setInlineActionDisplays] = useState<ActionDisplayEntry[]>([]);
  const [activeDisplayActionId, setActiveDisplayActionId] = useState<string | null>(null);
  const [pluginsVisible, setPluginsVisible] = useState(false);
  const [sessionOverrides, setSessionOverrides] = useState<Record<string, any>>({});
  const [sessionBaseConfig, setSessionBaseConfig] = useState<Record<string, any>>({});
  const [composerLeftSelectModalElement, setComposerLeftSelectModalElement] =
    useState<ModelPickerUiElement | null>(null);
  const [pluginActionInProgress, setPluginActionInProgress] = useState(false);
  const [androidKeyboardHeight, setAndroidKeyboardHeight] = useState(0);
  const {
    actionsById,
    sessionListFields,
  } = useApplicationPlugins();

	  const listRef = useRef<FlatListType<any> | null>(null);
  const composeTextRef = useRef<string>(initialComposeText ?? '');
  const onSaveComposeTextRef = useRef(onSaveComposeText);
  const onSaveScrollAnchorRef = useRef(onSaveScrollAnchor);
  const bottomGapPxRef = useRef<number>(0);
  const pinnedToBottomRef = useRef<boolean>(true);
  const initialScrollAnchorRef = useRef<ChatScrollAnchor | null>(
    isChatScrollAnchor(initialScrollAnchor) ? initialScrollAnchor : null,
  );
  const hasRestoredScrollRef = useRef(false);
  const lastEventsStatusRef = useRef<string | null>(null);
  const initialLoadControllerRef = useRef<FrontendChatController | null>(null);
  const initialLoadCompletedRef = useRef(false);
  const lastCacheSnapshotRef = useRef<{
    messagesRef: IndexedMessage[] | null;
    activeRequestId: string | null;
    dirty: boolean;
  } | null>(null);

  useEffect(() => {
    onSaveComposeTextRef.current = onSaveComposeText;
  }, [onSaveComposeText]);

  useEffect(() => {
    if (Platform.OS !== 'android') return;
    const show = Keyboard.addListener('keyboardDidShow', (e) => {
      setAndroidKeyboardHeight((e.endCoordinates?.height ?? 0) - 30);
    });
    const hide = Keyboard.addListener('keyboardDidHide', () => {
      setAndroidKeyboardHeight(0);
    });
    return () => {
      show.remove();
      hide.remove();
    };
  }, []);

  useEffect(() => {
    onSaveScrollAnchorRef.current = onSaveScrollAnchor;
  }, [onSaveScrollAnchor]);

  useEffect(() => {
    if (hasRestoredScrollRef.current) {
      return;
    }
    initialScrollAnchorRef.current = isChatScrollAnchor(initialScrollAnchor)
      ? initialScrollAnchor
      : null;
  }, [initialScrollAnchor]);

  const appendDebugNote = useCallback(
    (
      title: string,
      detail?: string | null,
      meta?: Record<string, any> | null,
      scope: DebugTimelineEntry['scope'] = 'chat',
    ) => {
      onAppendDebugTimelineEntry({
        scope,
        title,
        detail: detail ?? null,
        meta: meta ?? null,
      });
    },
    [onAppendDebugTimelineEntry],
  );

  const appendEventsToDebugBuffer = useCallback((events: Event[]) => {
    if (!events || events.length === 0) return;
    setDebugEvents((prev) => {
      const combined = [...prev, ...events];
      const max = 200;
      return combined.length > max ? combined.slice(combined.length - max) : combined;
    });
  }, []);

  useEffect(() => {
    const sub = AppState.addEventListener('change', (nextState) => {
      setIsAppActive(nextState === 'active');
    });
    return () => {
      sub.remove();
    };
  }, []);

  const eventsEnabled = !!(backend && sessionId && isActive && isAppActive);

  const { controller: chatController, state: chatState } = useChatController({
    backend,
    sessionId,
    initialMessages: cachedMessages ?? [],
    initialEventsCursorId: cachedEventsCursorId ?? null,
    initialActiveRequestId: cachedActiveRequestId ?? null,
    onEvents: appendEventsToDebugBuffer,
    eventsEnabled,
  });

  const messages: IndexedMessage[] = chatState?.messages ?? cachedMessages ?? [];
  const streamingRow = chatState?.streamingRow ?? null;
  const activeRequestId = chatState?.activeRequestId ?? cachedActiveRequestId ?? null;
  const activeError = chatState?.requestError ?? null;
  const loadingMessages = chatState?.loading ?? false;
  const sessionDirty = chatState?.dirty ?? false;
  const eventsStatus = chatState?.eventsStatus ?? 'idle';

  useEffect(() => {
    if (
      shouldClearPendingRequestRecovery({
        pending: pendingRequestRecovery,
        activeRequestId,
      })
    ) {
      setPendingRequestRecovery(null);
      appendDebugNote('Pending request reconciled', activeRequestId, {
        reason: 'active_request_known',
      });
    }
  }, [activeRequestId, appendDebugNote, pendingRequestRecovery]);

  useEffect(() => {
    if (lastEventsStatusRef.current === eventsStatus) {
      return;
    }
    lastEventsStatusRef.current = eventsStatus;
    appendDebugNote('Polling status changed', eventsStatus, {
      sessionId,
    });
  }, [appendDebugNote, eventsStatus, sessionId]);

  const hydrateChatCache = useCallback(
    (
      controller: NonNullable<typeof chatController>,
      cache: {
        messages: IndexedMessage[];
        eventsCursorId: string | null;
        activeRequestId: string | null;
        updatedAtMs: number | null;
      },
    ) => {
      controller.hydrateFromCache(cache);
    },
    [],
  );

  useHydrateControllerFromCache({
    controller: chatController,
    cache:
      cachedMessages != null
        ? {
            messages: cachedMessages,
            eventsCursorId: cachedEventsCursorId ?? null,
            activeRequestId: cachedActiveRequestId ?? null,
            updatedAtMs: lastLoadedAt ?? null,
          }
        : null,
    hydrate: hydrateChatCache,
  });

  useEffect(() => {
    if (!chatController) {
      return;
    }
    chatController.setHistoryRangeFromRangeText({
      startText: rangeStartText,
      endText: rangeEndText,
    });
  }, [chatController, rangeStartText, rangeEndText]);

  useEffect(() => {
    composeTextRef.current = composeText;
  }, [composeText]);

  useEffect(() => {
    if (!backend) return;
    agentsController?.ensureLoaded().catch(() => {
      // Non-fatal; status bar should still render.
    });
  }, [agentsController, backend]);

  useEffect(() => {
    const md = sessionSummary?.metadata;
    const raw = (md as any)?.agent_id;
    if (typeof raw === 'string' && raw.trim()) {
      setSessionAgentId(raw.trim());
    } else {
      setSessionAgentId(null);
    }
  }, [sessionId, sessionSummary]);

  useEffect(() => {
    const loadPinnedFromStorage = async () => {
      try {
        const messageRaw = await AsyncStorage.getItem(STORAGE_KEY_MESSAGE_ACTIONS);
        if (messageRaw) {
          try {
            const parsed = JSON.parse(messageRaw);
            if (parsed && typeof parsed === 'object') {
              const next: Record<string, MessageActionKey[]> = {};
              Object.entries(parsed).forEach(([role, value]) => {
                if (Array.isArray(value)) {
                  const filtered = (value as any[]).filter((key) => typeof key === 'string');
                  next[role] = filtered as MessageActionKey[];
                }
              });
              setPinnedMessageActionsByRole(next);
            }
          } catch (err) {
            console.log('Failed to parse stored pinned message actions', err);
          }
        }
      } catch (err) {
        console.log('Failed to load pinned message actions from storage', err);
      }
    };

    loadPinnedFromStorage();
  }, []);

  const { state: sessionUiSchemaState, controller: sessionUiSchemaController } =
    useSessionUiSchemaController({
      backend,
      cacheKey: connectionId ?? 'default',
      sessionId,
      enabled: !!(backend && isActive),
    });
  const { state: sessionAppUiSchemaState, controller: sessionAppUiSchemaController } = useSessionApplicationUiSchemaController({
    backend,
    cacheKey: connectionId ?? 'default',
    sessionId,
    enabled: !!(backend && isActive),
  });
  const { controller: sessionSettingsController } = useSessionSettingsController({
    backend,
    cacheKey: connectionId ?? 'default',
    sessionId,
    enabled: !!(backend && isActive),
  });
  const uiSchemaElements = sessionUiSchemaState?.elements ?? [];

  // Session-scoped application UI elements (from /sessions/{id}/application/ui-schema)
  // These are config-aware and filter based on the session's agent config.
  // Used ONLY for session_action and message_action in the chat context.
  // Do NOT combine with global application UI elements from useApplicationPlugins().
  const sessionAppUiElements = sessionAppUiSchemaState?.elements ?? [];

  // Session-scoped actions for chat context (config-aware)
  const visibleSessionActions = useMemo(
    () =>
      mergeSessionScopedActionElements({
        applicationActions: sessionAppUiElements.filter(
          (el): el is ActionUiElement => (el as any).ui_type === 'session_action',
        ),
        uiSchemaElements,
        uiType: 'session_action',
        context: sessionSummary ?? { session_id: sessionId, metadata: {} },
      }),
    [sessionAppUiElements, sessionId, sessionSummary, uiSchemaElements],
  );

  const visibleMessageActions = useMemo(
    () =>
      mergeSessionScopedActionElements({
        applicationActions: sessionAppUiElements.filter(
          (el): el is ActionUiElement => (el as any).ui_type === 'message_action',
        ),
        uiSchemaElements,
        uiType: 'message_action',
      }),
    [sessionAppUiElements, uiSchemaElements],
  );

  // const composerAttachmentElements: ComposerAttachmentUiElement[] = useMemo(() => {
  //   return (uiSchemaElements || []).filter((el) => {
  //     if (!el || el.ui_type !== 'composer_attachment') return false;
  //     const typed = el as any;
  //     if (typeof typed.attachment_type !== 'string' || !typed.attachment_type.trim()) return false;
  //     if (typed.display_placement !== 'above' && typed.display_placement !== 'below') return false;
  //     return true;
  //   }) as ComposerAttachmentUiElement[];
  // }, [uiSchemaElements]);

  /** Attachment drafts only support above/below placement. */
  const composerAttachmentElementsAll: ComposerAttachmentUiElement[] = useMemo(() => {
    return (uiSchemaElements || []).filter((el) => {
      if (!el || el.ui_type !== 'composer_attachment') return false;
      const typed = el as any;
      if (typeof typed.attachment_type !== 'string' || !typed.attachment_type.trim()) return false;
      return typed.display_placement === 'above' || typed.display_placement === 'below';
    }) as ComposerAttachmentUiElement[];
  }, [uiSchemaElements]);

  const modelPickerElements: ModelPickerUiElement[] = useMemo(() => {
    return (uiSchemaElements || []).filter((el) => {
      if (!el || el.ui_type !== 'model_picker') return false;
      const typed = el as any;
      if (typeof typed.attachment_type !== 'string' || !typed.attachment_type.trim()) return false;
      return typed.display_placement === 'left';
    }) as ModelPickerUiElement[];
  }, [uiSchemaElements]);

  const getComposerActionKey = useCallback(
    (el: ComposerAttachmentUiElement | ModelPickerUiElement) => {
      const pluginName =
        typeof (el as any).plugin === 'string' && (el as any).plugin
          ? String((el as any).plugin)
          : 'unknown';
      return typeof el.key === 'string' && el.key.trim()
        ? el.key.trim()
        : `composer_attachment:${pluginName}:${el.attachment_type}:${el.display_placement}`;
    },
    [],
  );

  const composerAttachmentElementByActionKey = useMemo(() => {
    const map: Record<string, ComposerAttachmentUiElement> = {};
    for (const el of composerAttachmentElementsAll) {
      map[getComposerActionKey(el)] = el;
    }
    return map;
  }, [composerAttachmentElementsAll, getComposerActionKey]);

  const modelPickerElementByActionKey = useMemo(() => {
    const map: Record<string, ModelPickerUiElement> = {};
    for (const el of modelPickerElements) {
      map[getComposerActionKey(el)] = el;
    }
    return map;
  }, [getComposerActionKey, modelPickerElements]);

  const composerActions: ActionDefinition[] = useMemo(() => {
    const builtins: ActionDefinition[] = [
      { key: 'resend', label: 'Resend', iconName: 'rotate-ccw' },
      { key: 'cancel', label: 'Cancel', iconName: 'x-circle' },
    ];

    const uiActions: ActionDefinition[] = [...composerAttachmentElementsAll, ...modelPickerElements].map(
      (el) => {
        const key = getComposerActionKey(el);
        const label =
          (typeof (el as any).title === 'string' && String((el as any).title).trim()) ||
          (typeof el.label === 'string' && el.label.trim()) ||
          el.attachment_type;
        const iconName =
          typeof (el as any).icon === 'string' && String((el as any).icon).trim()
            ? String((el as any).icon).trim()
            : el.attachment_type === 'image'
              ? 'image'
              : el.attachment_type === 'pdf'
                ? 'file-text'
                : el.attachment_type === 'dropdown' || el.attachment_type === 'select'
                  ? 'sliders'
                  : 'paperclip';
        return {
          key,
          label,
          iconName,
        } as ActionDefinition;
      },
    );

    return [...uiActions, ...builtins];
  }, [composerAttachmentElementsAll, getComposerActionKey, modelPickerElements]);

  /** Left-side model pickers that are pinned, so they show in the inline row. */
  const pinnedModelPickerElements = useMemo(() => {
    return modelPickerElements.filter((el) => {
      const actionKey = getComposerActionKey(el);
      return pinnedComposerActions.includes(actionKey);
    });
  }, [getComposerActionKey, modelPickerElements, pinnedComposerActions]);

  /** Pinned model picker keys are shown in the inline row only, not as icons in the action bar. */
  const pinnedComposerActionsForBar = useMemo(() => {
    const leftKeys = new Set(modelPickerElements.map((el) => getComposerActionKey(el)));
    return pinnedComposerActions.filter((key) => !leftKeys.has(key));
  }, [getComposerActionKey, modelPickerElements, pinnedComposerActions]);

  useEffect(() => {
    if (!backend || !sessionId || modelPickerElements.length === 0) return;
    let cancelled = false;
    Promise.all([backend.getSessionOverrides(sessionId), backend.getSessionBaseConfig(sessionId)])
      .then(([overrides, baseConfig]) => {
        if (!cancelled) {
          setSessionOverrides(overrides ?? {});
          setSessionBaseConfig(baseConfig ?? {});
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [backend, sessionId, modelPickerElements.length]);

  const normalizeSelectOptions = useCallback(
    (raw: ComposerActionOptions | undefined): Array<{ value: string; label: string }> => {
      if (!Array.isArray(raw)) return [];
      return raw
        .map((opt) => {
          if (typeof opt === 'string') return { value: opt, label: opt };
          if (opt && typeof opt === 'object' && typeof (opt as any).value === 'string') {
            const value = (opt as any).value;
            const label = typeof (opt as any).label === 'string' ? (opt as any).label : value;
            return { value, label };
          }
          return null;
        })
        .filter((v): v is { value: string; label: string } => v !== null);
    },
    [],
  );

  const handleComposerLeftSelectOption = useCallback(
    async (key: string, value: string) => {
      if (!backend || !sessionId) return;
      setComposerLeftSelectModalElement(null);
      try {
        await backend.patchSessionOverrides(sessionId, { [key]: value });
        setSessionOverrides((prev) => ({ ...prev, [key]: value }));
        sessionUiSchemaController?.invalidate();
        sessionUiSchemaController?.load();
      } catch {
        // leave modal closed
      }
    },
    [backend, sessionId, sessionUiSchemaController],
  );

  const hasDraftMessage =
    composeText.trim().length > 0 || attachmentsAbove.length > 0 || attachmentsBelow.length > 0;
  const draftAttachments = [...attachmentsAbove, ...attachmentsBelow];
  const blockingAttachmentDraft =
    draftAttachments.find((part) => isAttachmentDraftBlocking(part.status)) ?? null;
  const unresolvedAttachmentDraft =
    draftAttachments.find((part) => part.status !== 'ready' && part.status !== 'local') ?? null;
  const attachmentActionInProgress =
    attachmentBackgroundOperation != null || blockingAttachmentDraft != null;
  const attachmentActionText =
    attachmentBackgroundOperation?.kind === 'upload'
      ? `Uploading ${attachmentBackgroundOperation.filename}...`
      : attachmentBackgroundOperation?.kind === 'delete'
        ? `Deleting ${attachmentBackgroundOperation.filename}...`
        : blockingAttachmentDraft
          ? `${attachmentDraftStatusLabel(blockingAttachmentDraft.status, blockingAttachmentDraft.errorMessage)} ${blockingAttachmentDraft.content?.filename ?? blockingAttachmentDraft.title}...`
          : '';

  const attachmentsAboveStrip: AttachmentLike[] = useMemo(
    () =>
      attachmentsAbove.map((part) => ({
        id: part.draftId,
        type: part.type,
        content: part.content,
        metadata: part.metadata,
        previewUrl: part.previewUrl,
        status: part.status,
        errorMessage: part.errorMessage,
      })),
    [attachmentsAbove],
  );

  const attachmentsBelowStrip: AttachmentLike[] = useMemo(
    () =>
      attachmentsBelow.map((part) => ({
        id: part.draftId,
        type: part.type,
        content: part.content,
        metadata: part.metadata,
        previewUrl: part.previewUrl,
        status: part.status,
        errorMessage: part.errorMessage,
      })),
    [attachmentsBelow],
  );

  const attachmentsManageRows = useMemo(() => {
    if (!attachmentsManageVisible || !attachmentsManageSide) {
      return [];
    }
    const list = attachmentsManageSide === 'above' ? attachmentsAbove : attachmentsBelow;
    return list.map((part) => ({
      draftId: part.draftId,
      type: part.type,
      content: part.content,
      title: part.title,
      status: part.status,
      errorMessage: part.errorMessage,
    }));
  }, [
    attachmentsAbove,
    attachmentsBelow,
    attachmentsManageSide,
    attachmentsManageVisible,
  ]);

  const pluginSessionActionDefs = useMemo(
    () =>
      visibleSessionActions.map((el) => ({
        key: el.id,
        label: el.label,
        iconName: (el as any).icon || 'zap',
        defaultPinned: false,
      })),
    [visibleSessionActions],
  );

  const pluginMessageActionDefs = useMemo(
    () =>
      visibleMessageActions.map((el) => ({
        key: el.id,
        label: el.label,
        iconName: (el as any).icon || 'zap',
        defaultPinnedRoles: ['user', 'assistant', 'system', 'tool'],
        allowedRoles: ['user', 'assistant', 'system', 'tool'],
      })),
    [visibleMessageActions],
  );

  const applyMessageLimitAndReload = () => {
    setMessageLimitVisible(false);
    loadMessages({ reason: 'message_limit_reload', refreshUiSchema: true });
  };

  const syncCacheFromController = useCallback(
    (controller: NonNullable<typeof chatController>) => {
      const snapshot = controller.getCacheSnapshot();
      setLastReloadAt(new Date(snapshot.updatedAtMs ?? Date.now()));
      onUpdateCache(
        snapshot.messages,
        snapshot.eventsCursorId ?? null,
        snapshot.activeRequestId ?? null,
      );
      return snapshot;
    },
    [onUpdateCache],
  );

  const refreshSessionUiControllers = useCallback(() => {
    sessionUiSchemaController?.invalidate();
    sessionUiSchemaController?.load()?.catch(() => {});
    sessionAppUiSchemaController?.invalidate();
    sessionAppUiSchemaController?.load()?.catch(() => {});
    sessionSettingsController?.invalidate();
    sessionSettingsController?.load()?.catch(() => {});
  }, [
    sessionAppUiSchemaController,
    sessionSettingsController,
    sessionUiSchemaController,
  ]);

  const refreshSelectedSnapshot = useCallback(async () => {
    if (!backend) {
      setSelectedSnapshotId(null);
      return null;
    }
    try {
      const next = await backend.getSelectedSessionSnapshot(sessionId);
      setSelectedSnapshotId(next);
      return next;
    } catch {
      setSelectedSnapshotId(null);
      return null;
    }
  }, [backend, sessionId]);

  const loadSnapshots = useCallback(async () => {
    if (!backend) {
      setSnapshotItems([]);
      return;
    }
    setSnapshotsLoading(true);
    try {
      const items = await backend.listSessionSnapshots(sessionId);
      setSnapshotItems(items);
    } catch (err: any) {
      console.log('Failed to load snapshots', err);
      const message = err?.message || 'Failed to load snapshots';
      Alert.alert('Error', message);
    } finally {
      setSnapshotsLoading(false);
    }
  }, [backend, sessionId]);

  const loadMessages = useCallback(
    async (options: { silent?: boolean; reason?: string; refreshUiSchema?: boolean } = {}) => {
      if (!chatController) {
        const message = 'No active connection';
        if (!options.silent) {
          Alert.alert('Error', message);
        }
        return null;
      }
      if (options.refreshUiSchema) {
        refreshSessionUiControllers();
      }
      appendDebugNote('Reload started', options.reason ?? 'manual_reload', {
        rangeStartText,
        rangeEndText,
      });
      try {
        await chatController.loadMessagesFromRangeText({
          startText: rangeStartText,
          endText: rangeEndText,
        });
        const snapshot = syncCacheFromController(chatController);
        await refreshSelectedSnapshot();
        appendDebugNote('Reload succeeded', options.reason ?? 'manual_reload', {
          activeRequestId: snapshot.activeRequestId,
          eventsCursorId: snapshot.eventsCursorId,
        });
        return snapshot;
      } catch (err: any) {
        console.log('Failed to load messages', err);
        const message = err?.message || 'Failed to load messages';
        appendDebugNote('Reload failed', message, {
          reason: options.reason ?? 'manual_reload',
        });
        if (!options.silent) {
          Alert.alert('Error', message);
        }
        return null;
      }
    },
    [
      appendDebugNote,
      chatController,
      rangeEndText,
      rangeStartText,
      refreshSessionUiControllers,
      refreshSelectedSnapshot,
      syncCacheFromController,
    ],
  );

  const presentActionDisplay = useCallback((display: ActionDisplayPayload, context: RunActionContext) => {
    const nextEntry = createDisplayEntry(display, context);
    const presentation = display.presentation ?? 'modal';
    if (presentation === 'inline' || presentation === 'banner') {
      setActionResultDisplay(null);
      setInlineActionDisplays((current) => upsertInlineDisplay(current, nextEntry));
      return;
    }
    setActionResultDisplay(nextEntry);
  }, []);

  const executePluginAction = useCallback(
    async (element: ActionUiElement, context: RunActionContext) => {
      if (!backend) {
        Alert.alert('No connection', 'Connect to a server to run actions.');
        return;
      }

      setPluginActionInProgress(true);
      try {
        const { ok, effects, display, errorMessage } = await runApplicationAction({
          backend,
          element,
          actionsById,
          context,
          effects: {
            currentSessionId: sessionId,
            navigateOnCreatedSession: true,
          },
        });
        if (!ok) {
          Alert.alert('Action error', errorMessage || 'Failed to execute action');
          return;
        }

        for (const effect of effects) {
          if (effect.type === 'navigateToSession') {
            if (onNavigateToSession) {
              onNavigateToSession(effect.sessionId);
            }
            return;
          }
        }
        if (effects.some((effect) => effect.type === 'reloadSession')) {
          await loadMessages({ reason: 'action_reload', refreshUiSchema: true });
        }
        if (display) {
          presentActionDisplay(display, context);
        }
      } finally {
        setPluginActionInProgress(false);
      }
    },
    [actionsById, backend, loadMessages, onNavigateToSession, presentActionDisplay, sessionId],
  );

  const handleDisplayFollowupAction = useCallback(
    async (entry: ActionDisplayEntry, action: ActionDisplayFollowupAction) => {
      if (action.kind === 'open_url') {
        try {
          await Linking.openURL(action.url);
        } catch (err: any) {
          Alert.alert('Open link failed', err?.message || 'Unable to open the link.');
        }
        return;
      }
      if (action.kind === 'copy_text') {
        Clipboard.setString(action.text);
        Alert.alert('Copied', 'Copied to clipboard.');
        return;
      }
      if (action.kind === 'run_action') {
        if ((entry.display.presentation ?? 'modal') !== 'inline' && action.preserve_display !== true) {
          setActionResultDisplay((current) => (current?.key === entry.key ? null : current));
        }
        setActiveDisplayActionId(action.id);
        try {
          await executePluginAction(
            {
              ui_type: 'action_result_followup',
              plugin: action.plugin,
              id: action.id,
              label: action.label,
              action_id: action.action_id,
              action_owner: action.action_owner,
              fixed_params: action.fixed_params as Record<string, any> | undefined,
            },
            entry.context,
          );
        } finally {
          setActiveDisplayActionId(null);
        }
      }
    },
    [executePluginAction],
  );

  const recoverChatAfterResume = useCallback(
    async (reason: string) => {
      if (!chatController || !backend || !isActive) {
        return null;
      }

      setResumeRecoveryInProgress(true);
      appendDebugNote('Resume recovery started', reason, {
        sessionId,
        activeRequestId,
      });
      try {
        await chatController.recoverAfterResume();
        const snapshot = syncCacheFromController(chatController);
        appendDebugNote('Resume recovery succeeded', reason, {
          activeRequestId: snapshot.activeRequestId,
          eventsCursorId: snapshot.eventsCursorId,
        });
        if (snapshot.activeRequestId) {
          setPendingRequestRecovery(null);
        }
        return snapshot;
      } catch (err: any) {
        console.log('Failed to recover chat after resume', err);
        appendDebugNote('Resume recovery failed', err?.message || 'resume_recovery_failed', {
          reason,
          sessionId,
        });
        return null;
      } finally {
        setResumeRecoveryInProgress(false);
      }
    },
    [
      activeRequestId,
      appendDebugNote,
      backend,
      chatController,
      isActive,
      sessionId,
      syncCacheFromController,
    ],
  );

  useEffect(() => {
    if (!chatController) {
      initialLoadControllerRef.current = null;
      initialLoadCompletedRef.current = false;
      return;
    }

    if (initialLoadControllerRef.current === chatController) {
      return;
    }

    initialLoadControllerRef.current = chatController;
    initialLoadCompletedRef.current = false;

    if (!isActive || !isAppActive) {
      return;
    }

    let cancelled = false;
    void loadMessages({ reason: 'initial_open', silent: true }).then((snapshot) => {
      if (cancelled) {
        return;
      }
      initialLoadCompletedRef.current = snapshot != null;
      if (snapshot) {
        chatController.ensureEventStreamingStarted({
          initialSinceId: snapshot.eventsCursorId ?? null,
        });
      }
    });

    return () => {
      cancelled = true;
    };
  }, [chatController, isActive, isAppActive, loadMessages]);

  useEffect(() => {
    if (!chatController || !eventsEnabled) {
      return;
    }
    if (!initialLoadCompletedRef.current) {
      return;
    }
    chatController.ensureEventStreamingStarted();
  }, [chatController, eventsEnabled, eventsStatus, messages.length]);

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
          sessionSummary: context.sessionSummary || undefined,
          messageContext: isMessage
            ? { index: (context as any).index, message: (context as any).message }
            : undefined,
          dialogValues,
        });
      },
      [executePluginAction, sessionId],
    ),
  );

  const closeOverlays = useCallback(() => {
    setMessageLimitVisible(false);
    setDeleteRangeVisible(false);
    setAgentModalVisible(false);
    setSettingsVisible(false);
    setPluginsVisible(false);
    setDebugVisible(false);
    setImageAttachVisible(false);
    setImageAttachElement(null);
    handleCancelPluginDialog();
  }, [handleCancelPluginDialog]);

  useEffect(() => {
    if (isActive) return;
    closeOverlays();
  }, [closeOverlays, isActive]);

  const handleBack = useCallback(() => {
    closeOverlays();
    onBack();
  }, [closeOverlays, onBack]);

  useEffect(() => {
    if (cachedMessages != null && lastLoadedAt) {
      setLastReloadAt(new Date(lastLoadedAt));
    }
  }, [cachedMessages, connectionId, sessionId, lastLoadedAt]);

  useEffect(() => {
    if (!chatState) {
      return;
    }

    const prev = lastCacheSnapshotRef.current;
    const next = {
      messagesRef: chatState.messages,
      activeRequestId: chatState.activeRequestId ?? null,
      dirty: chatState.dirty ?? false,
    };

    const shouldPersist =
      prev == null ||
      prev.messagesRef !== next.messagesRef ||
      prev.activeRequestId !== next.activeRequestId ||
      prev.dirty !== next.dirty;
    if (!shouldPersist) {
      return;
    }

    lastCacheSnapshotRef.current = next;
    onUpdateCache(
      chatState.messages,
      chatState.eventsCursorId ?? null,
      chatState.activeRequestId ?? null,
    );
  }, [chatState?.messages, chatState?.activeRequestId, chatState?.dirty, onUpdateCache]);

  useEffect(() => {
    const saveMessagePinned = async () => {
      try {
        await AsyncStorage.setItem(
          STORAGE_KEY_MESSAGE_ACTIONS,
          JSON.stringify(pinnedMessageActionsByRole),
        );
      } catch (err) {
        console.log('Failed to save pinned message actions', err);
      }
    };
    saveMessagePinned();
  }, [pinnedMessageActionsByRole]);

  const persistScrollAnchor = useCallback(() => {
    onSaveScrollAnchorRef.current(
      createChatScrollAnchor({
        bottomGapPx: bottomGapPxRef.current,
        pinnedToBottom: pinnedToBottomRef.current,
      }),
    );
  }, []);

  const persistUiState = useCallback(() => {
    onSaveComposeTextRef.current(composeTextRef.current);
    persistScrollAnchor();
  }, [persistScrollAnchor]);

  const clearComposerDraft = useCallback(() => {
    setComposeText('');
    onSaveComposeText('');
    setAttachmentsAbove([]);
    setAttachmentsBelow([]);
  }, [onSaveComposeText]);

  const updateAttachmentDraft = useCallback(
    (
      side: AttachmentDraftSide,
      draftId: string,
      updater: (part: MultipartPartDraft) => MultipartPartDraft,
    ) => {
      const update = (prev: MultipartPartDraft[]) =>
        prev.map((part) => (part.draftId === draftId ? updater(part) : part));

      if (side === 'above') {
        setAttachmentsAbove(update);
        return;
      }
      setAttachmentsBelow(update);
    },
    [],
  );

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
        await deleteSessionAttachment({
          backend,
          sessionId,
          assetId,
          pluginId: typeof pluginId === 'string' && pluginId.trim() ? pluginId.trim() : undefined,
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

  const removeAttachmentFromSide = useCallback(
    async (side: AttachmentDraftSide, draftId: string) => {
      const list = side === 'above' ? attachmentsAbove : attachmentsBelow;
      const removed = list.find((p) => p.draftId === draftId);
      if (!removed) {
        return;
      }

      const assetId = selectSessionAssetId(removed?.content);
      if (!assetId) {
        if (side === 'above') {
          setAttachmentsAbove((prev) => prev.filter((p) => p.draftId !== draftId));
        } else {
          setAttachmentsBelow((prev) => prev.filter((p) => p.draftId !== draftId));
        }
        return;
      }

      const previousStatus = removed.status;
      updateAttachmentDraft(side, draftId, (part) => ({
        ...part,
        status: 'deleting',
        errorMessage: null,
      }));
      const deleted = await deleteStoredAttachmentAsset(
        assetId,
        removed?.content?.filename,
        false,
        removed?.pluginId,
      );
      if (deleted) {
        if (side === 'above') {
          setAttachmentsAbove((prev) => prev.filter((p) => p.draftId !== draftId));
        } else {
          setAttachmentsBelow((prev) => prev.filter((p) => p.draftId !== draftId));
        }
        return;
      }

      updateAttachmentDraft(side, draftId, (part) => ({
        ...part,
        status: previousStatus,
      }));
    },
    [attachmentsAbove, attachmentsBelow, deleteStoredAttachmentAsset, updateAttachmentDraft],
  );

  const moveAttachmentWithinSide = useCallback(
    (side: AttachmentDraftSide, draftId: string, direction: 'up' | 'down') => {
      const update = (prev: MultipartPartDraft[]) => {
        const idx = prev.findIndex((p) => p.draftId === draftId);
        if (idx < 0) return prev;
        const nextIdx = direction === 'up' ? idx - 1 : idx + 1;
        if (nextIdx < 0 || nextIdx >= prev.length) return prev;
        const next = [...prev];
        const tmp = next[idx];
        next[idx] = next[nextIdx];
        next[nextIdx] = tmp;
        return next;
      };

      if (side === 'above') {
        setAttachmentsAbove(update);
        return;
      }
      setAttachmentsBelow(update);
    },
    [],
  );

  const addAttachmentPart = useCallback((options: {
    element: ComposerAttachmentUiElement;
    content: any;
    metadata?: any;
    previewUrl?: string | null;
    draftId?: string;
    status?: AttachmentDraftStatus;
    errorMessage?: string | null;
  }) => {
    const pluginName =
      typeof (options.element as any).plugin === 'string' && (options.element as any).plugin
        ? String((options.element as any).plugin)
        : 'unknown';
    const attachmentKeyRaw =
      typeof options.element.key === 'string' && options.element.key.trim()
        ? options.element.key.trim()
        : `composer_attachment:${pluginName}:${options.element.attachment_type}:${options.element.display_placement}`;
    const titleRaw =
      (typeof (options.element as any).title === 'string' && String((options.element as any).title).trim()) ||
      (typeof options.element.label === 'string' && options.element.label.trim()) ||
      options.element.attachment_type;
    const iconNameRaw =
      typeof (options.element as any).icon === 'string' && String((options.element as any).icon).trim()
        ? String((options.element as any).icon).trim()
        : options.element.attachment_type === 'image'
          ? 'image'
          : options.element.attachment_type === 'pdf'
            ? 'file-text'
            : 'paperclip';

    const draftId =
      options.draftId || `${Date.now()}_${Math.random().toString(16).slice(2)}`;
    const part: MultipartPartDraft = {
      draftId,
      type: options.element.attachment_type,
      content: options.content,
      metadata: options.metadata ?? {},
      previewUrl: options.previewUrl ?? null,
      status: options.status ?? 'ready',
      errorMessage: options.errorMessage ?? null,
      attachmentKey: attachmentKeyRaw,
      pluginId: resolveAttachmentActionPluginId(options.element),
      title: String(titleRaw),
      iconName: iconNameRaw,
      metadataUi:
        options.element.metadata_ui && typeof options.element.metadata_ui === 'object'
          ? (options.element.metadata_ui as AttachmentMetadataUi)
          : null,
    };

    if (options.element.display_placement === 'above') {
      setAttachmentsAbove((prev) => [...prev, part]);
      return draftId;
    }
    setAttachmentsBelow((prev) => [...prev, part]);
    return draftId;
  }, []);

  const beginAddAttachmentPart = useCallback(
    (options: {
      element: ComposerAttachmentUiElement;
      content: any;
      previewUrl?: string | null;
      pendingAssetId?: string | null;
      draftId?: string | null;
    }) => {
      const side =
        options.element.display_placement === 'above' ? 'above' : 'below';
      const metadataUi =
        options.element.metadata_ui && typeof options.element.metadata_ui === 'object'
          ? (options.element.metadata_ui as AttachmentMetadataUi)
          : null;
      const defaults = buildAttachmentMetadataDefaults(metadataUi);
      const actionPluginId = resolveAttachmentActionPluginId(options.element);

      const shouldPrompt = shouldPromptForAttachmentMetadata({ metadataUi });
      if (shouldPrompt) {
        if (options.draftId) {
          updateAttachmentDraft(side, options.draftId, (part) => ({
            ...part,
            status: 'stored',
            errorMessage: null,
          }));
        }
        const titleRaw =
          (typeof (options.element as any).title === 'string' &&
            String((options.element as any).title).trim()) ||
          (typeof options.element.label === 'string' && options.element.label.trim()) ||
          options.element.attachment_type;

        setAttachmentMetadataTitle(`${String(titleRaw)} metadata`);
        setAttachmentMetadataUi(metadataUi);
        setAttachmentMetadataInitial(defaults);
        setAttachmentMetadataContext({
          kind: 'new',
          element: options.element,
          side,
          draftId: options.draftId ?? null,
          content: options.content,
          previewUrl: options.previewUrl ?? null,
          pendingAssetId: options.pendingAssetId ?? null,
          pluginId: actionPluginId,
        });
        setAttachmentMetadataVisible(true);
        return;
      }

      if (options.draftId) {
        updateAttachmentDraft(side, options.draftId, (part) => ({
          ...part,
          content: options.content,
          metadata: {
            ...(part.metadata || {}),
            ...defaults,
          },
          previewUrl: options.previewUrl ?? null,
          status: 'ready',
          errorMessage: null,
        }));
        return;
      }

      addAttachmentPart({
        element: options.element,
        content: options.content,
        metadata: {
          ...defaults,
          ...(
            actionPluginId && options.element.attachment_type === 'image'
              ? {
                  download_plugin_id: actionPluginId,
                }
              : {}
          ),
        },
        previewUrl: options.previewUrl ?? null,
        status: 'ready',
      });
    },
    [addAttachmentPart, updateAttachmentDraft],
  );

  const updateAttachmentMetadata = useCallback(
    (side: AttachmentDraftSide, draftId: string, metadata: Record<string, any>) => {
      const update = (prev: MultipartPartDraft[]) =>
        prev.map((part) => {
          if (part.draftId !== draftId) return part;
          return {
            ...part,
            metadata,
          };
        });

      if (side === 'above') {
        setAttachmentsAbove(update);
        return;
      }
      setAttachmentsBelow(update);
    },
    [],
  );

  const filenameFromUrl = useCallback((url: string): string => {
    const trimmed = url.trim();
    if (!trimmed) return 'image-url';
    const withoutHash = trimmed.split('#')[0] || trimmed;
    const withoutQuery = withoutHash.split('?')[0] || withoutHash;
    const parts = withoutQuery.split('/').filter(Boolean);
    const name = parts.length > 0 ? parts[parts.length - 1] : '';
    return name || 'image-url';
  }, []);

  const mimeTypeFromImageUrl = useCallback(
    (url: string, filenameFallback: string): string => {
      const trimmed = url.trim();
      if (trimmed.startsWith('data:')) {
        const match = trimmed.match(/^data:([^;]+);base64,/i);
        if (match && match[1]) return match[1];
      }

      const baseName = filenameFallback || 'image';
      const dotIdx = baseName.lastIndexOf('.');
      const ext = dotIdx >= 0 ? baseName.slice(dotIdx + 1).toLowerCase() : '';
      if (ext === 'png') return 'image/png';
      if (ext === 'jpg' || ext === 'jpeg') return 'image/jpeg';
      if (ext === 'gif') return 'image/gif';
      if (ext === 'webp') return 'image/webp';
      return 'image/*';
    },
    [],
  );

  const storePickedAttachment = useCallback(
    async (options: {
      element: ComposerAttachmentUiElement;
      filename: string;
      mimeType: string;
      dataUrl: string;
    }) => {
      if (!backend) {
        throw new Error('Connect to a server before uploading attachments.');
      }

      const previewUrl = options.element.attachment_type === 'image' ? options.dataUrl : null;
      const pluginId = resolveAttachmentActionPluginId(options.element);
      const draftId = addAttachmentPart({
        element: options.element,
        content: {
          filename: options.filename,
          mime_type: options.mimeType,
        },
        metadata:
          pluginId && options.element.attachment_type === 'image'
            ? { download_plugin_id: pluginId }
            : {},
        previewUrl,
        status: 'uploading_to_server',
      });
      const side = options.element.display_placement === 'above' ? 'above' : 'below';

      setAttachmentBackgroundOperation({
        kind: 'upload',
        filename: options.filename,
      });
      try {
        const stored = await storeSessionAttachment({
          backend,
          sessionId,
          attachmentType: options.element.attachment_type,
          filename: options.filename,
          mimeType: options.mimeType,
          dataUrl: options.dataUrl,
          pluginId: pluginId ?? undefined,
        });

        beginAddAttachmentPart({
          element: options.element,
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
        updateAttachmentDraft(side, draftId, (part) => ({
          ...part,
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
    [addAttachmentPart, backend, beginAddAttachmentPart, sessionId, updateAttachmentDraft],
  );

  const handlePickAttachment = useCallback(
    async (element: ComposerAttachmentUiElement) => {
      if (attachmentPickInProgress) return;
      if (element.attachment_type === 'image') {
        const supportsUpload = Boolean((element as any).supports_upload ?? true);
        const supportsUrl = Boolean((element as any).supports_url ?? true);
        if (!supportsUpload && !supportsUrl) {
          Alert.alert('Attachment unavailable', 'This provider does not allow image attachments.');
          return;
        }
        setImageAttachElement(element);
        setImageUrlText('');
        setImageAttachVisible(true);
        return;
      }

      setAttachmentPickInProgress(true);
      try {
        const picked = await pickAssetAsDataUrl({
          attachmentType: element.attachment_type,
          supportedFileTypes: Array.isArray(element.supported_file_types)
            ? element.supported_file_types
            : [],
        });
        if (!picked) {
          return;
        }

        await storePickedAttachment({
          element,
          filename: picked.filename,
          mimeType: picked.mimeType,
          dataUrl: picked.dataUrl,
        });
      } catch (err: any) {
        console.log('Failed to pick attachment', err);
        const message = err?.message || 'Failed to pick attachment';
        Alert.alert('Attachment error', message);
      } finally {
        setAttachmentPickInProgress(false);
      }
    },
    [attachmentPickInProgress, storePickedAttachment],
  );

  const pickImageForElement = useCallback(
    async (source: 'library' | 'camera') => {
      if (!imageAttachElement) {
        return;
      }
      if (attachmentPickInProgress) {
        return;
      }

      setAttachmentPickInProgress(true);
      try {
        const picked = await pickAssetAsDataUrl({
          attachmentType: 'image',
          imageSource: source,
          supportedFileTypes: Array.isArray(imageAttachElement.supported_file_types)
            ? imageAttachElement.supported_file_types
            : [],
        });
        if (!picked) {
          return;
        }
        setImageAttachVisible(false);

        await storePickedAttachment({
          element: imageAttachElement,
          filename: picked.filename,
          mimeType: picked.mimeType,
          dataUrl: picked.dataUrl,
        });
      } catch (err: any) {
        console.log('Failed to pick image attachment', err);
        const message = err?.message || 'Failed to pick image attachment';
        Alert.alert('Attachment error', message);
      } finally {
        setAttachmentPickInProgress(false);
      }
    },
    [attachmentPickInProgress, imageAttachElement, storePickedAttachment],
  );

  const addImageUrlForElement = useCallback(() => {
    if (!imageAttachElement) return;
    const url = imageUrlText.trim();
    if (!url) return;

    const looksLikeImageUrl =
      url.startsWith('http://') ||
      url.startsWith('https://') ||
      url.startsWith('data:image/');
    if (!looksLikeImageUrl) {
      Alert.alert(
        'Invalid URL',
        'Provide an http(s) image URL or a data:image/... URL.',
      );
      return;
    }

    const filename = filenameFromUrl(url);
    const mimeType = mimeTypeFromImageUrl(url, filename);
    setImageAttachVisible(false);

    beginAddAttachmentPart({
      element: imageAttachElement,
      content: {
        url,
        mime_type: mimeType,
        filename,
      },
    });
  }, [
    beginAddAttachmentPart,
    filenameFromUrl,
    imageAttachElement,
    imageUrlText,
    mimeTypeFromImageUrl,
  ]);

  useEffect(() => {
    return () => {
      persistUiState();
    };
  }, [persistUiState]);

  useEffect(() => {
    if (isActive) return;
    persistUiState();
  }, [isActive, persistUiState]);

  useEffect(() => {
    if (!snapshotsVisible) return;
    void loadSnapshots();
  }, [loadSnapshots, snapshotsVisible]);

  useEffect(() => {
    void refreshSelectedSnapshot();
  }, [refreshSelectedSnapshot]);

  const handleAppend = async () => {
    if (selectedSnapshotId) {
      Alert.alert('Read-only snapshot', 'Return to the live session before appending messages.');
      return;
    }
    const text = composeText.trim();
    const multipartContent = [...attachmentsAbove, ...attachmentsBelow].map(
      ({ type, content, metadata }) => ({
        type,
        content,
        metadata: metadata ?? {},
      }),
    );
    if (!text && multipartContent.length === 0) {
      return;
    }
    if (unresolvedAttachmentDraft) {
      Alert.alert('Attachment not ready', 'Resolve attachment upload issues before appending.');
      return;
    }
    if (attachmentActionInProgress) {
      Alert.alert('Attachment in progress', 'Wait for attachment uploads to finish before appending.');
      return;
    }
    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to append messages.');
      return;
    }
    setSendInProgress(true);
    try {
      await chatController.appendMessage({
        role: 'user',
        content: text,
        multipartContent,
      });
      clearComposerDraft();
    } catch (err: any) {
      console.log('Failed to append message', err);
      const message = err?.message || 'Failed to append message';
      Alert.alert('Error', message);
    } finally {
      setSendInProgress(false);
    }
  };

  const openAppendAsModal = useCallback(() => {
    if (!hasDraftMessage) {
      return;
    }
    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to append messages.');
      return;
    }
    if (
      sendInProgress ||
      activeRequestId ||
      pendingRequestRecovery ||
      attachmentActionInProgress ||
      unresolvedAttachmentDraft
    ) {
      return;
    }

    setAppendAsRole('user');
    setAppendAsVisible(true);
  }, [
    activeRequestId,
    attachmentActionInProgress,
    chatController,
    hasDraftMessage,
    sendInProgress,
    unresolvedAttachmentDraft,
  ]);

  const handleAppendAs = useCallback(async () => {
    const text = composeText.trim();
    const multipartContent = [...attachmentsAbove, ...attachmentsBelow].map(
      ({ type, content, metadata }) => ({
        type,
        content,
        metadata: metadata ?? {},
      }),
    );
    if (!text && multipartContent.length === 0) {
      return;
    }
    if (unresolvedAttachmentDraft) {
      Alert.alert('Attachment not ready', 'Resolve attachment upload issues before appending.');
      return;
    }
    if (attachmentActionInProgress) {
      Alert.alert('Attachment in progress', 'Wait for attachment uploads to finish before appending.');
      return;
    }
    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to append messages.');
      return;
    }
    if (
      sendInProgress ||
      activeRequestId ||
      pendingRequestRecovery ||
      attachmentActionInProgress ||
      unresolvedAttachmentDraft
    ) {
      return;
    }

    setSendInProgress(true);
    try {
      await chatController.appendMessage({
        role: appendAsRole as any,
        content: text,
        multipartContent,
      });
      clearComposerDraft();
      setAppendAsVisible(false);
    } catch (err: any) {
      console.log('Failed to append message', err);
      const message = err?.message || 'Failed to append message';
      Alert.alert('Error', message);
    } finally {
      setSendInProgress(false);
    }
  }, [
    activeRequestId,
    attachmentActionInProgress,
    appendAsRole,
    attachmentsAbove,
    attachmentsBelow,
    chatController,
    clearComposerDraft,
    composeText,
    pendingRequestRecovery,
    sendInProgress,
    unresolvedAttachmentDraft,
  ]);

  const handleSend = async () => {
    if (selectedSnapshotId) {
      Alert.alert('Read-only snapshot', 'Return to the live session before sending messages.');
      return;
    }
    const text = composeText.trim();
    const multipartContent = [...attachmentsAbove, ...attachmentsBelow].map(
      ({ type, content, metadata }) => ({
        type,
        content,
        metadata: metadata ?? {},
      }),
    );
    if (!text && multipartContent.length === 0) {
      return;
    }
    if (unresolvedAttachmentDraft) {
      Alert.alert('Attachment not ready', 'Resolve attachment upload issues before sending.');
      return;
    }
    if (attachmentActionInProgress) {
      Alert.alert('Attachment in progress', 'Wait for attachment uploads to finish before sending.');
      return;
    }
    if (sendInProgress) {
      return;
    }
    if (activeRequestId) {
      Alert.alert('Request in progress', 'Wait for the active request to finish before sending.');
      return;
    }
    if (pendingRequestRecovery) {
      Alert.alert(
        'Send status unclear',
        'Check status or retry the previous send before sending a new message.',
      );
      return;
    }
    setSendInProgress(true);
    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to send messages.');
      setSendInProgress(false);
      return;
    }
    const idempotencyKey = generateIdempotencyKey();
    try {
      appendDebugNote('Send started', text || 'multipart_message', {
        multipartCount: multipartContent.length,
        idempotencyKey,
      });
      chatController.clearRequestState();
      await chatController.sendMessage({
        message: {
          role: 'user',
          content: text,
          multipartContent,
        },
        idempotencyKey,
      });
      setPendingRequestRecovery(null);
      clearComposerDraft();
      appendDebugNote('Send acknowledged', text || 'multipart_message', {
        idempotencyKey,
      });
    } catch (err: any) {
      console.log('Failed to send request', err);
      const message = err?.message || 'Failed to send request';
      setPendingRequestRecovery({
        kind: 'send_message',
        idempotencyKey,
        requestedAtMs: Date.now(),
        errorMessage: message,
        message: {
          role: 'user',
          content: text,
          multipartContent,
        },
      });
      appendDebugNote('Send ack failed', message, {
        idempotencyKey,
        multipartCount: multipartContent.length,
      });
      Alert.alert('Error', message);
    } finally {
      setSendInProgress(false);
    }
  };

  const handleResend = async () => {
    if (pendingRequestRecovery) {
      Alert.alert(
        'Send status unclear',
        'Check status or retry the previous send before starting another resend.',
      );
      return;
    }
    setSendInProgress(true);
    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to resend.');
      setSendInProgress(false);
      return;
    }
    const idempotencyKey = generateIdempotencyKey();
    try {
      appendDebugNote('Resend started', null, {
        idempotencyKey,
      });
      chatController.clearRequestState();
      await chatController.send({ idempotencyKey });
      setPendingRequestRecovery(null);
      appendDebugNote('Resend acknowledged', null, {
        idempotencyKey,
      });
    } catch (err: any) {
      console.log('Failed to resend request', err);
      const message = err?.message || 'Failed to resend request';
      setPendingRequestRecovery({
        kind: 'send',
        idempotencyKey,
        requestedAtMs: Date.now(),
        errorMessage: message,
      });
      appendDebugNote('Resend ack failed', message, {
        idempotencyKey,
      });
      Alert.alert('Error', message);
    } finally {
      setSendInProgress(false);
    }
  };

  const handleCancel = async () => {
    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to cancel.');
      return;
    }
    if (!activeRequestId) {
      Alert.alert('No active request', 'There is no active request to cancel.');
      return;
    }
    try {
      await chatController.cancelActiveRequest();
      appendDebugNote('Cancel requested', activeRequestId, {
        sessionId,
      });
      void recoverChatAfterResume('cancel_request');
    } catch (err: any) {
      console.log('Failed to cancel request', err);
      const message = err?.message || 'Failed to cancel request';
      appendDebugNote('Cancel failed', message, {
        activeRequestId,
      });
      Alert.alert('Error', message);
    }
  };

  const handleCheckPendingRequestStatus = async () => {
    if (!pendingRequestRecovery) {
      return;
    }
    appendDebugNote(
      'Pending request status check started',
      describePendingRequestRecovery(pendingRequestRecovery),
      {
        idempotencyKey: pendingRequestRecovery.idempotencyKey,
      },
    );
    const snapshot = await recoverChatAfterResume('pending_status_check');
    if (snapshot?.activeRequestId) {
      setPendingRequestRecovery(null);
      return;
    }
    appendDebugNote(
      'Pending request still unresolved',
      pendingRequestRecovery.errorMessage,
      {
        idempotencyKey: pendingRequestRecovery.idempotencyKey,
      },
    );
  };

  const handleRetryPendingRequest = async () => {
    if (!pendingRequestRecovery || !chatController) {
      return;
    }

    setSendInProgress(true);
    appendDebugNote(
      'Pending request retry started',
      describePendingRequestRecovery(pendingRequestRecovery),
      {
        idempotencyKey: pendingRequestRecovery.idempotencyKey,
      },
    );

    try {
      chatController.clearRequestState();
      if (pendingRequestRecovery.kind === 'send_message') {
        await chatController.sendMessage({
          message: pendingRequestRecovery.message,
          configOverrides: pendingRequestRecovery.configOverrides,
          idempotencyKey: pendingRequestRecovery.idempotencyKey,
        });
      } else {
        await chatController.send({
          configOverrides: pendingRequestRecovery.configOverrides,
          idempotencyKey: pendingRequestRecovery.idempotencyKey,
        });
      }
      setPendingRequestRecovery(null);
      appendDebugNote(
        'Pending request retry acknowledged',
        describePendingRequestRecovery(pendingRequestRecovery),
        {
          idempotencyKey: pendingRequestRecovery.idempotencyKey,
        },
      );
    } catch (err: any) {
      const message = err?.message || 'Retry failed';
      console.log('Failed to retry pending request', err);
      setPendingRequestRecovery({
        ...pendingRequestRecovery,
        requestedAtMs: Date.now(),
        errorMessage: message,
      });
      appendDebugNote('Pending request retry failed', message, {
        idempotencyKey: pendingRequestRecovery.idempotencyKey,
      });
      Alert.alert('Retry failed', message);
    } finally {
      setSendInProgress(false);
    }
  };

  const handleComposerAction = useCallback(
    (key: string) => {
      if (key === 'resend') {
        handleResend().catch(() => {});
        return;
      }
      if (key === 'cancel') {
        handleCancel().catch(() => {});
        return;
      }

      const modelPicker = modelPickerElementByActionKey[key];
      if (modelPicker) {
        setComposerLeftSelectModalElement(modelPicker);
        return;
      }

      const element = composerAttachmentElementByActionKey[key];
      if (element) {
        handlePickAttachment(element).catch(() => {});
      }
    },
    [
      composerAttachmentElementByActionKey,
      handleCancel,
      handlePickAttachment,
      handleResend,
      modelPickerElementByActionKey,
    ],
  );

  const isComposerActionDisabled = useCallback(
    (key: string): boolean => {
      if (!backend) {
        return true;
      }
      if (key === 'resend') {
        return sendInProgress || !!activeRequestId || !!pendingRequestRecovery || hasDraftMessage;
      }
      if (key === 'cancel') {
        return sendInProgress || !activeRequestId;
      }

      if (composerAttachmentElementByActionKey[key] || modelPickerElementByActionKey[key]) {
        return (
          sendInProgress ||
          !!pendingRequestRecovery ||
          !!activeRequestId ||
          attachmentPickInProgress ||
          attachmentActionInProgress
        );
      }

      return false;
    },
    [
      activeRequestId,
      attachmentActionInProgress,
      attachmentPickInProgress,
      backend,
      composerAttachmentElementByActionKey,
      modelPickerElementByActionKey,
      hasDraftMessage,
      pendingRequestRecovery,
      sendInProgress,
    ],
  );
	  const confirmDeleteRange = async () => {
	    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to delete messages.');
      return;
    }
    try {
	      await chatController.deleteMessagesFromRangeText({
	        startText: deleteRangeStartText,
	        endText: deleteRangeEndText,
	      });
      setDeleteRangeVisible(false);
    } catch (err: any) {
	      const rawMessage = err?.message;
	      if (typeof rawMessage === 'string' && rawMessage.includes('Provide at least')) {
	        Alert.alert('Invalid range', rawMessage);
	        return;
	      }
	      console.log('Failed to delete range', err);
	      const message = rawMessage || 'Failed to delete messages';
	      Alert.alert('Error', message);
    }
  };

  const handleSwitchAgent = async (agentId: string) => {
	    if (!backend) {
	      Alert.alert('No connection', 'Connect to a server to switch agent.');
	      return;
	    }
	    try {
		      setAgentSwitchInProgress(true);
	      await backend.switchSessionAgent(sessionId, agentId);
	      setSessionAgentId(agentId && agentId.trim() ? agentId.trim() : null);
	      setAgentModalVisible(false);
	    } catch (err: any) {
	      console.log('Failed to switch agent', err);
	      const message = err?.message || 'Failed to switch agent';
	      Alert.alert('Error', message);
	    } finally {
		      setAgentSwitchInProgress(false);
	    }
	  };

	  const togglePinnedSessionAction = (action: SessionActionKey) => {
	    setPinnedSessionActions((prev) => {
	      if (prev.includes(action)) {
	        return prev.filter((a) => a !== action);
	      }
	      return [...prev, action];
	    });
	  };

  const handleCreateSnapshot = useCallback(async () => {
    if (!backend) {
      Alert.alert('No connection', 'Connect to a server to create snapshots.');
      return;
    }
    try {
      await backend.createSessionSnapshot(sessionId, { reason: 'manual' });
      await loadSnapshots();
    } catch (err: any) {
      console.log('Failed to create snapshot', err);
      Alert.alert('Error', err?.message || 'Failed to create snapshot');
    }
  }, [backend, loadSnapshots, sessionId]);

  const handleSelectSnapshot = useCallback(async (snapshotId: string) => {
    if (!backend) {
      Alert.alert('No connection', 'Connect to a server to select snapshots.');
      return;
    }
    try {
      await backend.selectSessionSnapshot(sessionId, snapshotId);
      await refreshSelectedSnapshot();
      await loadMessages({ reason: 'snapshot_select', refreshUiSchema: true });
    } catch (err: any) {
      console.log('Failed to select snapshot', err);
      Alert.alert('Error', err?.message || 'Failed to select snapshot');
    }
  }, [backend, loadMessages, refreshSelectedSnapshot, sessionId]);

  const handleClearSelectedSnapshot = useCallback(async () => {
    if (!backend) {
      Alert.alert('No connection', 'Connect to a server to return to the live session.');
      return;
    }
    try {
      await backend.clearSelectedSessionSnapshot(sessionId);
      await refreshSelectedSnapshot();
      await loadMessages({ reason: 'snapshot_clear', refreshUiSchema: true });
    } catch (err: any) {
      console.log('Failed to clear snapshot', err);
      Alert.alert('Error', err?.message || 'Failed to return to the live session');
    }
  }, [backend, loadMessages, refreshSelectedSnapshot, sessionId]);

  const handleRestoreSnapshot = useCallback(async (snapshotId: string) => {
    if (!backend) {
      Alert.alert('No connection', 'Connect to a server to restore snapshots.');
      return;
    }
    try {
      await backend.restoreSessionSnapshot(sessionId, snapshotId);
      await refreshSelectedSnapshot();
      await loadMessages({ reason: 'snapshot_restore', refreshUiSchema: true });
      await loadSnapshots();
    } catch (err: any) {
      console.log('Failed to restore snapshot', err);
      Alert.alert('Error', err?.message || 'Failed to restore snapshot');
    }
  }, [backend, loadMessages, loadSnapshots, refreshSelectedSnapshot, sessionId]);

  const handleDeleteSnapshot = useCallback(async (snapshotId: string) => {
    if (!backend) {
      Alert.alert('No connection', 'Connect to a server to delete snapshots.');
      return;
    }
    try {
      await backend.deleteSessionSnapshot(sessionId, snapshotId);
      if (selectedSnapshotId === snapshotId) {
        await refreshSelectedSnapshot();
      }
      await loadSnapshots();
    } catch (err: any) {
      console.log('Failed to delete snapshot', err);
      Alert.alert('Error', err?.message || 'Failed to delete snapshot');
    }
  }, [backend, loadSnapshots, refreshSelectedSnapshot, selectedSnapshotId, sessionId]);

  const handleSessionAction = async (action: SessionActionKey) => {
    if (action === 'reload') {
      chatController?.clearRequestState();
      await loadMessages({ reason: 'manual_reload', refreshUiSchema: true });
      return;
    }
    if (action === 'messageLimit') {
      setMessageLimitVisible(true);
      return;
    }
    if (action === 'deleteRange') {
      setDeleteRangeStartText('');
      setDeleteRangeEndText('');
      setDeleteRangeVisible(true);
      return;
    }
    if (action === 'agentSwitch') {
      setAgentModalVisible(true);
      if (!backend) {
        Alert.alert('No connection', 'Connect to a server to switch agent.');
        return;
      }
      if (availableAgents.length === 0 || sessionAgentId === null) {
        try {
		        await agentsController?.ensureLoaded();
	        const current = await backend.getSessionAgent(sessionId);
	          setSessionAgentId(current && current.trim() ? current.trim() : null);
        } catch (err: any) {
          console.log('Failed to load agents', err);
          const message = err?.message || 'Failed to load agents';
          Alert.alert('Error', message);
        }
      }
      return;
    }
    if (action === 'debugEvents') {
      setDebugVisible(true);
      return;
    }
    if (action === 'settings') {
      setSettingsVisible(true);
      return;
    }
    if (action === 'plugins') {
      setPluginsVisible(true);
      return;
    }
    if (action === 'snapshots') {
      setSnapshotsVisible(true);
      return;
    }

    const pluginEl = visibleSessionActions.find((el) => el.id === action);
    if (pluginEl) {
      openPluginDialogForElement(pluginEl, { kind: 'session', sessionSummary });
    }
  };

  const getPinnedActionsForRole = (role: string): MessageActionKey[] => {
    const allowedKeys = ALL_MESSAGE_ACTIONS
      .filter((def) => def.allowedRoles.includes(role))
      .map((def) => def.key as MessageActionKey);

    const existing = pinnedMessageActionsByRole[role];
    if (Array.isArray(existing)) {
      // Respect an explicit empty list (user chose to pin nothing).
      return existing;
    }

    const defaults: MessageActionKey[] = [];
    ALL_MESSAGE_ACTIONS.forEach((def) => {
      if (def.defaultPinnedRoles.includes(role) && def.allowedRoles.includes(role)) {
        defaults.push(def.key as MessageActionKey);
      }
    });
    return defaults;
  };

  const handleChangePinnedForRole = (role: string, pinned: MessageActionKey[]) => {
    setPinnedMessageActionsByRole((prev) => ({ ...prev, [role]: pinned }));
  };

  const handleStartEditMessage = (index: number, message: ApiMessage) => {
    const role = message.role || 'unknown';
    if (role === 'tool') {
      // Tool results cannot be modified.
      return;
    }
    const content = typeof message.content === 'string' ? message.content : '';
    setEditingIndex(index);
    setEditingText(content);
  };

  const handleSubmitEditMessage = async (
    index: number,
    _message: ApiMessage,
    newText: string,
  ) => {
    const trimmed = newText.trim();
    if (!trimmed) {
      Alert.alert('Invalid content', 'Message content cannot be empty.');
      return;
    }
    if (!chatController) {
      Alert.alert('No connection', 'Connect to a server to modify messages.');
      return;
    }
    try {
      await chatController.modifyMessage(index, trimmed);
      setEditingIndex(null);
      setEditingText('');
    } catch (err: any) {
      console.log('Failed to modify message', err);
      const msg = err?.message || 'Failed to modify message';
      Alert.alert('Error', msg);
    }
  };

  const handleCancelEditMessage = () => {
    setEditingIndex(null);
    setEditingText('');
  };

  const handleMessageAction = async (
    action: MessageActionKey,
    index: number,
    message: ApiMessage,
  ) => {
    if (action === 'modify') {
      handleStartEditMessage(index, message);
      return;
    }

    if (action === 'toggleMarkdown') {
      const role = message.role || 'unknown';
      if (role !== 'assistant') {
        return;
      }
      setMessageViewModeByIndex((prev) => {
        const current = prev[index] ?? 'markdown';
        const next: 'markdown' | 'raw' = current === 'markdown' ? 'raw' : 'markdown';
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
      Clipboard.setString(content);
      Alert.alert('Copied', 'Message content copied to clipboard.');
      return;
    }
    const pluginEl = visibleMessageActions.find((el) => el.id === action);
    if (pluginEl) {
      openPluginDialogForElement(pluginEl, {
        kind: 'message',
        index,
        message,
        sessionSummary,
      });
    }
  };


	  const sessionListFieldGroups = useMemo(
	    () => groupSessionListFields(sessionListFields || []),
	    [sessionListFields],
	  );

	  const sessionLabel = `Session ${sessionId.slice(0, 8)}`;

	  const sessionHeaderTitle = useMemo(() => {
	    if (!sessionSummary) {
	      return sessionLabel;
	    }
	    return deriveSessionListPresentationFromGroups(sessionSummary, sessionListFieldGroups).title;
	  }, [sessionSummary, sessionListFieldGroups, sessionLabel]);

	  const footerElements = useMemo(
	    () => filterFooterElements(uiSchemaElements),
	    [uiSchemaElements],
	  );

	  const statusBarElements = useMemo(
	    () => filterStatusBarElements(uiSchemaElements),
	    [uiSchemaElements],
	  );

	  const lastAssistantMessage = useMemo(
	    () => selectLastAssistantMessage({ messages, streamingRow }),
	    [messages, streamingRow],
	  );

	  const statusBarParts = useMemo(
	    () =>
	      deriveChatStatusBarParts({
	        sessionId,
	        sessionAgentId,
	        availableAgents,
	        lastAssistantMessage,
	        statusBarElements,
	      }),
	    [
	      sessionId,
	      sessionAgentId,
	      availableAgents,
	      lastAssistantMessage,
	      statusBarElements,
	    ],
	  );

	  const transcriptRows = useMemo<TranscriptRow[]>(() => {
	    const rows: TranscriptRow[] = [TRANSCRIPT_STATUS_ROW, TRANSCRIPT_STREAM_ROW];
	    for (let idx = messages.length - 1; idx >= 0; idx -= 1) {
	      rows.push(messages[idx]);
	    }
	    return rows;
	  }, [messages]);

  const inlineActionDisplaysContent = useMemo(() => {
    if (inlineActionDisplays.length === 0) {
      return null;
    }
    return (
      <View>
        {inlineActionDisplays.map((entry) => (
          <ActionResultInlineCard
            key={entry.key}
            display={entry.display}
            activeActionId={activeDisplayActionId}
            onDismiss={() =>
              setInlineActionDisplays((current) => current.filter((item) => item.key !== entry.key))
            }
            onFollowupAction={(action) => handleDisplayFollowupAction(entry, action)}
          />
        ))}
      </View>
    );
  }, [activeDisplayActionId, handleDisplayFollowupAction, inlineActionDisplays]);

	  const handleListScroll = useCallback((event: any) => {
	    const offset = event?.nativeEvent?.contentOffset?.y;
	    if (typeof offset !== 'number' || !Number.isFinite(offset)) {
	      return;
	    }
	    bottomGapPxRef.current = Math.max(0, offset);
	    pinnedToBottomRef.current =
	      bottomGapPxRef.current <= PINNED_TO_BOTTOM_THRESHOLD_PX;
	  }, []);

	  const maybeRestoreScroll = useCallback(() => {
	    if (hasRestoredScrollRef.current) {
	      return;
	    }
	    const list = listRef.current;
	    if (!list) {
	      return;
	    }
	
	    const anchor = initialScrollAnchorRef.current;
	    const offset = anchor && !anchor.pinnedToBottom ? anchor.bottomGapPx : 0;
	    list.scrollToOffset({ offset, animated: false });
	    bottomGapPxRef.current = offset;
	    pinnedToBottomRef.current = offset <= PINNED_TO_BOTTOM_THRESHOLD_PX;
	    hasRestoredScrollRef.current = true;
	  }, []);

    const openAttachmentMetadataForEdit = useCallback(
      (side: AttachmentDraftSide, draftId: string) => {
        const list = side === 'above' ? attachmentsAbove : attachmentsBelow;
        const part = list.find((p) => p.draftId === draftId);
        if (!part) {
          return;
        }

        setAttachmentsManageVisible(false);
        setAttachmentMetadataTitle(`${part.title} metadata`);
        setAttachmentMetadataUi(part.metadataUi);
        setAttachmentMetadataInitial({
          ...buildAttachmentMetadataDefaults(part.metadataUi),
          ...(part.metadata ?? {}),
        });
        setAttachmentMetadataContext({ kind: 'edit', side, draftId });
        setAttachmentMetadataVisible(true);
      },
      [attachmentsAbove, attachmentsBelow],
    );

    const handleAttachmentMetadataCancel = useCallback(() => {
      const ctx = attachmentMetadataContext;
      setAttachmentMetadataVisible(false);
      setAttachmentMetadataContext(null);
      if (ctx?.kind === 'new' && ctx.pendingAssetId) {
        if (ctx.draftId) {
          updateAttachmentDraft(ctx.side, ctx.draftId, (part) => ({
            ...part,
            status: 'deleting',
            errorMessage: null,
          }));
        }
        deleteStoredAttachmentAsset(
          ctx.pendingAssetId,
          ctx.content?.filename,
          false,
          ctx.pluginId,
        )
          .then((deleted) => {
            if (deleted && ctx.draftId) {
              if (ctx.side === 'above') {
                setAttachmentsAbove((prev) => prev.filter((part) => part.draftId !== ctx.draftId));
              } else {
                setAttachmentsBelow((prev) => prev.filter((part) => part.draftId !== ctx.draftId));
              }
            }
          })
          .catch(() => {});
      }
    }, [attachmentMetadataContext, deleteStoredAttachmentAsset, updateAttachmentDraft]);

    const handleAttachmentMetadataSave = useCallback(
      (metadata: Record<string, any>) => {
        const ctx = attachmentMetadataContext;
        if (!ctx) {
          setAttachmentMetadataVisible(false);
          return;
        }

        if (ctx.kind === 'new') {
          if (ctx.draftId) {
            updateAttachmentDraft(ctx.side, ctx.draftId, (part) => ({
              ...part,
              content: ctx.content,
              metadata,
              previewUrl: ctx.previewUrl ?? null,
              status: 'ready',
              errorMessage: null,
            }));
          } else {
            addAttachmentPart({
              element: ctx.element,
              content: ctx.content,
              metadata,
              previewUrl: ctx.previewUrl ?? null,
              status: 'ready',
            });
          }
        } else if (ctx.kind === 'edit') {
          updateAttachmentMetadata(ctx.side, ctx.draftId, metadata);
        }

        setAttachmentMetadataVisible(false);
        setAttachmentMetadataContext(null);
      },
      [addAttachmentPart, attachmentMetadataContext, updateAttachmentDraft, updateAttachmentMetadata],
    );

	  return (
	    <KeyboardAvoidingView
	      style={styles.keyboardAvoiding}
	      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
	      keyboardVerticalOffset={64}
	    >
	      <View
	        style={[
	          styles.container,
	          Platform.OS === 'android' &&
	            androidKeyboardHeight > 0 && { paddingBottom: androidKeyboardHeight },
	        ]}
	      >
	        <View style={styles.headerRow}>
	          <TouchableOpacity style={styles.backButton} onPress={handleBack}>
	            <Text style={styles.backButtonText}>← Sessions</Text>
	          </TouchableOpacity>
	          <Text style={styles.title} numberOfLines={1}>
	            {sessionHeaderTitle}
	          </Text>
          <View style={styles.headerButtons}>
            <SessionActionsBar
              renderIcon={({ name, size, color }) => (
                <Icon name={name} size={size} color={color} />
              )}
              renderPinIcon={({ size, color }) => (
                <Icon name="star" size={size} color={color} />
              )}
              renderCloseIcon={({ size, color, renderIcon }) =>
                renderIcon ? renderIcon({ name: 'x', size, color }) : null
              }
              pinned={pinnedSessionActions}
              onChangePinned={setPinnedSessionActions}
              onAction={handleSessionAction}
              isActionDisabled={(action) =>
                pluginActionInProgress ||
                ((sendInProgress || resumeRecoveryInProgress) && action === 'reload')
              }
              extraActions={pluginSessionActionDefs}
              isActive={isActive}
              modalContentStyle={styles.sessionActionsModalContent}
            />
          </View>
	        </View>

	      {sessionDirty && (
	        <View style={styles.dirtyBanner}>
	          <Text style={styles.dirtyBannerText} numberOfLines={1}>
	            Out of sync — Reload to recover
	          </Text>
	          <TouchableOpacity
	            style={[styles.button, styles.secondaryButton, styles.smallButton]}
	            onPress={async () => {
	              chatController?.clearRequestState();
                      await loadMessages({ reason: 'dirty_banner_reload', refreshUiSchema: true });
	            }}
	            disabled={!chatController || sendInProgress || loadingMessages || resumeRecoveryInProgress}
	          >
	            <Text
	              style={[
	                styles.buttonTextSecondary,
	                (!chatController || sendInProgress || loadingMessages || resumeRecoveryInProgress) &&
	                  styles.buttonTextDisabled,
	              ]}
	            >
	              Reload
	            </Text>
	          </TouchableOpacity>
	        </View>
	      )}

        {selectedSnapshotId && (
          <View style={styles.dirtyBanner}>
            <Text style={styles.dirtyBannerText} numberOfLines={1}>
              Viewing snapshot {selectedSnapshotId} · Read-only
            </Text>
            <TouchableOpacity
              style={[styles.button, styles.secondaryButton, styles.smallButton]}
              onPress={handleClearSelectedSnapshot}
              disabled={!backend}
            >
              <Text style={styles.buttonTextSecondary}>Live</Text>
            </TouchableOpacity>
          </View>
        )}

	      {(loadingMessages || pluginActionInProgress || attachmentActionInProgress || resumeRecoveryInProgress) && (
	        <View style={styles.loadingContainer}>
	          <ActivityIndicator size="small" color={theme.primary} />
	          <Text style={styles.loadingText}>
	            {loadingMessages
	              ? 'Loading messages...'
	              : resumeRecoveryInProgress
	                ? 'Revalidating chat after resume...'
	              : pluginActionInProgress
	                ? 'Running action...'
	                : attachmentActionText}
	          </Text>
	        </View>
	      )}
	
	      <DependencyFlatList
	        style={styles.messagesContainer}
	        ref={listRef}
	        data={transcriptRows}
	        inverted
          ListHeaderComponent={inlineActionDisplaysContent}
	        onLayout={() => {
	          maybeRestoreScroll();
	        }}
	        onContentSizeChange={() => {
	          maybeRestoreScroll();
	        }}
	        onScroll={handleListScroll}
	        scrollEventThrottle={16}
	        maintainVisibleContentPosition={{
	          minIndexForVisible: 0,
	          autoscrollToTopThreshold: PINNED_TO_BOTTOM_THRESHOLD_PX,
	        }}
	        keyExtractor={(row) => {
	          if ('kind' in row) {
	            return row.kind === 'status' ? 'row-status' : 'row-stream';
	          }
	          return `msg-${row.index}`;
	        }}
	        getItemDependencies={(row) => {
	          if ('kind' in row) {
	            if (row.kind === 'status') {
	              return [statusBarParts];
	            }
	            const lastMessageIndex = messages.length > 0 ? messages[messages.length - 1].index : null;
	            return [
	              streamingRow,
	              lastMessageIndex,
	              isActive,
	              footerElements,
	              pluginMessageActionDefs,
	            ];
	          }
	
	          const role = row.message.role || 'unknown';
	          const defaultModeForRole: 'markdown' | 'raw' =
	            role === 'assistant' ? 'markdown' : 'raw';
	          const renderMode = messageViewModeByIndex[row.index] ?? defaultModeForRole;
	          const isEditing = editingIndex === row.index;
	          return [
	            isActive,
	            footerElements,
	            pluginMessageActionDefs,
	            sessionSummary,
	            pinnedMessageActionsByRole[role],
	            renderMode,
	            isEditing,
	            isEditing ? editingText : null,
	          ];
	        }}
	        renderItem={({ item: row }) => {
	          if ('kind' in row) {
	            if (row.kind === 'status') {
	              if (!statusBarParts || statusBarParts.length === 0) {
	                return null;
	              }
	              return (
	                <View style={styles.statusBarContainer}>
	                  <Text style={styles.statusBarText}>{statusBarParts.join('   ')}</Text>
	                </View>
	              );
	            }
	
	            if (!streamingRow || (!streamingRow.content && !streamingRow.reasoning)) {
	              return null;
	            }
	            const streamingIndex =
	              messages.length > 0 ? messages[messages.length - 1].index + 1 : 0;
	            return (
	              <MessageBubble
	                index={streamingIndex}
	                isActive={isActive}
	                backend={backend}
	                sessionId={sessionId}
	                message={{
	                  role: 'assistant',
	                  content: streamingRow.content,
	                  metadata: {
	                    ...(streamingRow.metadata || {}),
	                    reasoning: streamingRow.reasoning,
	                  },
	                }}
	                pinnedActions={[]}
	                allowedActions={[]}
	                onAction={handleMessageAction}
	                onChangePinnedForRole={handleChangePinnedForRole}
	                isEditing={false}
	                renderMode="markdown"
	                footerElements={footerElements}
	                pluginActionDefs={pluginMessageActionDefs}
	              />
	            );
	          }

	          const m = row;
	          const role = m.message.role || 'unknown';
	          const allowedActions = ALL_MESSAGE_ACTIONS
	            .filter((def) => def.allowedRoles.includes(role))
	            .map((def) => def.key as MessageActionKey);
	          const pinnedForRole = getPinnedActionsForRole(role);
	          const isEditing = editingIndex === m.index;
	          const defaultModeForRole: 'markdown' | 'raw' =
	            role === 'assistant' ? 'markdown' : 'raw';
	          const renderMode = messageViewModeByIndex[m.index] ?? defaultModeForRole;
	          return (
	            <MessageBubble
	              index={m.index}
	              isActive={isActive}
	              backend={backend}
	              sessionId={sessionId}
	              message={m.message}
	              pinnedActions={pinnedForRole}
	              allowedActions={allowedActions}
	              onAction={handleMessageAction}
	              onChangePinnedForRole={handleChangePinnedForRole}
	              isEditing={isEditing}
	              editingText={isEditing ? editingText : undefined}
	              onChangeEditingText={isEditing ? setEditingText : undefined}
	              onSubmitEdit={handleSubmitEditMessage}
	              onCancelEdit={handleCancelEditMessage}
	              renderMode={renderMode}
	              footerElements={footerElements}
	              pluginActionDefs={pluginMessageActionDefs}
	            />
	          );
	        }}
	      />

      {activeError && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorTitle}>Error</Text>
          <Text style={styles.errorText}>{activeError.detail}</Text>
        </View>
      )}

      {pendingRequestRecovery && (
        <View style={styles.pendingRecoveryContainer}>
          <Text style={styles.pendingRecoveryTitle}>Send not yet confirmed</Text>
          <Text style={styles.pendingRecoveryText}>
            {pendingRequestRecovery.errorMessage}
          </Text>
          <Text style={styles.pendingRecoveryText}>
            Retry reuses the original idempotency key, so it will not duplicate a request that the
            server already accepted.
          </Text>
          <View style={styles.pendingRecoveryButtonsRow}>
            <TouchableOpacity
              style={[styles.button, styles.secondaryButton, styles.pendingRecoveryButton]}
              onPress={() => {
                handleCheckPendingRequestStatus().catch(() => {});
              }}
              disabled={sendInProgress || loadingMessages || resumeRecoveryInProgress}
            >
              <Text style={styles.buttonTextSecondary}>Check status</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.button, styles.primaryButton, styles.pendingRecoveryButton]}
              onPress={() => {
                handleRetryPendingRequest().catch(() => {});
              }}
              disabled={sendInProgress || loadingMessages || resumeRecoveryInProgress}
            >
              <Text style={styles.buttonText}>Retry</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      <View style={styles.composer}>
        <View style={styles.composerMainColumn}>
          <View style={styles.composerTopRow}>
            <View style={styles.composerInlineSelectRow}>
              {pinnedModelPickerElements.map((el) => {
                const key = typeof el.key === 'string' && el.key.trim() ? el.key : '';
                if (!key) return null;
                const options = normalizeSelectOptions(el.options);
                const elementDefault =
                  typeof (el as any).default === 'string' ? (el as any).default : undefined;
                const effectiveValue =
                  sessionOverrides[key] ??
                  sessionBaseConfig[key] ??
                  elementDefault ??
                  options[0]?.value ??
                  '';
                const selectedLabel =
                  options.find((o) => o.value === effectiveValue)?.label ?? String(effectiveValue);
                const label =
                  (typeof el.label === 'string' && el.label.trim() ? el.label : key);
                const isSelect =
                  el.attachment_type === 'select' ||
                  el.attachment_type === 'options' ||
                  el.attachment_type === 'dropdown';
                if (!isSelect) return null;
                return (
                  <TouchableOpacity
                    key={key}
                    style={styles.composerInlineSelectButton}
                    onPress={() => setComposerLeftSelectModalElement(el)}
                    disabled={
                      sendInProgress ||
                      !!pendingRequestRecovery ||
                      !!activeRequestId ||
                      attachmentActionInProgress ||
                      options.length === 0
                    }
                  >
                    <Text style={styles.composerInlineSelectLabel} numberOfLines={1}>
                      {label}:
                    </Text>
                    <Text style={styles.composerInlineSelectValue} numberOfLines={1}>
                      {selectedLabel}
                    </Text>
                    <Icon name="chevron-down" size={10} color={theme.textSecondary} />
                  </TouchableOpacity>
                );
              })}
            </View>
            <ActionsMenuBar<ActionDefinition>
                title="Composer actions"
                variant="modal"
                renderIcon={({ name, size, color }) => (
                  <Icon name={name} size={size} color={color} />
                )}
                renderPinIcon={({ pinned: isPinned, size, color }) => (
                  <Icon name={isPinned ? 'star' : 'star'} size={size} color={color} />
                )}
                renderCloseIcon={({ size, color, renderIcon }) =>
                  renderIcon ? renderIcon({ name: 'x', size, color }) : null
                }
                baseActions={composerActions as any}
                pinned={pinnedComposerActions}
                pinnedKeysForBar={pinnedComposerActionsForBar}
                onChangePinned={setPinnedComposerActions}
                onAction={handleComposerAction}
                isActionDisabled={isComposerActionDisabled}
                isActive={isActive}
              />
          </View>

            <AttachmentThumbnailStrip
              attachments={attachmentsAboveStrip}
              onPressManageAll={() => {
                setAttachmentsManageSide('above');
                setAttachmentsManageVisible(true);
              }}
              disabled={
                sendInProgress ||
                !!pendingRequestRecovery ||
                !!activeRequestId ||
                attachmentActionInProgress
              }
            />

            <TextInput
              style={styles.composerInput}
              placeholder="Type your message..."
              placeholderTextColor={theme.textSecondary}
              value={composeText}
              onChangeText={(text) => {
                setComposeText(text);
              }}
              onBlur={() => {
                onSaveComposeText(composeTextRef.current);
              }}
              multiline
            />

            {/** Compute per-button enablement so we can style text when disabled. */}
            {(() => {
              const canAppend =
                !!backend &&
                !selectedSnapshotId &&
                !sendInProgress &&
                !pendingRequestRecovery &&
                !activeRequestId &&
                !attachmentActionInProgress &&
                hasDraftMessage;
              const canSend =
                !!backend &&
                !selectedSnapshotId &&
                !sendInProgress &&
                !pendingRequestRecovery &&
                !activeRequestId &&
                !attachmentActionInProgress &&
                hasDraftMessage;

              return (
                <View style={styles.composerButtonsRow}>
                  <TouchableOpacity
                    style={[styles.button, styles.secondaryButton, styles.composerButton]}
                    onPress={openAppendAsModal}
                    disabled={!canAppend}
                  >
                    <Text
                      style={[
                        styles.buttonTextSecondary,
                        !canAppend && styles.buttonTextDisabled,
                      ]}
                    >
                      Append
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.button, styles.primaryButton, styles.composerButton]}
                    onPress={handleSend}
                    disabled={!canSend}
                  >
                    {sendInProgress || activeRequestId ? (
                      <ActivityIndicator size="small" color={theme.textOnPrimary} />
                    ) : (
                      <Text
                        style={[
                          styles.buttonText,
                          !canSend && styles.buttonTextDisabled,
                        ]}
                      >
                        Send
                      </Text>
                    )}
                  </TouchableOpacity>
                </View>
              );
            })()}

            <AttachmentThumbnailStrip
              attachments={attachmentsBelowStrip}
              onPressManageAll={() => {
                setAttachmentsManageSide('below');
                setAttachmentsManageVisible(true);
              }}
              disabled={
                sendInProgress ||
                !!pendingRequestRecovery ||
                !!activeRequestId ||
                attachmentActionInProgress
              }
            />
          </View>
      </View>

      <ComposerAttachmentsManageModal
        visible={attachmentsManageVisible}
        title={
          attachmentsManageSide === 'above'
            ? 'Attachments (above)'
            : attachmentsManageSide === 'below'
              ? 'Attachments (below)'
              : 'Attachments'
        }
        attachments={attachmentsManageRows}
        disabled={
          sendInProgress ||
          !!pendingRequestRecovery ||
          !!activeRequestId ||
          attachmentActionInProgress
        }
        onMove={(draftId, direction) => {
          if (!attachmentsManageSide) return;
          moveAttachmentWithinSide(attachmentsManageSide, draftId, direction);
        }}
        onEditMetadata={(draftId) => {
          if (!attachmentsManageSide) return;
          openAttachmentMetadataForEdit(attachmentsManageSide, draftId);
        }}
        onDelete={(draftId) => {
          if (!attachmentsManageSide) return;
          removeAttachmentFromSide(attachmentsManageSide, draftId);
        }}
        onRequestClose={() => {
          setAttachmentsManageVisible(false);
        }}
      />

      <AttachmentMetadataModal
        visible={attachmentMetadataVisible}
        title={attachmentMetadataTitle}
        metadataUi={attachmentMetadataUi}
        initialMetadata={attachmentMetadataInitial}
        onCancel={handleAttachmentMetadataCancel}
        onSave={handleAttachmentMetadataSave}
      />

      {imageAttachVisible && (
        <Modal
          visible={imageAttachVisible}
          transparent
          animationType="fade"
          onRequestClose={() => setImageAttachVisible(false)}
        >
          <TouchableWithoutFeedback onPress={() => setImageAttachVisible(false)}>
            <View style={styles.modalOverlay}>
              <TouchableWithoutFeedback onPress={() => {}}>
                <View style={styles.modalContent}>
                  <Text style={styles.modalTitle}>Add image</Text>
                  <Text style={styles.modalSubtitle}>
                    {Boolean((imageAttachElement as any)?.supports_upload ?? true) &&
                    Boolean((imageAttachElement as any)?.supports_url ?? true)
                      ? 'Choose a photo source or paste an image URL.'
                      : Boolean((imageAttachElement as any)?.supports_upload ?? true)
                        ? 'Choose a photo source.'
                        : 'Paste an image URL.'}
                  </Text>

                  {Boolean((imageAttachElement as any)?.supports_upload ?? true) && (
                    <View style={styles.imageSourceButtonsRow}>
                      <TouchableOpacity
                        style={[styles.button, styles.secondaryButton, styles.modalButton]}
                        onPress={() => pickImageForElement('library')}
                        disabled={
                          sendInProgress ||
                          !!pendingRequestRecovery ||
                          !!activeRequestId ||
                          attachmentPickInProgress ||
                          attachmentActionInProgress
                        }
                      >
                        <Text style={styles.buttonTextSecondary}>Photo library</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={[styles.button, styles.secondaryButton, styles.modalButton]}
                        onPress={() => pickImageForElement('camera')}
                        disabled={
                          sendInProgress ||
                          !!pendingRequestRecovery ||
                          !!activeRequestId ||
                          attachmentPickInProgress ||
                          attachmentActionInProgress
                        }
                      >
                        <Text style={styles.buttonTextSecondary}>Take photo</Text>
                      </TouchableOpacity>
                    </View>
                  )}

                  {Boolean((imageAttachElement as any)?.supports_url ?? true) && (
                    <>
                      <Text style={styles.rangeLabel}>Image URL</Text>
                      <TextInput
                        style={styles.modalInput}
                        value={imageUrlText}
                        onChangeText={setImageUrlText}
                        placeholder="https://... or data:image/..."
                        keyboardType="default"
                        autoCapitalize="none"
                        autoCorrect={false}
                      />
                    </>
                  )}

                  <View style={styles.modalButtonsRow}>
                    <TouchableOpacity
                      style={[styles.button, styles.secondaryButton, styles.modalButton]}
                      onPress={() => setImageAttachVisible(false)}
                    >
                      <Text style={styles.buttonTextSecondary}>Cancel</Text>
                    </TouchableOpacity>
                    {Boolean((imageAttachElement as any)?.supports_url ?? true) && (
                      <TouchableOpacity
                        style={[styles.button, styles.primaryButton, styles.modalButton]}
                        onPress={addImageUrlForElement}
                        disabled={!imageUrlText.trim() || attachmentActionInProgress}
                      >
                        <Text style={styles.buttonText}>Add URL</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                </View>
              </TouchableWithoutFeedback>
            </View>
          </TouchableWithoutFeedback>
        </Modal>
      )}

      {appendAsVisible && (
        <Modal
          visible={appendAsVisible}
          transparent
          animationType="fade"
          onRequestClose={() => setAppendAsVisible(false)}
        >
          <TouchableWithoutFeedback onPress={() => setAppendAsVisible(false)}>
            <View style={styles.modalOverlay}>
              <TouchableWithoutFeedback onPress={() => {}}>
                <View style={styles.modalContent}>
                  <Text style={styles.modalTitle}>Append as</Text>
                  <Text style={styles.modalSubtitle}>
                    Choose a role for the appended message.
                  </Text>

                  <View style={styles.chipsRow}>
                    {([
                      { key: 'system', label: 'System' },
                      { key: 'developer', label: 'Developer' },
                      { key: 'user', label: 'User' },
                      { key: 'assistant', label: 'Assistant' },
                    ] as Array<{ key: AppendAsRole; label: string }>).map((opt) => {
                      const selected = opt.key === appendAsRole;
                      return (
                        <TouchableOpacity
                          key={opt.key}
                          style={selected ? styles.chipSelected : styles.chip}
                          onPress={() => setAppendAsRole(opt.key)}
                        >
                          <Text style={selected ? styles.chipTextSelected : styles.chipText}>
                            {opt.label}
                          </Text>
                        </TouchableOpacity>
                      );
                    })}
                  </View>

                  <View style={styles.modalButtonsRow}>
                    <TouchableOpacity
                      style={[styles.button, styles.secondaryButton, styles.modalButton]}
                      onPress={() => setAppendAsVisible(false)}
                    >
                      <Text style={styles.buttonTextSecondary}>Cancel</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.button, styles.primaryButton, styles.modalButton]}
                      onPress={() => {
                        handleAppendAs().catch(() => {});
                      }}
                    >
                      {sendInProgress ? (
                        <ActivityIndicator size="small" color={theme.textOnPrimary} />
                      ) : (
                        <Text style={styles.buttonText}>Append</Text>
                      )}
                    </TouchableOpacity>
                  </View>
                </View>
              </TouchableWithoutFeedback>
            </View>
          </TouchableWithoutFeedback>
        </Modal>
      )}

	      {messageLimitVisible && (
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
	                Python-style range (start:end). Example: -50: for last 50 messages.
	              </Text>
	              <View style={styles.rangeRow}>
	                <View style={styles.rangeInputContainer}>
	                  <Text style={styles.rangeLabel}>Start</Text>
	                  <TextInput
	                    style={styles.modalInput}
	                    value={rangeStartText}
	                    onChangeText={setRangeStartText}
	                    placeholder="e.g. -50"
	                    keyboardType="default"
	                  />
	                </View>
	                <View style={styles.rangeInputContainer}>
	                  <Text style={styles.rangeLabel}>End</Text>
	                  <TextInput
	                    style={styles.modalInput}
	                    value={rangeEndText}
	                    onChangeText={setRangeEndText}
	                    placeholder="optional"
	                    keyboardType="default"
	                  />
	                </View>
	              </View>
	              <View style={styles.modalButtonsRow}>
	                <TouchableOpacity
	                  style={[styles.button, styles.secondaryButton, styles.modalButton]}
	                  onPress={() => setMessageLimitVisible(false)}
	                >
	                  <Text style={styles.buttonTextSecondary}>Cancel</Text>
	                </TouchableOpacity>
	                <TouchableOpacity
	                  style={[styles.button, styles.primaryButton, styles.modalButton]}
	                  onPress={applyMessageLimitAndReload}
	                >
	                  <Text style={styles.buttonText}>Apply</Text>
	                </TouchableOpacity>
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

	      {deleteRangeVisible && (
	        <Modal
	          visible={deleteRangeVisible}
	          transparent
	          animationType="fade"
	          onRequestClose={() => setDeleteRangeVisible(false)}
	        >
	          <View style={styles.modalOverlay}>
	            <View style={styles.modalContent}>
	              <Text style={styles.modalTitle}>Delete range</Text>
	              <Text style={styles.modalSubtitle}>
	                Python-style range (start:end). Messages in this range will be removed.
	              </Text>
	              <View style={styles.rangeRow}>
	                <View style={styles.rangeInputContainer}>
	                  <Text style={styles.rangeLabel}>Start</Text>
	                  <TextInput
	                    style={styles.modalInput}
	                    value={deleteRangeStartText}
	                    onChangeText={setDeleteRangeStartText}
	                    placeholder="e.g. 0 or -10"
	                    keyboardType="default"
	                  />
	                </View>
	                <View style={styles.rangeInputContainer}>
	                  <Text style={styles.rangeLabel}>End</Text>
	                  <TextInput
	                    style={styles.modalInput}
	                    value={deleteRangeEndText}
	                    onChangeText={setDeleteRangeEndText}
	                    placeholder="optional"
	                    keyboardType="default"
	                  />
	                </View>
	              </View>
	              <View style={styles.modalButtonsRow}>
	                <TouchableOpacity
	                  style={[styles.button, styles.secondaryButton, styles.modalButton]}
	                  onPress={() => setDeleteRangeVisible(false)}
	                >
	                  <Text style={styles.buttonTextSecondary}>Cancel</Text>
	                </TouchableOpacity>
	                <TouchableOpacity
	                  style={[styles.button, styles.primaryButton, styles.modalButton]}
	                  onPress={confirmDeleteRange}
	                >
	                  <Text style={styles.buttonText}>Delete</Text>
	                </TouchableOpacity>
	              </View>
	            </View>
	          </View>
	        </Modal>
	      )}
        <Modal
          visible={snapshotsVisible}
          transparent
          animationType="fade"
          onRequestClose={() => setSnapshotsVisible(false)}
        >
          <TouchableWithoutFeedback onPress={() => setSnapshotsVisible(false)}>
            <View style={styles.modalOverlay}>
              <TouchableWithoutFeedback onPress={() => {}}>
                <View style={styles.modalContent}>
                  <Text style={styles.modalTitle}>Snapshots</Text>
                  <Text style={styles.modalSubtitle}>
                    Browse readonly snapshots, restore one, or return to the live session.
                  </Text>
                  <View style={styles.modalButtonsRow}>
                    <TouchableOpacity
                      style={[styles.button, styles.secondaryButton, styles.modalButton]}
                      onPress={() => {
                        void handleCreateSnapshot();
                      }}
                      disabled={snapshotsLoading}
                    >
                      <Text style={styles.buttonTextSecondary}>Create</Text>
                    </TouchableOpacity>
                    {selectedSnapshotId ? (
                      <TouchableOpacity
                        style={[styles.button, styles.secondaryButton, styles.modalButton]}
                        onPress={() => {
                          void handleClearSelectedSnapshot();
                        }}
                      >
                        <Text style={styles.buttonTextSecondary}>Live session</Text>
                      </TouchableOpacity>
                    ) : null}
                  </View>
                  <ScrollView style={styles.settingsScroll}>
                    {snapshotsLoading ? (
                      <ActivityIndicator size="small" color={theme.textSecondary} />
                    ) : snapshotItems.length === 0 ? (
                      <Text style={styles.modalSubtitle}>No snapshots yet.</Text>
                    ) : (
                      snapshotItems.map((item) => {
                        const isSelected = selectedSnapshotId === item.snapshot_id;
                        return (
                          <View key={item.snapshot_id} style={styles.pluginRow}>
                            <View style={styles.pluginRowContent}>
                              <Text style={styles.pluginName}>{item.reason || 'snapshot'}</Text>
                              <Text style={styles.pluginMeta}>{item.created_at}</Text>
                              <Text style={styles.pluginMeta}>{item.snapshot_id}</Text>
                            </View>
                            <View style={styles.modalButtonsRow}>
                              <TouchableOpacity
                                style={[styles.button, styles.secondaryButton, styles.smallButton]}
                                onPress={() => {
                                  void handleSelectSnapshot(item.snapshot_id);
                                }}
                              >
                                <Text style={styles.buttonTextSecondary}>
                                  {isSelected ? 'Selected' : 'Select'}
                                </Text>
                              </TouchableOpacity>
                              <TouchableOpacity
                                style={[styles.button, styles.secondaryButton, styles.smallButton]}
                                onPress={() => {
                                  void handleRestoreSnapshot(item.snapshot_id);
                                }}
                              >
                                <Text style={styles.buttonTextSecondary}>Restore</Text>
                              </TouchableOpacity>
                              <TouchableOpacity
                                style={[styles.button, styles.secondaryButton, styles.smallButton]}
                                onPress={() => {
                                  void handleDeleteSnapshot(item.snapshot_id);
                                }}
                              >
                                <Text style={styles.buttonTextSecondary}>Delete</Text>
                              </TouchableOpacity>
                            </View>
                          </View>
                        );
                      })
                    )}
                  </ScrollView>
                </View>
              </TouchableWithoutFeedback>
            </View>
          </TouchableWithoutFeedback>
        </Modal>
	      <AgentSwitchModal
	        visible={agentModalVisible}
	        loading={agentsLoading || agentSwitchInProgress}
	        agents={availableAgents}
	        selectedAgentId={sessionAgentId}
	        onRequestClose={() => setAgentModalVisible(false)}
	        onSelectAgent={handleSwitchAgent}
	      />

	      <SessionSettingsModal
	        backend={backend}
	        cacheKey={connectionId ?? 'default'}
	        sessionId={sessionId}
	        visible={settingsVisible}
	        onRequestClose={() => setSettingsVisible(false)}
	      />
	      <OptionsPickerModal
	        visible={!!composerLeftSelectModalElement}
	        options={
	          composerLeftSelectModalElement
	            ? normalizeSelectOptions(composerLeftSelectModalElement.options)
	            : []
	        }
	        onSelect={(value) => {
	          if (composerLeftSelectModalElement?.key != null) {
	            handleComposerLeftSelectOption(
	              String(composerLeftSelectModalElement.key),
	              value,
	            );
	          }
	          setComposerLeftSelectModalElement(null);
	        }}
	        onRequestClose={() => setComposerLeftSelectModalElement(null)}
	      />
	      <SessionPluginsModal
	        backend={backend}
	        sessionId={sessionId}
	        visible={pluginsVisible}
	        onRequestClose={() => setPluginsVisible(false)}
	      />
	      <ApplicationActionDialog
	        visible={!!activePluginDialogElement}
	        dialog={(activePluginDialogElement as any)?.dialog || null}
	        titleFallback={activePluginDialogElement?.label}
	        prefillContext={{
	          session:
	            activePluginDialogContext && 'sessionSummary' in activePluginDialogContext
	              ? activePluginDialogContext.sessionSummary || undefined
	              : undefined,
	          message:
	            activePluginDialogContext && activePluginDialogContext.kind === 'message'
	              ? {
	                  index: (activePluginDialogContext as any).index,
	                  ...(activePluginDialogContext as any).message,
	                }
	              : undefined,
	        }}
	        onSubmit={handleSubmitPluginDialog}
	        onCancel={handleCancelPluginDialog}
	      />
        <ActionResultModal
          visible={!!actionResultDisplay}
          display={actionResultDisplay?.display ?? null}
          activeActionId={activeDisplayActionId}
          onRequestClose={() => setActionResultDisplay(null)}
          onFollowupAction={(action) => {
            if (!actionResultDisplay) return;
            handleDisplayFollowupAction(actionResultDisplay, action);
          }}
        />
	      {debugVisible && (
	        <View style={styles.debugOverlay}>
	          <DebugEventsView
              events={debugEvents}
              notes={debugTimeline}
              onClose={() => setDebugVisible(false)}
            />
	        </View>
	      )}
	    </View>
	    </KeyboardAvoidingView>
  );
};

const createStyles = (theme: Theme) =>
  StyleSheet.create({
    keyboardAvoiding: {
      flex: 1,
      backgroundColor: theme.background,
    },
    container: {
      flex: 1,
    },
    headerRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 8,
    },
    backButton: {
      paddingHorizontal: 8,
      paddingVertical: 4,
    },
    backButtonText: {
      color: theme.primary,
      fontSize: 14,
    },
    title: {
      flex: 1,
      textAlign: 'center',
      fontSize: 18,
      fontWeight: '600',
      color: theme.text,
    },
    headerButtons: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    sessionActionsModalContent: {
      width: '90%',
      maxHeight: '80%',
    },
    iconButton: {
      paddingHorizontal: 8,
      paddingVertical: 4,
      marginLeft: 4,
    },
    button: {
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderRadius: 8,
      marginLeft: 6,
    },
    primaryButton: {
      backgroundColor: theme.primary,
    },
    secondaryButton: {
      backgroundColor: theme.surfaceAlt,
    },
    smallButton: {
      paddingHorizontal: 8,
      paddingVertical: 4,
      marginLeft: 8,
    },
    buttonText: {
      color: theme.textOnPrimary,
      fontSize: 14,
      fontWeight: '600',
    },
    buttonTextSecondary: {
      color: theme.text,
      fontSize: 14,
      fontWeight: '600',
    },
    buttonTextDisabled: {
      color: theme.textSecondary,
    },
	    dirtyBanner: {
	      flexDirection: 'row',
	      alignItems: 'center',
	      marginHorizontal: 4,
	      marginBottom: 8,
	      paddingHorizontal: 10,
	      paddingVertical: 8,
	      borderRadius: 8,
	      borderWidth: 1,
	      borderColor: theme.primary,
	      backgroundColor: theme.primaryMuted,
	    },
	    dirtyBannerText: {
	      flex: 1,
	      fontSize: 14,
	      fontWeight: '600',
	      color: theme.text,
	      marginRight: 8,
	    },
    loadingContainer: {
      flexDirection: 'row',
      alignItems: 'center',
      marginBottom: 8,
    },
    loadingText: {
      marginLeft: 8,
      fontSize: 14,
      color: theme.textSecondary,
    },
    messagesContainer: {
      flex: 1,
      marginBottom: 8,
    },
    errorContainer: {
      marginHorizontal: 4,
      marginBottom: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: theme.danger,
      backgroundColor: theme.surface,
    },
    errorTitle: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.danger,
      marginBottom: 4,
    },
    errorText: {
      fontSize: 13,
      color: theme.text,
    },
    pendingRecoveryContainer: {
      marginHorizontal: 4,
      marginBottom: 8,
      paddingHorizontal: 10,
      paddingVertical: 10,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: theme.primary,
      backgroundColor: theme.primaryMuted,
    },
    pendingRecoveryTitle: {
      fontSize: 14,
      fontWeight: '600',
      color: theme.text,
      marginBottom: 4,
    },
    pendingRecoveryText: {
      fontSize: 13,
      color: theme.text,
      marginBottom: 4,
    },
    pendingRecoveryButtonsRow: {
      flexDirection: 'row',
      marginTop: 6,
      gap: 8,
    },
    pendingRecoveryButton: {
      flex: 1,
      alignItems: 'center',
    },
    composer: {
      borderTopWidth: 1,
      borderTopColor: theme.border,
      paddingTop: 8,
    },
    composerInlineSelectRow: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 6,
      marginRight: 8,
    },
    composerInlineSelectButton: {
      flexDirection: 'row',
      alignItems: 'center',
      paddingVertical: 3,
      paddingHorizontal: 5,
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 5,
      gap: 3,
      maxWidth: '100%',
    },
    composerInlineSelectLabel: {
      fontSize: 10,
      color: theme.textSecondary,
    },
    composerInlineSelectValue: {
      fontSize: 10,
      color: theme.text,
      maxWidth: 100,
    },
    composerMainColumn: {
      minWidth: 0,
    },
    composerTopRow: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingHorizontal: 10,
      marginBottom: 4,
    },
    composerInput: {
      minHeight: 60,
      maxHeight: 120,
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 8,
      fontSize: 14,
      marginBottom: 8,
      color: theme.text,
    },
    composerButtonsRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
    },
    composerButton: {
      flex: 1,
      minWidth: 0,
      alignItems: 'center',
      marginHorizontal: 4,
    },
    modalOverlay: {
      flex: 1,
      backgroundColor: theme.modalBackdrop,
      justifyContent: 'center',
      alignItems: 'center',
    },
    modalContent: {
      width: '80%',
      backgroundColor: theme.surface,
      borderRadius: 12,
      padding: 16,
    },
    modalTitle: {
      fontSize: 18,
      fontWeight: '600',
      marginBottom: 4,
      color: theme.text,
    },
    modalSubtitle: {
      fontSize: 12,
      color: theme.textSecondary,
      marginBottom: 12,
    },
    modalInput: {
      backgroundColor: theme.surface,
      borderWidth: 1,
      borderColor: theme.border,
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 6,
      fontSize: 14,
      marginBottom: 12,
      color: theme.text,
    },
    modalButtonsRow: {
      flexDirection: 'row',
      justifyContent: 'flex-end',
      marginBottom: 4,
    },
    imageSourceButtonsRow: {
      flexDirection: 'row',
      gap: 8,
      marginBottom: 12,
    },
    modalButton: {
      minWidth: 90,
      alignItems: 'center',
    },
    modalHelperText: {
      fontSize: 12,
      color: theme.textSecondary,
      textAlign: 'right',
    },
    chipsRow: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      marginBottom: 12,
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
    rangeRow: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: 12,
      marginTop: 8,
    },
    rangeInputContainer: {
      flex: 1,
      marginRight: 8,
    },
    rangeLabel: {
      fontSize: 12,
      color: theme.textSecondary,
      marginBottom: 4,
    },
    agentList: {
      maxHeight: 220,
      marginTop: 8,
      marginBottom: 8,
    },
    agentItem: {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
      paddingVertical: 8,
      paddingHorizontal: 10,
      borderRadius: 8,
      borderWidth: 1,
      borderColor: theme.border,
      marginBottom: 6,
    },
    agentItemSelected: {
      borderColor: theme.primary,
      backgroundColor: theme.primaryMuted,
    },
    agentItemText: {
      fontSize: 14,
      color: theme.text,
    },
    debugOverlay: {
      position: 'absolute',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: theme.modalBackdrop,
    },
    statusBarContainer: {
      marginTop: 8,
      paddingHorizontal: 10,
      paddingVertical: 6,
      borderTopWidth: 1,
      borderTopColor: theme.divider,
      backgroundColor: theme.surfaceAlt,
    },
    statusBarText: {
      fontSize: 11,
      color: theme.textSecondary,
      fontFamily: 'Courier',
    },
  });

export default SessionChatScreen;
