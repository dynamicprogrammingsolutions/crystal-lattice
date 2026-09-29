#import "AppDelegate.h"
#import "DesktopMenuNotifications.h"

#import <React/RCTBundleURLProvider.h>
#import <React/RCTRootView.h>
#import <React/RCTDevLoadingViewSetEnabled.h>
#import <ReactAppDependencyProvider/RCTAppDependencyProvider.h>
#import <math.h>

static NSString *const kTabStripStyleDefaultsKey = @"CrystalLattice.TabStripStyle";
static NSString *const kTabStripStyleToolbarTabs = @"toolbarTabs";
static NSString *const kTabStripStyleCodeTabs = @"codeTabs";
static NSString *const kTabStripStyleUnderlineTabs = @"underlineTabs";
static NSString *const kTabStripStyleRoundedPills = @"roundedPills";

static NSString *const kSessionsFollowActiveTabDefaultsKey =
    @"CrystalLattice.SessionsFollowActiveTabEnabled";
static NSString *const kSwitchConnectionWithActiveTabDefaultsKey =
    @"CrystalLattice.SwitchConnectionWithActiveTabEnabled";
static NSString *const kMarkdownBaseFontSizeDefaultsKey =
    @"CrystalLattice.MarkdownBaseFontSize";
static NSString *const kMarkdownHeaderSizeDefaultsKey =
    @"CrystalLattice.MarkdownHeaderSize";
static NSString *const kMarkdownHeaderSizeNormal = @"normal";
static NSString *const kMarkdownHeaderSizeSmall = @"small";
static NSString *const kRecentSessionsWindowDefaultsKey =
    @"CrystalLattice.RecentSessionsWindow";
static NSString *const kRecentSessionsWindow24Hours = @"24h";
static NSString *const kRecentSessionsWindow3Days = @"3d";
static NSString *const kRecentSessionsWindow1Week = @"1w";
static NSString *const kSessionDoubleClickActionDefaultsKey =
    @"CrystalLattice.SessionDoubleClickAction";
static NSString *const kSessionDoubleClickActionPreview = @"preview";
static NSString *const kSessionDoubleClickActionOpen = @"open";
static NSString *const kTimeTrackingEnabledDefaultsKey =
    @"CrystalLattice.TimeTrackingEnabled";
static NSString *const kTimeTrackingPluginIdDefaultsKey =
    @"CrystalLattice.TimeTrackingPluginId";
static NSString *const kTimeTrackingInactivitySecondsDefaultsKey =
    @"CrystalLattice.TimeTrackingInactivitySeconds";
static NSString *const kDefaultTimeTrackingPluginId = @"duration_tracking_app";

static BOOL EnvironmentFlagEnabled(NSString *name)
{
  NSString *value = [NSProcessInfo processInfo].environment[name];
  if (![value isKindOfClass:[NSString class]]) {
    return NO;
  }
  NSString *normalized = value.lowercaseString;
  return [normalized isEqualToString:@"1"] || [normalized isEqualToString:@"true"] ||
      [normalized isEqualToString:@"yes"];
}

static BOOL LaunchArgumentPresent(NSString *argument)
{
  return [[NSProcessInfo processInfo].arguments containsObject:argument];
}

@interface AppDelegate ()

@property(nonatomic, strong) NSMenuItem *toolbarTabsMenuItem;
@property(nonatomic, strong) NSMenuItem *codeTabsMenuItem;
@property(nonatomic, strong) NSMenuItem *underlineTabsMenuItem;
@property(nonatomic, strong) NSMenuItem *roundedPillsMenuItem;

@property(nonatomic, strong) NSMenuItem *sessionsFollowActiveTabMenuItem;
@property(nonatomic, strong) NSMenuItem *switchConnectionWithActiveTabMenuItem;
@property(nonatomic, strong) NSArray<NSMenuItem *> *markdownBaseFontSizeMenuItems;
@property(nonatomic, strong) NSArray<NSMenuItem *> *markdownHeaderSizeMenuItems;
@property(nonatomic, strong) NSMenuItem *clearStoredSessionCachesMenuItem;
@property(nonatomic, strong) NSMenuItem *globalSettingsMenuItem;

@property(nonatomic, strong) NSMutableArray<NSWindow *> *mainWindows;
@property(nonatomic, assign) NSPoint mainWindowCascadePoint;

@end

@implementation AppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)notification
{
  BOOL enableScrollTestHarness =
      EnvironmentFlagEnabled(@"CLC_ENABLE_SCROLL_TEST_HARNESS") || LaunchArgumentPresent(@"--scroll-test-harness");
  BOOL enableTranscriptScrollPersistenceHarness =
      EnvironmentFlagEnabled(@"CLC_ENABLE_TRANSCRIPT_SCROLL_PERSISTENCE_HARNESS") ||
      LaunchArgumentPresent(@"--transcript-scroll-persistence-harness");
  BOOL enableTranscriptRangeNavigationHarness =
      EnvironmentFlagEnabled(@"CLC_ENABLE_TRANSCRIPT_RANGE_NAVIGATION_HARNESS") ||
      LaunchArgumentPresent(@"--transcript-range-navigation-harness");
  BOOL enableSessionFiltersPopoverHarness =
      EnvironmentFlagEnabled(@"CLC_ENABLE_SESSION_FILTERS_POPOVER_HARNESS") ||
      LaunchArgumentPresent(@"--session-filters-popover-harness");
  BOOL enableNotificationRailHarness =
      EnvironmentFlagEnabled(@"CLC_ENABLE_NOTIFICATION_RAIL_HARNESS") ||
      LaunchArgumentPresent(@"--notification-rail-harness");
  BOOL enableMarkdownGeometryHarness =
      EnvironmentFlagEnabled(@"CLC_ENABLE_MARKDOWN_GEOMETRY_HARNESS") ||
      LaunchArgumentPresent(@"--markdown-geometry-harness");
  BOOL enableConnectionsPanelHarness =
      EnvironmentFlagEnabled(@"CLC_ENABLE_CONNECTIONS_PANEL_HARNESS") ||
      LaunchArgumentPresent(@"--connections-panel-harness");
  BOOL enableActionDisplayHarness =
      EnvironmentFlagEnabled(@"CLC_ENABLE_ACTION_DISPLAY_HARNESS") ||
      LaunchArgumentPresent(@"--action-display-harness");
  BOOL enableDesktopWorkspaceHarness =
      EnvironmentFlagEnabled(@"CLC_ENABLE_DESKTOP_WORKSPACE_HARNESS") ||
      LaunchArgumentPresent(@"--desktop-workspace-harness");
  BOOL enableRichSessionUiHarness =
      EnvironmentFlagEnabled(@"CLC_ENABLE_RICH_SESSION_UI_HARNESS") ||
      LaunchArgumentPresent(@"--rich-session-ui-harness");
  BOOL enableAnyTestHarness =
      enableScrollTestHarness ||
      enableTranscriptScrollPersistenceHarness ||
      enableTranscriptRangeNavigationHarness ||
      enableSessionFiltersPopoverHarness ||
      enableNotificationRailHarness ||
      enableMarkdownGeometryHarness ||
      enableConnectionsPanelHarness ||
      enableActionDisplayHarness ||
      enableDesktopWorkspaceHarness ||
      enableRichSessionUiHarness;
  if (enableAnyTestHarness) {
    RCTDevLoadingViewSetEnabled(NO);
  }
  if (enableActionDisplayHarness) {
    self.moduleName = @"DesktopActionDisplayHarness";
  } else if (enableRichSessionUiHarness) {
    self.moduleName = @"DesktopRichSessionUiHarness";
  } else if (enableDesktopWorkspaceHarness) {
    self.moduleName = @"DesktopWorkspaceHarness";
  } else if (enableConnectionsPanelHarness) {
    self.moduleName = @"DesktopConnectionsPanelHarness";
  } else if (enableMarkdownGeometryHarness) {
    self.moduleName = @"DesktopMarkdownGeometryHarness";
  } else if (enableTranscriptRangeNavigationHarness) {
    self.moduleName = @"DesktopTranscriptRangeNavigationHarness";
  } else if (enableNotificationRailHarness) {
    self.moduleName = @"DesktopNotificationRailHarness";
  } else if (enableSessionFiltersPopoverHarness) {
    self.moduleName = @"SessionFiltersPopoverHarness";
  } else if (enableTranscriptScrollPersistenceHarness) {
    self.moduleName = @"TranscriptScrollPersistenceHarness";
  } else if (enableScrollTestHarness) {
    self.moduleName = @"ProgressiveScrollHarness";
  } else {
    self.moduleName = @"CrystalLatticeControlDesktopRN";
  }
  NSString *tabStripStyle = [self loadTabStripStylePreference];
  BOOL followEnabled = [self loadSessionsFollowActiveTabEnabledPreference];
  BOOL switchConnectionEnabled =
      [self loadSwitchConnectionWithActiveTabEnabledPreference];
  NSInteger markdownBaseFontSize = [self loadMarkdownBaseFontSizePreference];
  NSString *markdownHeaderSize = [self loadMarkdownHeaderSizePreference];
  NSString *recentSessionsWindow = [self loadRecentSessionsWindowPreference];
  NSString *sessionDoubleClickAction =
      [self loadSessionDoubleClickActionPreference];
  NSMutableDictionary *initialProps = [@{
    @"initialTabStripStyle" : tabStripStyle,
    @"initialSessionsFollowActiveTabEnabled" : @(followEnabled),
    @"initialSwitchConnectionWithActiveTabEnabled" : @(switchConnectionEnabled),
    @"initialMarkdownBaseFontSize" : @(markdownBaseFontSize),
    @"initialMarkdownHeaderSize" : markdownHeaderSize,
    @"initialRecentSessionsWindow" : recentSessionsWindow,
    @"initialSessionDoubleClickAction" : sessionDoubleClickAction,
    @"enableScrollTestHarness" : @(enableScrollTestHarness),
    @"enableMarkdownGeometryHarness" : @(enableMarkdownGeometryHarness),
    @"connectionsHarnessCount" : [NSProcessInfo processInfo].environment[@"CLC_CONNECTIONS_HARNESS_COUNT"] ?: @"0",
    @"connectionsHarnessPreset" : [NSProcessInfo processInfo].environment[@"CLC_CONNECTIONS_HARNESS_PRESET"] ?: @"default",
    @"scrollHarnessRunId" : [NSProcessInfo processInfo].environment[@"CLC_SCROLL_HARNESS_RUN_ID"] ?: @"",
    @"scrollHarnessBackingList" : [NSProcessInfo processInfo].environment[@"CLC_PROGRESSIVE_SCROLL_BACKING_LIST"] ?: @"scrollView",
    @"scrollHarnessGrowOnly" : @(EnvironmentFlagEnabled(@"CLC_PROGRESSIVE_SCROLL_GROW_ONLY")),
    @"transcriptScrollListImplementation" : [NSProcessInfo processInfo].environment[@"CLC_TRANSCRIPT_SCROLL_LIST_IMPLEMENTATION"] ?: @"scrollView",
    @"progressiveScrollBackingList" : [NSProcessInfo processInfo].environment[@"CLC_PROGRESSIVE_SCROLL_BACKING_LIST"] ?: @"scrollView",
    @"initialRestoreReady" : @(!EnvironmentFlagEnabled(@"CLC_TRANSCRIPT_SCROLL_RESTORE_READY_FALSE")),
  } mutableCopy];
  if (LaunchArgumentPresent(@"--human-time-native-test")) {
    NSString *fixtureJson =
        [NSProcessInfo processInfo].environment[@"CLC_HUMAN_TIME_NATIVE_FIXTURE_JSON"];
    NSData *fixtureData = [fixtureJson dataUsingEncoding:NSUTF8StringEncoding];
    if (fixtureData != nil) {
      id fixture =
          [NSJSONSerialization JSONObjectWithData:fixtureData options:0 error:nil];
      if ([fixture isKindOfClass:[NSDictionary class]]) {
        initialProps[@"humanTimeNativeFixture"] = fixture;
      }
    }
  }
  self.initialProps = initialProps;
  self.dependencyProvider = [RCTAppDependencyProvider new];

  [super applicationDidFinishLaunching:notification];

  // Track the initial main window created by RCTAppDelegate so we can:
  // - release it when closed (so closing the window truly closes it)
  // - reopen / create windows when the Dock icon is clicked
  // - support opening additional main windows
  [self ensureMainWindowsTrackingInitialized];
  [self trackMainWindowIfNeeded:(NSWindow *)self.window];
  if (enableAnyTestHarness) {
    NSWindow *window = (NSWindow *)self.window;
    window.title = self.moduleName;
    window.accessibilityLabel = self.moduleName;
    window.accessibilityIdentifier = [NSString stringWithFormat:@"%@Window", self.moduleName];
    [(NSWindow *)self.window makeKeyAndOrderFront:nil];
    [NSApp activateIgnoringOtherApps:YES];
  }

  [self installTabStripStyleMenuWithSelectedStyle:tabStripStyle];
  [self installMarkdownDisplayMenusWithBaseFontSize:markdownBaseFontSize
                                         headerSize:markdownHeaderSize];
  [self installSessionsFollowActiveTabMenuWithEnabled:followEnabled];
  [self installSwitchConnectionWithActiveTabMenuWithEnabled:switchConnectionEnabled];
  [self installGlobalSettingsMenu];
  [self installClearStoredSessionCachesMenu];
  [self installDevelopMenu];
  if (enableScrollTestHarness) {
    [self installProgressiveScrollHarnessMenu];
  }
  if (enableTranscriptScrollPersistenceHarness) {
    [self installTranscriptScrollPersistenceHarnessMenu];
  }

  [[NSNotificationCenter defaultCenter]
      addObserver:self
         selector:@selector(handleDesktopGlobalSettingRequested:)
             name:CLCDesktopGlobalSettingRequestedNotification
           object:nil];
}

#pragma mark - Main window management (Dock reopen / New Window)

- (void)ensureMainWindowsTrackingInitialized
{
  if (self.mainWindows != nil) {
    return;
  }
  self.mainWindows = [NSMutableArray array];
  self.mainWindowCascadePoint = NSZeroPoint;
}

- (void)trackMainWindowIfNeeded:(NSWindow *)window
{
  if (window == nil) {
    return;
  }

  [self ensureMainWindowsTrackingInitialized];

  // Avoid double-registration.
  if ([self.mainWindows containsObject:window]) {
    return;
  }

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(mainWindowWillClose:)
                                               name:NSWindowWillCloseNotification
                                             object:window];

  [self.mainWindows addObject:window];
}

- (void)mainWindowWillClose:(NSNotification *)notification
{
  NSWindow *window = (NSWindow *)notification.object;
  if (window == nil) {
    return;
  }

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:NSWindowWillCloseNotification
                                                object:window];

  [self.mainWindows removeObject:window];

  // If the RN-created main window is being closed, release our reference so it can be recreated later.
  if ((NSWindow *)self.window == window) {
    // If another main window is still open, keep `self.window` pointing at one of them.
    self.window = (id)(self.mainWindows.lastObject);
  }
}

- (NSDictionary *)mainWindowInitialProps
{
  NSMutableDictionary *props = [NSMutableDictionary dictionary];
  if ([self.initialProps isKindOfClass:[NSDictionary class]]) {
    [props addEntriesFromDictionary:self.initialProps];
  }

  // Always read the latest preference so new windows match the current setting.
  props[@"initialTabStripStyle"] = [self loadTabStripStylePreference];
  props[@"initialSessionsFollowActiveTabEnabled"] = @([self loadSessionsFollowActiveTabEnabledPreference]);
  props[@"initialSwitchConnectionWithActiveTabEnabled"] =
      @([self loadSwitchConnectionWithActiveTabEnabledPreference]);
  props[@"initialMarkdownBaseFontSize"] = @([self loadMarkdownBaseFontSizePreference]);
  props[@"initialMarkdownHeaderSize"] = [self loadMarkdownHeaderSizePreference];
  props[@"initialRecentSessionsWindow"] =
      [self loadRecentSessionsWindowPreference];
  props[@"initialSessionDoubleClickAction"] =
      [self loadSessionDoubleClickActionPreference];
  return props;
}

- (NSWindow *)createMainWindow
{
  NSString *moduleName = self.moduleName;
  if (![moduleName isKindOfClass:[NSString class]] || moduleName.length == 0) {
    moduleName = @"CrystalLatticeControlDesktopRN";
  }

  NSDictionary *initialProps = [self mainWindowInitialProps];

  NSView *rootView = nil;
  if (self.rootViewFactory != nil) {
    @try {
      rootView = (NSView *)[self.rootViewFactory viewWithModuleName:moduleName initialProperties:initialProps];
    } @catch (__unused NSException *exception) {
      rootView = nil;
    }
  }

  if (rootView == nil) {
    // Fallback: should not happen, but keeps behavior consistent with DesktopWindowManager.
    rootView = [[RCTRootView alloc] initWithBridge:self.bridge moduleName:moduleName initialProperties:initialProps];
  }

  NSRect frame = NSMakeRect(0, 0, 1280, 720);
  NSWindow *window = [[NSWindow alloc] initWithContentRect:frame
                                                 styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskResizable |
                                                           NSWindowStyleMaskClosable | NSWindowStyleMaskMiniaturizable
                                                   backing:NSBackingStoreBuffered
                                                     defer:NO];
  window.title = moduleName;
  window.autorecalculatesKeyViewLoop = YES;

  NSViewController *rootViewController = [NSViewController new];
  rootViewController.view = rootView;
  rootView.frame = frame;
  rootView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
  window.contentViewController = rootViewController;

  // Keep explicit ownership until the window closes.
  window.releasedWhenClosed = NO;

  return window;
}

- (void)presentMainWindow:(NSWindow *)window
{
  if (window == nil) {
    return;
  }

  [self trackMainWindowIfNeeded:window];

  // Cascade new windows so "New Window" doesn't stack them perfectly.
  self.mainWindowCascadePoint = [window cascadeTopLeftFromPoint:self.mainWindowCascadePoint];

  [window makeKeyAndOrderFront:nil];
  [NSApp activateIgnoringOtherApps:YES];
}

- (void)openNewMainWindow:(__unused id)sender
{
  dispatch_async(dispatch_get_main_queue(), ^{
    NSWindow *window = [self createMainWindow];
    // Keep `self.window` pointing to the most recently created main window.
    self.window = (id)window;
    [self presentMainWindow:window];
  });
}

- (BOOL)applicationShouldHandleReopen:(__unused NSApplication *)sender
                    hasVisibleWindows:(BOOL)hasVisibleWindows
{
  // Match typical macOS behavior: clicking the Dock icon brings windows forward,
  // or creates a new main window when none exist.

  [NSApp activateIgnoringOtherApps:YES];
  [NSApp unhide:nil];

  BOOL restoredAnyWindow = NO;
  for (NSWindow *window in [self.mainWindows copy]) {
    // Restore only tracked main windows. Auxiliary windows such as popovers,
    // spelling panels, and other AppKit-managed helpers should not be revived
    // when clicking the Dock icon.
    if (![window isKindOfClass:[NSWindow class]] || !window.canBecomeKeyWindow || !window.isVisible) {
      continue;
    }

    if (window.isMiniaturized) {
      [window deminiaturize:nil];
    }

    [window makeKeyAndOrderFront:nil];
    restoredAnyWindow = YES;
  }

  if (!restoredAnyWindow && !hasVisibleWindows) {
    [self openNewMainWindow:nil];
  }

  return YES;
}

- (NSMenu *)applicationDockMenu:(__unused NSApplication *)sender
{
  NSMenu *menu = [[NSMenu alloc] initWithTitle:@""];

  NSMenuItem *newWindowItem =
      [[NSMenuItem alloc] initWithTitle:@"New Window" action:@selector(openNewMainWindow:) keyEquivalent:@""];
  newWindowItem.target = self;
  [menu addItem:newWindowItem];

  return menu;
}

- (NSURL *)sourceURLForBridge:(RCTBridge *)bridge
{
  return [self bundleURL];
}

- (NSURL *)bundleURL
{
  if (EnvironmentFlagEnabled(@"CLC_ENABLE_SCROLL_TEST_HARNESS") ||
      EnvironmentFlagEnabled(@"CLC_ENABLE_TRANSCRIPT_SCROLL_PERSISTENCE_HARNESS") ||
      EnvironmentFlagEnabled(@"CLC_ENABLE_TRANSCRIPT_RANGE_NAVIGATION_HARNESS") ||
      EnvironmentFlagEnabled(@"CLC_ENABLE_SESSION_FILTERS_POPOVER_HARNESS") ||
      EnvironmentFlagEnabled(@"CLC_ENABLE_NOTIFICATION_RAIL_HARNESS") ||
      EnvironmentFlagEnabled(@"CLC_ENABLE_MARKDOWN_GEOMETRY_HARNESS") ||
      EnvironmentFlagEnabled(@"CLC_ENABLE_CONNECTIONS_PANEL_HARNESS") ||
      EnvironmentFlagEnabled(@"CLC_ENABLE_ACTION_DISPLAY_HARNESS") ||
      EnvironmentFlagEnabled(@"CLC_ENABLE_DESKTOP_WORKSPACE_HARNESS") ||
      EnvironmentFlagEnabled(@"CLC_ENABLE_RICH_SESSION_UI_HARNESS") ||
      LaunchArgumentPresent(@"--scroll-test-harness") ||
      LaunchArgumentPresent(@"--transcript-scroll-persistence-harness") ||
      LaunchArgumentPresent(@"--transcript-range-navigation-harness") ||
      LaunchArgumentPresent(@"--session-filters-popover-harness") ||
      LaunchArgumentPresent(@"--notification-rail-harness") ||
      LaunchArgumentPresent(@"--markdown-geometry-harness") ||
      LaunchArgumentPresent(@"--connections-panel-harness") ||
      LaunchArgumentPresent(@"--action-display-harness") ||
      LaunchArgumentPresent(@"--desktop-workspace-harness") ||
      LaunchArgumentPresent(@"--rich-session-ui-harness")) {
    return [[NSBundle mainBundle] URLForResource:@"main" withExtension:@"jsbundle"];
  }

#if DEBUG
  return [[RCTBundleURLProvider sharedSettings] jsBundleURLForBundleRoot:@"index"];
#else
  return [[NSBundle mainBundle] URLForResource:@"main" withExtension:@"jsbundle"];
#endif
}

/// This method controls whether the `concurrentRoot`feature of React18 is turned on or off.
///
/// @see: https://reactjs.org/blog/2022/03/29/react-v18.html
/// @note: This requires to be rendering on Fabric (i.e. on the New Architecture).
/// @return: `true` if the `concurrentRoot` feature is enabled. Otherwise, it returns `false`.
- (BOOL)concurrentRootEnabled
{
#ifdef RN_FABRIC_ENABLED
  return true;
#else
  return false;
#endif
}

- (NSString *)loadTabStripStylePreference
{
  NSString *value = [[NSUserDefaults standardUserDefaults] stringForKey:kTabStripStyleDefaultsKey];
  if ([value isEqualToString:kTabStripStyleToolbarTabs] ||
      [value isEqualToString:kTabStripStyleCodeTabs] ||
      [value isEqualToString:kTabStripStyleUnderlineTabs] ||
      [value isEqualToString:kTabStripStyleRoundedPills]) {
    return value;
  }
  return kTabStripStyleToolbarTabs;
}

- (BOOL)loadSessionsFollowActiveTabEnabledPreference
{
  id raw = [[NSUserDefaults standardUserDefaults] objectForKey:kSessionsFollowActiveTabDefaultsKey];
  if (raw == nil) {
    return YES;
  }
  return [[NSUserDefaults standardUserDefaults] boolForKey:kSessionsFollowActiveTabDefaultsKey];
}

- (BOOL)loadSwitchConnectionWithActiveTabEnabledPreference
{
  id raw =
      [[NSUserDefaults standardUserDefaults] objectForKey:kSwitchConnectionWithActiveTabDefaultsKey];
  if (raw == nil) {
    return NO;
  }
  return [[NSUserDefaults standardUserDefaults] boolForKey:kSwitchConnectionWithActiveTabDefaultsKey];
}

- (void)saveSwitchConnectionWithActiveTabEnabledPreference:(BOOL)enabled
{
  [[NSUserDefaults standardUserDefaults] setBool:enabled
                                         forKey:kSwitchConnectionWithActiveTabDefaultsKey];
}

- (void)saveSessionsFollowActiveTabEnabledPreference:(BOOL)enabled
{
  [[NSUserDefaults standardUserDefaults] setBool:enabled forKey:kSessionsFollowActiveTabDefaultsKey];
}

- (NSInteger)loadMarkdownBaseFontSizePreference
{
  NSInteger value =
      [[NSUserDefaults standardUserDefaults] integerForKey:kMarkdownBaseFontSizeDefaultsKey];
  if (value == 13 || value == 19) {
    NSInteger migratedValue = value == 13 ? 14 : 17;
    [[NSUserDefaults standardUserDefaults] setInteger:migratedValue
                                               forKey:kMarkdownBaseFontSizeDefaultsKey];
    return migratedValue;
  }
  if (value == 14 || value == 15 || value == 16 || value == 17) {
    return value;
  }
  return 15;
}

- (NSString *)loadMarkdownHeaderSizePreference
{
  NSString *value =
      [[NSUserDefaults standardUserDefaults] stringForKey:kMarkdownHeaderSizeDefaultsKey];
  if ([value isEqualToString:kMarkdownHeaderSizeNormal] ||
      [value isEqualToString:kMarkdownHeaderSizeSmall]) {
    return value;
  }
  return kMarkdownHeaderSizeNormal;
}

- (void)saveMarkdownBaseFontSizePreference:(NSInteger)baseFontSize
{
  if (baseFontSize != 14 && baseFontSize != 15 &&
      baseFontSize != 16 && baseFontSize != 17) {
    return;
  }
  [[NSUserDefaults standardUserDefaults] setInteger:baseFontSize
                                             forKey:kMarkdownBaseFontSizeDefaultsKey];
}

- (void)saveMarkdownHeaderSizePreference:(NSString *)headerSize
{
  if (![headerSize isEqualToString:kMarkdownHeaderSizeNormal] &&
      ![headerSize isEqualToString:kMarkdownHeaderSizeSmall]) {
    return;
  }
  [[NSUserDefaults standardUserDefaults] setObject:headerSize
                                            forKey:kMarkdownHeaderSizeDefaultsKey];
}

- (NSString *)loadRecentSessionsWindowPreference
{
  NSString *value =
      [[NSUserDefaults standardUserDefaults] stringForKey:kRecentSessionsWindowDefaultsKey];
  if ([value isEqualToString:kRecentSessionsWindow24Hours] ||
      [value isEqualToString:kRecentSessionsWindow3Days] ||
      [value isEqualToString:kRecentSessionsWindow1Week]) {
    return value;
  }
  return kRecentSessionsWindow3Days;
}

- (void)saveRecentSessionsWindowPreference:(NSString *)value
{
  if (![value isEqualToString:kRecentSessionsWindow24Hours] &&
      ![value isEqualToString:kRecentSessionsWindow3Days] &&
      ![value isEqualToString:kRecentSessionsWindow1Week]) {
    return;
  }
  [[NSUserDefaults standardUserDefaults] setObject:value
                                            forKey:kRecentSessionsWindowDefaultsKey];
}

- (NSString *)loadSessionDoubleClickActionPreference
{
  NSString *value =
      [[NSUserDefaults standardUserDefaults] stringForKey:kSessionDoubleClickActionDefaultsKey];
  if ([value isEqualToString:kSessionDoubleClickActionPreview] ||
      [value isEqualToString:kSessionDoubleClickActionOpen]) {
    return value;
  }
  return kSessionDoubleClickActionPreview;
}

- (void)saveSessionDoubleClickActionPreference:(NSString *)value
{
  if (![value isEqualToString:kSessionDoubleClickActionPreview] &&
      ![value isEqualToString:kSessionDoubleClickActionOpen]) {
    return;
  }
  [[NSUserDefaults standardUserDefaults] setObject:value
                                            forKey:kSessionDoubleClickActionDefaultsKey];
}

- (void)installGlobalSettingsMenu
{
  NSMenu *mainMenu = [NSApp mainMenu];
  if (mainMenu == nil || mainMenu.itemArray.count == 0) {
    return;
  }
  NSMenuItem *applicationMenuItem = mainMenu.itemArray.firstObject;
  NSMenu *applicationMenu = applicationMenuItem.submenu;
  if (applicationMenu == nil) {
    return;
  }
  NSMenuItem *settingsItem = [applicationMenu itemWithTitle:@"Preferences…"];
  if (settingsItem == nil) {
    settingsItem = [applicationMenu itemWithTitle:@"Settings…"];
  }
  if (settingsItem == nil) {
    return;
  }
  self.globalSettingsMenuItem = settingsItem;
  settingsItem.title = @"Settings…";
  settingsItem.target = self;
  settingsItem.action = @selector(openGlobalSettings:);
  settingsItem.enabled = YES;
}

- (void)openGlobalSettings:(__unused id)sender
{
  [[NSNotificationCenter defaultCenter]
      postNotificationName:CLCOpenGlobalSettingsNotification
                    object:nil];
}

- (void)handleDesktopGlobalSettingRequested:(NSNotification *)notification
{
  NSString *key =
      notification.userInfo[CLCDesktopGlobalSettingKeyUserInfoKey];
  id value = notification.userInfo[CLCDesktopGlobalSettingValueUserInfoKey];
  if (![key isKindOfClass:[NSString class]]) {
    return;
  }

  if ([key isEqualToString:@"baseFontSize"] &&
      [value respondsToSelector:@selector(integerValue)]) {
    NSInteger baseFontSize = [value integerValue];
    if (baseFontSize != 14 && baseFontSize != 15 &&
        baseFontSize != 16 && baseFontSize != 17) {
      return;
    }
    [self saveMarkdownBaseFontSizePreference:baseFontSize];
    [self updateMarkdownDisplayMenuStateWithBaseFontSize:baseFontSize
                                              headerSize:[self loadMarkdownHeaderSizePreference]];
    [[NSNotificationCenter defaultCenter]
        postNotificationName:CLCMarkdownBaseFontSizeDidChangeNotification
                      object:nil
                    userInfo:@{
                      CLCMarkdownBaseFontSizeUserInfoKey : @(baseFontSize)
                    }];
    return;
  }

  if ([key isEqualToString:@"headerSize"] &&
      [value isKindOfClass:[NSString class]]) {
    NSString *headerSize = (NSString *)value;
    if (![headerSize isEqualToString:kMarkdownHeaderSizeNormal] &&
        ![headerSize isEqualToString:kMarkdownHeaderSizeSmall]) {
      return;
    }
    [self saveMarkdownHeaderSizePreference:headerSize];
    [self updateMarkdownDisplayMenuStateWithBaseFontSize:[self loadMarkdownBaseFontSizePreference]
                                              headerSize:headerSize];
    [[NSNotificationCenter defaultCenter]
        postNotificationName:CLCMarkdownHeaderSizeDidChangeNotification
                      object:nil
                    userInfo:@{
                      CLCMarkdownHeaderSizeUserInfoKey : headerSize
                    }];
    return;
  }

  if ([key isEqualToString:@"recentSessionsWindow"] &&
      [value isKindOfClass:[NSString class]]) {
    NSString *recentSessionsWindow = (NSString *)value;
    [self saveRecentSessionsWindowPreference:recentSessionsWindow];
    NSString *saved = [self loadRecentSessionsWindowPreference];
    [[NSNotificationCenter defaultCenter]
        postNotificationName:CLCRecentSessionsWindowDidChangeNotification
                      object:nil
                    userInfo:@{
                      CLCRecentSessionsWindowUserInfoKey : saved
                    }];
    return;
  }

  if ([key isEqualToString:@"sessionDoubleClickAction"] &&
      [value isKindOfClass:[NSString class]]) {
    NSString *sessionDoubleClickAction = (NSString *)value;
    [self saveSessionDoubleClickActionPreference:sessionDoubleClickAction];
    NSString *saved = [self loadSessionDoubleClickActionPreference];
    [[NSNotificationCenter defaultCenter]
        postNotificationName:CLCSessionDoubleClickActionDidChangeNotification
                      object:nil
                    userInfo:@{
                      CLCSessionDoubleClickActionUserInfoKey : saved
                    }];
    return;
  }

  if ([key isEqualToString:@"sessionsFollowActiveTabEnabled"] &&
      [value respondsToSelector:@selector(boolValue)]) {
    BOOL enabled = [value boolValue];
    [self saveSessionsFollowActiveTabEnabledPreference:enabled];
    if (self.sessionsFollowActiveTabMenuItem != nil) {
      self.sessionsFollowActiveTabMenuItem.state =
          enabled ? NSControlStateValueOn : NSControlStateValueOff;
    }
    [[NSNotificationCenter defaultCenter]
        postNotificationName:CLCSessionsFollowActiveTabDidChangeNotification
                      object:nil
                    userInfo:@{
                      CLCSessionsFollowActiveTabEnabledUserInfoKey : @(enabled)
                    }];
    return;
  }

  if ([key isEqualToString:@"switchConnectionWithActiveTabEnabled"] &&
      [value respondsToSelector:@selector(boolValue)]) {
    BOOL enabled = [value boolValue];
    [self saveSwitchConnectionWithActiveTabEnabledPreference:enabled];
    if (self.switchConnectionWithActiveTabMenuItem != nil) {
      self.switchConnectionWithActiveTabMenuItem.state =
          enabled ? NSControlStateValueOn : NSControlStateValueOff;
    }
    [[NSNotificationCenter defaultCenter]
        postNotificationName:CLCSwitchConnectionWithActiveTabDidChangeNotification
                      object:nil
                    userInfo:@{
                      CLCSwitchConnectionWithActiveTabEnabledUserInfoKey : @(enabled)
                    }];
    return;
  }

  if ([key isEqualToString:@"timeTrackingEnabled"] &&
      [value respondsToSelector:@selector(boolValue)]) {
    BOOL enabled = [value boolValue];
    [[NSUserDefaults standardUserDefaults] setBool:enabled
                                           forKey:kTimeTrackingEnabledDefaultsKey];
    [[NSNotificationCenter defaultCenter]
        postNotificationName:CLCTimeTrackingEnabledDidChangeNotification
                      object:nil
                    userInfo:@{
                      CLCTimeTrackingEnabledUserInfoKey : @(enabled)
                    }];
    return;
  }

  if ([key isEqualToString:@"timeTrackingPluginId"] &&
      [value isKindOfClass:[NSString class]]) {
    NSString *pluginId =
        [(NSString *)value stringByTrimmingCharactersInSet:
            [NSCharacterSet whitespaceAndNewlineCharacterSet]];
    if (pluginId.length == 0) {
      pluginId = kDefaultTimeTrackingPluginId;
    }
    [[NSUserDefaults standardUserDefaults] setObject:pluginId
                                              forKey:kTimeTrackingPluginIdDefaultsKey];
    [[NSNotificationCenter defaultCenter]
        postNotificationName:CLCTimeTrackingPluginIdDidChangeNotification
                      object:nil
                    userInfo:@{
                      CLCTimeTrackingPluginIdUserInfoKey : pluginId
                    }];
    return;
  }

  if ([key isEqualToString:@"timeTrackingInactivitySeconds"] &&
      [value respondsToSelector:@selector(doubleValue)]) {
    double seconds = [value doubleValue];
    if (!isfinite(seconds) || seconds <= 0) {
      seconds = 30.0;
    }
    [[NSUserDefaults standardUserDefaults]
        setDouble:seconds
           forKey:kTimeTrackingInactivitySecondsDefaultsKey];
    [[NSNotificationCenter defaultCenter]
        postNotificationName:CLCTimeTrackingInactivitySecondsDidChangeNotification
                      object:nil
                    userInfo:@{
                      CLCTimeTrackingInactivitySecondsUserInfoKey : @(seconds)
                    }];
  }
}

- (void)installClearStoredSessionCachesMenu
{
  NSMenu *mainMenu = [NSApp mainMenu];
  if (mainMenu == nil) {
    return;
  }

  NSMenuItem *helpMenuItem = [mainMenu itemWithTitle:@"Help"];
  if (helpMenuItem == nil || helpMenuItem.submenu == nil) {
    return;
  }

  NSMenu *helpMenu = helpMenuItem.submenu;

  if (self.clearStoredSessionCachesMenuItem == nil) {
    self.clearStoredSessionCachesMenuItem =
        [[NSMenuItem alloc] initWithTitle:@"Clear Stored Session Caches"
                                   action:@selector(clearStoredSessionCaches:)
                            keyEquivalent:@""];
    self.clearStoredSessionCachesMenuItem.target = self;
  }

  if (![helpMenu.itemArray containsObject:self.clearStoredSessionCachesMenuItem]) {
    if (helpMenu.numberOfItems > 0 && !helpMenu.itemArray.lastObject.isSeparatorItem) {
      [helpMenu addItem:[NSMenuItem separatorItem]];
    }
    [helpMenu addItem:self.clearStoredSessionCachesMenuItem];
  }
}

- (void)clearStoredSessionCaches:(__unused id)sender
{
  [[NSNotificationCenter defaultCenter] postNotificationName:CLCClearStoredSessionCachesNotification object:nil];
}

- (void)installDevelopMenu
{
  NSMenu *mainMenu = [NSApp mainMenu];
  if (mainMenu == nil) {
    return;
  }

  NSMenuItem *helpMenuItem = [mainMenu itemWithTitle:@"Help"];
  if (helpMenuItem == nil || helpMenuItem.submenu == nil) {
    return;
  }

  NSMenu *helpMenu = helpMenuItem.submenu;

  NSMenuItem *developMenuItem = [[NSMenuItem alloc] initWithTitle:@"Develop" action:nil keyEquivalent:@""];
  NSMenu *developMenu = [[NSMenu alloc] initWithTitle:@"Develop"];
  developMenuItem.submenu = developMenu;

  NSMenuItem *notificationTestingItem =
      [[NSMenuItem alloc] initWithTitle:@"Notification Testing"
                                 action:@selector(openNotificationTesting:)
                          keyEquivalent:@""];
  notificationTestingItem.target = self;
  [developMenu addItem:notificationTestingItem];

  if (![helpMenu.itemArray containsObject:developMenuItem]) {
    if (helpMenu.numberOfItems > 0 && !helpMenu.itemArray.lastObject.isSeparatorItem) {
      [helpMenu addItem:[NSMenuItem separatorItem]];
    }
    [helpMenu addItem:developMenuItem];
  }
}

- (void)openNotificationTesting:(__unused id)sender
{
  [[NSNotificationCenter defaultCenter] postNotificationName:CLCOpenNotificationTestingNotification object:nil];
}

- (void)installProgressiveScrollHarnessMenu
{
  NSMenu *mainMenu = [NSApp mainMenu];
  if (mainMenu == nil) {
    return;
  }

  NSMenuItem *harnessMenuItem = [[NSMenuItem alloc] initWithTitle:@"Scroll Harness" action:nil keyEquivalent:@""];
  NSMenu *harnessMenu = [[NSMenu alloc] initWithTitle:@"Scroll Harness"];
  harnessMenuItem.submenu = harnessMenu;

  NSArray<NSArray<NSString *> *> *items = @[
    @[ @"Scroll Harness Top", @"progressiveScrollHarnessTop:" ],
    @[ @"Scroll Harness Bottom", @"progressiveScrollHarnessBottom:" ],
    @[ @"Scroll Harness Message 60", @"progressiveScrollHarnessMessage60:" ],
    @[ @"Scroll Harness Message 120", @"progressiveScrollHarnessMessage120:" ],
    @[ @"Scroll Harness Window Top", @"progressiveScrollHarnessWindowTop:" ],
    @[ @"Scroll Harness Window Bottom", @"progressiveScrollHarnessWindowBottom:" ],
    @[ @"Scroll Harness Read Anchor", @"progressiveScrollHarnessReadAnchor:" ],
    @[ @"Scroll Harness Load Above", @"progressiveScrollHarnessLoadAbove:" ],
    @[ @"Scroll Harness Load Below", @"progressiveScrollHarnessLoadBelow:" ],
  ];

  for (NSArray<NSString *> *item in items) {
    SEL selector = NSSelectorFromString(item[1]);
    NSMenuItem *menuItem = [[NSMenuItem alloc] initWithTitle:item[0] action:selector keyEquivalent:@""];
    menuItem.target = self;
    [harnessMenu addItem:menuItem];
  }

  [mainMenu addItem:harnessMenuItem];
}

- (void)installTranscriptScrollPersistenceHarnessMenu
{
  NSMenu *mainMenu = [NSApp mainMenu];
  if (mainMenu == nil) {
    return;
  }

  NSMenuItem *harnessMenuItem =
      [[NSMenuItem alloc] initWithTitle:@"Transcript Scroll Harness" action:nil keyEquivalent:@""];
  NSMenu *harnessMenu = [[NSMenu alloc] initWithTitle:@"Transcript Scroll Harness"];
  harnessMenuItem.submenu = harnessMenu;

  NSArray<NSArray<NSString *> *> *items = @[
    @[ @"Transcript Harness Read", @"transcriptScrollHarnessRead:" ],
    @[ @"Transcript Harness Offset Round Trip", @"transcriptScrollHarnessOffsetRoundTrip:" ],
    @[ @"Transcript Harness Message Anchor Save", @"transcriptScrollHarnessMessageAnchorSave:" ],
    @[ @"Transcript Harness Message Anchor Restore", @"transcriptScrollHarnessMessageAnchorRestore:" ],
    @[ @"Transcript Harness Message Anchor Round Trip", @"transcriptScrollHarnessMessageAnchorRoundTrip:" ],
    @[ @"Transcript Harness Release Delayed Anchor", @"transcriptScrollHarnessReleaseDelayedAnchor:" ],
    @[ @"Transcript Harness Release Delayed Offset Anchor", @"transcriptScrollHarnessReleaseDelayedOffsetAnchor:" ],
    @[ @"Transcript Harness Navigation Separation", @"transcriptScrollHarnessNavigationSeparation:" ],
    @[ @"Transcript Harness Prepare Manual Detach", @"transcriptScrollHarnessPrepareManualDetach:" ],
    @[ @"Transcript Harness Semantic After Manual Detach", @"transcriptScrollHarnessSemanticAfterManualDetach:" ],
    @[ @"Transcript Harness Semantic After Manual Reattach", @"transcriptScrollHarnessSemanticAfterManualReattach:" ],
    @[ @"Transcript Harness Long Distance Bottom", @"transcriptScrollHarnessLongDistanceBottom:" ],
    @[ @"Transcript Harness Far Message Anchor", @"transcriptScrollHarnessFarMessageAnchor:" ],
    @[ @"Transcript Harness Semantic Content Follow", @"transcriptScrollHarnessSemanticContentFollow:" ],
    @[ @"Transcript Harness Feedback Loop", @"transcriptScrollHarnessFeedbackLoop:" ],
  ];

  for (NSArray<NSString *> *item in items) {
    SEL selector = NSSelectorFromString(item[1]);
    NSMenuItem *menuItem = [[NSMenuItem alloc] initWithTitle:item[0] action:selector keyEquivalent:@""];
    menuItem.target = self;
    [harnessMenu addItem:menuItem];
  }

  [mainMenu addItem:harnessMenuItem];
}

- (void)postProgressiveScrollHarnessCommand:(NSString *)command
{
  NSDictionary *payload = @{
    @"command" : command,
    @"runId" : [NSProcessInfo processInfo].environment[@"CLC_SCROLL_HARNESS_RUN_ID"] ?: @"",
    @"postedAtMs" : @((long long)([[NSDate date] timeIntervalSince1970] * 1000)),
  };
  NSData *data = [NSJSONSerialization dataWithJSONObject:payload options:0 error:nil];
  [data writeToFile:@"/tmp/clc-progressive-scroll-harness-command.json" atomically:YES];

  [[NSNotificationCenter defaultCenter]
      postNotificationName:CLCProgressiveScrollHarnessCommandNotification
                    object:nil
                  userInfo:@{
                    CLCProgressiveScrollHarnessCommandUserInfoKey : command,
                    @"postedAtMs" : payload[@"postedAtMs"],
                  }];
}

- (void)progressiveScrollHarnessTop:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"top"];
}

- (void)progressiveScrollHarnessBottom:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"bottom"];
}

- (void)progressiveScrollHarnessMessage60:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"message60"];
}

- (void)progressiveScrollHarnessMessage120:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"message120"];
}

- (void)progressiveScrollHarnessWindowTop:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"windowTop"];
}

- (void)progressiveScrollHarnessWindowBottom:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"windowBottom"];
}

- (void)progressiveScrollHarnessReadAnchor:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"readAnchor"];
}

- (void)progressiveScrollHarnessLoadAbove:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"loadAbove"];
}

- (void)progressiveScrollHarnessLoadBelow:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"loadBelow"];
}

- (void)transcriptScrollHarnessRead:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"read"];
}

- (void)transcriptScrollHarnessOffsetRoundTrip:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"offsetRoundTrip"];
}

- (void)transcriptScrollHarnessMessageAnchorSave:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"messageAnchorSave"];
}

- (void)transcriptScrollHarnessMessageAnchorRestore:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"messageAnchorRestore"];
}

- (void)transcriptScrollHarnessMessageAnchorRoundTrip:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"messageAnchorRoundTrip"];
}

- (void)transcriptScrollHarnessReleaseDelayedAnchor:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"releaseDelayedMessageAnchor"];
}

- (void)transcriptScrollHarnessReleaseDelayedOffsetAnchor:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"releaseDelayedOffsetAnchor"];
}

- (void)transcriptScrollHarnessNavigationSeparation:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"navigationSeparation"];
}

- (void)transcriptScrollHarnessPrepareManualDetach:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"prepareManualDetach"];
}

- (void)transcriptScrollHarnessSemanticAfterManualDetach:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"semanticAfterManualDetach"];
}

- (void)transcriptScrollHarnessSemanticAfterManualReattach:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"semanticAfterManualReattach"];
}

- (void)transcriptScrollHarnessLongDistanceBottom:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"longDistanceBottom"];
}

- (void)transcriptScrollHarnessFarMessageAnchor:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"farMessageAnchor"];
}

- (void)transcriptScrollHarnessSemanticContentFollow:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"semanticContentFollow"];
}

- (void)transcriptScrollHarnessFeedbackLoop:(__unused id)sender
{
  [self postProgressiveScrollHarnessCommand:@"feedbackLoop"];
}

- (void)installMarkdownDisplayMenusWithBaseFontSize:(NSInteger)baseFontSize
                                         headerSize:(NSString *)headerSize
{
  NSMenu *mainMenu = [NSApp mainMenu];
  NSMenuItem *viewMenuItem = [mainMenu itemWithTitle:@"View"];
  if (viewMenuItem == nil || viewMenuItem.submenu == nil) {
    return;
  }
  NSMenu *viewMenu = viewMenuItem.submenu;

  NSMenuItem *fontSizeItem =
      [[NSMenuItem alloc] initWithTitle:@"Font Size" action:nil keyEquivalent:@""];
  NSMenu *fontSizeMenu = [[NSMenu alloc] initWithTitle:@"Font Size"];
  fontSizeMenu.autoenablesItems = NO;
  NSArray<NSNumber *> *fontSizes = @[ @14, @15, @16, @17 ];
  NSMutableArray<NSMenuItem *> *fontSizeItems = [NSMutableArray array];
  for (NSNumber *fontSize in fontSizes) {
    NSString *title = fontSize.integerValue == 15
        ? @"15 (Default)"
        : fontSize.stringValue;
    NSMenuItem *item =
        [[NSMenuItem alloc] initWithTitle:title
                                   action:@selector(selectMarkdownBaseFontSize:)
                            keyEquivalent:@""];
    item.target = self;
    item.enabled = YES;
    item.representedObject = fontSize;
    [fontSizeMenu addItem:item];
    [fontSizeItems addObject:item];
  }
  self.markdownBaseFontSizeMenuItems = fontSizeItems;
  fontSizeItem.submenu = fontSizeMenu;

  NSMenuItem *headerSizeItem =
      [[NSMenuItem alloc] initWithTitle:@"Markdown Headers" action:nil keyEquivalent:@""];
  NSMenu *headerSizeMenu = [[NSMenu alloc] initWithTitle:@"Markdown Headers"];
  headerSizeMenu.autoenablesItems = NO;
  NSArray<NSArray<NSString *> *> *headerSizes = @[
    @[ @"Normal", kMarkdownHeaderSizeNormal ],
    @[ @"Small", kMarkdownHeaderSizeSmall ],
  ];
  NSMutableArray<NSMenuItem *> *headerSizeItems = [NSMutableArray array];
  for (NSArray<NSString *> *entry in headerSizes) {
    NSMenuItem *item =
        [[NSMenuItem alloc] initWithTitle:entry[0]
                                   action:@selector(selectMarkdownHeaderSize:)
                            keyEquivalent:@""];
    item.target = self;
    item.enabled = YES;
    item.representedObject = entry[1];
    [headerSizeMenu addItem:item];
    [headerSizeItems addObject:item];
  }
  self.markdownHeaderSizeMenuItems = headerSizeItems;
  headerSizeItem.submenu = headerSizeMenu;

  NSInteger insertionIndex = viewMenu.numberOfItems;
  for (NSInteger index = 0; index < viewMenu.numberOfItems; index++) {
    if ([[[viewMenu itemAtIndex:index] title] isEqualToString:@"Tab Strip Style"]) {
      insertionIndex = index + 1;
      break;
    }
  }
  [viewMenu insertItem:fontSizeItem atIndex:insertionIndex];
  [viewMenu insertItem:headerSizeItem atIndex:insertionIndex + 1];
  [self updateMarkdownDisplayMenuStateWithBaseFontSize:baseFontSize
                                            headerSize:headerSize];
}

- (void)updateMarkdownDisplayMenuStateWithBaseFontSize:(NSInteger)baseFontSize
                                             headerSize:(NSString *)headerSize
{
  for (NSMenuItem *item in self.markdownBaseFontSizeMenuItems) {
    NSNumber *value = item.representedObject;
    item.state = value.integerValue == baseFontSize
        ? NSControlStateValueOn
        : NSControlStateValueOff;
  }
  for (NSMenuItem *item in self.markdownHeaderSizeMenuItems) {
    NSString *value = item.representedObject;
    item.state = [value isEqualToString:headerSize]
        ? NSControlStateValueOn
        : NSControlStateValueOff;
  }
}

- (void)selectMarkdownBaseFontSize:(NSMenuItem *)sender
{
  NSNumber *value = sender.representedObject;
  NSInteger baseFontSize = value.integerValue;
  if (baseFontSize != 14 && baseFontSize != 15 &&
      baseFontSize != 16 && baseFontSize != 17) {
    return;
  }
  [self saveMarkdownBaseFontSizePreference:baseFontSize];
  [self updateMarkdownDisplayMenuStateWithBaseFontSize:baseFontSize
                                            headerSize:[self loadMarkdownHeaderSizePreference]];
  [[NSNotificationCenter defaultCenter]
      postNotificationName:CLCMarkdownBaseFontSizeDidChangeNotification
                    object:nil
                  userInfo:@{ CLCMarkdownBaseFontSizeUserInfoKey : @(baseFontSize) }];
}

- (void)selectMarkdownHeaderSize:(NSMenuItem *)sender
{
  NSString *headerSize = sender.representedObject;
  if (![headerSize isEqualToString:kMarkdownHeaderSizeNormal] &&
      ![headerSize isEqualToString:kMarkdownHeaderSizeSmall]) {
    return;
  }
  [self saveMarkdownHeaderSizePreference:headerSize];
  [self updateMarkdownDisplayMenuStateWithBaseFontSize:[self loadMarkdownBaseFontSizePreference]
                                            headerSize:headerSize];
  [[NSNotificationCenter defaultCenter]
      postNotificationName:CLCMarkdownHeaderSizeDidChangeNotification
                    object:nil
                  userInfo:@{ CLCMarkdownHeaderSizeUserInfoKey : headerSize }];
}

- (void)installSessionsFollowActiveTabMenuWithEnabled:(BOOL)enabled
{
  NSMenu *mainMenu = [NSApp mainMenu];
  if (mainMenu == nil) {
    return;
  }

  NSMenuItem *viewMenuItem = [mainMenu itemWithTitle:@"View"];
  if (viewMenuItem == nil || viewMenuItem.submenu == nil) {
    return;
  }

  NSMenu *viewMenu = viewMenuItem.submenu;

  if (self.sessionsFollowActiveTabMenuItem == nil) {
    self.sessionsFollowActiveTabMenuItem =
        [[NSMenuItem alloc] initWithTitle:@"Follow Active Tab in Sessions List"
                                   action:@selector(toggleSessionsFollowActiveTab:)
                            keyEquivalent:@""];
    self.sessionsFollowActiveTabMenuItem.target = self;
  }

  self.sessionsFollowActiveTabMenuItem.state = enabled ? NSControlStateValueOn : NSControlStateValueOff;

  // Insert near the tab strip style section if possible.
  NSInteger insertionIndex = viewMenu.numberOfItems;
  for (NSInteger i = 0; i < viewMenu.numberOfItems; i++) {
    NSMenuItem *item = [viewMenu itemAtIndex:i];
    if ([[item title] isEqualToString:@"Tab Strip Style"]) {
      insertionIndex = i + 1;
      break;
    }
  }

  if (![viewMenu.itemArray containsObject:self.sessionsFollowActiveTabMenuItem]) {
    [viewMenu insertItem:self.sessionsFollowActiveTabMenuItem atIndex:insertionIndex];
  }
}

- (void)toggleSessionsFollowActiveTab:(__unused id)sender
{
  BOOL current = [self loadSessionsFollowActiveTabEnabledPreference];
  BOOL next = !current;
  [self saveSessionsFollowActiveTabEnabledPreference:next];
  if (self.sessionsFollowActiveTabMenuItem != nil) {
    self.sessionsFollowActiveTabMenuItem.state = next ? NSControlStateValueOn : NSControlStateValueOff;
  }
  [[NSNotificationCenter defaultCenter] postNotificationName:CLCSessionsFollowActiveTabDidChangeNotification
                                                      object:nil
                                                    userInfo:@{ CLCSessionsFollowActiveTabEnabledUserInfoKey : @(next) }];
}

- (void)installSwitchConnectionWithActiveTabMenuWithEnabled:(BOOL)enabled
{
  NSMenu *mainMenu = [NSApp mainMenu];
  if (mainMenu == nil) {
    return;
  }

  NSMenuItem *viewMenuItem = [mainMenu itemWithTitle:@"View"];
  if (viewMenuItem == nil || viewMenuItem.submenu == nil) {
    return;
  }

  NSMenu *viewMenu = viewMenuItem.submenu;

  if (self.switchConnectionWithActiveTabMenuItem == nil) {
    self.switchConnectionWithActiveTabMenuItem =
        [[NSMenuItem alloc] initWithTitle:@"Switch Connection with Active Tab"
                                   action:@selector(toggleSwitchConnectionWithActiveTab:)
                            keyEquivalent:@""];
    self.switchConnectionWithActiveTabMenuItem.target = self;
  }

  self.switchConnectionWithActiveTabMenuItem.state =
      enabled ? NSControlStateValueOn : NSControlStateValueOff;

  NSInteger insertionIndex = viewMenu.numberOfItems;
  NSInteger followIndex =
      [viewMenu indexOfItem:self.sessionsFollowActiveTabMenuItem];
  if (followIndex >= 0) {
    insertionIndex = followIndex + 1;
  }

  if (![viewMenu.itemArray containsObject:self.switchConnectionWithActiveTabMenuItem]) {
    [viewMenu insertItem:self.switchConnectionWithActiveTabMenuItem
                 atIndex:insertionIndex];
  }
}

- (void)toggleSwitchConnectionWithActiveTab:(__unused id)sender
{
  BOOL current = [self loadSwitchConnectionWithActiveTabEnabledPreference];
  BOOL next = !current;
  [self saveSwitchConnectionWithActiveTabEnabledPreference:next];
  if (self.switchConnectionWithActiveTabMenuItem != nil) {
    self.switchConnectionWithActiveTabMenuItem.state =
        next ? NSControlStateValueOn : NSControlStateValueOff;
  }
  [[NSNotificationCenter defaultCenter]
      postNotificationName:CLCSwitchConnectionWithActiveTabDidChangeNotification
                    object:nil
                  userInfo:@{
                    CLCSwitchConnectionWithActiveTabEnabledUserInfoKey : @(next)
                  }];
}

- (void)saveTabStripStylePreference:(NSString *)style
{
  if (![style isEqualToString:kTabStripStyleToolbarTabs] &&
      ![style isEqualToString:kTabStripStyleCodeTabs] &&
      ![style isEqualToString:kTabStripStyleUnderlineTabs] &&
      ![style isEqualToString:kTabStripStyleRoundedPills]) {
    return;
  }
  [[NSUserDefaults standardUserDefaults] setObject:style forKey:kTabStripStyleDefaultsKey];
}

- (void)installTabStripStyleMenuWithSelectedStyle:(NSString *)style
{
  NSMenu *mainMenu = [NSApp mainMenu];
  if (mainMenu == nil) {
    return;
  }

  NSMenuItem *viewMenuItem = [mainMenu itemWithTitle:@"View"]; 
  if (viewMenuItem == nil || viewMenuItem.submenu == nil) {
    return;
  }

  NSMenu *viewMenu = viewMenuItem.submenu;

  NSMenuItem *tabStripStyleItem = [[NSMenuItem alloc] initWithTitle:@"Tab Strip Style" action:nil keyEquivalent:@""];
  NSMenu *tabStripSubmenu = [[NSMenu alloc] initWithTitle:@"Tab Strip Style"];
  tabStripSubmenu.autoenablesItems = NO;

  self.toolbarTabsMenuItem = [[NSMenuItem alloc] initWithTitle:@"Toolbar Tabs"
                                                       action:@selector(selectToolbarTabs:)
                                                keyEquivalent:@""];
  self.toolbarTabsMenuItem.target = self;
  self.toolbarTabsMenuItem.enabled = YES;

  self.codeTabsMenuItem = [[NSMenuItem alloc] initWithTitle:@"Code Tabs"
                                                    action:@selector(selectCodeTabs:)
                                             keyEquivalent:@""];
  self.codeTabsMenuItem.target = self;
  self.codeTabsMenuItem.enabled = YES;

  self.underlineTabsMenuItem = [[NSMenuItem alloc] initWithTitle:@"Underline Tabs"
                                                         action:@selector(selectUnderlineTabs:)
                                                  keyEquivalent:@""];
  self.underlineTabsMenuItem.target = self;
  self.underlineTabsMenuItem.enabled = YES;

  self.roundedPillsMenuItem = [[NSMenuItem alloc] initWithTitle:@"Rounded Pills"
                                                        action:@selector(selectRoundedPills:)
                                                 keyEquivalent:@""];
  self.roundedPillsMenuItem.target = self;
  self.roundedPillsMenuItem.enabled = YES;

  [tabStripSubmenu addItem:self.toolbarTabsMenuItem];
  [tabStripSubmenu addItem:self.codeTabsMenuItem];
  [tabStripSubmenu addItem:self.underlineTabsMenuItem];
  [tabStripSubmenu addItem:self.roundedPillsMenuItem];
  tabStripStyleItem.submenu = tabStripSubmenu;

  NSInteger insertionIndex = viewMenu.numberOfItems;
  for (NSInteger i = 0; i < viewMenu.numberOfItems; i++) {
    NSMenuItem *item = [viewMenu itemAtIndex:i];
    if (item.isSeparatorItem) {
      insertionIndex = i + 1;
      break;
    }
  }

  [viewMenu insertItem:tabStripStyleItem atIndex:insertionIndex];
  [self updateTabStripStyleMenuState:style];
}

- (void)updateTabStripStyleMenuState:(NSString *)style
{
  if (self.toolbarTabsMenuItem == nil ||
      self.codeTabsMenuItem == nil ||
      self.underlineTabsMenuItem == nil ||
      self.roundedPillsMenuItem == nil) {
    return;
  }

  self.toolbarTabsMenuItem.state = [style isEqualToString:kTabStripStyleToolbarTabs]
      ? NSControlStateValueOn
      : NSControlStateValueOff;
  self.codeTabsMenuItem.state = [style isEqualToString:kTabStripStyleCodeTabs]
      ? NSControlStateValueOn
      : NSControlStateValueOff;
  self.underlineTabsMenuItem.state = [style isEqualToString:kTabStripStyleUnderlineTabs]
      ? NSControlStateValueOn
      : NSControlStateValueOff;
  self.roundedPillsMenuItem.state = [style isEqualToString:kTabStripStyleRoundedPills]
      ? NSControlStateValueOn
      : NSControlStateValueOff;
}

- (void)selectToolbarTabs:(__unused id)sender
{
  [self applyTabStripStyle:kTabStripStyleToolbarTabs];
}

- (void)selectCodeTabs:(__unused id)sender
{
  [self applyTabStripStyle:kTabStripStyleCodeTabs];
}

- (void)selectUnderlineTabs:(__unused id)sender
{
  [self applyTabStripStyle:kTabStripStyleUnderlineTabs];
}

- (void)selectRoundedPills:(__unused id)sender
{
  [self applyTabStripStyle:kTabStripStyleRoundedPills];
}

- (void)applyTabStripStyle:(NSString *)style
{
  [self saveTabStripStylePreference:style];
  [self updateTabStripStyleMenuState:style];
  [[NSNotificationCenter defaultCenter] postNotificationName:CLCTabStripStyleDidChangeNotification
                                                      object:nil
                                                    userInfo:@{ CLCTabStripStyleUserInfoKey : style }];
}

@end
