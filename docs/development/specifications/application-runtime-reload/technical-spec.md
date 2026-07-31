# Application runtime reload technical specification

A stable application owner contains:

- the current replaceable `AgentApplication`;
- operation admission and active-operation accounting;
- shared event state;
- owner-lifetime application notifications;
- the reload worker and candidate factory.

Reload closes admission, waits for retained operations, constructs the
candidate from freshly read configuration/environment, swaps on success, then
closes old application resources before reporting completion.

Candidate failure keeps the old application active and reopens admission.
Concurrent reload requests are rejected or coalesced according to the owner
contract.

Application closure includes application plugins, runtime stores, async
runtime resources, tools, and MCP servers. Completion must not be reported
before required old-runtime cleanup finishes.

Owner integrations may be terminal/server, combined console/server, or a
future embedded mobile runtime. The contract does not require terminal-process
ownership.