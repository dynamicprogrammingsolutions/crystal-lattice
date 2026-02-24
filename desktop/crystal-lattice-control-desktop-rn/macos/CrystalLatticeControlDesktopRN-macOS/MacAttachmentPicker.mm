#import <Cocoa/Cocoa.h>

#import <React/RCTBridgeModule.h>
#import <React/RCTConvert.h>
#import <React/RCTUtils.h>

static NSString *CLCMimeTypeForExtension(NSString *ext)
{
  if (!ext) {
    return @"application/octet-stream";
  }
  NSString *lower = [ext lowercaseString];
  if ([lower isEqualToString:@"png"]) return @"image/png";
  if ([lower isEqualToString:@"jpg"] || [lower isEqualToString:@"jpeg"]) return @"image/jpeg";
  if ([lower isEqualToString:@"gif"]) return @"image/gif";
  if ([lower isEqualToString:@"webp"]) return @"image/webp";
  if ([lower isEqualToString:@"pdf"]) return @"application/pdf";
  return @"application/octet-stream";
}

@interface MacAttachmentPicker : NSObject <RCTBridgeModule>
@end

@implementation MacAttachmentPicker

RCT_EXPORT_MODULE(MacAttachmentPicker)

+ (BOOL)requiresMainQueueSetup
{
  return YES;
}

RCT_EXPORT_METHOD(pick
                  : (NSDictionary *)params
                  resolver
                  : (RCTPromiseResolveBlock)resolve
                  rejecter
                  : (RCTPromiseRejectBlock)reject)
{
  dispatch_async(dispatch_get_main_queue(), ^{
    @try {
      NSArray *allowedExtensions = params ? [RCTConvert NSArray:params[@"allowedExtensions"]] : nil;
      NSNumber *maxBytesNumber = params ? [RCTConvert NSNumber:params[@"maxBytes"]] : nil;
      long long maxBytes = maxBytesNumber != nil ? [maxBytesNumber longLongValue] : (15LL * 1024LL * 1024LL);

      NSOpenPanel *panel = [NSOpenPanel openPanel];
      panel.canChooseFiles = YES;
      panel.canChooseDirectories = NO;
      panel.allowsMultipleSelection = NO;
      panel.resolvesAliases = YES;

      if (allowedExtensions != nil && [allowedExtensions isKindOfClass:[NSArray class]] && allowedExtensions.count > 0) {
        NSMutableArray<NSString *> *types = [NSMutableArray array];
        for (id value in allowedExtensions) {
          if (![value isKindOfClass:[NSString class]]) {
            continue;
          }
          NSString *ext = [(NSString *)value stringByTrimmingCharactersInSet:[NSCharacterSet whitespaceAndNewlineCharacterSet]];
          if (ext.length == 0) {
            continue;
          }
          [types addObject:ext];
        }
        if (types.count > 0) {
          panel.allowedFileTypes = types;
        }
      }

      [panel beginWithCompletionHandler:^(NSModalResponse result) {
        if (result != NSModalResponseOK) {
          resolve(nil);
          return;
        }

        NSURL *url = panel.URL;
        if (url == nil) {
          resolve(nil);
          return;
        }

        NSError *error = nil;
        NSData *data = [NSData dataWithContentsOfURL:url options:NSDataReadingMappedIfSafe error:&error];
        if (data == nil || error != nil) {
          reject(@"read_failed", error.localizedDescription ?: @"Failed to read file", error);
          return;
        }

        if (maxBytes > 0 && data.length > (NSUInteger)maxBytes) {
          NSString *msg = [NSString stringWithFormat:@"File too large (%llu bytes). Limit is %lld bytes.", (unsigned long long)data.length, maxBytes];
          reject(@"file_too_large", msg, nil);
          return;
        }

        NSString *filename = url.lastPathComponent ?: @"";
        NSString *ext = url.pathExtension ?: @"";
        NSString *mimeType = CLCMimeTypeForExtension(ext);
        NSString *base64 = [data base64EncodedStringWithOptions:0] ?: @"";

        resolve(@{
          @"filename" : filename,
          @"mime_type" : mimeType,
          @"data_base64" : base64,
        });
      }];
    } @catch (NSException *exception) {
      reject(@"pick_failed", exception.reason ?: @"Failed to pick file", nil);
    }
  });
}

@end
