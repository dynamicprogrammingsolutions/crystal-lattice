#import <Cocoa/Cocoa.h>

#import <React/RCTComponent.h>
#import <React/RCTConvert.h>
#import <React/RCTViewManager.h>

@interface CLCMacSelect : NSPopUpButton

@property(nonatomic, copy) RCTBubblingEventBlock onChange;
@property(nonatomic, copy) NSArray<NSDictionary *> *options;
@property(nonatomic, copy) NSString *selectedValue;

@end

@implementation CLCMacSelect

- (instancetype)initWithFrame:(NSRect)frame
{
  if ((self = [super initWithFrame:frame pullsDown:NO])) {
    self.target = self;
    self.action = @selector(handleChange:);
    self.options = @[];
    self.selectedValue = @"";
  }
  return self;
}

- (void)handleChange:(__unused id)sender
{
  if (!self.onChange) {
    return;
  }

  NSMenuItem *item = self.selectedItem;
  NSString *value = @"";
  if (item.representedObject && [item.representedObject isKindOfClass:[NSString class]]) {
    value = (NSString *)item.representedObject;
  }

  self.onChange(@{ @"value" : value });
}

- (void)rebuildMenu
{
  [self removeAllItems];
  for (NSDictionary *opt in self.options) {
    if (![opt isKindOfClass:[NSDictionary class]]) {
      continue;
    }
    NSString *label = [RCTConvert NSString:opt[@"label"]] ?: @"";
    NSString *value = [RCTConvert NSString:opt[@"value"]] ?: @"";
    if (label.length == 0) {
      label = value;
    }
    if (value.length == 0) {
      continue;
    }

    [self addItemWithTitle:label];
    NSMenuItem *item = self.itemArray.lastObject;
    item.representedObject = value;
  }

  [self applySelectedValue];
}

- (void)applySelectedValue
{
  NSString *targetValue = self.selectedValue ?: @"";
  if (targetValue.length == 0) {
    return;
  }

  for (NSMenuItem *item in self.itemArray) {
    if ([item.representedObject isKindOfClass:[NSString class]] &&
        [(NSString *)item.representedObject isEqualToString:targetValue]) {
      [self selectItem:item];
      return;
    }
  }
}

@end

@interface MacSelectManager : RCTViewManager
@end

@implementation MacSelectManager

RCT_EXPORT_MODULE(MacSelect)

+ (BOOL)requiresMainQueueSetup
{
  return YES;
}

- (NSView *)view
{
  return [[CLCMacSelect alloc] initWithFrame:NSZeroRect];
}

RCT_EXPORT_VIEW_PROPERTY(onChange, RCTBubblingEventBlock)

RCT_CUSTOM_VIEW_PROPERTY(options, NSArray, CLCMacSelect)
{
  NSArray *options = json ? [RCTConvert NSArray:json] : @[];
  view.options = options;
  [view rebuildMenu];
}

RCT_CUSTOM_VIEW_PROPERTY(selectedValue, NSString, CLCMacSelect)
{
  view.selectedValue = json ? [RCTConvert NSString:json] : @"";
  [view applySelectedValue];
}

RCT_CUSTOM_VIEW_PROPERTY(enabled, BOOL, CLCMacSelect)
{
  view.enabled = json ? [RCTConvert BOOL:json] : YES;
}

@end
