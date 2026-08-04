# session-ordering-buckets-app

Application-level plugin defining bucketed ordering for session lists.

Pinned rank is derived from `session_summary.metadata.pinned` by default.
Set `application.session_pinned_metadata_key` to the same custom key used by
`session-pinned-app`; no top-level `pinned` summary field is required.

Archive rank is derived from `session_summary.metadata.archived` by default.
Set `application.session_archived_metadata_key` to the same custom key used by
`session-archive-app`.

The four ordering priorities are stable:

1. Archived sessions updated in the last 60 days sort below every other
   session.
2. Sessions updated in the last 24 hours sort before older sessions.
3. Pinned sessions sort before unpinned sessions within each remaining bucket.
4. Sessions then sort by last-updated time descending.

The archive rank uses the same effective last-updated timestamp as the rest of
the plugin (`session_updated_at` when enabled, otherwise `modified`). An
archived session older than 60 days is exempt from archive ordering and follows
the ordinary recency, pin, and last-updated ranks.

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
