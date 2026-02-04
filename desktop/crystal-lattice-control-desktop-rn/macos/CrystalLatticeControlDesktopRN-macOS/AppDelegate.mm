#import "AppDelegate.h"
#import "DesktopMenuNotifications.h"

#import <React/RCTBundleURLProvider.h>
#import <ReactAppDependencyProvider/RCTAppDependencyProvider.h>

static NSString *const kTabStripStyleDefaultsKey = @"CrystalLattice.TabStripStyle";
static NSString *const kTabStripStyleToolbarTabs = @"toolbarTabs";
static NSString *const kTabStripStyleCodeTabs = @"codeTabs";
static NSString *const kTabStripStyleUnderlineTabs = @"underlineTabs";
static NSString *const kTabStripStyleRoundedPills = @"roundedPills";

@interface AppDelegate ()

@property(nonatomic, strong) NSMenuItem *toolbarTabsMenuItem;
@property(nonatomic, strong) NSMenuItem *codeTabsMenuItem;
@property(nonatomic, strong) NSMenuItem *underlineTabsMenuItem;
@property(nonatomic, strong) NSMenuItem *roundedPillsMenuItem;

@end

@implementation AppDelegate

- (void)applicationDidFinishLaunching:(NSNotification *)notification
{
  self.moduleName = @"CrystalLatticeControlDesktopRN";
  NSString *tabStripStyle = [self loadTabStripStylePreference];
  self.initialProps = @{ @"initialTabStripStyle" : tabStripStyle };
  self.dependencyProvider = [RCTAppDependencyProvider new];

  [super applicationDidFinishLaunching:notification];
  [self installTabStripStyleMenuWithSelectedStyle:tabStripStyle];
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
