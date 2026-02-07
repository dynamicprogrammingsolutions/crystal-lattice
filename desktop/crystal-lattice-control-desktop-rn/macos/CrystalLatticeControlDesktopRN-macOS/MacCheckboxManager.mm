#import <Cocoa/Cocoa.h>

#import <React/RCTComponent.h>
#import <React/RCTConvert.h>
#import <React/RCTViewManager.h>

@interface CLCMacCheckbox : NSButton

@property(nonatomic, copy) RCTBubblingEventBlock onChange;

@end

@implementation CLCMacCheckbox

- (instancetype)initWithFrame:(NSRect)frame
{
  if ((self = [super initWithFrame:frame])) {
    [self setButtonType:NSButtonTypeSwitch];
    self.target = self;
    self.action = @selector(handleClick:);
  }
  return self;
}

- (void)handleClick:(__unused id)sender
{
  if (!self.onChange) {
    return;
  }
  BOOL value = self.state == NSControlStateValueOn;
  self.onChange(@{ @"value" : @(value) });
}

@end

@interface MacCheckboxManager : RCTViewManager
@end

@implementation MacCheckboxManager

RCT_EXPORT_MODULE(MacCheckbox)

+ (BOOL)requiresMainQueueSetup
{
  return YES;
}

- (NSView *)view
{
  return [[CLCMacCheckbox alloc] initWithFrame:NSZeroRect];
}

RCT_EXPORT_VIEW_PROPERTY(onChange, RCTBubblingEventBlock)

RCT_CUSTOM_VIEW_PROPERTY(label, NSString, CLCMacCheckbox)
{
  view.title = json ? [RCTConvert NSString:json] : @"";
}

RCT_CUSTOM_VIEW_PROPERTY(value, BOOL, CLCMacCheckbox)
{
  BOOL value = json ? [RCTConvert BOOL:json] : NO;
  view.state = value ? NSControlStateValueOn : NSControlStateValueOff;
}

RCT_CUSTOM_VIEW_PROPERTY(enabled, BOOL, CLCMacCheckbox)
{
  view.enabled = json ? [RCTConvert BOOL:json] : YES;
}

@end
