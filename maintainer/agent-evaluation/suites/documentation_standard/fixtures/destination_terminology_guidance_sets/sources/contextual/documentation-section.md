## Write pages readers can use

Context means where wording comes from, where it is used, and its audience.
Requests, conversations, tasks, specifications, existing files, and review
comments provide source context. Code, tests, records, and documentation have
their own context.

Marked examples illustrate individual transfers, not a complete list.

1. Use source context to determine required behavior, then choose names and
   organization for the current context and audience. Do not reuse wording
   merely because it appeared earlier.

   *Example:* A request for “calmer retries” may mean two delayed attempts; it
   does not establish `calm_retry`.

2. When a task leads to another context, keep its approved behavior and
   constraints without copying task-only grouping, ordering, or progress
   terminology.

   *Example:* A task may group work under “Follow-up workstream: storage
   migration.” The specification describes “Persisted record migration”
   without adopting the workstream label.

3. When changing existing code or documentation, review terminology and
   organization already present. Replace wording inherited from another
   context when it is not required or established for the current audience or
   interface.

   *Example:* A user guide may contain an old “Release checkpoint” heading
   copied from progress tracking. When the page is updated, organize it around
   the supported capability instead.

4. Keep exact wording when it is required or established by the product,
   public interface, or relevant domain.

   *Example:* Documentation and tests retain an established `--dry-run` flag.

5. Otherwise explain or translate terminology into the behavior, component,
   condition, outcome, or relationship needed in the current context.

   *Example:* Developer documentation may describe a write-ahead journal. User
   documentation says that queued work survives a restart unless the storage
   mechanism is itself part of the public interface.

<!-- SPECIFIC_RULES -->

Use verified examples when showing input and result clarifies installation,
configuration, an API, or recovery. Check them against current implementation
or tests.

Keep tracking in its owning records and translate current limitations when
users need them.
