import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { load } from "js-yaml";
import { isStagingSite, siteRoot } from "../../site-variant.mjs";
import type { PageDocument } from "./pageTypes";
import {
  sessionActionsPreviewAsset,
  sessionActionsPreviewEnabled,
  readSessionActionsRecipe,
  proofBatchPreviewEnabled,
  proofBatchPreviewFor,
  vibePreviewAsset,
} from "../../scripts/visual-assets/session-actions-preview.mjs";
import {
  applyWalkthroughCandidatePreview,
} from "../../scripts/visual-assets/walkthrough-candidate-preview.mjs";
import {
  applyWalkthroughFinalPreview,
} from "../../scripts/visual-assets/walkthrough-final-preview.mjs";
import {
  applyProductOverviewPreview,
} from "../../scripts/visual-assets/product-overview-preview.mjs";

const sharedPagesDir = join(process.cwd(), "src", "content", "pages");
const variantPagesDir = join(siteRoot(), "content", "pages");

export function loadPage(name: string): PageDocument {
  const variantPath = join(variantPagesDir, `${name}.yaml`);
  const sharedPath = join(sharedPagesDir, `${name}.yaml`);
  const path = existsSync(variantPath) ? variantPath : sharedPath;
  const parsed = load(readFileSync(path, "utf8"));
  if (!isPageDocument(parsed)) {
    throw new Error(`Invalid page content document: ${path}`);
  }
  const withProductionAdditions =
    !isStagingSite && name === "home"
      ? applyProductionHomeAdjustments(addProductionGettingStarted(parsed))
      : parsed;
  if (!isStagingSite || !sessionActionsPreviewEnabled || name !== "home") {
    return withProductionAdditions;
  }
  const previewAsset = sessionActionsPreviewAsset(readSessionActionsRecipe(process.cwd()));
  const previewPage = {
    ...withProductionAdditions,
    sections: withProductionAdditions.sections.map(section => section.type !== "featureShowcase" ? section : ({
      ...section,
      items: section.items?.map(item => item.id !== "feature-plugins"
        && !(proofBatchPreviewEnabled && ["feature-transparency", "feature-vibe-anything"].includes(item.id)) ? item : ({
        ...item,
        media: {
          ...item.media,
          assets: item.media?.assets?.map((asset, index) => {
            if (item.id === "feature-plugins" && index === 0) return { ...asset, ...previewAsset };
            if (item.id === "feature-vibe-anything" && index === 0) return { ...asset, ...vibePreviewAsset };
            const next = proofBatchPreviewEnabled ? proofBatchPreviewFor(item.id, index, process.cwd()) : undefined;
            return next ? {
              ...asset, ...next.asset,
              description: next.sampleData ? `${asset.description ?? ""} ${next.sampleNotice}`.trim() : asset.description,
            } : asset;
          }),
        },
      })),
    })),
  };
  return applyProductOverviewPreview(
    applyWalkthroughFinalPreview(
      applyWalkthroughCandidatePreview(previewPage),
    ),
  );
}

function addProductionGettingStarted(page: PageDocument): PageDocument {
  const sectionPath = join(
    siteRoot(),
    "content",
    "sections",
    "getting-started.yaml",
  );
  const section = load(readFileSync(sectionPath, "utf8"));
  if (
    !section ||
    typeof section !== "object" ||
    (section as { type?: unknown }).type !== "gettingStarted"
  ) {
    throw new Error(`Invalid production Getting Started section: ${sectionPath}`);
  }
  const heroIndex = page.sections.findIndex((item) => item.type === "hero");
  if (heroIndex < 0) {
    throw new Error("Production homepage is missing its historical hero");
  }
  return {
    ...page,
    sections: [
      ...page.sections.slice(0, heroIndex + 1),
      section as PageDocument["sections"][number],
      ...page.sections.slice(heroIndex + 1),
    ],
  };
}

function applyProductionHomeAdjustments(page: PageDocument): PageDocument {
  const adjustmentPath = join(
    siteRoot(),
    "content",
    "home-adjustments.yaml",
  );
  const adjustments = load(readFileSync(adjustmentPath, "utf8"));
  if (!adjustments || typeof adjustments !== "object") {
    throw new Error(`Invalid production homepage adjustments: ${adjustmentPath}`);
  }
  const heroAdjustments = (adjustments as {
    hero?: {
      removeInstall?: boolean;
      primaryAction?: { label?: string; href?: string };
    };
  }).hero;
  if (
    heroAdjustments?.removeInstall !== true ||
    !heroAdjustments.primaryAction?.label ||
    !heroAdjustments.primaryAction.href
  ) {
    throw new Error(
      `Production homepage adjustments must define the approved hero cleanup: ${adjustmentPath}`,
    );
  }
  return {
    ...page,
    sections: page.sections.map((section) => {
      if (section.type !== "hero") return section;
      const actions = Array.isArray(section.actions) ? section.actions : [];
      if (actions.length === 0) {
        throw new Error("Production homepage hero is missing its primary action");
      }
      return {
        ...section,
        install: undefined,
        actions: [
          {
            ...actions[0],
            label: heroAdjustments.primaryAction.label,
            href: heroAdjustments.primaryAction.href,
          },
          ...actions.slice(1),
        ],
      };
    }),
  };
}

function isPageDocument(value: unknown): value is PageDocument {
  if (!value || typeof value !== "object") {
    return false;
  }
  const sections = (value as { sections?: unknown }).sections;
  return (
    Array.isArray(sections) &&
    sections.every(
      (section) =>
        section &&
        typeof section === "object" &&
        typeof (section as { type?: unknown }).type === "string",
    )
  );
}
