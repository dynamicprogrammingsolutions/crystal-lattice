#!/bin/sh
set -eu

PYTHON_XCFRAMEWORK_PATH="CrystalLatticePythonRuntime/Vendor/Python.xcframework"
PYTHON_UTILS="$PROJECT_DIR/$PYTHON_XCFRAMEWORK_PATH/build/utils.sh"

if [ ! -f "$PYTHON_UTILS" ]; then
  echo "error: Embedded Python runtime is not prepared. Run npm run ios:prepare-python." >&2
  exit 1
fi

if [ "$EFFECTIVE_PLATFORM_NAME" = "-iphonesimulator" ]; then
  ARCHS="arm64"
  export ARCHS
fi

if [ -z "${EXPANDED_CODE_SIGN_IDENTITY:-}" ]; then
  EXPANDED_CODE_SIGN_IDENTITY="-"
  EXPANDED_CODE_SIGN_IDENTITY_NAME="Ad Hoc"
  export EXPANDED_CODE_SIGN_IDENTITY
  export EXPANDED_CODE_SIGN_IDENTITY_NAME
fi

. "$PYTHON_UTILS"
install_python "$PYTHON_XCFRAMEWORK_PATH"