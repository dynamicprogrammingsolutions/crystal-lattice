#import "DesktopWindowManager.h"
#import "DesktopMenuNotifications.h"

#import <Cocoa/Cocoa.h>
#import <React/RCTBridge.h>
#import <React/RCTRootView.h>
#import <objc/message.h>
#import <math.h>

@interface DesktopWindowManager () <NSPopoverDelegate>

@property(nonatomic, strong) NSWindow *connectionEditorWindow;
@property(nonatomic, strong) NSWindow *agentPickerWindow;
@property(nonatomic, strong) NSWindow *applicationActionDialogWindow;
@property(nonatomic, strong) NSMutableDictionary<NSString *, NSWindow *> *reactWindowsByKey;
@property(nonatomic, strong) NSMapTable<NSWindow *, NSString *> *reactWindowKeysByWindow;
@property(nonatomic, strong) NSPopover *applicationActionDialogPopover;
@property(nonatomic, strong) NSPopover *closingApplicationActionDialogPopover;
@property(nonatomic, strong) NSPopover *actionsPopover;
@property(nonatomic, copy) NSString *actionsPopoverMenuId;
@property(nonatomic, assign) CGFloat actionsPopoverMaxHeight;
@property(nonatomic, strong) NSPopover *messageLimitPopover;

@property(nonatomic, assign) BOOL suppressApplicationActionDialogPopoverCancel;

@end

@implementation DesktopWindowManager

RCT_EXPORT_MODULE();

- (instancetype)init
{
  if (self = [super init]) {
    _reactWindowsByKey = [[NSMutableDictionary alloc] init];
    _reactWindowKeysByWindow = [NSMapTable weakToStrongObjectsMapTable];
    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(handleApplicationWillHide:)
                                                 name:NSApplicationWillHideNotification
                                               object:nil];

    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(handleApplicationDidUnhide:)
                                                 name:NSApplicationDidUnhideNotification
                                               object:nil];
  }
  return self;
}

- (void)dealloc
{
  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:NSApplicationWillHideNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:NSApplicationDidUnhideNotification
                                                object:nil];
}

+ (BOOL)requiresMainQueueSetup
{
  return YES;
}

- (NSArray<NSString *> *)supportedEvents
{
  return @[ @"connectionEditorSaved", @"connectionEditorCancelled", @"agentPickerSelected", @"agentPickerCancelled", @"applicationActionDialogCancelled", @"reactWindowCancelled", @"tabStripStyleChanged", @"sessionsFollowActiveTabChanged", @"switchConnectionWithActiveTabChanged", @"markdownBaseFontSizeChanged", @"markdownHeaderSizeChanged", @"recentSessionsWindowChanged", @"sessionDoubleClickActionChanged", @"timeTrackingEnabledChanged", @"timeTrackingPluginIdChanged", @"timeTrackingInactivitySecondsChanged", @"clearStoredSessionCachesRequested", @"systemThemeChanged", @"progressiveScrollHarnessCommand" ];
}

- (void)startObserving
{
  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleTabStripStyleDidChange:)
                                               name:CLCTabStripStyleDidChangeNotification
                                             object:nil];

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleSessionsFollowActiveTabDidChange:)
                                               name:CLCSessionsFollowActiveTabDidChangeNotification
                                             object:nil];

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleSwitchConnectionWithActiveTabDidChange:)
                                               name:CLCSwitchConnectionWithActiveTabDidChangeNotification
                                             object:nil];

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleMarkdownBaseFontSizeDidChange:)
                                               name:CLCMarkdownBaseFontSizeDidChangeNotification
                                             object:nil];

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleMarkdownHeaderSizeDidChange:)
                                               name:CLCMarkdownHeaderSizeDidChangeNotification
                                             object:nil];

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleClearStoredSessionCaches:)
                                               name:CLCClearStoredSessionCachesNotification
                                             object:nil];

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleOpenGlobalSettings:)
                                               name:CLCOpenGlobalSettingsNotification
                                             object:nil];

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleRecentSessionsWindowDidChange:)
                                               name:CLCRecentSessionsWindowDidChangeNotification
                                             object:nil];

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleSessionDoubleClickActionDidChange:)
                                               name:CLCSessionDoubleClickActionDidChangeNotification
                                             object:nil];

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleTimeTrackingEnabledDidChange:)
                                               name:CLCTimeTrackingEnabledDidChangeNotification
                                             object:nil];

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleTimeTrackingPluginIdDidChange:)
                                               name:CLCTimeTrackingPluginIdDidChangeNotification
                                             object:nil];

  [[NSNotificationCenter defaultCenter]
      addObserver:self
         selector:@selector(handleTimeTrackingInactivitySecondsDidChange:)
             name:CLCTimeTrackingInactivitySecondsDidChangeNotification
           object:nil];

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleProgressiveScrollHarnessCommand:)
                                               name:CLCProgressiveScrollHarnessCommandNotification
                                             object:nil];

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleOpenNotificationTesting:)
                                               name:CLCOpenNotificationTestingNotification
                                             object:nil];

  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleSystemColorsDidChange:)
                                               name:@"NSSystemColorsDidChangeNotification"
                                             object:nil];

  [[NSDistributedNotificationCenter defaultCenter]
      addObserver:self
         selector:@selector(handleAppleInterfaceThemeDidChangeDistributed:)
             name:@"AppleInterfaceThemeChangedNotification"
           object:nil
  suspensionBehavior:NSNotificationSuspensionBehaviorDeliverImmediately];
}

- (void)stopObserving
{
  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:CLCTabStripStyleDidChangeNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:CLCSessionsFollowActiveTabDidChangeNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:CLCSwitchConnectionWithActiveTabDidChangeNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:CLCMarkdownBaseFontSizeDidChangeNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:CLCMarkdownHeaderSizeDidChangeNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:CLCClearStoredSessionCachesNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:CLCOpenGlobalSettingsNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:CLCRecentSessionsWindowDidChangeNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:CLCSessionDoubleClickActionDidChangeNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:CLCTimeTrackingEnabledDidChangeNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:CLCTimeTrackingPluginIdDidChangeNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter]
      removeObserver:self
                name:CLCTimeTrackingInactivitySecondsDidChangeNotification
              object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:CLCProgressiveScrollHarnessCommandNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:CLCOpenNotificationTestingNotification
                                                object:nil];

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:@"NSSystemColorsDidChangeNotification"
                                                object:nil];

  [[NSDistributedNotificationCenter defaultCenter] removeObserver:self
                                                            name:@"AppleInterfaceThemeChangedNotification"
                                                          object:nil];
}

- (void)handleApplicationWillHide:(NSNotification *)notification
{
  dispatch_async(dispatch_get_main_queue(), ^{
    NSLog(@"[DesktopWindowManager] NSApplicationWillHide: closing transient popovers/windows");
    [self closeActionsPopover];
    [self closeMessageLimitPopover];
    [self closeApplicationActionDialogPopover];
    [self closeApplicationActionDialogWindow];
  });
}

- (void)handleApplicationDidUnhide:(NSNotification *)notification
{
  dispatch_async(dispatch_get_main_queue(), ^{
    NSLog(@"[DesktopWindowManager] NSApplicationDidUnhide");
  });
}

- (void)handleTabStripStyleDidChange:(NSNotification *)notification
{
  NSString *style = notification.userInfo[CLCTabStripStyleUserInfoKey];
  if (![style isKindOfClass:[NSString class]]) {
    return;
  }
  [self sendEventWithName:@"tabStripStyleChanged" body:@{ @"style" : style }];
}

- (void)handleSessionsFollowActiveTabDidChange:(NSNotification *)notification
{
  id enabled = notification.userInfo[CLCSessionsFollowActiveTabEnabledUserInfoKey];
  BOOL resolved = NO;
  if ([enabled isKindOfClass:[NSNumber class]]) {
    resolved = [enabled boolValue];
  } else {
    resolved = NO;
  }
  [self sendEventWithName:@"sessionsFollowActiveTabChanged" body:@{ @"enabled" : @(resolved) }];
}

- (void)handleSwitchConnectionWithActiveTabDidChange:(NSNotification *)notification
{
  id enabled =
      notification.userInfo[CLCSwitchConnectionWithActiveTabEnabledUserInfoKey];
  BOOL resolved = NO;
  if ([enabled isKindOfClass:[NSNumber class]]) {
    resolved = [enabled boolValue];
  }
  [self sendEventWithName:@"switchConnectionWithActiveTabChanged"
                     body:@{ @"enabled" : @(resolved) }];
}

- (void)handleMarkdownBaseFontSizeDidChange:(NSNotification *)notification
{
  NSNumber *baseFontSize = notification.userInfo[CLCMarkdownBaseFontSizeUserInfoKey];
  if (![baseFontSize isKindOfClass:[NSNumber class]]) {
    return;
  }
  [self sendEventWithName:@"markdownBaseFontSizeChanged"
                     body:@{ @"baseFontSize" : baseFontSize }];
}

- (void)handleMarkdownHeaderSizeDidChange:(NSNotification *)notification
{
  NSString *headerSize = notification.userInfo[CLCMarkdownHeaderSizeUserInfoKey];
  if (![headerSize isKindOfClass:[NSString class]]) {
    return;
  }
  [self sendEventWithName:@"markdownHeaderSizeChanged"
                     body:@{ @"headerSize" : headerSize }];
}

- (void)handleClearStoredSessionCaches:(__unused NSNotification *)notification
{
  [self sendEventWithName:@"clearStoredSessionCachesRequested" body:@{}];
}

- (void)handleOpenGlobalSettings:(__unused NSNotification *)notification
{
  [self openReactWindow:@{
    @"windowKey" : @"globalSettings",
    @"moduleName" : @"GlobalSettingsWindow",
    @"title" : @"Settings",
    @"width" : @560,
    @"height" : @680,
    @"initialProps" : @{},
  }];
}

- (void)handleRecentSessionsWindowDidChange:(NSNotification *)notification
{
  NSString *value =
      notification.userInfo[CLCRecentSessionsWindowUserInfoKey];
  if (![value isKindOfClass:[NSString class]]) {
    return;
  }
  [self sendEventWithName:@"recentSessionsWindowChanged"
                     body:@{ @"recentSessionsWindow" : value }];
}

- (void)handleSessionDoubleClickActionDidChange:(NSNotification *)notification
{
  NSString *value =
      notification.userInfo[CLCSessionDoubleClickActionUserInfoKey];
  if (![value isKindOfClass:[NSString class]]) {
    return;
  }
  [self sendEventWithName:@"sessionDoubleClickActionChanged"
                     body:@{ @"sessionDoubleClickAction" : value }];
}

- (void)handleTimeTrackingEnabledDidChange:(NSNotification *)notification
{
  id enabled = notification.userInfo[CLCTimeTrackingEnabledUserInfoKey];
  if (![enabled isKindOfClass:[NSNumber class]]) {
    return;
  }
  [self sendEventWithName:@"timeTrackingEnabledChanged"
                     body:@{ @"enabled" : @([enabled boolValue]) }];
}

- (void)handleTimeTrackingPluginIdDidChange:(NSNotification *)notification
{
  NSString *pluginId = notification.userInfo[CLCTimeTrackingPluginIdUserInfoKey];
  if (![pluginId isKindOfClass:[NSString class]]) {
    return;
  }
  [self sendEventWithName:@"timeTrackingPluginIdChanged"
                     body:@{ @"pluginId" : pluginId }];
}

- (void)handleTimeTrackingInactivitySecondsDidChange:(NSNotification *)notification
{
  id seconds =
      notification.userInfo[CLCTimeTrackingInactivitySecondsUserInfoKey];
  if (![seconds isKindOfClass:[NSNumber class]]) {
    return;
  }
  [self sendEventWithName:@"timeTrackingInactivitySecondsChanged"
                     body:@{ @"seconds" : seconds }];
}

- (void)handleOpenNotificationTesting:(__unused NSNotification *)notification
{
  [self openReactWindow:@{
    @"windowKey" : @"notificationTesting",
    @"moduleName" : @"NotificationTestingWindow",
    @"title" : @"Notification Testing",
    @"width" : @560,
    @"height" : @640,
    @"initialProps" : @{},
  }];
}

- (void)handleProgressiveScrollHarnessCommand:(NSNotification *)notification
{
  NSString *command = notification.userInfo[CLCProgressiveScrollHarnessCommandUserInfoKey];
  if (![command isKindOfClass:[NSString class]]) {
    return;
  }
  id postedAtMs = notification.userInfo[@"postedAtMs"];
  id runId = notification.userInfo[@"runId"];
  NSMutableDictionary *body = [@{ @"command" : command } mutableCopy];
  if ([postedAtMs isKindOfClass:[NSNumber class]]) {
    body[@"postedAtMs"] = postedAtMs;
  }
  if ([runId isKindOfClass:[NSString class]]) {
    body[@"runId"] = runId;
  }
  [self sendEventWithName:@"progressiveScrollHarnessCommand" body:body];
}

RCT_EXPORT_METHOD(recordProgressiveScrollHarnessState:(NSDictionary *)state)
{
  NSMutableDictionary *payload = [NSMutableDictionary dictionary];
  if ([state isKindOfClass:[NSDictionary class]]) {
    [payload addEntriesFromDictionary:state];
  }
  payload[@"recordedAtMs"] = @((long long)([[NSDate date] timeIntervalSince1970] * 1000));

  NSError *error = nil;
  NSData *data = [NSJSONSerialization dataWithJSONObject:payload options:0 error:&error];
  if (data == nil || error != nil) {
    return;
  }
  [data writeToFile:@"/tmp/clc-progressive-scroll-harness-state.json" atomically:YES];
}

RCT_EXPORT_METHOD(recordMarkdownGeometryHarnessState:(NSDictionary *)state)
{
  NSMutableDictionary *payload = [NSMutableDictionary dictionary];
  if ([state isKindOfClass:[NSDictionary class]]) {
    [payload addEntriesFromDictionary:state];
  }
  payload[@"recordedAtMs"] = @((long long)([[NSDate date] timeIntervalSince1970] * 1000));

  NSError *error = nil;
  NSData *data = [NSJSONSerialization dataWithJSONObject:payload options:0 error:&error];
  if (data == nil || error != nil) {
    return;
  }
  [data writeToFile:@"/tmp/clc-markdown-geometry-harness-state.json" atomically:YES];
}

RCT_EXPORT_METHOD(recordConnectionsPanelHarnessState:(NSDictionary *)state)
{
  NSMutableDictionary *payload = [NSMutableDictionary dictionary];
  if ([state isKindOfClass:[NSDictionary class]]) {
    [payload addEntriesFromDictionary:state];
  }
  payload[@"recordedAtMs"] = @((long long)([[NSDate date] timeIntervalSince1970] * 1000));

  NSError *error = nil;
  NSData *data = [NSJSONSerialization dataWithJSONObject:payload options:0 error:&error];
  if (data == nil || error != nil) {
    return;
  }
  [data writeToFile:@"/tmp/clc-connections-panel-harness-state.json" atomically:YES];
}

RCT_EXPORT_METHOD(recordDesktopWorkspaceHarnessState:(NSDictionary *)state)
{
  NSMutableDictionary *payload = [NSMutableDictionary dictionary];
  if ([state isKindOfClass:[NSDictionary class]]) {
    [payload addEntriesFromDictionary:state];
  }
  payload[@"recordedAtMs"] =
      @((long long)([[NSDate date] timeIntervalSince1970] * 1000));

  NSError *error = nil;
  NSData *data =
      [NSJSONSerialization dataWithJSONObject:payload options:0 error:&error];
  if (data == nil || error != nil) {
    return;
  }
  [data writeToFile:@"/tmp/clc-desktop-workspace-harness-state.json"
         atomically:YES];
}

RCT_EXPORT_METHOD(readProgressiveScrollHarnessCommand:(RCTPromiseResolveBlock)resolve
                  rejecter:(__unused RCTPromiseRejectBlock)reject)
{
  NSData *data = [NSData dataWithContentsOfFile:@"/tmp/clc-progressive-scroll-harness-command.json"];
  if (data == nil) {
    resolve((id)kCFNull);
    return;
  }

  NSDictionary *payload = [NSJSONSerialization JSONObjectWithData:data options:0 error:nil];
  if (![payload isKindOfClass:[NSDictionary class]]) {
    resolve((id)kCFNull);
    return;
  }

  resolve(payload);
}

- (void)handleSystemColorsDidChange:(NSNotification *)notification
{
  [self emitSystemThemeChanged];
}

- (void)handleAppleInterfaceThemeDidChangeDistributed:(NSNotification *)notification
{
  [self emitSystemThemeChanged];
}

static id CLCPreferredAppearanceObject(NSString *appearance)
{
  NSString *name = [appearance isEqualToString:@"dark"] ? @"NSAppearanceNameDarkAqua" : @"NSAppearanceNameAqua";
  Class appearanceClass = NSClassFromString(@"NSAppearance");
  SEL selector = NSSelectorFromString(@"appearanceNamed:");
  if (appearanceClass != Nil && [appearanceClass respondsToSelector:selector]) {
    using MsgSendType = id (*)(id, SEL, NSString *);
    return ((MsgSendType)objc_msgSend)(appearanceClass, selector, name);
  }
  return nil;
}

typedef void (^CLCNoArgBlock)(void);

static void CLCPerformAsCurrentDrawingAppearance(id appearance, CLCNoArgBlock block)
{
  if (appearance == nil || block == nil) {
    if (block != nil) {
      block();
    }
    return;
  }

  SEL selector = NSSelectorFromString(@"performAsCurrentDrawingAppearance:");
  if ([appearance respondsToSelector:selector]) {
    using MsgSendType = void (*)(id, SEL, CLCNoArgBlock);
    ((MsgSendType)objc_msgSend)(appearance, selector, block);
    return;
  }

  block();
}

static NSString *CLCColorToString(NSColor *color, id appearance)
{
  if (color == nil) {
    return @"#000000";
  }

  __block CGFloat r = 0;
  __block CGFloat g = 0;
  __block CGFloat b = 0;
  __block CGFloat a = 1;

  CLCPerformAsCurrentDrawingAppearance(appearance, ^{
    NSColor *srgb = [color colorUsingColorSpace:[NSColorSpace sRGBColorSpace]];
    if (srgb == nil) {
      srgb = color;
    }
    [srgb getRed:&r green:&g blue:&b alpha:&a];
  });

  int ri = (int)lround(r * 255.0);
  int gi = (int)lround(g * 255.0);
  int bi = (int)lround(b * 255.0);
  ri = MAX(0, MIN(255, ri));
  gi = MAX(0, MIN(255, gi));
  bi = MAX(0, MIN(255, bi));

  if (a >= 0.999) {
    return [NSString stringWithFormat:@"#%02X%02X%02X", ri, gi, bi];
  }

  return [NSString stringWithFormat:@"rgba(%d, %d, %d, %.3f)", ri, gi, bi, a];
}

static NSString *CLCSystemAppearance(void)
{
  NSString *interfaceStyle = [[NSUserDefaults standardUserDefaults] stringForKey:@"AppleInterfaceStyle"];
  if ([interfaceStyle isKindOfClass:[NSString class]] && interfaceStyle.length > 0) {
    if ([[interfaceStyle lowercaseString] containsString:@"dark"]) {
      return @"dark";
    }
  }
  return @"light";
}

static NSColor *CLCSystemColor(NSString *selectorName, NSColor *fallback)
{
  SEL selector = NSSelectorFromString(selectorName);
  if ([NSColor respondsToSelector:selector]) {
    using MsgSendType = NSColor *(*)(id, SEL);
    return ((MsgSendType)objc_msgSend)(NSColor.class, selector);
  }
  return fallback;
}

- (NSDictionary *)currentSystemThemePayload
{
  NSString *appearance = CLCSystemAppearance();
  id preferredAppearance = CLCPreferredAppearanceObject(appearance);

  return @{
    @"appearance" : appearance,
    @"accent" : CLCColorToString(CLCSystemColor(@"controlAccentColor", [NSColor blueColor]), preferredAppearance),
    @"windowBackground" : CLCColorToString(CLCSystemColor(@"windowBackgroundColor", [NSColor windowBackgroundColor]), preferredAppearance),
    @"controlBackground" : CLCColorToString(CLCSystemColor(@"controlBackgroundColor", [NSColor controlColor]), preferredAppearance),
    @"separator" : CLCColorToString(CLCSystemColor(@"separatorColor", [NSColor lightGrayColor]), preferredAppearance),
    @"text" : CLCColorToString(CLCSystemColor(@"labelColor", [NSColor textColor]), preferredAppearance),
    @"textSecondary" : CLCColorToString(CLCSystemColor(@"secondaryLabelColor", [NSColor disabledControlTextColor]), preferredAppearance),
    @"textMuted" : CLCColorToString(CLCSystemColor(@"tertiaryLabelColor", [NSColor disabledControlTextColor]), preferredAppearance),
    @"danger" : CLCColorToString(CLCSystemColor(@"systemRedColor", [NSColor redColor]), preferredAppearance),
    @"success" : CLCColorToString(CLCSystemColor(@"systemGreenColor", [NSColor greenColor]), preferredAppearance),
    @"warning" : CLCColorToString(CLCSystemColor(@"systemYellowColor", [NSColor yellowColor]), preferredAppearance),
    @"notification" : CLCColorToString(CLCSystemColor(@"systemBlueColor", [NSColor blueColor]), preferredAppearance),
  };
}
- (void)emitSystemThemeChanged
{
  dispatch_async(dispatch_get_main_queue(), ^{
    NSDictionary *payload = [self currentSystemThemePayload];
    [self sendEventWithName:@"systemThemeChanged" body:payload];
  });
}

RCT_EXPORT_METHOD(getSystemTheme : (RCTPromiseResolveBlock)resolve rejecter : (RCTPromiseRejectBlock)reject)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    @try {
      resolve([self currentSystemThemePayload]);
    } @catch (NSException *exception) {
      reject(@"system_theme_error", exception.reason ?: @"Failed to read system theme", nil);
    }
  });
}

RCT_EXPORT_METHOD(openConnectionEditor : (NSDictionary *)params)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    if (self.connectionEditorWindow != nil) {
      [self.connectionEditorWindow makeKeyAndOrderFront:nil];
      return;
    }

    NSDictionary *initialProps = params ?: @{};
    NSView *rootView = nil;
    id appDelegate = NSApp.delegate;
    id rootViewFactory = nil;
    @try {
      rootViewFactory = [appDelegate valueForKey:@"rootViewFactory"];
    } @catch (__unused NSException *exception) {
      rootViewFactory = nil;
    }
    if (rootViewFactory != nil) {
      SEL selector = NSSelectorFromString(@"viewWithModuleName:initialProperties:");
      if ([rootViewFactory respondsToSelector:selector]) {
        using MsgSendType = NSView *(*)(id, SEL, NSString *, NSDictionary *);
        rootView = ((MsgSendType)objc_msgSend)(
            rootViewFactory,
            selector,
            @"ConnectionEditorWindow",
            initialProps);
      }
    }

    if (rootView == nil) {
      rootView =
          [[RCTRootView alloc] initWithBridge:self.bridge moduleName:@"ConnectionEditorWindow" initialProperties:initialProps];
    }

    NSRect frame = NSMakeRect(0, 0, 420, 320);
    NSWindow *window = [[NSWindow alloc] initWithContentRect:frame
                                                   styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable
                                                     backing:NSBackingStoreBuffered
                                                       defer:NO];
    window.title = @"Connection";
    window.accessibilityIdentifier = @"connectionEditorWindow";
    window.accessibilityLabel = @"connectionEditorWindow";
	    rootView.frame = frame;
	    rootView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
	    window.contentView = rootView;
    window.releasedWhenClosed = NO;

    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(connectionEditorWindowWillClose:)
                                                 name:NSWindowWillCloseNotification
                                               object:window];

    self.connectionEditorWindow = window;
    [window center];
    [window makeKeyAndOrderFront:nil];
  });
}

RCT_EXPORT_METHOD(openAgentPicker : (NSDictionary *)params)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    if (self.agentPickerWindow != nil) {
      [self.agentPickerWindow makeKeyAndOrderFront:nil];
      return;
    }

    NSDictionary *initialProps = params ?: @{};
    NSView *rootView = nil;
    id appDelegate = NSApp.delegate;
    id rootViewFactory = nil;
    @try {
      rootViewFactory = [appDelegate valueForKey:@"rootViewFactory"];
    } @catch (__unused NSException *exception) {
      rootViewFactory = nil;
    }
    if (rootViewFactory != nil) {
      SEL selector = NSSelectorFromString(@"viewWithModuleName:initialProperties:");
      if ([rootViewFactory respondsToSelector:selector]) {
        using MsgSendType = NSView *(*)(id, SEL, NSString *, NSDictionary *);
        rootView = ((MsgSendType)objc_msgSend)(
            rootViewFactory,
            selector,
            @"AgentPickerWindow",
            initialProps);
      }
    }

    if (rootView == nil) {
      rootView =
          [[RCTRootView alloc] initWithBridge:self.bridge moduleName:@"AgentPickerWindow" initialProperties:initialProps];
    }

    NSRect frame = NSMakeRect(0, 0, 900, 620);
    NSWindow *window = [[NSWindow alloc] initWithContentRect:frame
                                                   styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable
                                                     backing:NSBackingStoreBuffered
                                                       defer:NO];
    NSString *title = nil;
    if ([params[@"title"] isKindOfClass:[NSString class]]) {
      title = params[@"title"];
    }
    window.title = title ?: @"New Session";
    window.minSize = NSMakeSize(720, 480);
    rootView.frame = frame;
    rootView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
    window.contentView = rootView;
    window.releasedWhenClosed = NO;

    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(agentPickerWindowWillClose:)
                                                 name:NSWindowWillCloseNotification
                                               object:window];

    self.agentPickerWindow = window;
    [window center];
    [window makeKeyAndOrderFront:nil];
  });
}

RCT_EXPORT_METHOD(openApplicationActionDialogWindow : (NSDictionary *)params)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    NSLog(@"[DesktopWindowManager] openApplicationActionDialogWindow existing=%p", self.applicationActionDialogWindow);
    if (self.applicationActionDialogWindow != nil) {
      [self.applicationActionDialogWindow makeKeyAndOrderFront:nil];
      return;
    }

    NSDictionary *initialProps = @{ @"presentation" : @"window" };
    NSView *rootView = nil;
    id appDelegate = NSApp.delegate;
    id rootViewFactory = nil;
    @try {
      rootViewFactory = [appDelegate valueForKey:@"rootViewFactory"];
    } @catch (__unused NSException *exception) {
      rootViewFactory = nil;
    }
    if (rootViewFactory != nil) {
      SEL selector = NSSelectorFromString(@"viewWithModuleName:initialProperties:");
      if ([rootViewFactory respondsToSelector:selector]) {
        using MsgSendType = NSView *(*)(id, SEL, NSString *, NSDictionary *);
        rootView = ((MsgSendType)objc_msgSend)(
            rootViewFactory,
            selector,
            @"ApplicationActionDialogWindow",
            initialProps);
      }
    }

    if (rootView == nil) {
      rootView =
          [[RCTRootView alloc] initWithBridge:self.bridge moduleName:@"ApplicationActionDialogWindow" initialProperties:initialProps];
    }

    NSRect frame = NSMakeRect(0, 0, 540, 520);
    NSWindow *window = [[NSWindow alloc] initWithContentRect:frame
                                                   styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable
                                                     backing:NSBackingStoreBuffered
                                                       defer:NO];
    NSString *title = nil;
    if ([params[@"title"] isKindOfClass:[NSString class]]) {
      title = params[@"title"];
    }
    window.title = title ?: @"Action";
    rootView.frame = frame;
    rootView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
    window.contentView = rootView;
    window.releasedWhenClosed = NO;

    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(applicationActionDialogWindowWillClose:)
                                                 name:NSWindowWillCloseNotification
                                               object:window];

    self.applicationActionDialogWindow = window;
    [window center];
    [window makeKeyAndOrderFront:nil];
  });
}

RCT_EXPORT_METHOD(openSessionSettingsWindow : (NSDictionary *)params)
{
  [self openReactWindow:@{
    @"windowKey": @"sessionSettings",
    @"moduleName": @"SessionSettingsWindow",
    @"title": [params[@"title"] isKindOfClass:[NSString class]] ? params[@"title"] : @"Session settings",
    @"width": @560,
    @"height": @640,
    @"initialProps": @{},
  }];
}

RCT_EXPORT_METHOD(closeSessionSettingsWindow)
{
  [self closeReactWindow:@{ @"windowKey": @"sessionSettings" }];
}

RCT_REMAP_METHOD(getDesktopGlobalSettings,
                 getDesktopGlobalSettingsWithResolver:(RCTPromiseResolveBlock)resolve
                 rejecter:(__unused RCTPromiseRejectBlock)reject)
{
  NSUserDefaults *defaults = [NSUserDefaults standardUserDefaults];
  NSInteger baseFontSize =
      [defaults integerForKey:@"CrystalLattice.MarkdownBaseFontSize"];
  if (baseFontSize != 14 && baseFontSize != 15 &&
      baseFontSize != 16 && baseFontSize != 17) {
    baseFontSize = 15;
  }
  NSString *headerSize =
      [defaults stringForKey:@"CrystalLattice.MarkdownHeaderSize"];
  if (![headerSize isEqualToString:@"normal"] &&
      ![headerSize isEqualToString:@"small"]) {
    headerSize = @"normal";
  }
  NSString *recentSessionsWindow =
      [defaults stringForKey:@"CrystalLattice.RecentSessionsWindow"];
  if (![recentSessionsWindow isEqualToString:@"24h"] &&
      ![recentSessionsWindow isEqualToString:@"3d"] &&
      ![recentSessionsWindow isEqualToString:@"1w"]) {
    recentSessionsWindow = @"3d";
  }
  NSString *sessionDoubleClickAction =
      [defaults stringForKey:@"CrystalLattice.SessionDoubleClickAction"];
  if (![sessionDoubleClickAction isEqualToString:@"preview"] &&
      ![sessionDoubleClickAction isEqualToString:@"open"]) {
    sessionDoubleClickAction = @"preview";
  }
  id rawSessionsFollowActiveTabEnabled =
      [defaults objectForKey:@"CrystalLattice.SessionsFollowActiveTabEnabled"];
  BOOL sessionsFollowActiveTabEnabled =
      rawSessionsFollowActiveTabEnabled == nil
      ? YES
      : [defaults boolForKey:@"CrystalLattice.SessionsFollowActiveTabEnabled"];
  BOOL switchConnectionWithActiveTabEnabled =
      [defaults boolForKey:@"CrystalLattice.SwitchConnectionWithActiveTabEnabled"];
  BOOL timeTrackingEnabled =
      [defaults boolForKey:@"CrystalLattice.TimeTrackingEnabled"];
  NSString *timeTrackingPluginId =
      [defaults stringForKey:@"CrystalLattice.TimeTrackingPluginId"];
  if (![timeTrackingPluginId isKindOfClass:[NSString class]] ||
      timeTrackingPluginId.length == 0) {
    timeTrackingPluginId = @"duration_tracking_app";
  }
  id rawTimeTrackingInactivitySeconds =
      [defaults objectForKey:@"CrystalLattice.TimeTrackingInactivitySeconds"];
  double timeTrackingInactivitySeconds =
      rawTimeTrackingInactivitySeconds == nil
      ? 30.0
      : [defaults doubleForKey:@"CrystalLattice.TimeTrackingInactivitySeconds"];
  if (!isfinite(timeTrackingInactivitySeconds) ||
      timeTrackingInactivitySeconds <= 0) {
    timeTrackingInactivitySeconds = 30.0;
  }
  resolve(@{
    @"baseFontSize" : @(baseFontSize),
    @"headerSize" : headerSize,
    @"recentSessionsWindow" : recentSessionsWindow,
    @"sessionDoubleClickAction" : sessionDoubleClickAction,
    @"sessionsFollowActiveTabEnabled" : @(sessionsFollowActiveTabEnabled),
    @"switchConnectionWithActiveTabEnabled" : @(switchConnectionWithActiveTabEnabled),
    @"timeTrackingEnabled" : @(timeTrackingEnabled),
    @"timeTrackingPluginId" : timeTrackingPluginId,
    @"timeTrackingInactivitySeconds" : @(timeTrackingInactivitySeconds),
  });
}

RCT_EXPORT_METHOD(setDesktopGlobalSetting:(NSDictionary *)params)
{
  if (![params[@"key"] isKindOfClass:[NSString class]]) {
    return;
  }
  id value = params[@"value"];
  if (value == nil || value == (id)kCFNull) {
    return;
  }
  [[NSNotificationCenter defaultCenter]
      postNotificationName:CLCDesktopGlobalSettingRequestedNotification
                    object:nil
                  userInfo:@{
                    CLCDesktopGlobalSettingKeyUserInfoKey : params[@"key"],
                    CLCDesktopGlobalSettingValueUserInfoKey : value,
                  }];
}

RCT_EXPORT_METHOD(openReactWindow : (NSDictionary *)params)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    if (![params[@"windowKey"] isKindOfClass:[NSString class]] || ![params[@"moduleName"] isKindOfClass:[NSString class]]) {
      return;
    }

    NSString *windowKey = (NSString *)params[@"windowKey"];
    NSString *moduleName = (NSString *)params[@"moduleName"];

    NSWindow *existing = self.reactWindowsByKey[windowKey];
    if (existing != nil) {
      [existing makeKeyAndOrderFront:nil];
      return;
    }

    NSDictionary *initialProps = @{};
    if ([params[@"initialProps"] isKindOfClass:[NSDictionary class]]) {
      initialProps = (NSDictionary *)params[@"initialProps"];
    }

    NSView *rootView = nil;
    id appDelegate = NSApp.delegate;
    id rootViewFactory = nil;
    @try {
      rootViewFactory = [appDelegate valueForKey:@"rootViewFactory"];
    } @catch (__unused NSException *exception) {
      rootViewFactory = nil;
    }
    if (rootViewFactory != nil) {
      SEL selector = NSSelectorFromString(@"viewWithModuleName:initialProperties:");
      if ([rootViewFactory respondsToSelector:selector]) {
        using MsgSendType = NSView *(*)(id, SEL, NSString *, NSDictionary *);
        rootView = ((MsgSendType)objc_msgSend)(rootViewFactory, selector, moduleName, initialProps);
      }
    }
    if (rootView == nil) {
      rootView = [[RCTRootView alloc] initWithBridge:self.bridge moduleName:moduleName initialProperties:initialProps];
    }

    CGFloat width = 560;
    CGFloat height = 640;
    if ([params[@"width"] respondsToSelector:@selector(doubleValue)]) {
      width = (CGFloat)[params[@"width"] doubleValue];
    }
    if ([params[@"height"] respondsToSelector:@selector(doubleValue)]) {
      height = (CGFloat)[params[@"height"] doubleValue];
    }
    NSRect frame = NSMakeRect(0, 0, width, height);
    NSWindow *window = [[NSWindow alloc] initWithContentRect:frame
                                                   styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable
                                                     backing:NSBackingStoreBuffered
                                                       defer:NO];

    NSString *title = nil;
    if ([params[@"title"] isKindOfClass:[NSString class]]) {
      title = (NSString *)params[@"title"];
    }
    window.title = title ?: moduleName;
    window.accessibilityIdentifier = [NSString stringWithFormat:@"%@Window", windowKey];
    window.accessibilityLabel = windowKey;
    rootView.frame = frame;
    rootView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
    window.contentView = rootView;
    window.releasedWhenClosed = NO;

    [[NSNotificationCenter defaultCenter] addObserver:self
                                             selector:@selector(reactWindowWillClose:)
                                                 name:NSWindowWillCloseNotification
                                               object:window];

    self.reactWindowsByKey[windowKey] = window;
    [self.reactWindowKeysByWindow setObject:windowKey forKey:window];

    [window center];
    [window makeKeyAndOrderFront:nil];
  });
}

RCT_EXPORT_METHOD(closeReactWindow : (NSDictionary *)params)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    if (![params[@"windowKey"] isKindOfClass:[NSString class]]) {
      return;
    }
    NSString *windowKey = (NSString *)params[@"windowKey"];
    NSWindow *window = self.reactWindowsByKey[windowKey];
    if (window == nil) {
      return;
    }
    [window close];
  });
}

RCT_EXPORT_METHOD(openApplicationActionDialogPopover : (NSDictionary *)params)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    NSLog(@"[DesktopWindowManager] openApplicationActionDialogPopover existing=%p shown=%d", self.applicationActionDialogPopover, self.applicationActionDialogPopover != nil ? self.applicationActionDialogPopover.isShown : 0);
    if (self.applicationActionDialogPopover != nil && self.applicationActionDialogPopover.isShown) {
      self.suppressApplicationActionDialogPopoverCancel = YES;
      self.closingApplicationActionDialogPopover = self.applicationActionDialogPopover;
      [self.applicationActionDialogPopover performClose:nil];
      self.applicationActionDialogPopover = nil;
    }

    NSNumber *anchorTag = params[@"anchorTag"];
    NSView *sourceView = nil;
    if ([anchorTag isKindOfClass:[NSNumber class]]) {
      sourceView = [self.viewRegistry_DEPRECATED viewForReactTag:anchorTag];
    }
    if (sourceView == nil) {
      sourceView = NSApp.keyWindow.contentView;
    }
    if (sourceView == nil) {
      return;
    }

    CGFloat width = 460;
    CGFloat height = 420;
    if ([params[@"width"] respondsToSelector:@selector(doubleValue)]) {
      width = (CGFloat)[params[@"width"] doubleValue];
    }
    if ([params[@"height"] respondsToSelector:@selector(doubleValue)]) {
      height = (CGFloat)[params[@"height"] doubleValue];
    }

    NSDictionary *initialProps = @{ @"presentation" : @"popover" };
    NSView *rootView = nil;
    id appDelegate = NSApp.delegate;
    id rootViewFactory = nil;
    @try {
      rootViewFactory = [appDelegate valueForKey:@"rootViewFactory"];
    } @catch (__unused NSException *exception) {
      rootViewFactory = nil;
    }
    if (rootViewFactory != nil) {
      SEL selector = NSSelectorFromString(@"viewWithModuleName:initialProperties:");
      if ([rootViewFactory respondsToSelector:selector]) {
        using MsgSendType = NSView *(*)(id, SEL, NSString *, NSDictionary *);
        rootView = ((MsgSendType)objc_msgSend)(
            rootViewFactory,
            selector,
            @"ApplicationActionDialogWindow",
            initialProps);
      }
    }
    if (rootView == nil) {
      rootView =
          [[RCTRootView alloc] initWithBridge:self.bridge moduleName:@"ApplicationActionDialogWindow" initialProperties:initialProps];
    }

    rootView.frame = NSMakeRect(0, 0, width, height);
    rootView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;

    NSViewController *controller = [[NSViewController alloc] init];
    controller.view = rootView;

    NSPopover *popover = [[NSPopover alloc] init];
    popover.behavior = NSPopoverBehaviorTransient;
    popover.contentViewController = controller;
    popover.contentSize = NSMakeSize(width, height);
    popover.delegate = (id<NSPopoverDelegate>)self;

    self.applicationActionDialogPopover = popover;

    NSRect anchorRect = sourceView.bounds;
    if (![anchorTag isKindOfClass:[NSNumber class]]) {
      anchorRect = NSMakeRect(NSMidX(anchorRect), NSMidY(anchorRect), 1, 1);
    }

    [popover showRelativeToRect:anchorRect ofView:sourceView preferredEdge:NSRectEdgeMaxY];
  });
}

RCT_EXPORT_METHOD(closeApplicationActionDialogPopover)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    NSLog(@"[DesktopWindowManager] closeApplicationActionDialogPopover existing=%p", self.applicationActionDialogPopover);
    if (self.applicationActionDialogPopover == nil) {
      return;
    }

    self.suppressApplicationActionDialogPopoverCancel = YES;
    self.closingApplicationActionDialogPopover = self.applicationActionDialogPopover;
    self.applicationActionDialogPopover = nil;
    [self.closingApplicationActionDialogPopover performClose:nil];
  });
}

RCT_EXPORT_METHOD(closeApplicationActionDialogWindow)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    NSLog(@"[DesktopWindowManager] closeApplicationActionDialogWindow existing=%p", self.applicationActionDialogWindow);
    if (self.applicationActionDialogWindow == nil) {
      return;
    }
    [[NSNotificationCenter defaultCenter] removeObserver:self
                                                    name:NSWindowWillCloseNotification
                                                  object:self.applicationActionDialogWindow];
    [self.applicationActionDialogWindow close];
    self.applicationActionDialogWindow = nil;
  });
}

RCT_EXPORT_METHOD(toggleActionsPopover : (NSDictionary *)params)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    if (self.actionsPopover != nil && self.actionsPopover.isShown) {
      [self.actionsPopover performClose:nil];
      self.actionsPopover = nil;
      return;
    }

    NSNumber *anchorTag = params[@"anchorTag"];
    NSView *sourceView = nil;
    if ([anchorTag isKindOfClass:[NSNumber class]]) {
      sourceView = [self.viewRegistry_DEPRECATED viewForReactTag:anchorTag];
    }
    if (sourceView == nil) {
      sourceView = NSApp.keyWindow.contentView;
    }
    if (sourceView == nil) {
      return;
    }

    CGFloat width = 320;
    CGFloat height = 320;
    if ([params[@"width"] respondsToSelector:@selector(doubleValue)]) {
      width = (CGFloat)[params[@"width"] doubleValue];
    }
    if ([params[@"height"] respondsToSelector:@selector(doubleValue)]) {
      height = (CGFloat)[params[@"height"] doubleValue];
    }

    // Measure with the system font used by the React action rows. Leave room
    // for their padding, optional icon, state value, and independent pin target.
    NSArray *rows = params[@"rows"];
    if ([rows isKindOfClass:[NSArray class]]) {
      CGFloat fontSize = [params[@"fontSize"] doubleValue];
      CGFloat stateFontSize = [params[@"stateFontSize"] doubleValue];
      NSFont *font = [NSFont systemFontOfSize:fontSize > 0 ? fontSize : 15];
      NSFont *stateFont = [NSFont systemFontOfSize:stateFontSize > 0 ? stateFontSize : 13];
      for (NSDictionary *row in rows) {
        NSString *label = row[@"label"];
        NSString *stateLabel = row[@"stateLabel"];
        CGFloat rowWidth = 24 + 44 + ([row[@"hasIcon"] boolValue] ? 42 : 0);
        rowWidth += [label sizeWithAttributes:@{NSFontAttributeName: font}].width;
        if ([stateLabel isKindOfClass:[NSString class]] && stateLabel.length > 0) {
          rowWidth += 12 + [stateLabel sizeWithAttributes:@{NSFontAttributeName: stateFont}].width;
        }
        width = MAX(width, ceil(rowWidth) + 2);
      }
    }
    NSRect visibleFrame = (sourceView.window.screen ?: NSScreen.mainScreen).visibleFrame;
    CGFloat availableWidth = MIN(visibleFrame.size.width, sourceView.window.contentView.bounds.size.width);
    width = MIN(width, MIN(480, MAX(1, availableWidth - 32)));
    self.actionsPopoverMaxHeight = floor(visibleFrame.size.height * 0.8);
    height = MIN(height, self.actionsPopoverMaxHeight);
    self.actionsPopoverMenuId = params[@"menuId"];

    NSDictionary *initialProps = @{};
    NSDictionary *environment = [NSProcessInfo processInfo].environment;
    NSString *captureAppearance = environment[@"CLC_WEBSITE_VISUAL_THEME"];
    if ([environment[@"CLC_ENABLE_WEBSITE_VISUAL_HARNESS"] isEqualToString:@"1"] &&
        ([captureAppearance isEqualToString:@"light"] || [captureAppearance isEqualToString:@"dark"])) {
      initialProps = @{@"captureAppearance": captureAppearance};
    }
    NSView *rootView = nil;
    id appDelegate = NSApp.delegate;
    id rootViewFactory = nil;
    @try {
      rootViewFactory = [appDelegate valueForKey:@"rootViewFactory"];
    } @catch (__unused NSException *exception) {
      rootViewFactory = nil;
    }
    if (rootViewFactory != nil) {
      SEL selector = NSSelectorFromString(@"viewWithModuleName:initialProperties:");
      if ([rootViewFactory respondsToSelector:selector]) {
        using MsgSendType = NSView *(*)(id, SEL, NSString *, NSDictionary *);
        rootView = ((MsgSendType)objc_msgSend)(
            rootViewFactory,
            selector,
            @"ActionsPopoverView",
            initialProps);
      }
    }
    if (rootView == nil) {
      rootView = [[RCTRootView alloc] initWithBridge:self.bridge moduleName:@"ActionsPopoverView" initialProperties:initialProps];
    }

    rootView.frame = NSMakeRect(0, 0, width, height);
    rootView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;

    NSViewController *controller = [[NSViewController alloc] init];
    controller.view = rootView;

    NSPopover *popover = [[NSPopover alloc] init];
    popover.behavior = NSPopoverBehaviorTransient;
    popover.contentViewController = controller;
    popover.contentSize = NSMakeSize(width, height);
    popover.delegate = (id<NSPopoverDelegate>)self;

    self.actionsPopover = popover;

    if (initialProps[@"captureAppearance"] != nil) {
      popover.appearance = sourceView.window.effectiveAppearance;
    }
    [popover showRelativeToRect:sourceView.bounds ofView:sourceView preferredEdge:NSRectEdgeMaxY];
  });
}

RCT_EXPORT_METHOD(closeActionsPopover)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    if (self.actionsPopover == nil) {
      return;
    }
    [self.actionsPopover performClose:nil];
    self.actionsPopover = nil;
  });
}

RCT_EXPORT_METHOD(resizeActionsPopover : (NSDictionary *)params)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    // A layout event from a dismissed menu must not resize its successor.
    if (!self.actionsPopover.isShown ||
        ![self.actionsPopoverMenuId isEqualToString:params[@"menuId"]]) {
      return;
    }
    CGFloat height = [params[@"height"] doubleValue];
    if (!isfinite(height) || height <= 0) {
      return;
    }
    NSSize size = self.actionsPopover.contentSize;
    size.height = MIN(ceil(height), self.actionsPopoverMaxHeight);
    self.actionsPopover.contentSize = size;
  });
}

RCT_EXPORT_METHOD(openMessageLimitPopover : (NSDictionary *)params)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    if (self.messageLimitPopover != nil && self.messageLimitPopover.isShown) {
      [self.messageLimitPopover performClose:nil];
      self.messageLimitPopover = nil;
    }

    NSNumber *anchorTag = params[@"anchorTag"];
    NSView *sourceView = nil;
    if ([anchorTag isKindOfClass:[NSNumber class]]) {
      sourceView = [self.viewRegistry_DEPRECATED viewForReactTag:anchorTag];
    }
    if (sourceView == nil) {
      sourceView = NSApp.keyWindow.contentView;
    }
    if (sourceView == nil) {
      return;
    }

    CGFloat width = 380;
    CGFloat height = 260;
    if ([params[@"width"] respondsToSelector:@selector(doubleValue)]) {
      width = (CGFloat)[params[@"width"] doubleValue];
    }
    if ([params[@"height"] respondsToSelector:@selector(doubleValue)]) {
      height = (CGFloat)[params[@"height"] doubleValue];
    }

    NSDictionary *initialProps = @{};
    NSView *rootView = nil;
    id appDelegate = NSApp.delegate;
    id rootViewFactory = nil;
    @try {
      rootViewFactory = [appDelegate valueForKey:@"rootViewFactory"];
    } @catch (__unused NSException *exception) {
      rootViewFactory = nil;
    }
    if (rootViewFactory != nil) {
      SEL selector = NSSelectorFromString(@"viewWithModuleName:initialProperties:");
      if ([rootViewFactory respondsToSelector:selector]) {
        using MsgSendType = NSView *(*)(id, SEL, NSString *, NSDictionary *);
        rootView = ((MsgSendType)objc_msgSend)(
            rootViewFactory,
            selector,
            @"MessageLimitPopoverView",
            initialProps);
      }
    }
    if (rootView == nil) {
      rootView = [[RCTRootView alloc] initWithBridge:self.bridge moduleName:@"MessageLimitPopoverView" initialProperties:initialProps];
    }

    rootView.frame = NSMakeRect(0, 0, width, height);
    rootView.autoresizingMask = NSViewWidthSizable | NSViewHeightSizable;
    NSString *popoverId = [params[@"popoverId"] isKindOfClass:[NSString class]]
        ? params[@"popoverId"]
        : @"desktop-popover";
    rootView.accessibilityIdentifier = popoverId;
    rootView.accessibilityLabel = popoverId;

    NSViewController *controller = [[NSViewController alloc] init];
    controller.view = rootView;

    NSPopover *popover = [[NSPopover alloc] init];
    popover.behavior = NSPopoverBehaviorTransient;
    popover.contentViewController = controller;
    popover.contentSize = NSMakeSize(width, height);
    popover.delegate = (id<NSPopoverDelegate>)self;

    self.messageLimitPopover = popover;

    NSRect anchorRect = sourceView.bounds;
    if (![anchorTag isKindOfClass:[NSNumber class]]) {
      anchorRect = NSMakeRect(NSMidX(anchorRect), NSMidY(anchorRect), 1, 1);
    }
    [popover showRelativeToRect:anchorRect ofView:sourceView preferredEdge:NSRectEdgeMaxY];
  });
}

RCT_EXPORT_METHOD(closeMessageLimitPopover)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    if (self.messageLimitPopover == nil) {
      return;
    }
    [self.messageLimitPopover performClose:nil];
    self.messageLimitPopover = nil;
  });
}

RCT_EXPORT_METHOD(submitConnectionEditor : (NSDictionary *)payload)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    [self sendEventWithName:@"connectionEditorSaved" body:payload ?: @{}];
    [self closeConnectionEditorWindow];
  });
}

RCT_EXPORT_METHOD(cancelConnectionEditor)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    [self sendEventWithName:@"connectionEditorCancelled" body:@{}];
    [self closeConnectionEditorWindow];
  });
}

RCT_EXPORT_METHOD(submitAgentPicker : (NSDictionary *)payload)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    [self sendEventWithName:@"agentPickerSelected" body:payload ?: @{}];
    [self closeAgentPickerWindow];
  });
}

RCT_EXPORT_METHOD(cancelAgentPicker)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    [self sendEventWithName:@"agentPickerCancelled" body:@{}];
    [self closeAgentPickerWindow];
  });
}

- (void)closeConnectionEditorWindow
{
  if (self.connectionEditorWindow == nil) {
    return;
  }
  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:NSWindowWillCloseNotification
                                                object:self.connectionEditorWindow];
  [self.connectionEditorWindow close];
  self.connectionEditorWindow = nil;
}

- (void)connectionEditorWindowWillClose:(NSNotification *)notification
{
  if (notification.object == self.connectionEditorWindow) {
    [self sendEventWithName:@"connectionEditorCancelled" body:@{}];
    [[NSNotificationCenter defaultCenter] removeObserver:self
                                                    name:NSWindowWillCloseNotification
                                                  object:self.connectionEditorWindow];
    self.connectionEditorWindow = nil;
  }
}

- (void)closeAgentPickerWindow
{
  if (self.agentPickerWindow == nil) {
    return;
  }
  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:NSWindowWillCloseNotification
                                                object:self.agentPickerWindow];
  [self.agentPickerWindow close];
  self.agentPickerWindow = nil;
}

- (void)agentPickerWindowWillClose:(NSNotification *)notification
{
  if (notification.object == self.agentPickerWindow) {
    [self sendEventWithName:@"agentPickerCancelled" body:@{}];
    [[NSNotificationCenter defaultCenter] removeObserver:self
                                                    name:NSWindowWillCloseNotification
                                                  object:self.agentPickerWindow];
    self.agentPickerWindow = nil;
  }
}

- (void)applicationActionDialogWindowWillClose:(NSNotification *)notification
{
  if (notification.object == self.applicationActionDialogWindow) {
    [self sendEventWithName:@"applicationActionDialogCancelled" body:@{}];
    [[NSNotificationCenter defaultCenter] removeObserver:self
                                                    name:NSWindowWillCloseNotification
                                                  object:self.applicationActionDialogWindow];
    self.applicationActionDialogWindow = nil;
  }
}

- (void)reactWindowWillClose:(NSNotification *)notification
{
  NSWindow *window = (NSWindow *)notification.object;
  if (window == nil) {
    return;
  }

  NSString *windowKey = [self.reactWindowKeysByWindow objectForKey:window];
  if (![windowKey isKindOfClass:[NSString class]] || windowKey.length == 0) {
    return;
  }

  [[NSNotificationCenter defaultCenter] removeObserver:self
                                                  name:NSWindowWillCloseNotification
                                                object:window];

  [self.reactWindowKeysByWindow removeObjectForKey:window];
  [self.reactWindowsByKey removeObjectForKey:windowKey];

  [self sendEventWithName:@"reactWindowCancelled" body:@{ @"windowKey" : windowKey }];
}

- (void)popoverDidClose:(NSNotification *)notification
{
  NSPopover *popover = (NSPopover *)notification.object;
  NSLog(@"[DesktopWindowManager] popoverDidClose popover=%p appAction=%p closing=%p suppress=%d", popover, self.applicationActionDialogPopover, self.closingApplicationActionDialogPopover, self.suppressApplicationActionDialogPopoverCancel);
  if (popover == self.closingApplicationActionDialogPopover) {
    self.closingApplicationActionDialogPopover = nil;
    self.suppressApplicationActionDialogPopoverCancel = NO;
    return;
  }

  if (popover == self.applicationActionDialogPopover) {
    self.applicationActionDialogPopover = nil;
    [self sendEventWithName:@"applicationActionDialogCancelled" body:@{}];
    return;
  }

  if (popover == self.actionsPopover) {
    self.actionsPopover = nil;
    return;
  }

  if (popover == self.messageLimitPopover) {
    self.messageLimitPopover = nil;
    return;
  }
}

@end
