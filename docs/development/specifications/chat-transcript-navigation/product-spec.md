# Chat transcript navigation product specification

## Purpose

Long sessions cannot always keep every message loaded and rendered. Transcript
navigation therefore has two distinct responsibilities:

- choose which part of session history is loaded;
- move the viewport within the loaded messages.

Users should be able to inspect earlier or later history without losing the
message they were reading, while still having direct ways to reach the oldest
and newest currently loaded content.

## Terms

**Session history** is the ordered message sequence in the selected live
session or read-only session snapshot.

**Message index** is a zero-based position in that session-history snapshot.
It is not a stable identity across mutations that insert or delete earlier
messages.

**Loaded range** is the subset of session history currently held by the chat
controller.

**Viewport** is the visible portion of the loaded range.

**Visual top** and **visual bottom** are the user-visible transcript edges,
independent of whether the native list is inverted.

**Tail range** has no upper bound and is relative to the newest messages, such
as `-50:`.

**Absolute range** uses concrete bounds, such as `150:250`.

**Overlap** is the set of message indices present in both the old and new
loaded ranges.

**Viewport anchor** identifies a visible message index and its
viewport-relative offset.

**Pinned to bottom** means the viewport is within the platform's configured
threshold of the newest loaded content and is eligible for normal tail
following.

## Baseline behavior

### Initial and persisted ranges

- A newly opened chat defaults to the final 50 session messages.
- The selected range is scoped to the connection and session.
- A previously persisted range may replace the default when the chat is
  restored.
- Users may continue to enter an arbitrary Python-style range through the
  existing message-range settings surface.

### Loaded-range controls

The transcript exposes contextual actions where they can change the loaded
range:

- **Show older** loads an earlier overlapping window.
- **Show newer** loads a later overlapping window.
- **Show all** clears both range bounds.
- **Show last 50** selects the final 50 messages.

Older and show-all actions belong at the visual top. Newer and show-last
actions belong at the visual bottom. An inapplicable action is absent, and a
range action cannot be invoked while another message load is in progress.

Ordinary range navigation uses pages of 50 messages and keeps at most 100
messages loaded before sliding a bounded window. Show-all is an explicit
exception to that ordinary bound.

### Viewport controls

Scroll-to-top and scroll-to-bottom change only the viewport. They do not load
messages outside the current range.

- Scroll-to-top reaches the oldest loaded content.
- Scroll-to-bottom reaches the newest loaded content.
- A control is absent when its destination is already within the platform's
  edge threshold.
- Explicit edge navigation is bounded, can be superseded by later user input,
  and must converge on the actual loaded edge rather than merely issuing one
  best-effort native scroll command.

### Position preservation

When older or newer range navigation retains messages that were visible before
the load, the frontend preserves the user's place:

- one overlapping visible message is selected as the operation's viewport
  anchor before replacing the loaded data;
- after the new range is rendered, that same message index is restored at
  approximately the same viewport-relative offset;
- the frontend does not default to the top or bottom of the new range while a
  valid overlap anchor remains available.

Show-last intentionally returns to the newest edge. Behavior for show-all and
arbitrary range changes is not yet normalized beyond retaining any behavior
explicitly selected by those actions.

### Tail following

New content may follow the viewport while the transcript is pinned to the
bottom. Manual movement or explicit navigation away from the bottom detaches
that affinity. Streaming or rendering updates must not pull a detached user
back to the bottom. Explicit bottom navigation restores bottom affinity after
arrival.

## Acceptance examples

### Expanding a tail range

If messages `175` through `224` are loaded by `-50:`, Show 50 older selects
`-100:`. A visible overlapping message remains at approximately its previous
screen position after messages `125` through `224` render.

### Moving beyond the bounded tail

If the final 100 messages are already loaded and earlier messages exist,
another older action selects an absolute 100-message window with a 50-message
overlap. Repeated navigation slides that bounded window toward the start of
history.

### Moving toward newer history

From `150:250`, Show 50 newer first expands or slides the loaded window toward
newer indices. When the requested absolute range reaches the end of history,
the frontend returns to an appropriate tail range.

### Loaded-edge navigation

From the middle of a loaded transcript, scroll-to-top reaches the oldest
loaded row without fetching earlier messages. Scroll-to-bottom then reaches
the newest loaded row and restores bottom affinity.

### Detached streaming

If the user scrolls away from the newest loaded message while an answer is
streaming, subsequent chunks do not take control of the viewport. The user can
explicitly return with scroll-to-bottom.

## Baseline non-goals

- Previous or next user-message navigation.
- Direct navigation to an arbitrary message index.
- A lightweight session-wide message index or preview response.
- Stable message identity independent of session-history position.
- One shared native scroll implementation.
- Automatic replacement of show-all for very large histories.