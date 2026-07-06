import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Clipboard,
  Linking,
  Modal,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
  findNodeHandle,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

import {
  ActionsMenuBar,
  ApplicationActionDialog,
  getLastActionsPopoverAnchorTag,
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
} from '@crystal-lattice/frontend-sdk';
import {
  attachmentDraftStatusLabel,
  resolveAttachmentActionPluginId,
  deleteSessionAttachment,
  deriveSessionListPresentationFromGroups,
  filterFooterElements,
  groupSessionListFields,
  isAttachmentDraftBlocking,
  mergeSessionScopedActionElements,
  normalizeActionDisplayForSurface,
  runApplicationAction,
  selectSessionAssetId,
  selectDisplayContent,
  storeSessionAttachment,
  type ComposerAttachmentUiElement as SharedComposerAttachmentUiElement,
  type AttachmentDraftStatus,
} from '@crystal-lattice/frontend-sdk';
import {
  useApplicationPlugins,
  useChatController,
  useHydrateControllerFromCache,
  usePersistentPinnedActions,
  usePluginActionDialog,
  useSessionSettingsController,
  useSessionUiSchemaController,
  useSessionApplicationUiSchemaController,
} from '@crystal-lattice/frontend-sdk-react';
import { MacTextView, type MacTextViewHandle } from '@crystal-lattice/react-native-mac-text-view';

import type { MessagesCacheEntry } from '../cache/types';
import type { TabStripStyle } from '../tabs/tabStripStyle';
import { asyncStorageKeyValueStore } from '../storage/asyncStorageKeyValueStore';
import { desktopEventBus } from '../events/desktopEventBus';
import { truncateByChars } from '../utils/text';
import { DependencyFlatList } from '../ui/DependencyFlatList';
import { DependencyVirtualizedScroll } from '../ui/DependencyVirtualizedScroll';
import { PlaceholderFlatList } from '../ui/PlaceholderFlatList';
import { ActionResultModal } from '../ui/ActionResultModal';
import { ActionResultInlineCard } from '../ui/ActionResultInlineCard';
import { DesktopWindowManager } from '../windows/desktopWindowManager';
import { closeDesktopPopover, openDesktopPopover } from '../windows/desktopPopoverCoordinator';
import { MessageLimitPopoverContent } from '../windows/MessageLimitPopoverContent';
import { setActiveSessionSettingsWindow } from '../windows/sessionSettingsCoordinator';
import { setActiveSessionPluginsWindow } from '../windows/sessionPluginsCoordinator';
import { useMacOSApplicationActionDialog } from '../windows/useMacOSApplicationActionDialog';
import { pickMacAttachment } from '../native/MacAttachmentPicker';
import { AppendAsPopoverContent, type AppendAsRole } from './AppendAsPopoverContent';
import {
  buildAttachmentMetadataDefaults,
  hasEditableAttachmentMetadataFields,
  shouldPromptForAttachmentMetadata,
  type AttachmentMetadataUi,
} from './AttachmentMetadataPopoverContent';
import { AttachmentThumbnailStrip, type AttachmentLike } from './AttachmentThumbnailStrip';
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
import { PinnedMessageActionsProvider } from './PinnedMessageActionsContext';
import { useSessionStatusBarParts } from './useSessionStatusBarParts';
import { usePersistedChatDraft } from './usePersistedChatDraft';
import { useProactiveChatScrollPersistence } from './useProactiveChatScrollPersistence';
import { openAttachmentMetadataWindow } from '../windows/attachmentMetadataCoordinator';

const DEFAULT_HISTORY_WINDOW = 50;
const PINNED_SESSION_ACTIONS_STORAGE_KEY_BASE = 'clc_pinned_chat_session_actions_v1';
const PINNED_COMPOSER_ACTIONS_STORAGE_KEY_BASE = 'clc_pinned_chat_composer_actions_v1';
const PINNED_MESSAGE_ACTIONS_STORAGE_KEY_BASE = 'clc_pinned_message_actions_by_role_v1';

const TRANSCRIPT_LIST_IMPLEMENTATION = ((globalThis as any).CLC_TRANSCRIPT_LIST_IMPLEMENTATION ??
  'flatList') as 'scrollView' | 'flatList' | 'virtualizedScroll';

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

const FLATLIST_DISABLE_VIRTUALIZATION = readGlobalBoolean(
  'CLC_FLATLIST_DISABLE_VIRTUALIZATION',
  false,
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
const FLATLIST_WINDOW_SIZE = readOptionalGlobalNumber('CLC_FLATLIST_WINDOW_SIZE');
const FLATLIST_REMOVE_CLIPPED_SUBVIEWS = readOptionalGlobalBoolean(
  'CLC_FLATLIST_REMOVE_CLIPPED_SUBVIEWS',
);
const FLATLIST_MAINTAIN_VISIBLE_CONTENT_POSITION = readGlobalBoolean(
  'CLC_FLATLIST_MAINTAIN_VISIBLE_CONTENT_POSITION',
  false,
);
const FLATLIST_FORWARD_SCROLL_END_DRAG = readGlobalBoolean(
  'CLC_FLATLIST_FORWARD_SCROLL_END_DRAG',
  true,
);
const FLATLIST_FORWARD_MOMENTUM_SCROLL_END = readGlobalBoolean(
  'CLC_FLATLIST_FORWARD_MOMENTUM_SCROLL_END',
  true,
);
const FLATLIST_STICK_TO_BOTTOM = readGlobalBoolean('CLC_FLATLIST_STICK_TO_BOTTOM', false);
const FLATLIST_STICK_TO_BOTTOM_THRESHOLD_PX =
  readOptionalGlobalNumber('CLC_FLATLIST_STICK_TO_BOTTOM_THRESHOLD_PX') ?? 80;

const DEFAULT_PINNED_MESSAGE_ACTIONS_BY_ROLE: Record<string, MessageActionKey[]> = {
  user: ['modify', 'copy'],
  assistant: ['modify', 'toggleMarkdown', 'copy'],
  system: ['modify', 'copy'],
  tool: ['copy'],
};

type ChatSessionActionKey = 'reload' | 'agentSwitch' | 'messageLimit' | 'settings' | 'plugins';

type ChatComposerActionKey = 'append' | 'appendAs' | 'resend' | 'cancel';

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
  | { kind: 'message'; index: number; message: ApiMessage; sessionSummary: SessionSummary | null };

type ActionDisplayEntry = {
  key: string;
  display: ActionDisplayPayload;
  context: RunActionContext;
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

const BUILTIN_SESSION_ACTIONS: ActionDefinition[] = [
  { key: 'reload', label: 'Reload', iconName: 'refresh-ccw' },
  { key: 'agentSwitch', label: 'Switch agent', iconName: 'user' },
  { key: 'messageLimit', label: 'Message limit', iconName: 'sliders' },
  { key: 'settings', label: 'Settings…', iconName: 'settings' },
  { key: 'plugins', label: 'Plugins…', iconName: 'package' },
];

const BUILTIN_COMPOSER_ACTIONS: ActionDefinition[] = [
  { key: 'append', label: 'Append', iconName: 'plus-circle' },
  { key: 'appendAs', label: 'Append as…', iconName: 'layers' },
  { key: 'resend', label: 'Resend', iconName: 'repeat' },
  { key: 'cancel', label: 'Cancel', iconName: 'x-circle' },
];

const DEFAULT_PINNED_SESSION_ACTION_KEYS: ActionKey[] = ['reload'];
const DEFAULT_PINNED_COMPOSER_ACTION_KEYS: ActionKey[] = ['append', 'resend', 'cancel'];

export interface ChatPaneProps {
	isActive: boolean;
  connectionId: string;
  connectionName: string;
  sessionId: string;
  sessionSummary?: SessionSummary | null;
  title: string;
  subtitle?: string;
  backend: AgentBackend | null;
  cachedEntry: MessagesCacheEntry | null;
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
  styleVariant?: TabStripStyle;
}

export const ChatPane = React.memo(function ChatPane({
	isActive,
	connectionId,
	connectionName,
	sessionId,
	sessionSummary,
	title,
	subtitle,
	backend,
	cachedEntry,
	onOpenSessionTab,
	onUpdateCache,
	styleVariant = 'toolbarTabs',
}: ChatPaneProps): React.JSX.Element {
  const theme = useTheme();
  const styles = useMemo(() => createStyles(theme, styleVariant), [theme, styleVariant]);

  const [messageViewModeByIndex, setMessageViewModeByIndex] = useState<
    Record<number, 'markdown' | 'raw'>
  >({});
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [editingText, setEditingText] = useState('');
  const [editingInitialText, setEditingInitialText] = useState('');
  const [pinnedMessageActionsByRole, setPinnedMessageActionsByRole] = useState<
    Record<string, MessageActionKey[]>
  >({});

  const [loadError, setLoadError] = useState<string | null>(null);
  const [rangeStartText, setRangeStartText] = useState(
    cachedEntry?.rangeStartText ?? `-${DEFAULT_HISTORY_WINDOW}`,
  );
  const [rangeEndText, setRangeEndText] = useState(cachedEntry?.rangeEndText ?? '');
	const didHydrateRangeFromCacheRef = useRef(false);
  const [lastReloadAt, setLastReloadAt] = useState<Date | null>(null);
  const [messageLimitVisible, setMessageLimitVisible] = useState(false);
  const [sendInFlight, setSendInFlight] = useState(false);
  const [reloadInFlight, setReloadInFlight] = useState(false);
  const [cancelInFlight, setCancelInFlight] = useState(false);
  const [pluginActionRunning, setPluginActionRunning] = useState(false);
  const [actionResultDisplay, setActionResultDisplay] = useState<ActionDisplayEntry | null>(null);
  const [inlineActionDisplays, setInlineActionDisplays] = useState<ActionDisplayEntry[]>([]);
  const [activeDisplayActionId, setActiveDisplayActionId] = useState<string | null>(null);
  const [attachmentBackgroundOperation, setAttachmentBackgroundOperation] =
    useState<AttachmentBackgroundOperation>(null);
  const [openingAgentPicker, setOpeningAgentPicker] = useState(false);
  const composerRef = useRef<MacTextViewHandle | null>(null);
  const attachmentPlusButtonRef = useRef<any>(null);
  const attemptedInitialLoadRef = useRef(false);
  const pendingPersistTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastPersistKeyRef = useRef<string | null>(null);

  const [composerHeight, setComposerHeight] = useState(34);
  const handleComposerHeightChange = useCallback((height: number) => {
    const next = Math.round(height);
    setComposerHeight((prev) => {
      if (Math.abs(prev - next) < 1) {
        return prev;
	}
      return next;
    });
  }, []);

  // Debug logging removed; composer uses native MacTextView on macOS.

  const { controller: chatController, state: chatState } = useChatController({
    backend,
    sessionId,
    initialMessages: cachedEntry?.messages ?? [],
    initialEventsCursorId: cachedEntry?.cursorEventId ?? null,
    initialActiveRequestId: cachedEntry?.activeRequestId ?? null,
	  eventsEnabled: isActive && backend != null,
  });

  const pinnedSessionActionsStorageKey = useMemo(() => {
    return `${PINNED_SESSION_ACTIONS_STORAGE_KEY_BASE}:${connectionId}`;
  }, [connectionId]);

  const { pinned: pinnedSessionActionKeys, setPinned: setPinnedSessionActionKeys } =
    usePersistentPinnedActions<ActionKey>({
      store: asyncStorageKeyValueStore,
      key: pinnedSessionActionsStorageKey,
      initialPinned: DEFAULT_PINNED_SESSION_ACTION_KEYS,
    });

  const pinnedComposerActionsStorageKey = useMemo(() => {
    return `${PINNED_COMPOSER_ACTIONS_STORAGE_KEY_BASE}:${connectionId}`;
  }, [connectionId]);

  const { pinned: pinnedComposerActionKeys, setPinned: setPinnedComposerActionKeys } =
    usePersistentPinnedActions<ActionKey>({
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
      console.log('Loading pinned message actions from storage with key', pinnedMessageActionsStorageKey);
      try {
        const messageRaw = await asyncStorageKeyValueStore.get(pinnedMessageActionsStorageKey);
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
      console.log('Saving pinned message actions to storage with key', pinnedMessageActionsStorageKey, pinnedMessageActionsByRole);
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
  const { state: sessionAppUiSchemaState } = useSessionApplicationUiSchemaController({
    backend,
    cacheKey: connectionId,
    sessionId,
    enabled: !!(backend && isActive),
  });
  useSessionSettingsController({
    backend,
    cacheKey: connectionId,
    sessionId,
	  enabled: !!(backend && isActive),
  });

  const {
    actionsById,
    sessionListFields,
  } = useApplicationPlugins();

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
      return truncateByChars(presentation.title || sessionSummary.preview || sessionId, 80);
    }

    const titleSource = typeof title === 'string' && title.trim() ? title : sessionId;
    return truncateByChars(titleSource, 80);
  }, [sessionId, sessionListFieldGroups, sessionSummary, title]);

  const displaySubtitle = useMemo(() => {
    if (sessionSummary) {
      const presentation = deriveSessionListPresentationFromGroups(
        sessionSummary,
        sessionListFieldGroups,
      );
      const subtitleSource = presentation.subtitle ?? sessionSummary.preview ?? '';
      return truncateByChars(subtitleSource, 80);
    }

    const subtitleSource = typeof subtitle === 'string' && subtitle.trim() ? subtitle : '';
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
      }),
    [sessionAppUiElements, uiSchemaElements],
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
    composerAttachmentElements.forEach((el) => {
      const attachmentType = String((el as any).attachment_type ?? '');
      if (!attachmentType) {
        return;
      }
      const key =
        typeof (el as any).key === 'string' && (el as any).key
          ? String((el as any).key)
          : `${String((el as any).plugin ?? 'unknown')}:attachment:${attachmentType}`;
      map[key] = el;
    });
    return map;
  }, [composerAttachmentElements]);

  const composerAttachmentPlusRows = useMemo((): ComposerAttachmentPlusRow[] => {
    const rows: ComposerAttachmentPlusRow[] = [];
    composerAttachmentElements.forEach((el) => {
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
          : `${String((el as any).plugin ?? 'unknown')}:attachment:${attachmentType}`;

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

  const [attachmentsAbove, setAttachmentsAbove] = useState<ComposerAttachmentDraft[]>([]);
  const [attachmentsBelow, setAttachmentsBelow] = useState<ComposerAttachmentDraft[]>([]);
  const [attachmentsAboveExpanded, setAttachmentsAboveExpanded] = useState(false);
  const [attachmentsBelowExpanded, setAttachmentsBelowExpanded] = useState(false);

  const hasAttachments = attachmentsAbove.length + attachmentsBelow.length > 0;

  const pluginSessionActionDefs: ActionDefinition[] = useMemo(() => {
    if (!backend) {
      return [];
    }

    return (visibleSessionActions || [])
      .map((el) => ({
        key: el.id,
        label: el.label,
        iconName: (el as any).icon || 'zap',
      }))
      .filter((def) => typeof def.key === 'string' && def.key);
  }, [backend, visibleSessionActions]);

  const pluginMessageActionDefs: MessageActionDefinition[] = useMemo(() => {
    if (!backend) {
      return [];
    }

    return (visibleMessageActions || [])
      .map((el) => ({
        key: el.id,
        label: el.label,
        iconName: (el as any).icon || 'zap',
        defaultPinnedRoles: ['user', 'assistant', 'system', 'tool'],
        allowedRoles: ['user', 'assistant', 'system', 'tool'],
      }))
      .filter((def) => typeof def.key === 'string' && def.key);
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
      const hasInitialSnapshot = snapshot.eventsCursorId != null || snapshot.messages.length > 0;
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
	}, [cachedEntry?.rangeEndText, cachedEntry?.rangeStartText, rangeEndText, rangeStartText]);

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
      (chatState?.eventsCursorId != null) ||
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
	}, [chatController, chatState?.eventsCursorId, chatState?.loading, chatState?.messages, isActive, loadInitialMessages]);

  const messages: IndexedMessage[] = useMemo(() => {
    return chatState?.messages ?? cachedEntry?.messages ?? [];
  }, [chatState?.messages, cachedEntry?.messages]);

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
    composerRef,
  });

  const transcriptScroll = useProactiveChatScrollPersistence({
    connectionId,
    sessionId,
    cachedScrollAnchor: cachedEntry?.scrollAnchor,
    getMessagesForCache,
    onUpdateCache,
    enabled: isActive,
    stickToBottomEnabled: FLATLIST_STICK_TO_BOTTOM,
    stickToBottomThresholdPx: FLATLIST_STICK_TO_BOTTOM_THRESHOLD_PX,
  });

  const requestPersistTranscriptScroll = transcriptScroll.requestPersist;
  const resetTranscriptRestore = transcriptScroll.resetRestore;

  const prevIsActiveRef = useRef(isActive);
  useEffect(() => {
    const prev = prevIsActiveRef.current;
    prevIsActiveRef.current = isActive;
    if (prev && !isActive) {
      requestPersistTranscriptScroll('tabDeactivated');
    }
    if (!prev && isActive) {
      resetTranscriptRestore('becameActive');
    }
  }, [isActive, requestPersistTranscriptScroll, resetTranscriptRestore]);


  const streamingRow = chatState?.streamingRow ?? null;

  const { statusBarParts, ensureAgentsLoaded, agentsLoading } = useSessionStatusBarParts({
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
    draftAttachments.find((draft) => isAttachmentDraftBlocking(draft.status)) ?? null;
  const unresolvedAttachmentDraft =
    draftAttachments.find((draft) => draft.status !== 'ready' && draft.status !== 'local') ?? null;
  const attachmentActionInProgress =
    attachmentBackgroundOperation != null || blockingAttachmentDraft != null;
  const attachmentActionText =
    attachmentBackgroundOperation?.kind === 'upload'
      ? `Uploading ${attachmentBackgroundOperation.filename}...`
      : attachmentBackgroundOperation?.kind === 'delete'
        ? `Deleting ${attachmentBackgroundOperation.filename}...`
        : blockingAttachmentDraft
          ? `${attachmentDraftStatusLabel(blockingAttachmentDraft.status, blockingAttachmentDraft.errorMessage)} ${blockingAttachmentDraft.content?.filename ?? blockingAttachmentDraft.type}...`
          : '';

	const canSend =
    backend != null &&
    chatController != null &&
    isActive &&
    !sendInFlight &&
    !chatState?.activeRequestId &&
    !attachmentActionInProgress &&
    !unresolvedAttachmentDraft;

  const canSendNow = canSend && (composeText.trim().length > 0 || hasAttachments);

  const buildMultipartContentPayload = useCallback(() => {
    const mapDraft = (d: ComposerAttachmentDraft) => ({
      type: d.type,
      content: d.content,
      metadata: d.metadata,
    });
    return [...attachmentsAbove.map(mapDraft), ...attachmentsBelow.map(mapDraft)];
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

  const updateDraftMetadata = useCallback(
    (draftId: string, placement: 'above' | 'below', nextMetadata: Record<string, any>) => {
      const updater = (prev: ComposerAttachmentDraft[]) =>
        prev.map((d) => (d.draftId === draftId ? { ...d, metadata: nextMetadata } : d));
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
        prev.map((draft) => (draft.draftId === draftId ? updater(draft) : draft));
      if (placement === 'above') {
        setAttachmentsAbove(update);
      } else {
        setAttachmentsBelow(update);
      }
    },
    [],
  );

  const openAttachmentMetadataEditorWindowForDraft = useCallback(
    (params: { draft: ComposerAttachmentDraft; element: ComposerAttachmentUiElement }) => {
      const metadataUi = ((params.element as any).metadata_ui ?? null) as AttachmentMetadataUi | null;
      if (!metadataUi) {
        Alert.alert('No metadata', 'This attachment type does not define metadata fields.');
        return;
      }
      if (!hasEditableAttachmentMetadataFields(metadataUi)) {
        Alert.alert('No metadata', 'No metadata fields are defined for this attachment type.');
        return;
      }

      const attachmentType = String((params.element as any).attachment_type ?? params.draft.type);
      const title =
        typeof (params.element as any).label === 'string' && (params.element as any).label
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
        onSave: (metadata) => {
          updateDraftMetadata(params.draft.draftId, params.draft.placement, metadata);
        },
      });
    },
    [connectionId, sessionId, updateDraftMetadata],
  );

  const findElementForDraft = useCallback(
    (draft: ComposerAttachmentDraft): ComposerAttachmentUiElement | null => {
      if (draft.schemaKey && composerAttachmentElementByActionKey[draft.schemaKey]) {
        return composerAttachmentElementByActionKey[draft.schemaKey];
      }

      const byType = composerAttachmentElements.find(
        (el) => String((el as any).attachment_type ?? '') === draft.type,
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
      const attachmentType = String((params.element as any).attachment_type ?? '');
      if (!attachmentType) {
        return null;
      }

      const actionKey =
        typeof (params.element as any).key === 'string' && (params.element as any).key
          ? String((params.element as any).key)
          : `${String((params.element as any).plugin ?? 'unknown')}:attachment:${attachmentType}`;

      const draft: ComposerAttachmentDraft = {
        draftId: params.draftId ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`,
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
      const metadataUi = ((params.element as any).metadata_ui ?? null) as AttachmentMetadataUi | null;
      const defaults = buildAttachmentMetadataDefaults(metadataUi);

      if (
        shouldPromptForAttachmentMetadata({ metadataUi }) &&
        hasEditableAttachmentMetadataFields(metadataUi)
      ) {
        if (params.draftId) {
          updateDraftState(params.draftId, params.placement, (draft) => ({
            ...draft,
            status: 'stored',
            errorMessage: null,
          }));
        }
        const attachmentType = String((params.element as any).attachment_type ?? '');
        const title =
          typeof (params.element as any).label === 'string' && (params.element as any).label
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
                updateDraftState(params.draftId, params.placement, (draft) => ({
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
                .then((deleted) => {
                  if (deleted && params.draftId) {
                    const remove = (prev: ComposerAttachmentDraft[]) =>
                      prev.filter((draft) => draft.draftId !== params.draftId);
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
          onSave: (metadata) => {
            if (params.draftId) {
              updateDraftState(params.draftId, params.placement, (draft) => ({
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
        updateDraftState(params.draftId, params.placement, (draft) => ({
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
        const stored = await storeSessionAttachment({
          backend,
          sessionId,
          attachmentType: String((params.element as any).attachment_type ?? ''),
          filename: params.filename,
          mimeType: params.mimeType,
          dataBase64: params.dataBase64,
          pluginId: resolveAttachmentActionPluginId(params.element) ?? undefined,
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
        updateDraftState(draftId, params.placement, (draft) => ({
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
    [addDraftAttachment, backend, beginAddDraftAttachment, sessionId, updateDraftState],
  );

  const handleSend = useCallback(async (overrideText?: string) => {
    if (!canSendNow) {
      if (unresolvedAttachmentDraft) {
        Alert.alert('Attachment not ready', 'Resolve attachment upload issues before sending.');
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

    setSendInFlight(true);
    try {
      await chatController.appendMessage({
        role: 'user',
        content,
        multipartContent,
      });
      setComposeText('');
      composerRef.current?.setText('');
      clearComposerAttachments();
      chatController.clearRequestState();
      await chatController.send();
      composerRef.current?.focus();
    } catch (err: any) {
      const message =
        typeof err?.message === 'string' && err.message
          ? err.message
          : 'Failed to send message.';
      Alert.alert('Failed to send', message);
    } finally {
      setSendInFlight(false);
    }
  }, [
    buildMultipartContentPayload,
    canSendNow,
    chatController,
    clearComposerAttachments,
    composeText,
    composeTextRef,
    setComposeText,
    unresolvedAttachmentDraft,
  ]);

  const canRunComposerActions = backend != null && chatController != null && isActive;

  const canOpenAttachmentPlus =
    canRunComposerActions &&
    composerAttachmentPlusRows.length > 0 &&
    !sendInFlight &&
    !chatState?.activeRequestId &&
    !attachmentActionInProgress;

  const appendMessageForRole = useCallback(
    async (role: AppendAsRole) => {
      const raw = composeTextRef.current || composeText;
      const content = String(raw ?? '').trim();
      const multipartContent = buildMultipartContentPayload();
      if (!content && multipartContent.length === 0) {
        return;
      }
      if (unresolvedAttachmentDraft) {
        Alert.alert('Attachment not ready', 'Resolve attachment upload issues before appending.');
        return;
      }
      if (!canRunComposerActions) {
        Alert.alert('Offline', 'Connect to a server to append messages.');
        return;
      }
      if (sendInFlight || chatState?.activeRequestId || attachmentActionInProgress) {
        return;
      }

      setSendInFlight(true);
      try {
        await chatController.appendMessage({ role: role as any, content: content.length > 0 ? content : '', multipartContent });
        composerRef.current?.focus();
      } catch (err: any) {
        const message = err?.message || 'Failed to append message.';
        Alert.alert('Failed to append', message);
      } finally {
        setSendInFlight(false);
      }
    },
    [
      attachmentActionInProgress,
      buildMultipartContentPayload,
      canRunComposerActions,
      chatController,
      chatState?.activeRequestId,
      composeText,
      composeTextRef,
      sendInFlight,
      unresolvedAttachmentDraft,
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
      Alert.alert('Attachment not ready', 'Resolve attachment upload issues before appending.');
      return;
    }
    if (!canRunComposerActions) {
      Alert.alert('Offline', 'Connect to a server to append messages.');
      return;
    }
    if (sendInFlight || chatState?.activeRequestId || attachmentActionInProgress || unresolvedAttachmentDraft) {
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
          onSelectRole={(role) => {
            appendMessageForRole(role).catch(() => {});
          }}
        />
      ),
    });
  }, [
    appendMessageForRole,
    attachmentActionInProgress,
    buildMultipartContentPayload,
    canRunComposerActions,
    chatState?.activeRequestId,
    composeText,
    composeTextRef,
    connectionId,
    sendInFlight,
    sessionId,
    unresolvedAttachmentDraft,
  ]);

  const handleResend = useCallback(async () => {
    if (!canRunComposerActions) {
      Alert.alert('Offline', 'Connect to a server to resend.');
      return;
    }
    if (sendInFlight || chatState?.activeRequestId) {
      return;
    }

    setSendInFlight(true);
    try {
      chatController.clearRequestState();
      await chatController.send();
      composerRef.current?.focus();
    } catch (err: any) {
      const message = err?.message || 'Failed to resend request.';
      Alert.alert('Failed to resend', message);
    } finally {
      setSendInFlight(false);
    }
  }, [canRunComposerActions, chatController, chatState?.activeRequestId, sendInFlight]);

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
  }, [canRunComposerActions, cancelInFlight, chatController, chatState?.activeRequestId]);

  const openAttachmentUrlPopover = useCallback(
    (params: { element: ComposerAttachmentUiElement; anchorTag?: number }) => {
      const attachmentType = String((params.element as any).attachment_type ?? '');
      const attachmentTitle =
        typeof (params.element as any).label === 'string' && (params.element as any).label
          ? String((params.element as any).label)
          : attachmentType;

      const popoverId = `attachment-url:${connectionId}:${sessionId}:${attachmentType}`;
      openDesktopPopover({
        id: popoverId,
        title: 'Attach URL',
        anchorTag: params.anchorTag ?? getLastActionsPopoverAnchorTag() ?? undefined,
        width: 520,
        height: 200,
        content: (
          <AttachmentUrlPopoverContent
            title={attachmentTitle}
            onCancel={() => closeDesktopPopover(popoverId)}
            onAttach={(url) => {
              beginAddDraftAttachment({
                element: params.element,
                placement:
                  (params.element as any).display_placement === 'above' ? 'above' : 'below',
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
      const supported = Array.isArray((params.element as any).supported_file_types)
        ? ((params.element as any).supported_file_types as any[]).filter((v) => typeof v === 'string')
        : [];
      const allowedExtensions = supported.map((v) => String(v));

      const picked = await pickMacAttachment({
        allowedExtensions,
        maxBytes: 15 * 1024 * 1024,
      });

      if (!picked) {
        return;
      }

      await storePickedAttachment({
        element: params.element,
        placement: (params.element as any).display_placement === 'above' ? 'above' : 'below',
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
          onSelectRow={(rowId) => {
            closeDesktopPopover(popoverId);

            const method = rowId.endsWith(':url') ? 'url' : rowId.endsWith(':file') ? 'file' : null;
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
  }, [composerAttachmentElementByActionKey, composerAttachmentPlusRows, connectionId, getAttachmentPlusAnchorTag, openAttachmentUrlPopover, pickAttachmentFile, sessionId]);

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
    },
    [handleAppend, handleCancel, handleResend, openAppendAsPopover],
  );

  const buildAttachmentStripRows = useCallback(
    (drafts: ComposerAttachmentDraft[]): AttachmentLike[] => {
      return drafts.map((d) => ({
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
      return drafts.map((d) => ({
        draftId: d.draftId,
        type: d.type,
        content: d.content,
        title: typeof d.metadata?.title === 'string' ? d.metadata?.title : undefined,
        status: d.status,
        errorMessage: d.errorMessage,
      }));
    },
    [],
  );

  const handleMoveDraft = useCallback(
    (placement: 'above' | 'below', draftId: string, direction: 'up' | 'down') => {
      const update = (prev: ComposerAttachmentDraft[]) => {
        const idx = prev.findIndex((d) => d.draftId === draftId);
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
      const draft = list.find((d) => d.draftId === draftId);
      if (!draft) {
        return;
      }
      const update = (prev: ComposerAttachmentDraft[]) => {
        const next = prev.filter((d) => d.draftId !== draftId);
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
      updateDraftState(draftId, placement, (current) => ({
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

      updateDraftState(draftId, placement, (current) => ({
        ...current,
        status: previousStatus,
      }));
    },
    [attachmentsAbove, attachmentsBelow, deleteStoredAttachmentAsset, updateDraftState],
  );

  const handleEditDraftMetadata = useCallback(
    (placement: 'above' | 'below', draftId: string, _anchorTag?: number) => {
      const list = placement === 'above' ? attachmentsAbove : attachmentsBelow;
      const draft = list.find((d) => d.draftId === draftId);
      if (!draft) return;
      const element = findElementForDraft(draft);
      if (!element) {
        Alert.alert('Not supported', 'Attachment metadata schema was not found.');
        return;
      }
      openAttachmentMetadataEditorWindowForDraft({ draft, element });
    },
    [attachmentsAbove, attachmentsBelow, findElementForDraft, openAttachmentMetadataEditorWindowForDraft],
  );

	const canRunHeaderActions = backend != null && chatController != null && isActive;

  const handleReload = useCallback(async () => {
    if (!canRunHeaderActions) {
      return;
    }
    if (reloadInFlight) {
      return;
    }

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
    } catch (err: any) {
      const message =
        typeof err?.message === 'string' && err.message
          ? err.message
          : 'Failed to reload messages.';
      setLoadError(message);
      Alert.alert('Failed to reload', message);
    } finally {
      setReloadInFlight(false);
    }
  }, [canRunHeaderActions, chatController, rangeEndText, rangeStartText, reloadInFlight]);

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
        Alert.alert('Offline', 'Connect to a server to run actions.');
        return;
      }

      setPluginActionRunning(true);
      try {
        const { ok, effects, display, errorMessage } = await runApplicationAction({
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
          Alert.alert('Action error', errorMessage || 'Failed to execute action');
          return;
        }

        if (effects.some((effect) => effect.type === 'reloadSessionsList')) {
          desktopEventBus.publish('sessionsReloadRequested', {
            connectionId,
            reason: `action:${element.id}`,
          });
        }

        if (effects.some((effect) => effect.type === 'reloadSession')) {
          await handleReload();
        }

        const navigateEffect = effects.find((effect) => effect.type === 'navigateToSession');
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
      } finally {
        setPluginActionRunning(false);
      }
    },
    [
      actionsById,
      backend,
      connectionId,
      handleReload,
      onOpenSessionTab,
      presentActionDisplay,
      sessionId,
    ],
  );

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
              param_map: action.param_map,
              form: entry.display.form,
            },
            {
              ...entry.context,
              formValues,
            },
          );
        } finally {
          setActiveDisplayActionId(null);
        }
      }
    },
    [executePluginAction],
  );

  const applyMessageLimitAndReload = useCallback(
    async (params: { startText: string; endText: string }) => {
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
        const snapshot = chatController.getCacheSnapshot();
        setLastReloadAt(new Date(snapshot.updatedAtMs ?? Date.now()));
      } catch (err: any) {
        const message = err?.message || 'Failed to reload messages.';
        setLoadError(message);
        Alert.alert('Failed to reload', message);
      }
    },
    [backend, chatController],
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
          onApply={(params) => {
            applyMessageLimitAndReload(params).catch(() => {});
          }}
        />
      ),
    });
  }, [applyMessageLimitAndReload, connectionId, lastReloadAt, rangeEndText, rangeStartText, sessionId]);

  const openAgentPickerForSwitch = useCallback(async () => {
    if (!backend) {
      return;
    }
    if (openingAgentPicker) {
      return;
    }

    setOpeningAgentPicker(true);
    try {
	  	const agents = await ensureAgentsLoaded();

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

      DesktopWindowManager?.openAgentPicker({
        mode: 'switchSessionAgent',
        title: 'Switch Agent',
        primaryButtonLabel: 'Switch',
        sessionId,
        connectionId,
        connectionName,
        initialAgentId,
        agents,
      });
    } catch (err: any) {
      Alert.alert('Error', err?.message || 'Failed to load agents');
    } finally {
      setOpeningAgentPicker(false);
    }
  }, [backend, connectionId, connectionName, ensureAgentsLoaded, openingAgentPicker, sessionId]);

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
          Alert.alert('Not supported', 'This backend does not support session settings.');
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
          Alert.alert('Not supported', 'This backend does not support session plugins.');
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

      const pluginEl = visibleSessionActions.find((el) => el.id === key);
      if (pluginEl) {
        openPluginDialogForElement(pluginEl, {
          kind: 'session',
          sessionSummary: sessionSummary ?? null,
        });
      }
    },
    [
      backend,
      connectionId,
      connectionName,
      handleReload,
      openPluginDialogForElement,
      openAgentPickerForSwitch,
      openMessageLimitPopover,
      visibleSessionActions,
      sessionId,
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
	    setPinnedMessageActionsByRole((prev) => ({ ...prev, [role]: pinned }));
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
      const content = typeof message.content === 'string' ? message.content : '';
      setEditingIndex(index);
      setEditingText(content);
      setEditingInitialText(content);
    },
    [],
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

      try {
        await chatController.modifyMessage(index, trimmed);
        setEditingIndex(null);
        setEditingText('');
        setEditingInitialText('');
      } catch (err: any) {
        const message = err?.message || 'Failed to modify message.';
        Alert.alert('Error', message);
      }
    },
    [backend, chatController],
  );

  const handleCancelEditMessage = useCallback(() => {
    setEditingIndex(null);
    setEditingText('');
    setEditingInitialText('');
  }, []);

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
        setMessageViewModeByIndex((prev) => {
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

      const pluginEl = visibleMessageActions.find((el) => el.id === action);
      if (pluginEl) {
        openPluginDialogForElement(pluginEl, {
          kind: 'message',
          index,
          message: message as ApiMessage,
          sessionSummary: sessionSummary ?? null,
        });
      }
    },
    [handleStartEditMessage, openPluginDialogForElement, sessionSummary, visibleMessageActions],
  );

  const streamingFooter = useMemo(() => {
    const hasStreaming = !!(streamingRow && (streamingRow.content || streamingRow.reasoning));
    const hasInlineDisplays = inlineActionDisplays.length > 0;
    if (!hasStreaming && !hasInlineDisplays) {
      return null;
    }

    return (
      <View>
        {hasStreaming ? (
          <DesktopMessageBubble
            index={messages.length > 0 ? messages[messages.length - 1].index + 1 : 0}
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
        ) : null}
        {inlineActionDisplays.map((entry) => (
          <ActionResultInlineCard
            key={entry.key}
            display={entry.display}
            activeActionId={activeDisplayActionId}
            onDismiss={() =>
              setInlineActionDisplays((current) => current.filter((item) => item.key !== entry.key))
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
    footerElements,
    handleDisplayFollowupAction,
    inlineActionDisplays,
    messages,
    streamingRow,
  ]);

  const renderMessageItem = useCallback(
    ({ item: msg }: { item: IndexedMessage; index: number }) => {
      const role = msg.message.role || 'unknown';
      const allowedActions = ALL_MESSAGE_ACTIONS
        .filter((def) => def.allowedRoles.includes(role))
        .map((def) => def.key as MessageActionKey);
      const isEditing = editingIndex === msg.index;
      const defaultModeForRole: 'markdown' | 'raw' = role === 'assistant' ? 'markdown' : 'raw';
      const renderMode = messageViewModeByIndex[msg.index] ?? defaultModeForRole;

      return (
        <DesktopMessageBubble
          index={msg.index}
          message={msg.message}
          allowedActions={allowedActions}
          onAction={(action, index, message) => handleMessageAction(action, index, message)}
          isEditing={isEditing}
          editingInitialText={isEditing ? editingInitialText : undefined}
          editingText={isEditing ? editingText : undefined}
          onChangeEditingText={isEditing ? setEditingText : undefined}
          onSubmitEdit={(index, _message, nextText) => handleSubmitEditMessage(index, nextText)}
          onCancelEdit={handleCancelEditMessage}
          renderMode={renderMode}
          footerElements={footerElements}
          pluginActionDefs={pluginMessageActionDefs}
        />
      );
    },
    [
      editingIndex,
      editingInitialText,
      editingText,
      footerElements,
      handleCancelEditMessage,
      handleMessageAction,
      handleSubmitEditMessage,
      messageViewModeByIndex,
      pluginMessageActionDefs,
    ],
  );

  return (
	  <View style={styles.root}>
      <ActionResultModal
        visible={!!actionResultDisplay}
        display={actionResultDisplay?.display ?? null}
        activeActionId={activeDisplayActionId}
        onRequestClose={() => setActionResultDisplay(null)}
          onFollowupAction={(action, formValues) => {
          if (!actionResultDisplay) return;
            handleDisplayFollowupAction(actionResultDisplay, action, formValues);
        }}
      />
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.title} numberOfLines={2}>
            {displayTitle}
          </Text>
          <View style={styles.metaRow}>
            <Text style={styles.metaText} numberOfLines={1}>
              {connectionName}
            </Text>
            <Text style={styles.metaDot}>•</Text>
            <Text style={styles.metaText} numberOfLines={1}>
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
          </View>
          <Text style={styles.subtitle} numberOfLines={2}>
            {displaySubtitle}
          </Text>
        </View>

        <View style={styles.headerRight}>
          <ActionsMenuBar<ActionDefinition>
            title="Session actions"
            variant="dropdown"
	          isActive={isActive}
            renderIcon={({ name, size, color }) => <Icon name={name} size={size} color={color} />}
            baseActions={BUILTIN_SESSION_ACTIONS}
	            extraActions={pluginSessionActionDefs}
            pinned={pinnedSessionActionKeys}
            onChangePinned={(next) => setPinnedSessionActionKeys(next)}
            onAction={handleSessionAction}
            isActionDisabled={(key) => {
	              if (pluginActionRunning) {
	                return true;
	              }
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
                if (caps && (!caps.sessionUiSchema || !caps.sessionConfigOverrides)) {
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
              return false;
            }}
          />
        </View>
      </View>

      <View style={styles.body}>
        <View style={styles.statusRow}>
          <Text style={styles.hintSecondary}>Messages: {messagesCount}</Text>
          <Text style={styles.hintSecondary}>
            Streaming: {chatController?.isEventStreaming() ? 'on' : 'off'}
          </Text>
        </View>

        {chatState?.loading ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator size="small" color={theme.textSecondary} />
            <Text style={styles.hintSecondary}>Loading…</Text>
          </View>
        ) : null}

        {attachmentActionInProgress ? (
          <View style={styles.loadingRow}>
            <ActivityIndicator size="small" color={theme.textSecondary} />
            <Text style={styles.hintSecondary}>{attachmentActionText}</Text>
          </View>
        ) : null}

        {loadError ? (
          <View style={styles.errorRow}>
            <Text style={styles.errorText} numberOfLines={2}>
              {loadError}
            </Text>
            <Pressable
              style={({ pressed }) => [styles.retryButton, pressed && styles.retryButtonPressed]}
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

        <View style={styles.transcriptFrame}>
          <PinnedMessageActionsProvider value={pinnedMessageActionsContextValue}>
            {TRANSCRIPT_LIST_IMPLEMENTATION === 'flatList' ? (
              <DependencyFlatList
	              listRef={transcriptScroll.listRef}
	              style={styles.transcript}
	              contentContainerStyle={styles.transcriptContent}
	              data={messages}
	              keyExtractor={(item) => String(item.index)}
	              getItemDependencies={(item) => {
	                const role = item.message.role || 'unknown';
	                const defaultModeForRole: 'markdown' | 'raw' =
	                  role === 'assistant' ? 'markdown' : 'raw';
	                const renderMode =
	                  messageViewModeByIndex[item.index] ?? defaultModeForRole;
	                const isEditing = item.index === editingIndex;
	                return [
	                  renderMode,
	                  footerElements,
	                  isEditing,
	                  isEditing ? editingInitialText : null,
	                  isEditing ? editingText : null,
	                ];
	              }}
	              scrollEventThrottle={16}
	              disableVirtualization={FLATLIST_DISABLE_VIRTUALIZATION}
	              initialNumToRender={FLATLIST_INITIAL_NUM_TO_RENDER}
	              maxToRenderPerBatch={FLATLIST_MAX_TO_RENDER_PER_BATCH}
	              updateCellsBatchingPeriod={FLATLIST_UPDATE_CELLS_BATCHING_PERIOD}
	              windowSize={FLATLIST_WINDOW_SIZE}
	              removeClippedSubviews={FLATLIST_REMOVE_CLIPPED_SUBVIEWS}
	              maintainVisibleContentPosition={
	                FLATLIST_MAINTAIN_VISIBLE_CONTENT_POSITION
	                  ? { minIndexForVisible: 0 }
	                  : undefined
	              }
	              onLayout={transcriptScroll.onLayout}
	              onContentSizeChange={transcriptScroll.onContentSizeChange}
	              onScroll={transcriptScroll.onScroll}
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
	              renderItem={renderMessageItem}
	              ListEmptyComponent={
	                !chatState?.loading ? <Text style={styles.hintSecondary}>No messages.</Text> : null
	              }
	              ListFooterComponent={streamingFooter}
	            />
            ) : TRANSCRIPT_LIST_IMPLEMENTATION === 'virtualizedScroll' ? (
              <DependencyVirtualizedScroll
	              listRef={transcriptScroll.listRef}
	              style={styles.transcript}
	              contentContainerStyle={styles.transcriptContent}
	              data={messages}
	              keyExtractor={(item) => String(item.index)}
	              getItemDependencies={(item) => {
	                const role = item.message.role || 'unknown';
	                const defaultModeForRole: 'markdown' | 'raw' =
	                  role === 'assistant' ? 'markdown' : 'raw';
	                const renderMode =
	                  messageViewModeByIndex[item.index] ?? defaultModeForRole;
	                const isEditing = item.index === editingIndex;
	                return [
	                  renderMode,
	                  footerElements,
	                  isEditing,
	                  isEditing ? editingInitialText : null,
	                  isEditing ? editingText : null,
	                ];
	              }}
	              scrollEventThrottle={16}
	              disableVirtualization={FLATLIST_DISABLE_VIRTUALIZATION}
	              initialNumToRender={FLATLIST_INITIAL_NUM_TO_RENDER}
	              maxToRenderPerBatch={FLATLIST_MAX_TO_RENDER_PER_BATCH}
	              updateCellsBatchingPeriod={FLATLIST_UPDATE_CELLS_BATCHING_PERIOD}
	              windowSize={FLATLIST_WINDOW_SIZE}
	              removeClippedSubviews={FLATLIST_REMOVE_CLIPPED_SUBVIEWS}
	              maintainVisibleContentPosition={
	                FLATLIST_MAINTAIN_VISIBLE_CONTENT_POSITION
	                  ? { minIndexForVisible: 0 }
	                  : undefined
	              }
	              onLayout={transcriptScroll.onLayout}
	              onContentSizeChange={transcriptScroll.onContentSizeChange}
	              onScroll={transcriptScroll.onScroll}
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
	              renderItem={renderMessageItem}
	              ListEmptyComponent={
	                !chatState?.loading ? <Text style={styles.hintSecondary}>No messages.</Text> : null
	              }
	              ListFooterComponent={streamingFooter}
	            />
            ) : (
              <PlaceholderFlatList
	              listRef={transcriptScroll.listRef}
	              style={styles.transcript}
	              contentContainerStyle={styles.transcriptContent}
	              data={messages}
	              keyExtractor={(item) => String(item.index)}
	              showsVerticalScrollIndicator
	              getItemDependencies={(item) => {
	                const role = item.message.role || 'unknown';
	                const defaultModeForRole: 'markdown' | 'raw' =
	                  role === 'assistant' ? 'markdown' : 'raw';
	                const renderMode =
	                  messageViewModeByIndex[item.index] ?? defaultModeForRole;
	                const isEditing = item.index === editingIndex;
	                return [
	                  renderMode,
	                  footerElements,
	                  isEditing,
	                  isEditing ? editingInitialText : null,
	                  isEditing ? editingText : null,
	                ];
	              }}
	              scrollEventThrottle={16}
	              onLayout={transcriptScroll.onLayout}
	              onContentSizeChange={transcriptScroll.onContentSizeChange}
	              onScroll={transcriptScroll.onScroll}
	              onScrollEndDrag={transcriptScroll.onScrollEndDrag}
	              onMomentumScrollEnd={transcriptScroll.onMomentumScrollEnd}
	              renderItem={renderMessageItem}
	              ListEmptyComponent={
	                !chatState?.loading ? <Text style={styles.hintSecondary}>No messages.</Text> : null
	              }
	              ListFooterComponent={streamingFooter}
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

        <View style={styles.composerArea}>
          <View style={styles.composerHeaderRow}>
            <View style={styles.composerHeaderLeft} />
            <View style={styles.composerHeaderRight}>
              <ActionsMenuBar<ActionDefinition>
                title="Composer actions"
                variant="dropdown"
                isActive={isActive}
                renderIcon={({ name, size, color }) => <Icon name={name} size={size} color={color} />}
                baseActions={BUILTIN_COMPOSER_ACTIONS}
                pinned={pinnedComposerActionKeys}
                onChangePinned={(next) => setPinnedComposerActionKeys(next)}
                onAction={handleComposerAction}
                isActionDisabled={(key) => {
                  if (!canRunComposerActions) {
                    return true;
                  }
                  if (key === 'append' || key === 'appendAs') {
                    if (sendInFlight || chatState?.activeRequestId || attachmentActionInProgress) {
                      return true;
                    }
                    return !composeText.trim() && !hasAttachments;
                  }
                  if (key === 'resend') {
                    return sendInFlight || !!chatState?.activeRequestId;
                  }
                  if (key === 'cancel') {
                    return cancelInFlight || !chatState?.activeRequestId;
                  }
                  return false;
                }}
              />
            </View>
          </View>

          {attachmentsAbove.length > 0 ? (
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
                    <Icon name="chevron-up" size={16} color={theme.textSecondary} />
                  </Pressable>
                </View>
                <ComposerAttachmentsExpandedPanel
                  attachments={buildManageRows(attachmentsAbove)}
                  disabled={!canRunComposerActions || attachmentActionInProgress}
                  onMove={(draftId, direction) => handleMoveDraft('above', draftId, direction)}
                  onEditMetadata={(draftId, anchorTag) =>
                    handleEditDraftMetadata('above', draftId, anchorTag)
                  }
                  onDelete={(draftId) => handleDeleteDraft('above', draftId)}
                />
              </View>
            ) : (
              <AttachmentThumbnailStrip
                attachments={buildAttachmentStripRows(attachmentsAbove)}
                disabled={!canRunComposerActions || attachmentActionInProgress}
                expanded={false}
                onToggleExpanded={() => setAttachmentsAboveExpanded(true)}
              />
            )
          ) : null}

          <View style={styles.composerRow}>
            {composerAttachmentPlusRows.length > 0 ? (
              <View ref={attachmentPlusButtonRef} collapsable={false}>
                <Pressable
                  style={({ pressed }) => [
                    styles.attachmentPlusButton,
                    !canOpenAttachmentPlus && styles.attachmentPlusButtonDisabled,
                    pressed && canOpenAttachmentPlus && styles.attachmentPlusButtonPressed,
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
                      canOpenAttachmentPlus ? theme.textSecondary : theme.textMuted
                    }
                  />
                </Pressable>
              </View>
            ) : null}
            <View
              style={[
                styles.composerInputFrame,
                { height: composerHeight },
                !backend && styles.composerInputDisabled,
              ]}
            >
              <MacTextView
                ref={composerRef}
                style={styles.composerInput}
                initialText={initialComposeText}
                placeholder={backend ? 'Type a message…' : 'Offline (read-only)'}
                placeholderTextColor={theme.textMuted}
                textColor={theme.text}
                fontSize={13}
                editable={backend != null && !sendInFlight}
                autoGrow
                minHeight={34}
                maxHeight={120}
                onHeightChange={handleComposerHeightChange}
                onChangeText={(text) => {
                  handleComposerChangeText(text);
                }}
                onSubmit={(text) => {
                  handleSend(text).catch(() => {
                    // errors are handled in `handleSend`
                  });
                }}
              />
            </View>
            <Pressable
              style={({ pressed }) => [
                styles.sendButton,
                !canSendNow && styles.sendButtonDisabled,
                pressed && canSendNow && styles.sendButtonPressed,
              ]}
              disabled={!canSendNow}
              onPress={() => {
                handleSend(composeTextRef.current).catch(() => {
                  // errors are handled in `handleSend`
                });
              }}
            >
              <Text style={styles.sendButtonText}>{sendInFlight ? '…' : 'Send'}</Text>
            </Pressable>
          </View>

          {attachmentsBelow.length > 0 ? (
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
                    <Icon name="chevron-up" size={16} color={theme.textSecondary} />
                  </Pressable>
                </View>
                <ComposerAttachmentsExpandedPanel
                  attachments={buildManageRows(attachmentsBelow)}
                  disabled={!canRunComposerActions || attachmentActionInProgress}
                  onMove={(draftId, direction) => handleMoveDraft('below', draftId, direction)}
                  onEditMetadata={(draftId, anchorTag) =>
                    handleEditDraftMetadata('below', draftId, anchorTag)
                  }
                  onDelete={(draftId) => handleDeleteDraft('below', draftId)}
                />
              </View>
            ) : (
              <AttachmentThumbnailStrip
                attachments={buildAttachmentStripRows(attachmentsBelow)}
                disabled={!canRunComposerActions || attachmentActionInProgress}
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
                Python-style range (start:end). Example: -{DEFAULT_HISTORY_WINDOW}: for last{' '}
                {DEFAULT_HISTORY_WINDOW} messages. Leave blank for all messages.
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
                    applyMessageLimitAndReload({ startText: rangeStartText, endText: rangeEndText }).catch(
                      () => {},
                    );
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
          onSubmit={(values) => handleSubmitPluginDialog(values)}
          onCancel={handleCancelPluginDialog}
        />
      )}
    </View>
  );
});

function createStyles(theme: ReturnType<typeof useTheme>, styleVariant: TabStripStyle) {
  const codeLike = styleVariant === 'codeTabs' || styleVariant === 'underlineTabs';
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
    headerRight: {
      paddingTop: Platform.OS === 'macos' ? 2 : 0,
    },
    title: {
      fontSize: 14,
      fontWeight: '700',
      color: theme.text,
      flexShrink: 1,
    },
    subtitle: {
      fontSize: 12,
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
      fontSize: 11,
      color: theme.textMuted,
      fontWeight: '600',
    },
    metaDot: {
      fontSize: 11,
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
      backgroundColor: 'rgba(0,0,0,0.4)',
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
      fontSize: 12,
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
      fontSize: 12,
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
      fontSize: 13,
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
      fontSize: 13,
      fontWeight: '700',
      color: theme.text,
    },
    modalButtonPrimaryText: {
      fontSize: 13,
      fontWeight: '800',
      color: theme.textOnPrimary,
    },
    modalHelperText: {
      fontSize: 11,
      color: theme.textMuted,
    },
    body: {
      flex: 1,
      padding: 12,
      gap: 10,
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
      backgroundColor: 'rgba(255, 0, 0, 0.08)',
      borderWidth: separatorWidth,
      borderColor: theme.border,
    },
    errorText: {
      flex: 1,
      fontSize: 12,
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
      fontSize: 12,
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
      fontSize: 11,
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
      paddingTop: Platform.OS === 'macos' ? 2 : 0,
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
      fontSize: 13,
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
      backgroundColor: 'rgba(120, 120, 120, 0.12)',
    },
    messageMeta: {
      fontSize: 11,
      fontWeight: '600',
      color: theme.textSecondary,
    },
    messageText: {
      fontSize: 13,
      lineHeight: 18,
      color: theme.text,
    },
    hint: {
      fontSize: 13,
      color: theme.text,
    },
    hintSecondary: {
      fontSize: 12,
      color: theme.textSecondary,
    },
  });
}
