#import "CLPythonHostSupport.h"

#import <Python/Python.h>

static NSString *const CLPythonRuntimeErrorDomain =
    @"com.dynamicprogrammingsolutions.crystallattice.python-runtime";

@implementation CLPythonHostSupport

+ (nullable NSDictionary<NSString *, id> *)startWithStdlibPath:
    (NSString *)stdlibPath
    appArchive:(NSString *)appArchive
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

  wchar_t *stdlibWidePath = Py_DecodeLocale(stdlibPath.UTF8String, NULL);
  if (stdlibWidePath == NULL) {
    PyConfig_Clear(&config);
    [self setError:error
              code:1
           message:@"Could not decode the bundled Python standard-library path."];
    return nil;
  }

  PyStatus status =
      PyWideStringList_Append(&config.module_search_paths, stdlibWidePath);
  PyMem_RawFree(stdlibWidePath);
  if (PyStatus_Exception(status)) {
    NSString *message = status.err_msg == NULL
                            ? @"Could not configure the Python module path."
                            : [NSString stringWithUTF8String:status.err_msg];
    PyConfig_Clear(&config);
    [self setError:error code:2 message:message];
    return nil;
  }

  NSString *dynloadPath =
      [stdlibPath stringByAppendingPathComponent:@"lib-dynload"];
  wchar_t *dynloadWidePath = Py_DecodeLocale(dynloadPath.UTF8String, NULL);
  if (dynloadWidePath == NULL) {
    PyConfig_Clear(&config);
    [self setError:error
              code:3
           message:@"Could not decode the Python extension-module path."];
    return nil;
  }
  status = PyWideStringList_Append(&config.module_search_paths, dynloadWidePath);
  PyMem_RawFree(dynloadWidePath);
  if (PyStatus_Exception(status)) {
    NSString *message = status.err_msg == NULL
                            ? @"Could not configure the Python extension-module path."
                            : [NSString stringWithUTF8String:status.err_msg];
    PyConfig_Clear(&config);
    [self setError:error code:4 message:message];
    return nil;
  }

  wchar_t *appArchivePath = Py_DecodeLocale(appArchive.UTF8String, NULL);
  if (appArchivePath == NULL) {
    PyConfig_Clear(&config);
    [self setError:error
              code:5
           message:@"Could not decode the bundled Crystal Lattice source path."];
    return nil;
  }
  status = PyWideStringList_Append(&config.module_search_paths, appArchivePath);
  PyMem_RawFree(appArchivePath);
  if (PyStatus_Exception(status)) {
    NSString *message = status.err_msg == NULL
                            ? @"Could not configure the Crystal Lattice source path."
                            : [NSString stringWithUTF8String:status.err_msg];
    PyConfig_Clear(&config);
    [self setError:error code:6 message:message];
    return nil;
  }

  status = Py_InitializeFromConfig(&config);
  PyConfig_Clear(&config);
  if (PyStatus_Exception(status) || !Py_IsInitialized()) {
    NSString *message = status.err_msg == NULL
                            ? @"The bundled Python interpreter did not initialize."
                            : [NSString stringWithUTF8String:status.err_msg];
    [self setError:error code:7 message:message];
    return nil;
  }

  PyEval_SaveThread();
  return [self runtimeInfo];
}

+ (nullable NSDictionary<NSString *, id> *)runSmoke:
    (NSError *_Nullable *_Nullable)error {
  if (!Py_IsInitialized()) {
    [self setError:error
              code:6
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
    [self setError:error code:7 message:@"The bundled Python smoke program failed."];
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

+ (nullable NSDictionary<NSString *, id> *)runApplicationSmokeAtRoot:
    (NSString *)runtimeRoot
    error:(NSError *_Nullable *_Nullable)error {
  if (!Py_IsInitialized()) {
    [self setError:error
              code:8
           message:@"The bundled Python interpreter has not been initialized."];
    return nil;
  }

  PyGILState_STATE gilState = PyGILState_Ensure();
  PyObject *module = PyImport_ImportModule("crystal_lattice_mobile_runtime");
  if (module == NULL) {
    NSString *message = [self currentPythonError];
    PyGILState_Release(gilState);
    [self setError:error code:9 message:message];
    return nil;
  }

  PyObject *function = PyObject_GetAttrString(module, "run_application_smoke");
  Py_DECREF(module);
  if (function == NULL || !PyCallable_Check(function)) {
    Py_XDECREF(function);
    NSString *message = [self currentPythonError];
    PyGILState_Release(gilState);
    [self setError:error code:10 message:message];
    return nil;
  }

  PyObject *argument = PyUnicode_FromString(runtimeRoot.UTF8String);
  PyObject *result = PyObject_CallOneArg(function, argument);
  Py_DECREF(argument);
  Py_DECREF(function);
  if (result == NULL) {
    NSString *message = [self currentPythonError];
    PyGILState_Release(gilState);
    [self setError:error code:11 message:message];
    return nil;
  }

  NSDictionary<NSString *, id> *dictionary =
      [self dictionaryFromPythonObject:result error:error];
  Py_DECREF(result);
  PyGILState_Release(gilState);
  return dictionary;
}

+ (NSDictionary<NSString *, id> *)runtimeInfo {
  return @{
    @"status" : @"ready",
    @"pythonVersion" : [NSString stringWithUTF8String:Py_GetVersion()],
    @"pythonPlatform" : [NSString stringWithUTF8String:Py_GetPlatform()],
  };
}

+ (nullable NSDictionary<NSString *, id> *)dictionaryFromPythonObject:
    (PyObject *)object
    error:(NSError *_Nullable *_Nullable)error {
  PyObject *jsonModule = PyImport_ImportModule("json");
  if (jsonModule == NULL) {
    [self setError:error code:12 message:[self currentPythonError]];
    return nil;
  }
  PyObject *dumps = PyObject_GetAttrString(jsonModule, "dumps");
  Py_DECREF(jsonModule);
  if (dumps == NULL || !PyCallable_Check(dumps)) {
    Py_XDECREF(dumps);
    [self setError:error code:13 message:[self currentPythonError]];
    return nil;
  }

  PyObject *encoded = PyObject_CallOneArg(dumps, object);
  Py_DECREF(dumps);
  if (encoded == NULL) {
    [self setError:error code:14 message:[self currentPythonError]];
    return nil;
  }
  const char *utf8 = PyUnicode_AsUTF8(encoded);
  if (utf8 == NULL) {
    Py_DECREF(encoded);
    [self setError:error code:15 message:[self currentPythonError]];
    return nil;
  }

  NSData *data = [[NSString stringWithUTF8String:utf8]
      dataUsingEncoding:NSUTF8StringEncoding];
  Py_DECREF(encoded);
  id value = [NSJSONSerialization JSONObjectWithData:data options:0 error:error];
  return [value isKindOfClass:[NSDictionary class]] ? value : nil;
}

+ (NSString *)currentPythonError {
  if (!PyErr_Occurred()) {
    return @"Python operation failed without an exception.";
  }

  PyObject *type = NULL;
  PyObject *value = NULL;
  PyObject *traceback = NULL;
  PyErr_Fetch(&type, &value, &traceback);
  PyErr_NormalizeException(&type, &value, &traceback);
  PyObject *text = value == NULL ? NULL : PyObject_Str(value);
  NSString *message = text == NULL
                          ? @"Python operation failed."
                          : [NSString stringWithUTF8String:PyUnicode_AsUTF8(text)];
  Py_XDECREF(text);
  Py_XDECREF(type);
  Py_XDECREF(value);
  Py_XDECREF(traceback);
  return message;
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