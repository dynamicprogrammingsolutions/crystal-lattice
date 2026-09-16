## Write pages readers can use

Requests and conversations describe outcomes; tasks record approved work;
specifications, requirements, and decisions define behavior and constraints;
code, tests, and documentation maintain the system.

Marked examples illustrate individual transfers, not a complete list.

1. Carry required behavior through records, but choose names and organization
   for the specification, requirement, decision, code, test, or documentation.
   Do not reuse wording merely because it appeared in an earlier record.

   *Example:* A request for “calmer retries” may mean two delayed attempts; it
   does not establish `calm_retry`.

2. When writing a specification, requirements, decisions, code, tests, or
   documentation from a task, keep the approved behavior and constraints
   without copying task-only grouping, ordering, or progress terminology.

   *Example:* A task may group work under “Follow-up workstream: storage
   migration.” The specification describes “Persisted record migration”
   without adopting the workstream label.

3. When changing existing code or documentation, review terminology and
   organization already present. Replace wording inherited from planning,
   tracking, or another record when it is not required or established for the
   people or interfaces that use it.

   *Example:* A user guide may contain an old “Release checkpoint” heading
   copied from progress tracking. When the page is updated, organize it around
   the supported capability instead.

4. Keep exact wording when it is required or established by the product,
   public interface, or relevant domain.

   *Example:* Documentation and tests retain an established `--dry-run` flag.

5. Otherwise explain or translate terminology into the behavior, component,
   condition, outcome, or relationship needed there.

   *Example:* Developer documentation may describe a write-ahead journal. User
   documentation says that queued work survives a restart unless the storage
   mechanism is itself part of the public interface.

<!-- SPECIFIC_RULES -->

Use verified examples when showing input and result clarifies installation,
configuration, an API, or recovery. Check them against current implementation
or tests.

Keep tracking in its owning records and translate current limitations when
users need them.
