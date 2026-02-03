#import "DesktopWindowManager.h"

#import <Cocoa/Cocoa.h>
#import <React/RCTBridge.h>
#import <React/RCTRootView.h>
#import <React/RCTUtils.h>

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
  return @[ @"connectionEditorSaved", @"connectionEditorCancelled" ];
}

RCT_EXPORT_METHOD(openConnectionEditor : (NSDictionary *)params)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    if (self.connectionEditorWindow != nil) {
      [self.connectionEditorWindow makeKeyAndOrderFront:nil];
      return;
    }

    NSDictionary *initialProps = params ?: @{};
    RCTRootView *rootView =
        [[RCTRootView alloc] initWithBridge:self.bridge moduleName:@"ConnectionEditorWindow" initialProperties:initialProps];

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
