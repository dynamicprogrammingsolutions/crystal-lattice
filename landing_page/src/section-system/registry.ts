import type { SectionDefinition } from "../content/pageTypes";
import { heroSection } from "../sections/hero";
import { providersSection } from "../sections/providers";
import { featuresSection } from "../sections/features";
import { quickstartSection } from "../sections/quickstart";
import { ctaSection } from "../sections/cta";
import { actionGuideSection } from "../sections/actionGuide";
import { featureMatrixSection } from "../sections/featureMatrix";
import { featureShowcaseSection } from "../sections/featureShowcase";
import { productWalkthroughSection } from "../sections/productWalkthrough";
import { gettingStartedSection } from "../sections/gettingStarted";
import { featureCodeShowcaseSection } from "../sections/featureCodeShowcase";
import { screenshotGallerySection } from "../sections/screenshotGallery";
import { promptBlockSection } from "../sections/promptBlock";
import { codeExampleSection } from "../sections/codeExample";
import { mobileHeroSection } from "../sections/mobileHero";
import { mobileFeaturesSection } from "../sections/mobileFeatures";
import { mobileConnectSection } from "../sections/mobileConnect";
import { mobileDownloadSection } from "../sections/mobileDownload";
import { legalContentSection } from "../sections/legalContent";

export const sectionDefinitions: SectionDefinition[] = [
  heroSection,
  providersSection,
  featuresSection,
  quickstartSection,
  actionGuideSection,
  featureMatrixSection,
  featureShowcaseSection,
  productWalkthroughSection,
  gettingStartedSection,
  featureCodeShowcaseSection,
  screenshotGallerySection,
  promptBlockSection,
  codeExampleSection,
  ctaSection,
  mobileHeroSection,
  mobileFeaturesSection,
  mobileConnectSection,
  mobileDownloadSection,
  legalContentSection,
];

export const sectionDefinitionByType = new Map(
  sectionDefinitions.map((definition) => [definition.type, definition]),
);
