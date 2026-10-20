export const walkthroughFinalPreviewEnabled =
  process.env.CRYSTAL_WALKTHROUGH_FINAL_PREVIEW === "1";

const prefix = "/__preview/walkthrough-final";
const sourceDirectory = "artifacts/walkthrough-final-preview";
const compactHeights = {
  compose: 1500,
  messages: 1570,
  "session-actions": 1450,
  "session-settings": 1450,
  workspace: 1370,
};

function walkthroughImage(name, alt) {
  return {
    src: `${prefix}/${name}-wide.webp`,
    srcDark: `${prefix}/${name}-wide-dark.webp`,
    srcCompact: `${prefix}/${name}-compact.webp`,
    srcCompactDark: `${prefix}/${name}-compact-dark.webp`,
    alt,
    width: 1800,
    height: 1013,
    widthCompact: 1000,
    heightCompact: compactHeights[name],
  };
}

const chapters = [
  {
    id: "compose",
    label: "Compose",
    title: "Steer the next request.",
    role:
      "The composer is where you write the next instruction and control a request that is already running.",
    distinction:
      "The selected profile can place its model, reasoning, and web-search controls beside the composer. Cancel signals the active provider and tool; soft cancel lets a running tool finish and save its result before the loop stops.",
    caption:
      "The active conversation remains visible while request lifecycle and provider-specific controls share the composer surface.",
    image: walkthroughImage(
      "compose",
      "An active Crystal Lattice conversation with the Composer actions menu, model, reasoning, web-search, cancel, and soft-cancel controls enlarged beside the composer.",
    ),
  },
  {
    id: "messages",
    label: "Messages",
    title: "Act from any message.",
    role:
      "Each response remains a specific point in the conversation, with its own content, metadata, and actions.",
    distinction:
      "Provider-supplied usage stays attached to the response that produced it. Built-in and optional plugin actions can modify, copy, fork, summarize, delete, or export from that exact point.",
    caption:
      "The terminal assistant response shows its Message actions alongside the provider-supplied metadata attached to that response.",
    image: walkthroughImage(
      "messages",
      "A Starlette compatibility response with provider usage metadata and the real Message actions menu enlarged from the terminal assistant message.",
    ),
  },
  {
    id: "session-actions",
    label: "Session actions",
    title: "Control the whole session.",
    role:
      "Session actions apply to the task as a whole rather than to one selected message.",
    distinction:
      "Switch the agent, open settings or plugins, inspect snapshots, update the title, and pin the controls you use most. Plugins can add other task-level operations to the same surface.",
    caption:
      "The real popup keeps its menu chrome while the enlarged view makes the whole-task controls an unfamiliar visitor needs first readable.",
    image: walkthroughImage(
      "session-actions",
      "The Starlette session header and a focused Session actions menu showing agent, settings, plugins, snapshots, title, and related whole-session controls.",
    ),
  },
  {
    id: "session-settings",
    label: "Session settings",
    title: "Configure this session.",
    role:
      "Every session carries an agent setup that establishes how the task should run.",
    distinction:
      "A Crystal Lattice profile can select the provider route, instructions, tools, features, and UI controls. Provider settings and enabled plugins can then be adjusted for this session.",
    caption:
      "The agent profile establishes the defaults; focused settings and plugin views show the session-level controls it contributes.",
    image: walkthroughImage(
      "session-settings",
      "The Codex agent profile beside enlarged provider-specific settings and per-session plugin controls.",
    ),
  },
  {
    id: "workspace",
    label: "Workspace",
    title: "Keep many sessions moving.",
    role:
      "The workspace helps you search, recognize, and return to multiple durable agent sessions.",
    distinction:
      "Plugin-driven titles, subtitles, status, and pinning turn sessions into recognizable work items. A separate request-state indicator shows what the currently open runtime is doing now.",
    caption:
      "The Starlette session remains the first work item while durable task status and transient request state are labeled separately.",
    image: walkthroughImage(
      "workspace",
      "A Crystal Lattice session list led by the Starlette compatibility task, with readable title, subtitle, pin, durable task status, and current request-state indicators.",
    ),
  },
];

export const walkthroughFinalSourceCopies = chapters.flatMap(chapter =>
  ["wide", "compact"].flatMap(shape =>
    ["", "-dark"].map(suffix => ({
      source: `${sourceDirectory}/${chapter.id}-${shape}${suffix}.webp`,
      destination: `${chapter.id}-${shape}${suffix}.webp`,
    })),
  ),
);

export function walkthroughFinalSection() {
  return {
    type: "productWalkthrough",
    id: "product-walkthrough",
    title: "Familiar chat. More control at every level.",
    intro:
      "Start with the AI chat interface you already know, then move outward from the next request to one message, the whole session, its configuration, and finally the workspace around many sessions.",
    chapters,
  };
}

export function applyWalkthroughFinalPreview(page) {
  if (!walkthroughFinalPreviewEnabled) return page;
  if (process.env.CRYSTAL_WALKTHROUGH_CANDIDATE_PREVIEW === "1") {
    throw new Error(
      "Enable either the candidate walkthrough preview or the final walkthrough preview, not both.",
    );
  }
  const walkthrough = walkthroughFinalSection();
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
      if (section.type !== "featureShowcase" || section.id !== "product-highlights") {
        return section;
      }
      return {
        ...section,
        items: section.items?.filter(
          item => !["feature-model-families", "session-workbench"].includes(item.id),
        ),
      };
    }),
  };
}