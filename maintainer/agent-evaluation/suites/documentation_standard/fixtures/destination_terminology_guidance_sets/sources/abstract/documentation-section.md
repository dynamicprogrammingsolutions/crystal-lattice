## Write pages readers can use

Input material is a request, conversation, task, specification, existing file,
or review comment used to guide a change. The destination is the maintained
artifact being written or edited.

Marked examples illustrate individual transfers, not a complete list.

1. Use input material to determine required behavior, then choose names and
   organization for the destination. Do not use an input phrase as a
   maintained name merely because it appeared in the source.

   *Example:* A request for “calmer retries” may mean two delayed attempts; it
   does not establish `calm_retry`.

2. When creating a destination from a task, preserve the approved behavior and
   constraints without copying task-only grouping, ordering, or progress
   terminology.

   *Example:* A task may group work under “Follow-up workstream: storage
   migration.” The specification describes “Persisted record migration”
   without adopting the workstream label.

3. When editing an existing destination, reassess terminology and organization
   already present. Replace wording inherited from planning, tracking, or
   another source when it is not required or established for the destination.

   *Example:* A user guide may contain an old “Release checkpoint” heading
   copied from progress tracking. When the page is updated, organize it around
   the supported capability instead.

4. Retain exact wording when it is required or established by the product,
   public interface, or destination domain.

   *Example:* Documentation and tests retain an established `--dry-run` flag.

5. Otherwise explain or translate terminology into the behavior, component,
   condition, outcome, or relationship meaningful to the destination.

   *Example:* Developer documentation may describe a write-ahead journal. User
   documentation says that queued work survives a restart unless the storage
   mechanism is itself part of the public interface.

<!-- SPECIFIC_RULES -->

Use verified examples when showing input and result clarifies installation,
configuration, an API, or recovery. Check them against current implementation
or tests.

Write for the destination reader, keep tracking in its owning records, and
translate current limitations when users need them.
