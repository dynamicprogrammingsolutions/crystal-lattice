# `@crystal-lattice/react-native-mac-text-view`

Reusable macOS-native multiline text view for React Native New Architecture consumers.

## Scope

- macOS-focused
- Fabric / Codegen-based package shape
- preserves the existing Crystal Lattice desktop composer behavior:
  - imperative `setText(...)`
  - imperative `focus()`
  - placeholder support
  - editable mode
  - auto-grow and content-height reporting
  - configurable Enter-to-submit behavior
  - submit callback

## Example

See [example/MacTextViewExample.tsx](./example/MacTextViewExample.tsx) for a package-owned usage example that exercises the public API.

## Testing

This package does not currently define a package-local automated test script.
When changing it, verify through the consuming React Native macOS desktop app or
the package-owned example as appropriate.

## License

Copyright 2026 Dynamic Programming Solutions Kft.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
