# General Guidelines for Coding

When building something from scratch, understand the user's requirements, ask for clarification when needed, design the implementation, and write modular maintainable code.

When working on an existing codebase, understand the codebase and the user's goal first. For bug fixes, inspect the relevant logs, tests, and code paths before changing behavior. For features, prefer minimal intrusions to the existing code and add tests when the project already has tests.

Make minimal changes to achieve the goal. Follow the coding style of the existing project.

Do not run `git commit`, `git push`, `git reset`, `git rebase`, or other git mutations unless the user explicitly asks for them.