# Application runtime reload product specification

Reload applies current configuration, environment, and plugin revisions
without restarting the complete CLI/server process.

When reload is requested:

1. new application operations are rejected;
2. already admitted operations finish;
3. a candidate application is constructed and validated;
4. the old application is replaced and closed;
5. admission reopens.

Requested, completed, and failed states are communicated through application
notifications. Candidate failure keeps the active application available.

The server listener, CLI process, bridge, Bonjour integration, and frontend
connections remain alive.

Running-request policy, cancellation-on-reload, secure credential mutation,
and partial live configuration activation remain deferred.