export const proofBatchRecipes = [
  {
    id: "homepage-message-actions", scene: "message-actions",
    configFile: "landing_page/visual_assets/runtime/proof-batch/message-actions.json",
    feature: "feature-plugins", slot: 1,
    alt: "Three configured plugins add Fork here, Summarize messages up to here, Share as PDF, and Share as Markdown to the assistant message menu.",
    layouts: {
      wide: {
        width: 2400, height: 1350,
        code: { x: 50, y: 310, width: 830, height: 850, fontSize: 32, lineHeight: 56, entryGap: 38 },
        context: { x: 960, y: 65, width: 1360 },
        focus: { x: 1350, y: 510, width: 880 },
      },
      compact: {
        presentation: "stacked-highlights", width: 1200, height: 1600,
        code: { x: 72, y: 40, width: 1056, height: 660, fontSize: 42, lineHeight: 54, entryGap: 8, paddingHorizontal: 24, suffixScale: 0.6, highlightRows: true },
        focus: { x: 160, y: 830, width: 880, headerHeight: 64, cropBreakHeight: 10, outlineInset: 12, outlineTop: 13, cornerRadius: 9, selectedRowsOnly: true },
      },
    },
  },
  {
    id: "homepage-session-list", scene: "session-list",
    configFile: "landing_page/visual_assets/runtime/proof-batch/session-list.json",
    feature: "feature-plugins", slot: 2,
    alt: "The pin, archive, and status plugins provide the real star and action-bar controls in a session list with titles, subtitles, and To do, In progress, and Done states.",
    layouts: {
      wide: {
        width: 2400, height: 1350,
        code: { x: 50, y: 310, width: 830, height: 850, fontSize: 32, lineHeight: 56, entryGap: 38 },
        context: { x: 960, y: 65, width: 1360 },
        focus: { x: 1350, y: 730, width: 880, listRow: true },
      },
      compact: {
        presentation: "stacked-list", width: 1200, height: 1600,
        code: { x: 72, y: 40, width: 1056, height: 660, fontSize: 42, lineHeight: 54, entryGap: 8, paddingHorizontal: 24, suffixScale: 0.6, highlightRows: true },
        context: { x: 230, y: 665, width: 740 },
        focus: { x: 96, y: 1100, width: 1008, listRow: true },
      },
    },
  },
  {
    id: "homepage-compiled-instructions", scene: "compiled", type: "report",
    feature: "feature-transparency", slot: 0,
    alt: "The real compiled-system-message window shows the beginning of the current Codex default instructions.",
    wideReportHeight: 390,
    compactExcerpts: [
      { source: "report-compact", x: 0, y: 0, width: 360, height: 580,
        destination: { x: 110, y: 10, width: 980 } },
    ],
  },
  {
    id: "homepage-usage-overview", scene: "usage-overview", type: "report",
    feature: "feature-transparency", slot: 1, sampleData: true,
    sampleNotice: "Sample data. This example assumes about $550 for 100% of a seven-day ChatGPT window.",
    alt: "A plugin-driven illustrative report shows three days of claude and zai bucket costs alongside ChatGPT usage since reset, $220.00 estimated cost, and a 0% to 40% weekly usage change.",
    wideReportHeight: 500,
    reportOnly: true,
    compactExcerpts: [
      { source: "report-compact", x: 0, y: 0, width: 360, height: 515,
        destination: { x: 60, y: 20, width: 1080 } },
    ],
  },
  {
    id: "homepage-cost-report", scene: "cost", type: "report",
    feature: "feature-transparency", slot: 1, sampleData: true,
    sampleNotice: "Sample data. Totals combine recorded and estimated costs.",
    alt: "A real cost report over sample records shows recorded totals, provider buckets, and activity by project and day, with related usage metadata.",
    wideReportHeight: 565,
    metadataExcerpt: {
      x: 15, y: 581, width: 330, height: 37,
      destination: { x: 60, y: 1120, width: 760 },
    },
    compactExcerpts: [
      { source: "report", x: 0, y: 0, width: 365, height: 294,
        destination: { x: 96, y: 40, width: 1008 } },
      { source: "report", x: 25, y: 302, width: 340, height: 235,
        destination: { x: 96, y: 895, width: 1008 } },
    ],
  },
  {
    id: "homepage-chatgpt-usage", scene: "usage", type: "report",
    feature: "feature-transparency", slot: 2, sampleData: true,
    alt: "The real ChatGPT usage report over sample journal records shows estimated token and cost totals, remaining limits, reset times, and usage history.",
    wideReportHeight: 518,
    compactExcerpts: [
      { source: "report", x: 0, y: 0, width: 420, height: 345,
        destination: { x: 60, y: 40, width: 1080 } },
      { source: "report", x: 20, y: 350, width: 400, height: 165,
        destination: { x: 60, y: 1075, width: 1080 } },
    ],
  },
].map(recipe => ({
  maxBytes: 240000,
  captureDirectory: `desktop/crystal-lattice-control-desktop-rn/artifacts/website-proof-batch/${recipe.scene}`,
  candidateDirectory: `artifacts/visual-assets/${recipe.id}`,
  previewPrefix: `/__preview/proof-batch/${recipe.scene}`,
  recipeFile: "visual_assets/proof-batch-recipes.mjs",
  ...recipe,
}));