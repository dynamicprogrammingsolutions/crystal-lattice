#import "AppDelegate.h"
#import "DesktopMenuNotifications.h"

#import <React/RCTBundleURLProvider.h>
#import <React/RCTRootView.h>
#import <ReactAppDependencyProvider/RCTAppDependencyProvider.h>

static NSString *const kTabStripStyleDefaultsKey = @"CrystalLattice.TabStripStyle";
static NSString *const kTabStripStyleToolbarTabs = @"toolbarTabs";
static NSString *const kTabStripStyleCodeTabs = @"codeTabs";
static NSString *const kTabStripStyleUnderlineTabs = @"underlineTabs";
static NSString *const kTabStripStyleRoundedPills = @"roundedPills";

static NSString *const kSessionsFollowActiveTabDefaultsKey =
    @"CrystalLattice.SessionsFollowActiveTabEnabled";

@interface AppDelegate ()

@property(nonatomic, strong) NSMenuItem *toolbarTabsMenuItem;
@property(nonatomic, strong) NSMenuItem *codeTabsMenuItem;
@property(nonatomic, strong) NSMenuItem *underlineTabsMenuItem;
@property(nonatomic, strong) NSMenuItem *roundedPillsMenuItem;

@property(nonatomic, strong) NSMenuItem *sessionsFollowActiveTabMenuItem;

@property(nonatomic, strong) NSMutableArray<NSWindow *> *mainWindows;
@property(nonatomic, assign) NSPoint mainWindowCascadePoint;

@end

@implementation AppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)notification
{
  self.moduleName = @"CrystalLatticeControlDesktopRN";
  NSString *tabStripStyle = [self loadTabStripStylePreference];
  BOOL followEnabled = [self loadSessionsFollowActiveTabEnabledPreference];
  self.initialProps = @{
    @"initialTabStripStyle" : tabStripStyle,
    @"initialSessionsFollowActiveTabEnabled" : @(followEnabled),
  };
  self.dependencyProvider = [RCTAppDependencyProvider new];

  [super applicationDidFinishLaunching:notification];

  // Track the initial main window created by RCTAppDelegate so we can:
  // - release it when closed (so closing the window truly closes it)
  // - reopen / create windows when the Dock icon is clicked
  // - support opening additional main windows
  [self ensureMainWindowsTrackingInitialized];
  [self trackMainWindowIfNeeded:(NSWindow *)self.window];

  [self installTabStripStyleMenuWithSelectedStyle:tabStripStyle];
  [self installSessionsFollowActiveTabMenuWithEnabled:followEnabled];
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

- (void)saveSessionsFollowActiveTabEnabledPreference:(BOOL)enabled
{
  [[NSUserDefaults standardUserDefaults] setBool:enabled forKey:kSessionsFollowActiveTabDefaultsKey];
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
