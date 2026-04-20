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
  - submit callback

## Example

See [example/MacTextViewExample.tsx](./example/MacTextViewExample.tsx) for a package-owned usage example that exercises the public API.