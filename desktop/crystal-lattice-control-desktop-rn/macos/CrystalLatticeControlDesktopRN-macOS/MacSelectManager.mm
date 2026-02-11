#import <Cocoa/Cocoa.h>

#import <React/RCTComponent.h>
#import <React/RCTConvert.h>
#import <React/RCTViewManager.h>

@interface CLCMacSelect : NSPopUpButton

@property(nonatomic, copy) RCTBubblingEventBlock onChange;
@property(nonatomic, copy) NSArray<NSDictionary *> *options;
@property(nonatomic, copy) NSString *selectedValue;
@property(nonatomic, copy) NSString *placeholder;

@end

@implementation CLCMacSelect

- (BOOL)isPlaceholderConfigured
{
  return (self.placeholder ?: @"").length > 0;
}

- (BOOL)isPlaceholderItem:(NSMenuItem *)item
{
  if (!item) {
    return NO;
  }
  if (![self isPlaceholderConfigured]) {
    return NO;
  }
  if (item != self.itemArray.firstObject) {
    return NO;
  }
  if ([item.representedObject isKindOfClass:[NSString class]]) {
    return [(NSString *)item.representedObject length] == 0;
  }
  return NO;
}

- (void)applyTitleAppearance
{
  NSMenuItem *selected = self.selectedItem;
  if ([self isPlaceholderItem:selected]) {
    NSString *title = self.placeholder ?: @"";
    NSDictionary *attrs = @{ NSForegroundColorAttributeName : [NSColor secondaryLabelColor] };
    self.attributedTitle = [[NSAttributedString alloc] initWithString:title attributes:attrs];
    return;
  }

  // Restore default appearance.
  self.attributedTitle = nil;
}

- (instancetype)initWithFrame:(NSRect)frame
{
  if ((self = [super initWithFrame:frame pullsDown:NO])) {
    self.target = self;
    self.action = @selector(handleChange:);
    self.options = @[];
    self.selectedValue = @"";
    self.placeholder = @"";
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

  [self applyTitleAppearance];

  self.onChange(@{ @"value" : value });
}

- (void)rebuildMenu
{
  [self removeAllItems];

  NSString *placeholderTitle = self.placeholder ?: @"";
  if (placeholderTitle.length > 0) {
    [self addItemWithTitle:placeholderTitle];
    NSMenuItem *placeholderItem = self.itemArray.lastObject;
    placeholderItem.representedObject = @"";
    NSDictionary *attrs = @{ NSForegroundColorAttributeName : [NSColor secondaryLabelColor] };
    placeholderItem.attributedTitle = [[NSAttributedString alloc] initWithString:placeholderTitle
                                                                     attributes:attrs];
    // Keep it selectable so users can return to the "none" state.
    placeholderItem.enabled = YES;
  }

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
  [self applyTitleAppearance];
}

- (void)applySelectedValue
{
  NSString *targetValue = self.selectedValue ?: @"";

  // If the value is empty, show placeholder (if present) instead of implicitly
  // selecting the first option.
  if (targetValue.length == 0) {
    if ((self.placeholder ?: @"").length > 0 && self.itemArray.count > 0) {
      [self selectItemAtIndex:0];
    }
    [self applyTitleAppearance];
    return;
  }

  for (NSMenuItem *item in self.itemArray) {
    if ([item.representedObject isKindOfClass:[NSString class]] &&
        [(NSString *)item.representedObject isEqualToString:targetValue]) {
      [self selectItem:item];
      [self applyTitleAppearance];
      return;
    }
  }

  // If no option matches, fall back to placeholder (if present).
  if ((self.placeholder ?: @"").length > 0 && self.itemArray.count > 0) {
    [self selectItemAtIndex:0];
  }
  [self applyTitleAppearance];
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

RCT_CUSTOM_VIEW_PROPERTY(placeholder, NSString, CLCMacSelect)
{
  view.placeholder = json ? [RCTConvert NSString:json] : @"";
  [view rebuildMenu];
}

RCT_CUSTOM_VIEW_PROPERTY(enabled, BOOL, CLCMacSelect)
{
  view.enabled = json ? [RCTConvert BOOL:json] : YES;
}

@end
