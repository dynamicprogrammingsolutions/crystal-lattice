#import "CLPythonHostSupport.h"

#import <Python/Python.h>

static NSString *const CLPythonRuntimeErrorDomain =
    @"com.dynamicprogrammingsolutions.crystallattice.python-runtime";

@implementation CLPythonHostSupport

+ (nullable NSDictionary<NSString *, id> *)startWithStdlibArchive:
    (NSString *)stdlibArchive
    error:(NSError *_Nullable *_Nullable)error {
  if (Py_IsInitialized()) {
    return [self runtimeInfo];
  }

  PyConfig config;
  PyConfig_InitIsolatedConfig(&config);
  config.write_bytecode = 0;
  config.site_import = 0;
  config.user_site_directory = 0;
  config.module_search_paths_set = 1;

  wchar_t *archivePath = Py_DecodeLocale(stdlibArchive.UTF8String, NULL);
  if (archivePath == NULL) {
    PyConfig_Clear(&config);
    [self setError:error
              code:1
           message:@"Could not decode the bundled Python standard-library path."];
    return nil;
  }

  PyStatus status =
      PyWideStringList_Append(&config.module_search_paths, archivePath);
  PyMem_RawFree(archivePath);
  if (PyStatus_Exception(status)) {
    NSString *message = status.err_msg == NULL
                            ? @"Could not configure the Python module path."
                            : [NSString stringWithUTF8String:status.err_msg];
    PyConfig_Clear(&config);
    [self setError:error code:2 message:message];
    return nil;
  }

  status = Py_InitializeFromConfig(&config);
  PyConfig_Clear(&config);
  if (PyStatus_Exception(status) || !Py_IsInitialized()) {
    NSString *message = status.err_msg == NULL
                            ? @"The bundled Python interpreter did not initialize."
                            : [NSString stringWithUTF8String:status.err_msg];
    [self setError:error code:3 message:message];
    return nil;
  }

  PyEval_SaveThread();
  return [self runtimeInfo];
}

+ (nullable NSDictionary<NSString *, id> *)runSmoke:
    (NSError *_Nullable *_Nullable)error {
  if (!Py_IsInitialized()) {
    [self setError:error
              code:4
           message:@"The bundled Python interpreter has not been initialized."];
    return nil;
  }

  PyGILState_STATE gilState = PyGILState_Ensure();
  int status = PyRun_SimpleString(
      "import sys\n"
      "assert 6 * 7 == 42\n"
      "assert sys.version_info[:2] == (3, 12)\n");
  if (status != 0) {
    PyErr_Print();
    PyGILState_Release(gilState);
    [self setError:error code:5 message:@"The bundled Python smoke program failed."];
    return nil;
  }

  NSDictionary<NSString *, id> *info = @{
    @"status" : @"ready",
    @"answer" : @42,
    @"pythonVersion" : [NSString stringWithUTF8String:Py_GetVersion()],
    @"pythonPlatform" : [NSString stringWithUTF8String:Py_GetPlatform()],
  };
  PyGILState_Release(gilState);
  return info;
}

+ (NSDictionary<NSString *, id> *)runtimeInfo {
  return @{
    @"status" : @"ready",
    @"pythonVersion" : [NSString stringWithUTF8String:Py_GetVersion()],
    @"pythonPlatform" : [NSString stringWithUTF8String:Py_GetPlatform()],
  };
}

+ (void)setError:(NSError *_Nullable *_Nullable)error
             code:(NSInteger)code
          message:(NSString *)message {
  if (error == NULL) {
    return;
  }
  *error = [NSError errorWithDomain:CLPythonRuntimeErrorDomain
                               code:code
                           userInfo:@{NSLocalizedDescriptionKey : message}];
}

@end