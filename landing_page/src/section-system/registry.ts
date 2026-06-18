import type { SectionDefinition } from "../content/pageTypes";
import { heroSection } from "../sections/hero";
import { providersSection } from "../sections/providers";
import { featuresSection } from "../sections/features";
import { quickstartSection } from "../sections/quickstart";
import { ctaSection } from "../sections/cta";
import { mobileHeroSection } from "../sections/mobileHero";
import { mobileFeaturesSection } from "../sections/mobileFeatures";
import { mobileConnectSection } from "../sections/mobileConnect";
import { mobileDownloadSection } from "../sections/mobileDownload";
import { legalContentSection } from "../sections/legalContent";

export const sectionDefinitions = [
  heroSection,
  providersSection,
  featuresSection,
  quickstartSection,
  ctaSection,
  mobileHeroSection,
  mobileFeaturesSection,
  mobileConnectSection,
  mobileDownloadSection,
  legalContentSection,
] satisfies SectionDefinition[];

export const sectionDefinitionByType = new Map(
  sectionDefinitions.map((definition) => [definition.type, definition]),
);
