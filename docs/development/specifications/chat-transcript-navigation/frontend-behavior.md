# Portable frontend transcript-navigation behavior

This page defines framework-independent behavior shared by the mobile and
desktop chat frontends. Native list coordinates, measurement APIs, and scroll
coordination remain platform-specific.

## Navigation dimensions

Loaded-range and viewport navigation are independent:

| Action | Changes loaded range | Changes viewport | Destination |
|---|---:|---:|---|
| Scroll to top | No | Yes | Oldest loaded content |
| Scroll to bottom | No | Yes | Newest loaded content |
| Show older | Yes | Yes | Earlier overlapping history |
| Show newer | Yes | Yes | Later overlapping history |
| Show all | Yes | Platform's current explicit range-change behavior | Entire session history |
| Show last 50 | Yes | Yes | Newest edge of the final 50 messages |
| Apply arbitrary range | Yes | Platform's current explicit range-change behavior | User-selected slice |

A viewport edge control never implies that more history will be loaded.

## Shared range planning

Contextual range actions derive their availability and next range from:

- current start and end bounds;
- first and last loaded message indices;
- loaded message count;
- page size;
- maximum ordinary loaded-range size.

The baseline page size is 50 and the maximum ordinary loaded range is 100.

### Show older

- A tail smaller than 100 grows by 50.
- A full 100-message tail converts to an absolute 100-message window with
  approximately 50 messages of overlap.
- A bounded absolute window smaller than 100 expands toward index zero.
- A full bounded window slides toward index zero while retaining its size.
- The action is absent when the loaded range starts at index zero.

### Show newer

- A bounded window smaller than 100 expands its end by 50.
- A full bounded window slides toward newer indices while retaining its size.
- If the server returns fewer messages than the requested range before its
  requested end, the next plan returns to a tail range.
- A tail or open all-message range does not expose Show newer.

### Show all and show last

- Show all clears both range bounds and is absent when both are already clear.
- Show last selects `-50:` and is absent when that exact tail is already
  selected.

### Labels and placement

- Show older labels are capped by both page size and the known hidden count.
- Show newer labels use the page size.
- Older and show-all controls render at the visual top.
- Newer and show-last controls render at the visual bottom.
- Controls expose accessible button roles and labels.

## Overlap-anchor preservation

Show older and Show newer are one navigation operation spanning range
selection, loading, rendering, and viewport restoration.

Before issuing the load, the frontend:

1. identifies visible message rows and their viewport-relative offsets;
2. chooses a deterministic anchor expected to exist in the planned range;
3. records the anchor index, offset, navigation operation identity, and
   response consistency context available at that point.

After the response has replaced the loaded messages and the target row is
measurable, the frontend:

1. confirms the operation has not been superseded;
2. confirms that the anchor index exists in the response and that response
   consistency has not invalidated the operation;
3. restores that row to approximately the recorded offset;
4. stops bounded correction after the target is stable, the user intervenes,
   the operation is superseded, or its budget expires.

If the selected anchor is unavailable but another old/new overlap exists, the
frontend chooses a deterministic nearby overlap. If no overlap exists, older
navigation falls back to the newer edge of the newly loaded older window and
newer navigation falls back to the older edge of the newly loaded newer
window.

The pixel tolerance, measurement mechanism, and correction budget may differ
by platform. Native verification must assert the visible message index and a
bounded offset tolerance rather than merely asserting that a scroll method was
called.

## Edge navigation

Edge controls are derived from measured visual top and bottom gaps. Exact
thresholds may be platform-specific but must avoid flickering at an edge.

An explicit edge operation:

- converges on the visual destination;
- remains distinct from automatic content following;
- is cancelled or superseded by later user navigation;
- stops after a bounded time or correction count;
- updates bottom affinity from confirmed native position.

## Bottom affinity and content changes

- Initial tail views restore to the newest edge unless a valid persisted
  detached anchor is restored.
- New semantic content follows only while bottom affinity is pinned.
- Geometry feedback alone does not renew content-follow permission
  indefinitely.
- User interaction away from the bottom detaches bottom affinity.
- Explicit or manual return to the bottom restores affinity after native
  metrics confirm arrival.

## Mobile refinement

The mobile transcript uses an inverted list:

- native offset zero is the visual bottom;
- the maximum offset is the visual top;
- ordinary pinned content changes may use
  `maintainVisibleContentPosition`;
- explicit far-top navigation uses bounded retries because one native
  `scrollToEnd` call is not sufficient for a long virtualized transcript.

`maintainVisibleContentPosition` is an implementation aid, not proof that a
range replacement preserved the required overlap anchor.

## Desktop refinement

The desktop transcript uses macOS scroll metrics and a scroll coordinator:

- explicit edge navigation and automatic content-follow operations remain
  separate;
- detached message-viewport anchors may use a message index and offset from
  the viewport top;
- the list may use bounded item-anchor correction for virtualized rows.

Persisting and restoring an anchor across tab or application state is separate
from capturing and restoring an operation-scoped anchor around a range load.