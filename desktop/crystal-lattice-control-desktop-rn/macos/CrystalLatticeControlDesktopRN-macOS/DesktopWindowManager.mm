#import "DesktopWindowManager.h"
#import "DesktopMenuNotifications.h"

#import <Cocoa/Cocoa.h>
#import <React/RCTBridge.h>
#import <React/RCTRootView.h>
#import <objc/message.h>

@interface DesktopWindowManager ()

@property(nonatomic, strong) NSWindow *connectionEditorWindow;
@property(nonatomic, strong) NSWindow *agentPickerWindow;
@property(nonatomic, strong) NSPopover *actionsPopover;

@end

@implementation DesktopWindowManager

RCT_EXPORT_MODULE();

+ (BOOL)requiresMainQueueSetup
{
  return YES;
}

- (NSArray<NSString *> *)supportedEvents
{
  return @[ @"connectionEditorSaved", @"connectionEditorCancelled", @"agentPickerSelected", @"agentPickerCancelled", @"tabStripStyleChanged", @"systemThemeChanged" ];
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

    NSRect frame = NSMakeRect(0, 0, 460, 380);
    NSWindow *window = [[NSWindow alloc] initWithContentRect:frame
                                                   styleMask:NSWindowStyleMaskTitled | NSWindowStyleMaskClosable | NSWindowStyleMaskResizable
                                                     backing:NSBackingStoreBuffered
                                                       defer:NO];
    window.title = @"New Session";
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

    self.actionsPopover = popover;

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

@end
