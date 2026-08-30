# Stage A Visual Accessibility and Alt-Text Review

Status: Accepted for the completed task-025 early visual baseline on
August 30, 2026.

This review applies only to the six retained proof images. It does not approve
the final task-160 visual set.

| Visual | Alternative text outcome | Dimensions | Theme behavior | Review |
|---|---|---:|---|---|
| Provider reasoning | Names reasoning enabled, medium reasoning effort, and medium verbosity. | 1000 × 1315 | Matching light/dark WebP; one active source | Accepted |
| Provider usage/cost | Names visible input, cached, output, cost, and duration metadata. | 940 × 1334 | Matching light/dark WebP; one active source | Accepted with narrowed claim |
| Chat actions | Describes the session action menu and representative plugin-provided actions. | 1000 × 2025 | Matching light/dark WebP; one active source | Accepted |
| Session snapshots | Names automatic pre-compaction and pre-deletion recovery points plus Select, Restore, and Delete controls. | 1000 × 2025 | Matching light/dark WebP; one active source | Accepted |
| Session settings/plugins | Describes model, reasoning, verbosity, prompt-cache, web-search, and compaction-transcript controls. | 1000 × 2025 | Matching light/dark WebP; one active source | Accepted |
| Mobile active session | Describes a Starlette compatibility follow-up with visible reasoning, turn usage, estimated cost, agent, and session status. | 1000 × 2025 | Matching light/dark WebP; one active source; CSS phone frame only on the mobile page | Accepted |

## Presentation checks

- Every retained image has explicit width and height.
- Below-the-fold images use lazy loading and asynchronous decoding.
- Provider proof uses two desktop columns and one mobile column.
- Workbench proof uses three desktop columns and a wider horizontal snap layout
  below the desktop breakpoint.
- The mobile-page hero uses an unframed reviewed source inside a generic CSS
  phone frame and keeps the same source reusable by unframed consumers.
- Light and dark startup, theme toggling, and Astro client navigation select
  the correct source without creating duplicate image elements.
- The rejected diagrams and captures are absent from current public content.

## Limitations

- Screenshot text remains supporting visual proof; the surrounding headings and
  descriptions carry the primary meaning.
- The current captures are provisional and must be refreshed when their listed
  asset-catalog freshness triggers occur.
- Native screen-reader behavior belongs to the mobile application and is not
  established by these website screenshots.