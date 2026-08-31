# session-actions-app

Application-level plugin providing copy/fork/delete session actions.

This repo is installed and loaded via the application plugin manager.

## Actions

The plugin contributes:

- Copy session
- Fork here
- Delete
- Delete from here
- Delete messages
- Delete session

Successful message deletion creates a full session snapshot immediately before
the mutation. Snapshot creation is enabled by default and applies to
single-message, explicit-index, range, and last-message deletion.

Reasons use normalized message indices:

```text
Before deleting message [14]
Before deleting messages [18, 22, 25]
Before deleting messages [357:]
```

No-op deletion does not create a snapshot. If saving the modified session
fails, the provisional snapshot is removed before the error is returned.

Automatic snapshots are not pruned or limited. See the
[session snapshot guide](../../application/python/docs/session-snapshots.md)
for readonly selection, restore behavior, storage cost, and manual deletion.

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
