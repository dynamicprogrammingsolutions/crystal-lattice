#import <Foundation/Foundation.h>

static NSNotificationName const CLCTabStripStyleDidChangeNotification = @"CrystalLattice.TabStripStyleDidChange";
static NSString *const CLCTabStripStyleUserInfoKey = @"style";

static NSNotificationName const CLCSessionsFollowActiveTabDidChangeNotification =
    @"CrystalLattice.SessionsFollowActiveTabDidChange";
static NSString *const CLCSessionsFollowActiveTabEnabledUserInfoKey = @"enabled";

static NSNotificationName const CLCSwitchConnectionWithActiveTabDidChangeNotification =
    @"CrystalLattice.SwitchConnectionWithActiveTabDidChange";
static NSString *const CLCSwitchConnectionWithActiveTabEnabledUserInfoKey =
    @"enabled";

static NSNotificationName const CLCMarkdownBaseFontSizeDidChangeNotification =
    @"CrystalLattice.MarkdownBaseFontSizeDidChange";
static NSString *const CLCMarkdownBaseFontSizeUserInfoKey = @"baseFontSize";

static NSNotificationName const CLCMarkdownHeaderSizeDidChangeNotification =
    @"CrystalLattice.MarkdownHeaderSizeDidChange";
static NSString *const CLCMarkdownHeaderSizeUserInfoKey = @"headerSize";

static NSNotificationName const CLCClearStoredSessionCachesNotification =
    @"CrystalLattice.ClearStoredSessionCaches";

static NSNotificationName const CLCProgressiveScrollHarnessCommandNotification =
    @"CrystalLattice.ProgressiveScrollHarnessCommand";
static NSString *const CLCProgressiveScrollHarnessCommandUserInfoKey = @"command";

static NSNotificationName const CLCOpenNotificationTestingNotification =
    @"CrystalLattice.OpenNotificationTesting";

static NSNotificationName const CLCOpenGlobalSettingsNotification =
    @"CrystalLattice.OpenGlobalSettings";

static NSNotificationName const CLCDesktopGlobalSettingRequestedNotification =
    @"CrystalLattice.DesktopGlobalSettingRequested";
static NSString *const CLCDesktopGlobalSettingKeyUserInfoKey = @"key";
static NSString *const CLCDesktopGlobalSettingValueUserInfoKey = @"value";

static NSNotificationName const CLCRecentSessionsWindowDidChangeNotification =
    @"CrystalLattice.RecentSessionsWindowDidChange";
static NSString *const CLCRecentSessionsWindowUserInfoKey =
    @"recentSessionsWindow";

static NSNotificationName const CLCSessionDoubleClickActionDidChangeNotification =
    @"CrystalLattice.SessionDoubleClickActionDidChange";
static NSString *const CLCSessionDoubleClickActionUserInfoKey =
    @"sessionDoubleClickAction";

static NSNotificationName const CLCTimeTrackingEnabledDidChangeNotification =
    @"CrystalLattice.TimeTrackingEnabledDidChange";
static NSString *const CLCTimeTrackingEnabledUserInfoKey = @"enabled";

static NSNotificationName const CLCTimeTrackingPluginIdDidChangeNotification =
    @"CrystalLattice.TimeTrackingPluginIdDidChange";
static NSString *const CLCTimeTrackingPluginIdUserInfoKey = @"pluginId";

static NSNotificationName const CLCTimeTrackingInactivitySecondsDidChangeNotification =
    @"CrystalLattice.TimeTrackingInactivitySecondsDidChange";
static NSString *const CLCTimeTrackingInactivitySecondsUserInfoKey = @"seconds";
