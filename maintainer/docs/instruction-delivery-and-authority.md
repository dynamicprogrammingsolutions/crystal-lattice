# Instruction delivery and authority

Maintained text does not acquire one fixed instruction priority merely because
it lives in an `AGENTS.md`, task-guidance, or documentation file. Interpret
agent behavior by separating five properties:

| Property | Question |
|---|---|
| Source | Which maintained file, configuration value, or generated text supplied the content? |
| Delivery | Was the content sent through system instructions, developer instructions, a user message, automatic repository-guidance collection, or a file/tool read? |
| Authority | What precedence does that delivery channel have in the active runtime? |
| Availability | Was the content already in request context, automatically discovered, available only in the workspace, or reachable through another page? |
| Observed use | Did evidence show that the agent read or otherwise received the content, and did its behavior plausibly reflect it? |

Do not use “always loaded” to collapse these properties.

## Direct instruction channels

System and developer instructions are delivered by the host as instruction
channels. Their precedence is governed by the runtime and model protocol.
Repository or Markdown source used to construct those instructions should be
recorded separately from the delivered role.

For example, `agents/TASKS-v7.md` is a maintained Markdown source. In a
task-enabled Crystal Lattice request its content is delivered through the
developer-message layer. The source path and developer delivery are both part
of the provenance.

Provider adapters may represent the same effective instruction through a
native system message, developer message, or top-level instruction field.
Evaluation should record the effective role and adapter strategy instead of
inferring authority from the source filename.

## Repository guidance and ordinary files

A repository file can reach an agent in several different ways:

- a host may collect and inject it as request instructions;
- an evaluator may inject its content directly at a selected role;
- another instruction may route the agent to read it;
- the file may exist in the workspace but remain unread.

These cases are not equivalent. A file read through a tool remains subject to
higher-priority instructions and the active user request. Availability alone
does not prove that the agent discovered, read, or followed it.

When testing routing, leave the routed page as an ordinary workspace file and
record the read before the first relevant mutation. When testing wording in
isolation, direct injection is valid, but the result must be described as an
injection test rather than discovery evidence.

## Crystal Lattice system-message compilation

The default Crystal Lattice Codex and Claude configurations read source files
while compiling their normal system/developer message:

- the Codex project-instructions helper reads workspace or repository-root
  `AGENTS.md`;
- the Claude AGENTS-section helper reads the same workspace/repository source;
- the conditional `TASKS` variable reads `${CONFIG_DIR}/TASKS_v7.md` when
  `include_tasks` is enabled.

Those files are sources. Their observed delivery is the resulting compiled
Codex developer instructions or Claude system message. An evaluator that aims
to represent an ordinary Crystal Lattice run must exercise this production
compilation path, including the standard model-family message. It must not
replace or append the content through a suite-specific injector unless that
alternate delivery is the behavior being tested.

Runner fidelity also includes the tool contract paired with that message.
Codex instructions expect Codex tool schemas; Claude instructions expect
Claude tool schemas. Keeping the message while replacing its tools can change
agent behavior and is a different evaluation setup.

The direct verification is to compare source hashes and exact occurrence
counts with the message produced by the existing system-message inspection and
request-initialization paths. A structured provenance record may summarize
that evidence, but must not become another delivery mechanism.

## User requests and conflicts

User requests operate below applicable system and developer instructions. A
repository page read as ordinary content does not automatically outrank the
user request. If the host gives repository guidance a stronger role, that
delivery must be explicit in the evidence.

Tests involving possible conflicts should state:

- which text was direct system or developer instruction;
- which text was supplied by the user;
- which files were merely present;
- which files were actually read;
- what conflict-resolution behavior the host promised.

## Evaluation provenance

Every guidance evaluation should retain:

- source path or identifier and content hash;
- compiled effective content hash;
- delivery role, position, and adapter strategy;
- whether the content was pre-supplied, automatically collected, or
  discoverable;
- file-read evidence when discovery is part of the behavior under test;
- user prompt and follow-up messages;
- model, reasoning effort, tools, and relevant runtime configuration.

A report should say “developer-message task guidance,” “system-message
injection,” “compiled root repository guidance,” or “workspace page read after
routing” rather than “always-loaded guidance.”

## Interpreting existing results

Historical reports remain evidence for the delivery they actually used.
Clarify their terminology instead of silently reclassifying them:

- the September 15 task-guidance matrix directly injected the documentation
  guide and `TASKS-v7`; it did not test discovery through root `AGENTS.md`;
- routing tests such as Test 27 left the detailed pages in the workspace and
  verified that the agent read them;
- compiled root task mode directly supplied root guidance and developer-message
  task guidance, so it tests interaction but not independent page discovery.
