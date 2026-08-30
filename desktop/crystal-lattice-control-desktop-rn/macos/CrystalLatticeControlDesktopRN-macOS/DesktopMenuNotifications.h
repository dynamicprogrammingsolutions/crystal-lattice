#import <Foundation/Foundation.h>

static NSNotificationName const CLCTabStripStyleDidChangeNotification = @"CrystalLattice.TabStripStyleDidChange";
static NSString *const CLCTabStripStyleUserInfoKey = @"style";

static NSNotificationName const CLCSessionsFollowActiveTabDidChangeNotification =
    @"CrystalLattice.SessionsFollowActiveTabDidChange";
static NSString *const CLCSessionsFollowActiveTabEnabledUserInfoKey = @"enabled";

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
