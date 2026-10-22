export const walkthroughFinalPreviewEnabled =
  process.env.CRYSTAL_WALKTHROUGH_FINAL_PREVIEW === "1";

const prefix = "/__preview/walkthrough-final";
const sourceDirectory = "artifacts/walkthrough-final-preview";

function walkthroughFrame({
  id,
  title,
  caption,
  alt,
  heightCompact,
}) {
  return {
    id,
    title,
    caption,
    image: {
      src: `${prefix}/${id}-wide.webp`,
      srcDark: `${prefix}/${id}-wide-dark.webp`,
      srcCompact: `${prefix}/${id}-compact.webp`,
      srcCompactDark: `${prefix}/${id}-compact-dark.webp`,
      alt,
      width: 1600,
      height: 1000,
      widthCompact: 1000,
      heightCompact,
    },
  };
}

export const walkthroughFinalChapters = [
  {
    id: "compose",
    label: "Compose",
    title: "Steer the next request.",
    role:
      "The composer is where you write the next instruction and control a request that is already running.",
    distinction:
      "The selected profile can place its model, reasoning, and web-search controls beside the composer. Request actions let you add another instruction or decide how running work should stop.",
    frames: [
      walkthroughFrame({
        id: "compose-controls",
        title: "Write the next instruction",
        caption:
          "The current conversation and message field stay together, so the next instruction starts from the work already visible in the session.",
        alt:
          "A Crystal Lattice conversation shown with the message field used to write the next instruction.",
        heightCompact: 1100,
      }),
      walkthroughFrame({
        id: "compose-running",
        title: "Control work that is already running",
        caption:
          "Open Composer actions to append another instruction, signal the active provider and tool to stop, or let the current foreground tool finish before the session stops.",
        alt:
          "An active Crystal Lattice request with the Composer actions menu showing append, cancel, soft cancel, model, reasoning, and web-search controls.",
        heightCompact: 1050,
      }),
    ],
  },
  {
    id: "messages",
    label: "Messages",
    title: "Act from any message.",
    role:
      "Every response remains a specific point in the conversation, with its own content, metadata, and actions.",
    distinction:
      "Provider and plugin metadata stays attached to the response that produced it. Message actions can branch, revise, summarize, export, or remove history from that exact point.",
    frames: [
      walkthroughFrame({
        id: "message-metadata",
        title: "Inspect the response in context",
        caption:
          "Usage, estimated cost, and output details stay with the response that produced them instead of being separated into a global report.",
        alt:
          "A Crystal Lattice assistant response with provider usage, estimated cost, reasoning, and turn metadata attached to its footer.",
        heightCompact: 720,
      }),
      walkthroughFrame({
        id: "message-actions",
        title: "Continue from this point in history",
        caption:
          "The Message actions menu operates from this response: modify or fork the conversation, summarize it, export it, or remove later history.",
        alt:
          "The Message actions menu opened from a selected Crystal Lattice assistant response.",
        heightCompact: 1100,
      }),
    ],
  },
  {
    id: "session-actions",
    label: "Session actions",
    title: "Control the whole session.",
    role:
      "Session actions affect the current task as a whole rather than one selected message.",
    distinction:
      "Application controls and enabled plugin actions share one session-level surface. Frequently used actions can be selected from the same menu for quicker access.",
    frames: [
      walkthroughFrame({
        id: "session-controls",
        title: "Open whole-session controls",
        caption:
          "Switch the agent, open session settings or plugins, inspect snapshots, and manage the task without tying the action to one response.",
        alt:
          "The Crystal Lattice Session actions menu showing agent, settings, plugins, snapshots, and task-level controls.",
        heightCompact: 1160,
      }),
      walkthroughFrame({
        id: "session-pinning",
        title: "Choose the actions you use most",
        caption:
          "The stars beside session actions select controls for quicker access, while the complete menu remains available when needed.",
        alt:
          "The upper portion of the Session actions menu with star controls beside reload, message limit, agent switch, resend, and cancellation actions.",
        heightCompact: 760,
      }),
    ],
  },
  {
    id: "session-settings",
    label: "Session settings",
    title: "Configure this session.",
    role:
      "Every session has an agent setup that establishes how its work should run.",
    distinction:
      "A profile can define the provider route, instructions, tools, features, and UI controls. Provider settings and enabled plugins can then be adjusted for this session without changing every other session.",
    frames: [
      walkthroughFrame({
        id: "agent-profile",
        title: "Choose the agent profile",
        caption:
          "A profile is more than a model name: the selected entry describes the starting provider, purpose, features, and tools for this session.",
        alt:
          "The Crystal Lattice Desktop agent picker with Codex selected and its default tools listed in a separate details pane.",
        heightCompact: 1050,
      }),
      walkthroughFrame({
        id: "provider-settings",
        title: "Adjust provider-specific settings",
        caption:
          "The selected provider contributes the controls it understands—here including authentication mode and flex processing—and the values can be overridden for this session.",
        alt:
          "Crystal Lattice Session settings showing authentication mode, flex processing, and reasoning effort.",
        heightCompact: 760,
      }),
      walkthroughFrame({
        id: "session-plugins",
        title: "Change plugins for this session",
        caption:
          "Plugin features can be enabled or disabled for this session, or reset together to the selected agent profile's defaults.",
        alt:
          "The Crystal Lattice Plugins window showing feature switches and the Reset to defaults action.",
        heightCompact: 950,
      }),
    ],
  },
  {
    id: "workspace",
    label: "Workspace",
    title: "Keep many sessions moving.",
    role:
      "The workspace helps you recognize, search, and return to multiple durable agent sessions.",
    distinction:
      "Titles, subtitles, pinning, task status, filters, and request state turn sessions into recognizable work items rather than anonymous transcripts. Plugin-driven presentation fields can be disabled, replaced, or refined.",
    frames: [
      walkthroughFrame({
        id: "workspace-sessions",
        title: "Find the session by the work it represents",
        caption:
          "Descriptive titles and subtitles identify the work, while pinning, task status, search, and filters help keep the important sessions in reach.",
        alt:
          "A Crystal Lattice workspace with a search field and three sessions showing titles, subtitles, pins, task statuses, and request states.",
        heightCompact: 1050,
      }),
      walkthroughFrame({
        id: "workspace-status",
        title: "See what is running now",
        caption:
          "Task status records where the work belongs in the workflow. A separate request indicator shows whether its current agent run is in progress, completed, or interrupted.",
        alt:
          "Three Crystal Lattice session rows comparing durable task statuses with in-progress, completed, and interrupted request indicators.",
        heightCompact: 900,
      }),
    ],
  },
  {
    id: "connections",
    label: "Connections",
    title: "Open the workspace where it runs.",
    role:
      "A connection tells the client which Crystal Lattice runtime owns the sessions it should display.",
    distinction:
      "Desktop and mobile can open sessions from the same runtime instead of creating unrelated client-local conversations. The connection method determines whether that runtime is reached locally or remotely.",
    frames: [
      walkthroughFrame({
        id: "desktop-connection",
        title: "See which workspace is active in Desktop",
        caption:
          "The Sessions panel names the focused connection above the list, so Desktop shows which runtime currently supplies its agents and sessions.",
        alt:
          "The Crystal Lattice Desktop Sessions panel naming Local workspace as its focused online connection above search and session controls.",
        heightCompact: 400,
      }),
      walkthroughFrame({
        id: "mobile-connection",
        title: "Reach a workspace from mobile",
        caption:
          "The mobile app starts from the same connection model: choose how to reach a Crystal Lattice runtime, then open the sessions it exposes.",
        alt:
          "The Crystal Lattice mobile New connection window showing manual address, automatic discovery, bridge, and cloud connection methods.",
        heightCompact: 1200,
      }),
    ],
  },
];

export const walkthroughFinalSourceCopies = walkthroughFinalChapters.flatMap(
  chapter => chapter.frames.flatMap(frame =>
    ["wide", "compact"].flatMap(shape =>
      ["", "-dark"].map(suffix => ({
        source: `${sourceDirectory}/${frame.id}-${shape}${suffix}.webp`,
        destination: `${frame.id}-${shape}${suffix}.webp`,
      })),
    ),
  ),
);

export function walkthroughFinalSection() {
  return {
    type: "productWalkthrough",
    id: "product-walkthrough",
    title: "Familiar chat. More control at every level.",
    intro:
      "Start with the AI chat interface you already know. Then move outward from the next request to one response, the whole session, its configuration, the workspace around many sessions, and the connections that make those sessions available to each client.",
    chapters: walkthroughFinalChapters,
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