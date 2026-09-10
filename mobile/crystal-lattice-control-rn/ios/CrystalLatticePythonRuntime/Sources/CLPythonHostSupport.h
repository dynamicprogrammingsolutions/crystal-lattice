#import <Foundation/Foundation.h>

NS_ASSUME_NONNULL_BEGIN

@interface CLPythonHostSupport : NSObject

+ (nullable NSDictionary<NSString *, id> *)startWithStdlibPath:
    (NSString *)stdlibPath
    appArchive:(NSString *)appArchive
    error:(NSError *_Nullable *_Nullable)error;

+ (nullable NSDictionary<NSString *, id> *)runSmoke:
    (NSError *_Nullable *_Nullable)error;

+ (nullable NSDictionary<NSString *, id> *)runApplicationSmokeAtRoot:
    (NSString *)runtimeRoot
    error:(NSError *_Nullable *_Nullable)error;

@end

NS_ASSUME_NONNULL_END