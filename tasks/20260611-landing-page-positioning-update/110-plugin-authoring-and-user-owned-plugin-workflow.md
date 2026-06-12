# Plugin Authoring And User-Owned Plugin Workflow

Make plugin creation outside the Crystal Lattice repository a tested product
path, then expose that path in the landing page plugin section.

## Requirements checklist

- [ ] Define the recommended layout for a user-owned plugin outside this repo.
- [ ] Add or document commands for initializing specific plugin types, for example `crystal-lattice plugin init tool ./my-tool`.
- [ ] Add validation for user-owned plugins, for example `crystal-lattice plugin validate ./my-tool`.
- [ ] Consider a `plugin-author` or `plugin-dev` built-in agent, similar in spirit to `cloud-script-author`, that reads plugin docs, chooses a plugin type, copies a template, writes tests, and validates loading.
- [ ] Support a simple way to load a local plugin during development, for example `crystal-lattice start --plugin ./my-tool` or `crystal-lattice plugin add path:./my-tool`.
- [ ] Add tests that prove a plugin outside the Crystal Lattice repo can be created, loaded, and used.

Parent Task: `tasks/20260611-landing-page-positioning-update/000-main.md`

## Context

The landing page wants to say that a user's workflow does not need to be
accepted upstream to exist. That claim is strongest if there is a tried and
tested path for user-owned plugins outside the monorepo.

The current proposed plugin section can use a prompt as a baseline, but the
product should eventually support a smoother flow with templates, validation,
and possibly a plugin-authoring agent.