# Homepage First-User Release Visual Plan

Status: **Draft for owner review — not implemented.**

Updated: 2026-10-23

This plan maps the proposed opening copy to desktop and mobile compositions.
It does not select a copy direction or approve image sources.

## Visual role

The opening page should feel like a coherent product introduction, not a
documentation gallery or a sequence of unrelated screenshots.

It should:

- establish one product proposition;
- show the complete application before focused controls;
- distinguish visible, configurable, and extensible behavior;
- explain the Desktop/mobile relationship;
- lead naturally into Getting Started;
- give text, figures, and captions stable visual relationships.

## Selected planning principles

- Do not use a universal alternating text/image pattern.
- Do not let screenshot aspect ratio determine paragraph width.
- Use section tone according to information role, not automatic alternation.
- Treat screenshot title, bounded image surface, and caption as one figure.
- Use one large application image, then focused proofs.
- Use device/window frames only when client identity or cross-device
  relationship matters.
- Capture a smaller real window before using magnification or aggressive crop.
- Do not place several complete windows into one unreadable collage.
- Mobile receives an authored composition rather than automatic desktop
  stacking.

## Proposed page rhythm

| Section | Tone | Visual job |
| --- | --- | --- |
| Navigation and hero | Dark product surface | Proposition and primary action |
| Product at a glance | Soft neutral/tinted surface | Establish the complete application |
| Visible/configurable/extensible | White editorial surface | Three consistent proof relationships |
| Desktop and mobile | Soft neutral/tinted surface | Explain client continuity |
| Getting Started | White, grouped step surfaces | First-success path |
| Secondary routes/final action | Dark product surface | Route deeper audiences |

The light and dark themes preserve the same information hierarchy. Tone names
refer to role, not fixed literal colors.

## Desktop composition

```text
┌──────────────────────────────────────────────────────────────┐
│ DARK HERO                                                   │
│ eyebrow                                                      │
│ concise proposition                                         │
│ supporting copy                                             │
│ [Get started]  [View source]                                │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ PRODUCT AT A GLANCE — TINTED                                │
│ centered or left-aligned intro at stable editorial measure  │
│                                                              │
│ ┌ macOS-style Crystal Lattice Desktop frame ──────────────┐ │
│ │ session list | selected conversation | composer          │ │
│ └───────────────────────────────────────────────────────────┘ │
│ Persistent sessions | Profiles | Controls | Clients          │
│ concise caption                                              │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ VISIBLE / CONFIGURABLE / EXTENSIBLE — WHITE                 │
│ section intro at one stable measure                         │
│                                                              │
│ ┌ text 36% ┆ bounded focused figure 64% ┐                   │
│ │ visible behavior                       │                   │
│ └─────────────────────────────────────────┘                   │
│ ┌ text 36% ┆ bounded focused figure 64% ┐                   │
│ │ profile configuration                  │                   │
│ └─────────────────────────────────────────┘                   │
│ ┌ text 36% ┆ bounded focused figure 64% ┐                   │
│ │ provider/plugin UI                     │                   │
│ └─────────────────────────────────────────┘                   │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ DESKTOP AND MOBILE — TINTED                                 │
│ centered intro                                               │
│                                                              │
│ ┌ Desktop frame ─────────────────┐  ┌ phone frame ────────┐ │
│ │ matching session               │  │ same session        │ │
│ └─────────────────────────────────┘  └─────────────────────┘ │
│ one shared caption                                            │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│ GETTING STARTED — WHITE                                     │
│ six-step path with Mobile access grouping                   │
└──────────────────────────────────────────────────────────────┘
```

## Intermediate widths

At approximately 1024 and 768 pixels:

- keep the product-at-a-glance figure wide;
- proof rows may use a 40/60 relationship while labels remain readable;
- the Desktop/mobile pair may remain side by side only when the mobile client
  is not enlarged to compete with Desktop;
- otherwise stack Desktop above mobile inside one shared relationship;
- do not reduce screenshot scale merely to preserve a two-column layout.

## Mobile composition

```text
hero eyebrow
hero title
supporting copy
[Get started]
[View source]

product-overview heading
body
framed Desktop overview as a horizontally complete responsive image
four short supporting labels
caption

visible title and body
focused figure
caption

profile title and body
focused figure
caption

provider-control title and body
focused figure
caption

Desktop/mobile heading and body
Desktop frame
mobile frame
shared caption

Getting Started
```

The mobile composition preserves one text measure and ordinary vertical
reading. It introduces no carousel, horizontal screenshot strip, hidden tabs,
swipe requirement, or image-edge navigation.

## Text measures

Suggested maximum measures:

| Text role | Maximum measure |
| --- | --- |
| Hero supporting copy | 680 pixels |
| Section introduction | 700 pixels |
| Proof-row body | 500 pixels |
| Centered continuity body | 620 pixels |
| Figure caption | 620 pixels or the figure width, whichever is smaller |

Headings and paragraphs do not inherit different widths solely because a
source image is portrait or landscape.

## Figure system

Each figure contains:

1. a direct interface-oriented title;
2. a bounded figure surface;
3. the product image or frame;
4. a concise caption;
5. an optional enlarge action only when secondary details justify it.

### Bounded surface

The figure surface provides:

- visible separation from text;
- theme-aware background;
- restrained border;
- consistent radius;
- consistent internal padding;
- optional shallow shadow where it helps distinguish a native window;
- no decorative browser controls unrelated to the product.

### Frames

Use:

- a restrained macOS window frame for the large Desktop overview when the
  capture itself has no native title bar;
- a restrained phone frame for mobile in the continuity pair;
- separate Desktop and mobile frames rather than one blended raster canvas.

Do not frame:

- provider-control focus callouts;
- usage/cost response crops;
- modal/detail crops whose surrounding application context is already present;
- diagrams.

Frames are presentation, not product proof. They must not obscure genuine
controls or imply a platform the source did not use.

## Apparent magnification

Readability is assessed at rendered size, not source resolution.

Targets:

- large Desktop overview: approximately 1040–1120 CSS pixels at wide desktop;
- focused proof figure: approximately 680–760 CSS pixels at wide desktop;
- mobile figure: full available content width, normally 340–358 CSS pixels at
  a 390-pixel viewport;
- important product labels should generally render at no less than about
  12–13 CSS pixels.

If proof-bearing labels are smaller:

1. reduce the real source window before capture;
2. reduce irrelevant content in the deterministic fixture;
3. select a tighter genuine state;
4. use one genuine focus callout only when context must remain visible.

Do not solve readability by enlarging the entire page section, placing a tiny
full window beside unrelated text, or repainting labels.

## Product-at-a-glance figure

The figure should use one coherent Desktop state rather than a separate
Composer and Workspace image.

Required visible relationships:

- several recognizable sessions;
- one selected session;
- selected conversation;
- composer;
- profile/model identity;
- one truthful current request or session state when it does not clutter the
  overview.

The session list and conversation must be visibly populated. Automated review
should fail when the image source is missing, transparent, or visually blank.

## Profile figure

Capture a smaller real profile-picker window before producing the website
derivative.

Target state:

- selected profile;
- one or two comparison profiles at most;
- selected profile title and description;
- contributed tools;
- no large unused list or window region;
- no later crop that makes the source look like a window size that never
  existed.

## Visible/configurable/extensible proof rows

Use the same layout contract for all three rows:

- consistent text column;
- consistent figure column;
- consistent figure title and caption placement;
- no left/right alternation;
- image scale selected from proof-bearing UI, not equal raster height.

Portrait sources may use a narrower centered image inside the same figure
surface, but their interface labels should render at a comparable scale to
landscape sources.

## Desktop/mobile continuity figure

The relationship should be understandable before reading the caption:

- matching session identity;
- matching profile;
- matching user request;
- matching response or state.

Desktop supplies context. Mobile is a supporting client rather than an equally
large duplicate window. At narrow widths both frames become full width in
semantic order.

## Accessibility

- Figures use semantic `figure`/`figcaption`.
- Alt text states the relevant visible relationship without repeating the
  entire caption.
- Informative UI text is not embedded only in CSS backgrounds.
- An enlarge action, if used, is keyboard accessible and has a distinct
  accessible name.
- Meaning does not depend on frame color, shadow, or left/right position.
- Reduced motion removes nonessential transitions.
- Primary understanding remains available without JavaScript.

## Visual review matrix

Review light and dark themes at:

- 1440 pixels;
- 1024 pixels;
- 768 pixels;
- 390 pixels;
- 320 pixels.

For every width, inspect:

- hero line balance and action hierarchy;
- consistent editorial measures;
- product-at-a-glance image presence;
- screenshot UI scale;
- figure/text separation;
- profile readability;
- Desktop/mobile frame relationship;
- path length before Getting Started;
- absence of horizontal overflow;
- heading and figure order without JavaScript.

## Visual acceptance criteria

- The large application figure is the dominant proof before Getting Started.
- Focused images have comparable apparent UI scale.
- Text and figures do not visually merge into one undifferentiated column.
- Figure titles and captions align predictably.
- No screenshot appears missing or blank.
- No complete window is reduced until important controls become unreadable.
- The profile figure is readable without opening a full-size source.
- Desktop and mobile appear as clients, not pasted rectangles.
- Mobile remains a straightforward document.
- The final design uses Crystal Lattice's theme, not the Dynamic Programming
  Solutions website's palette or typography.
