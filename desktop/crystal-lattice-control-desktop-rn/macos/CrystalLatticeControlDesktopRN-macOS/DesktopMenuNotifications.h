#import <Foundation/Foundation.h>

static NSNotificationName const CLCTabStripStyleDidChangeNotification = @"CrystalLattice.TabStripStyleDidChange";
static NSString *const CLCTabStripStyleUserInfoKey = @"style";

static NSNotificationName const CLCSessionsFollowActiveTabDidChangeNotification =
    @"CrystalLattice.SessionsFollowActiveTabDidChange";
static NSString *const CLCSessionsFollowActiveTabEnabledUserInfoKey = @"enabled";
