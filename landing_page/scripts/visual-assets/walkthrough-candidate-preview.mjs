export const walkthroughCandidatePreviewEnabled =
  process.env.CRYSTAL_WALKTHROUGH_CANDIDATE_PREVIEW === "1";

const prefix = "/__preview/walkthrough";

function mobileAsset(name, alt) {
  return {
    src: `${prefix}/${name}-light.png`,
    srcDark: `${prefix}/${name}-dark.png`,
    alt,
    width: 1206,
    height: 2622,
  };
}

function proofBatchAsset(scene, alt) {
  return {
    src: `/__preview/proof-batch/${scene}/wide.webp`,
    srcDark: `/__preview/proof-batch/${scene}/wide-dark.webp`,
    srcCompact: `/__preview/proof-batch/${scene}/compact.webp`,
    srcCompactDark: `/__preview/proof-batch/${scene}/compact-dark.webp`,
    alt,
    width: 2400,
    height: 1350,
    widthCompact: 1200,
    heightCompact: 1600,
  };
}

const composer = mobileAsset(
  "composer-active",
  "An active Crystal Lattice mobile conversation with model and request controls beside the composer and the Composer actions menu open.",
);
const footer = {
  src: `${prefix}/message-footer-light.webp`,
  srcDark: `${prefix}/message-footer-dark.webp`,
  alt: "A completed assistant response with provider-supplied usage and estimated cost metadata in its message footer.",
  width: 1200,
  height: 900,
};
const messageActions = proofBatchAsset(
  "message-actions",
  "A real assistant message and Message actions menu showing built-in and plugin-contributed actions.",
);
const sessionActions = mobileAsset(
  "actions",
  "The production Session actions menu over a real conversation.",
);
const providerSettings = mobileAsset(
  "provider-settings",
  "Session settings showing provider-specific authentication, flex processing, and reasoning controls.",
);
const plugins = mobileAsset(
  "plugins",
  "The per-session Plugins window showing independently enabled and disabled features.",
);
const systemTemplate = mobileAsset(
  "system-template",
  "A System-role message showing the authored instruction template and its unresolved placeholders.",
);
const workspaces = mobileAsset(
  "workspaces-list",
  "A session list with descriptive titles, plugin-driven status and pin controls, and visible request status.",
);
const requestStatus = {
  src: `${prefix}/request-status-light.webp`,
  srcDark: `${prefix}/request-status-dark.webp`,
  alt: "Focused request-state indicators showing work in progress, completed, and interrupted across sessions.",
  width: 1200,
  height: 900,
};
const home = mobileAsset(
  "home",
  "The local Watchlist and Recent Sessions workspace across saved connections.",
);
const connections = mobileAsset(
  "connections",
  "The production mobile connection-method screen with local address, automatic discovery, bridge, and cloud choices.",
);
const crossDevice = {
  src: `${prefix}/cross-device-light.webp`,
  srcDark: `${prefix}/cross-device-dark.webp`,
  alt: "Crystal Lattice Desktop and mobile showing the same reviewed session, question, and answer.",
  width: 1800,
  height: 1013,
};

export const walkthroughCandidateSourceCopies = [
  ...[
    "composer-active",
    "actions",
    "provider-settings",
    "plugins",
    "system-template",
    "workspaces-list",
    "home",
    "connections",
  ].flatMap(name => [
    {
      source: `artifacts/walkthrough-candidates/mobile/${name}-light.png`,
      destination: `${name}-light.png`,
    },
    {
      source: `artifacts/walkthrough-candidates/mobile/${name}-dark.png`,
      destination: `${name}-dark.png`,
    },
  ]),
  {
    source: "artifacts/walkthrough-candidates/message-footer-light.webp",
    destination: "message-footer-light.webp",
  },
  {
    source: "artifacts/walkthrough-candidates/message-footer-dark.webp",
    destination: "message-footer-dark.webp",
  },
  {
    source: "artifacts/walkthrough-candidates/request-status-light.webp",
    destination: "request-status-light.webp",
  },
  {
    source: "artifacts/walkthrough-candidates/request-status-dark.webp",
    destination: "request-status-dark.webp",
  },
  {
    source: "artifacts/walkthrough-candidates/cross-device-light.webp",
    destination: "cross-device-light.webp",
  },
  {
    source: "artifacts/walkthrough-candidates/cross-device-dark.webp",
    destination: "cross-device-dark.webp",
  },
];

export function walkthroughCandidateSection() {
  return {
    type: "featureShowcase",
    id: "product-walkthrough-candidates",
    title: "Familiar chat. More control at every level.",
    body: [
      "Crystal Lattice starts with the AI chat interface you already know. Composer controls steer the next request, message actions operate from a point in history, session controls configure the whole task, and workspace views organize many sessions.",
    ],
    layout: "two-column",
    presentation: "editorial",
    reviewStatus: "Candidate review only",
    items: [
      {
        id: "walkthrough-compose",
        layout: "full-width",
        title: "Steer the next request.",
        description:
          "Use the familiar composer, then choose the model, reasoning, and web-search controls supplied by the selected profile. Cancel signals the provider and active tool to stop; soft cancel lets a running tool finish and save its result before the loop stops.",
        media: {
          kind: "Compose candidate",
          status: "candidate-review",
          assets: [
            {
              label: "C01 · Active Composer actions",
              description:
                "Built-in request controls and provider/plugin settings share one surface while retaining separate ownership.",
              ...composer,
            },
          ],
        },
      },
      {
        id: "walkthrough-messages",
        layout: "full-width",
        title: "Act from any message.",
        description:
          "Each response remains a point you can inspect and act from. Footers keep provider-supplied metadata with that response, while built-in and plugin actions can edit, fork, delete, summarize, compact, or export from that exact point.",
        media: {
          kind: "Message candidates",
          status: "candidate-review",
          assets: [
            {
              label: "C02 · Message footer",
              description:
                "Provider-supplied usage and estimated cost remain attached to the response that produced them.",
              ...footer,
            },
            {
              label: "C03 · Message actions",
              description:
                "Built-in history controls and optional workflow actions operate from one selected message.",
              ...messageActions,
            },
          ],
        },
      },
      {
        id: "walkthrough-session-actions",
        layout: "full-width",
        title: "Control the whole session.",
        description:
          "Session actions affect the task as a whole: switch the agent, open settings or plugins, inspect snapshots, update title or status, and pin the controls you use most.",
        media: {
          kind: "Session action candidate",
          status: "candidate-review",
          assets: [
            {
              label: "C04 · Focused Session actions",
              description:
                "The real production menu distinguishes whole-session controls from the actions attached to one message.",
              ...sessionActions,
            },
          ],
        },
      },
      {
        id: "walkthrough-session-configuration",
        layout: "full-width",
        title: "Configure this session.",
        description:
          "An agent profile supplies the initial provider, instructions, tools, and features. Provider-specific settings and the enabled plugin set can then be adjusted for this session.",
        media: {
          kind: "Session configuration candidates",
          status: "candidate-review",
          assets: [
            {
              label: "C05 · Agent picker",
              description:
                "Ordered Crystal Lattice profiles expose their title, purpose, and safe plugin/tool preview.",
              src: "/homepage-draft/agent-codex-light.webp",
              srcDark: "/homepage-draft/agent-codex-dark.webp",
              alt: "Crystal Lattice Desktop agent picker with the Codex-oriented profile and tool preview.",
              width: 1400,
              height: 980,
            },
            {
              label: "C06 · Provider-specific settings",
              description:
                "The active provider contributes settings such as authentication mode, processing tier, and reasoning effort.",
              ...providerSettings,
            },
            {
              label: "C07 · Session plugins and tools",
              description:
                "Providers, extensions, features, and tools can be enabled or disabled for one session and reset to the agent defaults.",
              ...plugins,
            },
          ],
        },
      },
      {
        id: "walkthrough-workspace",
        layout: "full-width",
        title: "Keep many sessions moving.",
        description:
          "Search and filter sessions, preview or open them, and use title, status, pinning, and current request state to return to the right task. A local Watchlist and recent-session view organize work across saved connections.",
        media: {
          kind: "Workspace candidates",
          status: "candidate-review",
          assets: [
            {
              label: "C10 · Standard session list",
              description:
                "Plugin-driven titles, subtitles, status, and pin controls turn session rows into recognizable work items.",
              ...workspaces,
            },
            {
              label: "C11 · Current request state",
              description:
                "Transient request indicators show which sessions are in progress, completed, or interrupted.",
              ...requestStatus,
            },
            {
              label: "C12 · Local Watchlist and Recent Sessions",
              description:
                "Watchlist membership, order, and notes are local device state and remain distinct from server-side pinning.",
              ...home,
            },
          ],
        },
      },
    ],
  };
}

export function applyWalkthroughCandidatePreview(page) {
  if (!walkthroughCandidatePreviewEnabled) return page;
  const walkthrough = walkthroughCandidateSection();
  const sections = [];
  for (const section of page.sections) {
    sections.push(section);
    if (section.type === "hero" && section.id === "hero") {
      sections.push(walkthrough);
    }
  }
  return {
    ...page,
    sections: sections.map(section => {
      if (section.type === "featureShowcase" && section.id === "product-highlights") {
        return {
          ...section,
          items: section.items
            ?.filter(item => !["feature-model-families", "session-workbench"].includes(item.id))
            .map(item => {
              if (item.id === "feature-work-anywhere") {
                return {
                  ...item,
                  media: {
                    kind: "Cross-device session",
                    status: "candidate-review",
                    assets: [
                      {
                        label: "C14 · Same session across clients",
                        description:
                          "Desktop and mobile retain the same title, agent, latest prompt, and answer.",
                        ...crossDevice,
                      },
                    ],
                  },
                };
              }
              if (item.id === "feature-transparency") {
                return {
                  ...item,
                  media: {
                    kind: "Inspectable execution",
                    status: "candidate-review",
                    assets: [
                      {
                        label: "C08 · Authored System template",
                        description:
                          "The stored System-role message remains visible with its unresolved placeholders.",
                        ...systemTemplate,
                      },
                      {
                        label: "C09 · Compiled System message",
                        description:
                          "The real inspection action resolves the effective Codex instructions without sending a model request.",
                        ...proofBatchAsset(
                          "compiled",
                          "The real compiled-system-message window shows the beginning of the maintained Codex default.",
                        ),
                      },
                      ...(item.media?.assets?.slice(1) ?? []),
                    ],
                  },
                };
              }
              return item;
            }),
        };
      }
      if (section.type === "gettingStarted" && section.id === "getting-started") {
        return {
          ...section,
          steps: section.steps?.map(step =>
            step.id === "connect-mobile"
              ? {
                  ...step,
                  media: {
                    kind: "Mobile connection proof",
                    status: "candidate-review",
                    src: connections.src,
                    srcDark: connections.srcDark,
                    alt: connections.alt,
                    width: connections.width,
                    height: connections.height,
                  },
                }
              : step,
          ),
        };
      }
      return section;
    }),
  };
}