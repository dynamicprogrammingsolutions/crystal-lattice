# Agent guidance compiler testing strategy

Deterministic tests cover:

- valid bundle, candidate, target, and local-section resolution;
- every missing, duplicate, unknown, and unused-slot failure;
- path validation;
- independent bundle and target repositories;
- location-independent hashes;
- optional Git provenance and dirty-state detection;
- exact destination checking;
- explicit preview and write behavior;
- current, candidate, and historical source selection by path.

Tests use neutral section names. Consumer-specific suites separately verify
that their chosen content and project targets behave as intended.
