# summarize-range-app

Application-level plugin providing summarize-range session actions.

The `summarize_range` action runs in the background: it validates the
request, reserves the session's application operation, and returns promptly
with an accepted operation envelope. The summarization model request runs on
a worker thread while progress, cancellation, and completion are delivered
through session notifications with Cancel and Retry followups, mirroring the
OpenAI Responses native-compaction flow. A snapshot is created before the
summarized session is committed, and concurrent session modifications are
detected through reconciled persistence instead of being overwritten. The
`cancel_summarize_range` action requests cancellation of a running
operation.

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
