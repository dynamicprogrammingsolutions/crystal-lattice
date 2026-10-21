# Frontend Rn Components

Frontend Rn Components package for Crystal Lattice.

## Testing

Run the package tests from the repository root:

```bash
npm --workspace @crystal-lattice/frontend-rn-components test
```

Or from this package directory:

```bash
npm test
```

This package currently has fast Vitest coverage only; it does not define
integration or e2e scripts.

Development documentation starts at
[docs/development/index.md](docs/development/index.md).

## Action forms

`ApplicationActionForm` owns field initialization, validation, and submission
for both action dialogs and embedded result forms. Custom text-field renderers
should forward the optional `params.onFocus` callback to their native input so
mobile scroll containers can reveal the focused field after a keyboard or
viewport change. Custom Android inputs should also set `disableFullscreenUI`
to keep modal controls visible while editing in landscape.

Mobile `ApplicationActionDialog` measures its safe, keyboard-adjusted viewport
and keeps its title and Cancel/OK controls outside the scrollable body. A host
using `ApplicationActionDialogLayout` directly can supply `maxHeight` to select
this bounded layout. Hosts without that constraint retain their existing
content layout, including macOS keyboard submission.

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
