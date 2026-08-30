# Session request-status implementation

`types/sessionRequestStatus.ts` owns the wire projection and defensive
normalizer. Unknown or malformed status entries are omitted while the snapshot
remains usable. This lets older clients tolerate a future server vocabulary
without presenting states they do not understand.

`RestAgentBackend.getSessionRequestStatuses()` sends one explicit-ID batch to
`POST /sessions/request-statuses`. The method is optional on `AgentBackend` for
compatibility with older and in-process implementations.

`connections/sessionStatusReader.ts` defines the saved-connection read result.
Frontend hosts own connection-kind construction because only the host knows
whether a closed cloud request can avoid waking a runtime and which bridge
credentials are available.

`Transport.request()` accepts an optional abort signal. Direct fetch and HTTP
bridge requests combine that signal with their timeout controllers so
foreground/background consumer changes stop in-flight status reads.