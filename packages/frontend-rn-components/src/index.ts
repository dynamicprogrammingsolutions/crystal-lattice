export type {
  ActionKey,
  ActionDefinition,
  ActionsMenuModel,
  ActionsMenuPinnedRenderParams,
} from "./actions/types";

export type { Theme } from "./theme";
export { ThemeProvider, useTheme } from "./theme";

export type {
  FlushOutcome,
  HumanTimeDiagnosticEntry,
  HumanTimeDiagnosticUploadStatus,
  HumanTimeIngestionResult,
  HumanTimeSpan,
  HumanTimeSpanTrackerOptions,
  HumanTimeUploadEvent,
  HumanTimeUploaderOptions,
  SpanCacheStore,
} from "./humanTimeTelemetry";
export {
  DEFAULT_CLOSE_DEBOUNCE_MS,
  DEFAULT_HUMAN_TIME_PLUGIN_ID,
  DEFAULT_SPAN_INACTIVITY_MS,
  DEFAULT_TRANSIENT_RETRY_INTERVAL_MS,
  DEFAULT_UPLOAD_BATCH_LIMIT,
  HUMAN_TIME_ACTION_ID,
  HUMAN_TIME_ACTION_OWNER,
  HUMAN_TIME_SPANS_SOFT_CAP,
  HUMAN_TIME_SPANS_STORAGE_KEY,
  HUMAN_TIME_TELEMETRY_WARNING_DISPLAY_ID,
  HumanTimeSpanTracker,
  HumanTimeSpanUploader,
  RECENT_HUMAN_TIME_DIAGNOSTIC_ENTRY_LIMIT,
  appendHumanTimeSpan,
  emitHumanTimeTelemetryWarning,
  humanTimeDiagnosticSpanKey,
  humanTimeDiagnosticUploadStatus,
  isDefinitiveActionErrorType,
  isDefinitiveActionFailure,
  loadHumanTimeSpans,
  mergePendingHumanTimeDiagnosticEntries,
  newestHumanTimeDiagnosticEntries,
  removeFirstHumanTimeSpans,
  removeHumanTimeSpans,
  toIsoUtc,
  updateHumanTimeDiagnosticEntries,
} from "./humanTimeTelemetry";

export type {
  HomeSessionCollections,
  HomeSessionItem,
  HomeSessionsCache,
  HomeSessionsCacheEntry,
  RecentSessionsWindow,
  WatchedSessionIdentity,
} from "./homeWorkspace";
export {
  DEFAULT_RECENT_SESSIONS_WINDOW,
  MAX_SESSION_NOTE_LENGTH,
  deriveHomeSessionCollections,
  moveWatchedSession,
  normalizeRecentSessionsWindow,
  normalizeSessionNotes,
  normalizeWatchlist,
  watchedSessionKey,
} from "./homeWorkspace";

export type {
  ReorderItemFrame,
  ReorderPreviewSlot,
  ReorderRenderSlot,
} from "./reorderGeometry";
export {
  applyReorderKeyOrder,
  buildReorderPreview,
  buildReorderRenderSlots,
  moveReorderValues,
  resolveReorderDropTarget,
  resolveReorderDropTranslation,
} from "./reorderGeometry";

export type { SessionRequestStatusIndicatorProps } from "./SessionRequestStatusIndicator";
export { SessionRequestStatusIndicator } from "./SessionRequestStatusIndicator";
export type { SessionRequestStatusTone } from "./sessionRequestStatus";
export {
  SESSION_REQUEST_STATUS_LABELS,
  SESSION_REQUEST_STATUS_TONES,
  getSessionRequestStatusPresentation,
} from "./sessionRequestStatus";

export type {
  CodeBlockRendererId,
  MarkdownBaseFontSize,
  MarkdownDisplayPreferences,
  MarkdownDisplayPreferencesProviderProps,
  MarkdownHeaderSize,
  MarkdownRendererCapabilities,
  MarkdownRendererId,
  MarkdownTypography,
  ResolvedMarkdownRendererPreferences,
} from "./markdownDisplayPreferences";
export {
  CODE_BLOCK_RENDERER_OPTIONS,
  DEFAULT_MARKDOWN_DISPLAY_PREFERENCES,
  DISPLAY_TYPOGRAPHY_PRESETS,
  MARKDOWN_BASE_FONT_SIZES,
  MARKDOWN_BASE_FONT_SIZE_OPTIONS,
  MARKDOWN_HEADER_SIZE_OPTIONS,
  MARKDOWN_RENDERER_OPTIONS,
  MarkdownDisplayPreferencesProvider,
  applyDisplayTypographyPreset,
  deriveMarkdownTypography,
  normalizeCodeBlockRendererId,
  normalizeMarkdownBaseFontSize,
  normalizeMarkdownDisplayPreferences,
  normalizeMarkdownHeaderSize,
  normalizeMarkdownRendererId,
  resolveMarkdownRendererPreferences,
  useMarkdownDisplayPreferences,
} from "./markdownDisplayPreferences";

export type {
  SessionActionKey,
  SessionActionDefinition,
} from "./sessionActions";
export { SESSION_ACTIONS, ALL_SESSION_ACTIONS } from "./sessionActions";
export type { LocalSessionActionKey } from "./localSessionActions";
export {
  LOCAL_NOTE_SESSION_ACTION_KEY,
  LOCAL_WATCHLIST_SESSION_ACTION_KEY,
  buildLocalSessionActionDefinitions,
  isLocalSessionActionKey,
} from "./localSessionActions";

export type {
  ApplicationActionDialogFieldRenderer,
  ApplicationActionDialogFieldRenderers,
  ApplicationActionDialogFieldRenderParams,
  ApplicationActionDialogPrefillContext,
  ApplicationActionDialogProps,
  ApplicationActionFormHandle,
  ApplicationActionFormProps,
  DialogInputField,
} from "./ApplicationActionDialog";
export { ApplicationActionDialog } from "./ApplicationActionDialog";
export { ApplicationActionDialogLayout } from "./ApplicationActionDialog";
export { ApplicationActionForm } from "./ApplicationActionDialog";
export type { ApplicationActionsMenuProps } from "./actions/ApplicationActionsMenu";
export { ApplicationActionsMenu } from "./actions/ApplicationActionsMenu";
export type { NotificationBannerProps } from "./notifications/NotificationBanner";
export { NotificationBanner } from "./notifications/NotificationBanner";
export type {
  NotificationBannerHostItem,
  NotificationBannerHostProps,
} from "./notifications/NotificationBannerHost";
export { NotificationBannerHost } from "./notifications/NotificationBannerHost";
export type { SessionNotificationsHostProps } from "./notifications/SessionNotificationsHost";
export { SessionNotificationsHost } from "./notifications/SessionNotificationsHost";

export {
  buildActionsMenuModel,
  limitPinnedActionsForBar,
  normalizeActionDefinitions,
  togglePinnedKey,
} from "./actions/model";

export type {
  UseActionsMenuModelOptions,
  UseActionsMenuModelResult,
} from "./actions/useActionsMenuModel";
export { useActionsMenuModel } from "./actions/useActionsMenuModel";

export type {
  ActionsMenuContentProps,
  ActionsMenuRenderItemParams,
} from "./actions/ActionsMenuContent";
export { ActionsMenuContent } from "./actions/ActionsMenuContent";

export type { MenuSurfaceBaseProps } from "./actions/MenuSurfaces";
export { ModalMenuSurface, DropdownMenuSurface } from "./actions/MenuSurfaces";
export {
  actionsPopoverInvokeAction,
  actionsPopoverRequestClose,
  actionsPopoverTogglePinned,
  clearActiveActionsPopoverMenu,
  getLastActionsPopoverAnchorTag,
  getActiveActionsPopoverMenu,
  setActiveActionsPopoverMenu,
  setLastActionsPopoverAnchorTag,
  updateActiveActionsPopoverMenuData,
  useActiveActionsPopoverMenu,
  type ActionsPopoverMenuData,
  type ActionsPopoverMenuHandlers,
  type ActionsPopoverMenuState,
} from "./actions/actionsPopoverCoordinator";

export type { ActionsMenuProps } from "./actions/ActionsMenu";
export { ActionsMenu } from "./actions/ActionsMenu";

export type { ActionsMenuPanelProps } from "./actions/ActionsMenuPanel";
export { ActionsMenuPanel } from "./actions/ActionsMenuPanel";

export type { ActionsMenuBarProps } from "./actions/ActionsMenuBar";
export {
  ACTIONS_MENU_BAR_ITEM_WIDTH,
  ActionsMenuBar,
} from "./actions/ActionsMenuBar";

export type { SessionActionsBarProps } from "./actions/SessionActionsBar";
export { SessionActionsBar } from "./actions/SessionActionsBar";
export type {
  RichConfigDropdownControlProps,
  RichConfigDropdownPanelProps,
  RichConfigToggleControlProps,
} from "./actions/RichConfigDropdown";
export {
  RichConfigDropdownControl,
  RichConfigDropdownPanel,
  RichConfigToggleControl,
  truncatePinnedValue,
} from "./actions/RichConfigDropdown";

export type {
  SessionListActionsBarProps,
  SessionListRichActionControlProps,
  SessionListPluginActionDefinition,
  SessionListRichActionListProps,
} from "./actions/SessionListActionsBar";
export {
  SessionListActionsBar,
  SessionListRichActionControl,
  SessionListRichActionList,
} from "./actions/SessionListActionsBar";
export { resolveSemanticToneColor } from "./actions/semanticTone";

export { SessionPluginsList } from "./SessionPluginsList";

export type { SessionListFiltersPanelProps } from "./SessionListFiltersPanel";
export { SessionListFiltersPanel } from "./SessionListFiltersPanel";
