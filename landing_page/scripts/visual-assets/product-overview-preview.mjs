export const productOverviewPreviewEnabled =
  process.env.CRYSTAL_PRODUCT_OVERVIEW_PREVIEW === "1";

const prefix = "/__preview/product-overview";
const sourceDirectory = "artifacts/product-overview-preview";

function previewImage({
  id,
  title,
  caption,
  alt,
  width,
  height,
  widthCompact = width,
  heightCompact = height,
}) {
  return {
    id,
    title,
    caption,
    src: `${prefix}/${id}-wide.webp`,
    srcDark: `${prefix}/${id}-wide-dark.webp`,
    srcCompact: `${prefix}/${id}-compact.webp`,
    srcCompactDark: `${prefix}/${id}-compact-dark.webp`,
    alt,
    width,
    height,
    widthCompact,
    heightCompact,
  };
}

export const productOverviewStories = [
  {
    id: "overview-session",
    number: "01",
    title: "Work in an agent session.",
    description:
      "A session keeps the conversation, the next instruction, and the controls for how the selected agent should respond in one place.",
    detail:
      "The selected profile can put its model, reasoning effort, web search, and other contributed controls beside the composer. Stars keep frequently used controls within reach.",
    images: [
      previewImage({
        id: "session-composer",
        title: "Conversation and composer",
        caption:
          "The visible conversation, provider controls, and message field stay together in one continuous session screen.",
        alt:
          "A continuous Crystal Lattice session showing the active conversation, model, reasoning effort, web-search control, and composer.",
        width: 1000,
        height: 1200,
      }),
    ],
  },
  {
    id: "overview-workspace",
    number: "02",
    title: "Sessions stay organized.",
    description:
      "The workspace turns separate conversations into recognizable work you can search, open, and return to.",
    detail:
      "Titles and subtitles identify the task. Pinning, durable task status, and a separate request indicator show what matters and what is running now.",
    images: [
      previewImage({
        id: "workspace",
        title: "Workspace",
        caption:
          "The selected session remains open beside a list that shows task identity, pinning, durable status, and current request state.",
        alt:
          "Crystal Lattice Desktop with three named sessions and an open conversation; session rows show pin, task status, and request state.",
        width: 1600,
        height: 960,
        widthCompact: 1000,
        heightCompact: 1200,
      }),
    ],
  },
  {
    id: "overview-configuration",
    number: "03",
    title: "Configure the agent, not just the model.",
    description:
      "An agent profile can choose the provider route, instructions, features, and tools that form the starting point for a session.",
    detail:
      "Provider-specific settings and enabled plugins can then change the behavior and controls visible in that session without changing every other one.",
    images: [
      previewImage({
        id: "agent-profile",
        title: "Agent profile",
        caption:
          "The selected profile describes its purpose and the tools it contributes, rather than acting as a model-name picker alone.",
        alt:
          "Crystal Lattice Desktop agent picker with Codex selected, other configured profiles visible, and the selected profile's tools listed.",
        width: 1400,
        height: 980,
        widthCompact: 1000,
        heightCompact: 1120,
      }),
      previewImage({
        id: "provider-controls",
        title: "Provider controls",
        caption:
          "The active provider contributes controls it understands, such as reasoning effort and response verbosity.",
        alt:
          "Crystal Lattice Session settings with reasoning effort and verbosity controls magnified over their source context.",
        width: 1000,
        height: 1315,
      }),
    ],
  },
  {
    id: "overview-continuity",
    number: "04",
    title: "Continue the same session from another screen.",
    description:
      "Desktop and mobile are clients for the same Crystal Lattice runtime, not separate places where unrelated conversations are created.",
    detail:
      "Open the same session at your desk or on your phone. Getting Started explains local discovery, address and port, and remote bridge access.",
    images: [
      previewImage({
        id: "cross-device",
        title: "Desktop and mobile",
        caption:
          "The same task, selected agent, latest prompt, and response remain recognizable on both clients.",
        alt:
          "Crystal Lattice Desktop and mobile showing the same Starlette compatibility session, prompt, and assistant response.",
        width: 1600,
        height: 1000,
        widthCompact: 1000,
        heightCompact: 1250,
      }),
    ],
  },
];

export const productOverviewSourceCopies = productOverviewStories.flatMap(
  story => story.images.flatMap(image =>
    ["wide", "compact"].flatMap(shape =>
      ["", "-dark"].map(suffix => ({
        source: `${sourceDirectory}/${image.id}-${shape}${suffix}.webp`,
        destination: `${image.id}-${shape}${suffix}.webp`,
      })),
    ),
  ),
);

export function productOverviewSection() {
  return {
    type: "productOverview",
    id: "product-overview",
    eyebrow: "How Crystal Lattice fits together",
    title: "From one conversation to a complete workspace.",
    intro:
      "Start with a familiar conversation. Crystal Lattice keeps the session, its agent setup, the workspace around it, and the clients that open it connected as one product.",
    stories: productOverviewStories,
  };
}

export function applyProductOverviewPreview(page) {
  if (!productOverviewPreviewEnabled) return page;
  if (
    process.env.CRYSTAL_WALKTHROUGH_CANDIDATE_PREVIEW === "1" ||
    process.env.CRYSTAL_WALKTHROUGH_FINAL_PREVIEW === "1"
  ) {
    throw new Error(
      "Enable the product overview preview or a walkthrough preview, not both.",
    );
  }

  const overview = productOverviewSection();
  const secondaryVibe = page.sections
    .find(section =>
      section.type === "featureShowcase" &&
      section.id === "product-highlights"
    )
    ?.items?.find(item => item.id === "feature-vibe-anything");

  const sections = [];
  for (const section of page.sections) {
    if (
      section.type === "featureShowcase" &&
      section.id === "product-highlights"
    ) {
      continue;
    }

    if (section.type === "hero" && section.id === "hero") {
      sections.push({
        ...section,
        titleHtml:
          'Your AI agents and sessions.<br /><span class="highlight">One workspace.</span>',
        subtitle:
          "Crystal Lattice runs on your computer and gives you one place to work with configurable AI agents, keep their sessions organized, and continue the same work from Desktop or mobile.",
        actions: [
          {
            label: "See how it works",
            href: "#product-overview",
            variant: "primary",
            icon: "arrow",
          },
          {
            label: "Get started",
            href: "#getting-started",
            variant: "outline",
            icon: "arrow",
          },
        ],
      });
      sections.push(overview);
      continue;
    }

    sections.push(section);
    if (
      section.type === "gettingStarted" &&
      secondaryVibe
    ) {
      sections.push({
        type: "featureShowcase",
        id: "secondary-product-proof",
        eyebrow: "Beyond coding",
        title: "Adapt the workspace to another kind of work.",
        body: [
          "The same session and plugin model can support research, operations, evaluations, content, and other workflows built from reviewed tools and instructions.",
        ],
        items: [secondaryVibe],
      });
    }
  }

  return {
    ...page,
    sections,
  };
}