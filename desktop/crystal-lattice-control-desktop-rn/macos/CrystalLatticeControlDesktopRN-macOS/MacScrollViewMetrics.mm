#import <Cocoa/Cocoa.h>
#import <React/RCTBridge.h>
#import <React/RCTBridgeModule.h>
#import <React/RCTUIManager.h>

@interface MacScrollViewMetrics : NSObject <RCTBridgeModule>

@property (nonatomic, weak) RCTBridge *bridge;

@end

@implementation MacScrollViewMetrics

@synthesize bridge = _bridge;

RCT_EXPORT_MODULE(MacScrollViewMetrics)

+ (BOOL)requiresMainQueueSetup
{
  return YES;
}

- (NSScrollView *)findScrollViewInView:(NSView *)view
{
  if ([view isKindOfClass:[NSScrollView class]]) {
    return (NSScrollView *)view;
  }
  for (NSView *child in view.subviews) {
    NSScrollView *found = [self findScrollViewInView:child];
    if (found) {
      return found;
    }
  }
  return nil;
}

RCT_EXPORT_METHOD(getMetrics:(nonnull NSNumber *)reactTag
                  resolver:(RCTPromiseResolveBlock)resolve
                  rejecter:(RCTPromiseRejectBlock)reject)
{
  [self.bridge.uiManager addUIBlock:^(__unused RCTUIManager *uiManager, NSDictionary<NSNumber *, NSView *> *viewRegistry) {
    NSView *view = viewRegistry[reactTag];
    if (!view) {
      reject(@"not_found", @"View not found for reactTag", nil);
      return;
    }

    NSScrollView *scrollView = [self findScrollViewInView:view];
    if (!scrollView) {
      reject(@"not_scroll_view", @"No NSScrollView found under reactTag", nil);
      return;
    }

    NSView *documentView = scrollView.documentView;
    if (!documentView) {
      reject(@"no_document_view", @"ScrollView has no documentView", nil);
      return;
    }

    CGFloat offsetY = scrollView.contentView.bounds.origin.y;
    CGFloat viewportHeight = scrollView.contentView.bounds.size.height;
    CGFloat contentHeight = documentView.bounds.size.height;

    resolve(@{
      @"offsetY": @(offsetY),
      @"viewportHeight": @(viewportHeight),
      @"contentHeight": @(contentHeight),
    });
  }];
}

@end
