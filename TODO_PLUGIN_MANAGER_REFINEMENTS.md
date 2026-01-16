# TODO: Plugin Manager Refinements and Tests

1. [x] Embedded `${env:VAR}` substitution within strings (not whole-string only)
2. [x] Log canonical plugin items and loader errors in `AgentApplication`
3. [x] Support entries list for specs (`{path|git, entries: [...]}`)
4. [x] Support module-only specs for local path and git
5. [x] Prefer descriptor `agent_plugin.json` `entries` over discovery
6. [x] Auto-discover only providers/tools/extensions/application (skip non-plugins)
7. [x] Accept dotted module-only strings (e.g., `path:..::dev_plugins.module`)
8. [x] Default `allow_remote` to false for git installer
9. [x] Tests: entries list (localpath, git)
10. [x] Tests: module-only (dict, localpath)
11. [x] Tests: module-only (string, localpath and git)
12. [x] Tests: descriptor precedence (git repo with `agent_plugin.json`)
13. [x] Tests: env substitution embedded placeholders
14. [x] Tests: remote git disallowed by default
15. [ ] Tests: negative discovery (decoy non-plugin class excluded)
16. [ ] Tests: sys.path precedence remains core-first (append), optional policy coverage
17. [ ] Descriptor search robustness doc and optional module-root search for local path as well
18. [ ] Documentation updates for spec forms and security (expanded examples)
19. [ ] Consider host allowlist policy and pinned ref warnings
20. [ ] Consider exposing `AgentApplication._config_errors` via accessor for tests
