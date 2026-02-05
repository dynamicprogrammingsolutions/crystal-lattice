#import "DesktopWindowManager.h"
#import "DesktopMenuNotifications.h"

#import <Cocoa/Cocoa.h>
#import <React/RCTBridge.h>
#import <React/RCTRootView.h>
#import <React/RCTUtils.h>
#import <objc/message.h>

@interface DesktopWindowManager ()

@property(nonatomic, strong) NSWindow *connectionEditorWindow;

@end

@implementation DesktopWindowManager

RCT_EXPORT_MODULE();

+ (BOOL)requiresMainQueueSetup
{
  return YES;
}

- (NSArray<NSString *> *)supportedEvents
{
  return @[ @"connectionEditorSaved", @"connectionEditorCancelled", @"tabStripStyleChanged", @"systemThemeChanged" ];
}

- (void)startObserving
{
  [[NSNotificationCenter defaultCenter] addObserver:self
                                           selector:@selector(handleTabStripStyleDidChange:)
                                               name:CLCTabStripStyleDidChangeNotification
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
                                                  name:@"NSSystemColorsDidChangeNotification"
                                                object:nil];

  [[NSDistributedNotificationCenter defaultCenter] removeObserver:self
                                                            name:@"AppleInterfaceThemeChangedNotification"
                                                          object:nil];
}

- (void)handleTabStripStyleDidChange:(NSNotification *)notification
{
  NSString *style = notification.userInfo[CLCTabStripStyleUserInfoKey];
  if (![style isKindOfClass:[NSString class]]) {
    return;
  }
  [self sendEventWithName:@"tabStripStyleChanged" body:@{ @"style" : style }];
}

- (void)handleSystemColorsDidChange:(NSNotification *)notification
{
  [self handleSystemThemeNotification:notification source:@"NSSystemColorsDidChangeNotification"];
}

- (void)handleAppleInterfaceThemeDidChangeDistributed:(NSNotification *)notification
{
  [self handleSystemThemeNotification:notification source:@"AppleInterfaceThemeChangedNotification(distributed)"];
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

static NSString *CLCAppearanceDebugName(id appearance)
{
  if (appearance == nil) {
    return @"<nil>";
  }
  SEL nameSelector = NSSelectorFromString(@"name");
  if ([appearance respondsToSelector:nameSelector]) {
    using MsgSendType = NSString *(*)(id, SEL);
    NSString *name = ((MsgSendType)objc_msgSend)(appearance, nameSelector);
    if ([name isKindOfClass:[NSString class]] && name.length > 0) {
      return name;
    }
  }
  return [appearance description];
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
  };
}

static void CLCDebugLogThemeEvent(NSNotification *notification,
                                 NSString *source,
                                 NSString *appearance,
                                 id preferredAppearance,
                                 NSDictionary *payload)
{
#if DEBUG
  NSString *userInfoDescription = notification.userInfo != nil ? [notification.userInfo description] : @"<nil>";
  NSString *objectDescription = notification.object != nil ? [notification.object description] : @"<nil>";
  NSString *interfaceStyle = [[NSUserDefaults standardUserDefaults] stringForKey:@"AppleInterfaceStyle"];
  id appAppearance = nil;
  id appEffectiveAppearance = nil;
  SEL appearanceSelector = NSSelectorFromString(@"appearance");
  SEL effectiveAppearanceSelector = NSSelectorFromString(@"effectiveAppearance");
  if ([NSApp respondsToSelector:appearanceSelector]) {
    using MsgSendType = id (*)(id, SEL);
    appAppearance = ((MsgSendType)objc_msgSend)(NSApp, appearanceSelector);
  }
  if ([NSApp respondsToSelector:effectiveAppearanceSelector]) {
    using MsgSendType = id (*)(id, SEL);
    appEffectiveAppearance = ((MsgSendType)objc_msgSend)(NSApp, effectiveAppearanceSelector);
  }

  NSWindow *keyWindow = NSApp.keyWindow;
  id keyWindowAppearance = nil;
  id keyWindowEffective = nil;
  if (keyWindow != nil && [keyWindow respondsToSelector:appearanceSelector]) {
    using MsgSendType = id (*)(id, SEL);
    keyWindowAppearance = ((MsgSendType)objc_msgSend)(keyWindow, appearanceSelector);
  }
  if (keyWindow != nil && [keyWindow respondsToSelector:effectiveAppearanceSelector]) {
    using MsgSendType = id (*)(id, SEL);
    keyWindowEffective = ((MsgSendType)objc_msgSend)(keyWindow, effectiveAppearanceSelector);
  }

  id viewAppearance = nil;
  id viewEffective = nil;
  if ([notification.object isKindOfClass:[NSView class]]) {
    NSView *view = (NSView *)notification.object;
    if ([view respondsToSelector:appearanceSelector]) {
      using MsgSendType = id (*)(id, SEL);
      viewAppearance = ((MsgSendType)objc_msgSend)(view, appearanceSelector);
    }
    if ([view respondsToSelector:effectiveAppearanceSelector]) {
      using MsgSendType = id (*)(id, SEL);
      viewEffective = ((MsgSendType)objc_msgSend)(view, effectiveAppearanceSelector);
    }
  }

  NSLog(
      @"[desktop-theme/native] source=%@ event=%@ appearance=%@ AppleInterfaceStyle=%@ windows=%ld preferredAppearance=%@ app.appearance=%@ app.effective=%@ key.appearance=%@ key.effective=%@ view.appearance=%@ view.effective=%@ notification.userInfo=%@ notification.object=%@ payload=%@",
      source,
        notification.name,
        appearance,
        interfaceStyle ?: @"<nil>",
        (long)NSApp.windows.count,
        CLCAppearanceDebugName(preferredAppearance),
        CLCAppearanceDebugName(appAppearance),
        CLCAppearanceDebugName(appEffectiveAppearance),
        CLCAppearanceDebugName(keyWindowAppearance),
        CLCAppearanceDebugName(keyWindowEffective),
      CLCAppearanceDebugName(viewAppearance),
      CLCAppearanceDebugName(viewEffective),
      userInfoDescription,
      objectDescription,
        payload);
#else
  (void)notification;
  (void)source;
  (void)appearance;
  (void)preferredAppearance;
  (void)payload;
#endif
}

- (void)handleSystemThemeNotification:(NSNotification *)notification source:(NSString *)source
{
  dispatch_async(dispatch_get_main_queue(), ^{
    NSString *appearance = CLCSystemAppearance();
    NSDictionary *payload = [self currentSystemThemePayload];
    id preferredAppearance = CLCPreferredAppearanceObject(appearance);
    CLCDebugLogThemeEvent(notification, source, appearance, preferredAppearance, payload);
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

@end
