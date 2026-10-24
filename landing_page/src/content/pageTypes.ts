import type { Root } from "mdast";

export type SectionBase<Type extends string> = {
  type: Type;
  id?: string;
  eyebrow?: string;
  title?: string;
  body?: string | string[];
};

export type ActionVariant = "primary" | "outline";
export type ActionIcon = "arrow" | "github";

export type LinkAction = {
  label: string;
  href: string;
  variant: ActionVariant;
  icon?: ActionIcon;
  target?: string;
};

export type InstallationLink = {
  label: string;
  href: string;
  target?: string;
};

export type InstallationCommandMethod = {
  id: string;
  tabLabel: string;
  panelLabel: string;
  kind: "command";
  prompt: string;
  command: string;
  support: string;
  documentation: InstallationLink;
};

export type InstallationManualMethod = {
  id: string;
  tabLabel: string;
  panelLabel: string;
  kind: "manual";
  description: string;
  platforms: string[];
  download: InstallationLink;
  documentation: InstallationLink;
};

export type InstallationChooserContent = {
  ariaLabel: string;
  defaultMethod: string;
  methods: Array<InstallationCommandMethod | InstallationManualMethod>;
};

export type CodeSnippet = {
  language?: string;
  value: string;
  status?: string;
};

export type FeatureMediaAsset = {
  label?: string;
  description?: string;
  src?: string;
  srcDark?: string;
  alt?: string;
  width?: number;
  height?: number;
  placeholder?: string;
  srcCompact?: string;
  srcCompactDark?: string;
  widthCompact?: number;
  heightCompact?: number;
};

export type MediaPlaceholder = {
  kind?: string;
  status?: string;
  src?: string;
  srcDark?: string;
  alt?: string;
  secondarySrc?: string;
  secondarySrcDark?: string;
  secondaryAlt?: string;
  secondaryWidth?: number;
  secondaryHeight?: number;
  width?: number;
  height?: number;
  desktop?: string;
  assets?: FeatureMediaAsset[];
};

export type HeroSection = SectionBase<"hero"> & {
  badge?: string;
  titleHtml: string;
  subtitle: string;
  actions?: LinkAction[];
  install?: InstallationChooserContent;
};

export type ProvidersSection = SectionBase<"providers"> & {
  label: string;
  providers?: string[];
};

export type FeaturesSection = SectionBase<"features"> & {
  items?: Array<{
    icon: "lock" | "provider" | "stream" | "file" | "tool" | "plugin" | string;
    title: string;
    desc?: string;
    descHtml?: string;
  }>;
};

export type QuickstartSection = SectionBase<"quickstart"> & {
  steps?: Array<{
    num: string;
    title: string;
    body?: Array<{ html: string }>;
    codeBlocks?: string[];
    after?: Array<{ html: string }>;
    afterCodeBlocks?: string[];
  }>;
};

export type CtaSection = SectionBase<"cta"> & {
  actions?: LinkAction[];
};

export type ActionGuideSection = SectionBase<"actionGuide"> & {
  body?: string[];
  note?: string;
  action?: {
    title?: string;
    steps?: Array<{
      label: string;
      text?: string;
      link?: {
        label: string;
        href: string;
      };
      code?: string;
    }>;
  };
  visual?: MediaPlaceholder;
};

export type FeatureMatrixColumn = {
  key: string;
  label: string;
};

export type FeatureMatrixSection = SectionBase<"featureMatrix"> & {
  intro?: string;
  columns?: FeatureMatrixColumn[];
  rows?: Array<Record<string, string>>;
};

export type FeatureShowcaseSection = SectionBase<"featureShowcase"> & {
  body?: string[];
  layout?: "two-column" | "three-column";
  presentation?: "cards" | "editorial";
  reviewStatus?: string;
  items?: Array<{
    id?: string;
    layout?: "compact" | "full-width";
    title: string;
    description: string;
    reviewStatus?: string;
    media?: MediaPlaceholder;
  }>;
  visual?: MediaPlaceholder;
};

export type ProductWalkthroughFrame = {
  id: string;
  title: string;
  caption: string;
  image: {
    src: string;
    srcDark?: string;
    srcCompact?: string;
    srcCompactDark?: string;
    alt: string;
    width: number;
    height: number;
    widthCompact?: number;
    heightCompact?: number;
  };
};

export type ProductWalkthroughChapter = {
  id: string;
  label: string;
  title: string;
  role: string;
  distinction: string;
  frames: ProductWalkthroughFrame[];
};

export type ProductWalkthroughSection = SectionBase<"productWalkthrough"> & {
  intro: string;
  chapters: ProductWalkthroughChapter[];
};

export type ProductOverviewImage = {
  id: string;
  title: string;
  caption: string;
  src: string;
  srcDark?: string;
  srcCompact?: string;
  srcCompactDark?: string;
  alt: string;
  width: number;
  height: number;
  widthCompact?: number;
  heightCompact?: number;
};

export type ProductOverviewStory = {
  id: string;
  number: string;
  title: string;
  description: string;
  detail: string;
  images: ProductOverviewImage[];
};

export type ProductOverviewSection = SectionBase<"productOverview"> & {
  intro: string;
  stories: ProductOverviewStory[];
};

export type GettingStartedPlatform = {
  id: string;
  label: string;
  status: "available" | "coming-soon";
  detail?: string;
};

export type GettingStartedMethod = {
  title: string;
  description: string;
  code?: string;
};

export type GettingStartedStep = {
  id: string;
  kind:
    | "install"
    | "command"
    | "desktop-download"
    | "desktop-connect"
    | "mobile-download"
    | "mobile-connect";
  title: string;
  description: string;
  reviewStatus?: string;
  install?: InstallationChooserContent;
  code?: string;
  platforms?: GettingStartedPlatform[];
  methods?: GettingStartedMethod[];
  media?: MediaPlaceholder;
  waitlist?: {
    label: string;
    status: "disabled-prototype";
    note?: string;
  };
};

export type GettingStartedSection = SectionBase<"gettingStarted"> & {
  intro?: string;
  reviewStatus?: string;
  steps?: GettingStartedStep[];
};

export type FeatureCodeShowcaseSection = SectionBase<"featureCodeShowcase"> & {
  body?: string[];
  note?: string;
  cards?: Array<{
    title: string;
    description: string;
    code?: CodeSnippet;
  }>;
};

export type ScreenshotGallerySection = SectionBase<"screenshotGallery"> & {
  body?: string[];
  gallery?: Array<{
    title: string;
    description: string;
    src?: string;
    srcDark?: string;
    alt?: string;
    width?: number;
    height?: number;
    status?: string;
    placeholder?: string;
  }>;
};

export type PromptBlockSection = SectionBase<"promptBlock"> & {
  intro?: string;
  prompt: string;
  configExample?: {
    code?: string;
    language?: string;
  };
};

export type CodeExampleSection = SectionBase<"codeExample"> & {
  body?: string[];
  code?: CodeSnippet;
};

export type MobileIcon = "apple" | "android" | "play" | "github" | string;

export type StoreButton = {
  href: string;
  className?: string;
  icon: MobileIcon;
  sub: string;
  name: string;
  comingSoon?: boolean;
};

export type MobileHeroSection = SectionBase<"mobileHero"> & {
  label: string;
  titleHtml: string;
  subtitle: string;
  platforms?: Array<{
    label: string;
    icon: MobileIcon;
  }>;
  storeButtons?: StoreButton[];
  note?: string;
  image?: {
    src: string;
    srcDark?: string;
    alt: string;
    width?: number;
    height?: number;
  };
};

export type MobileFeaturesSection = SectionBase<"mobileFeatures"> & {
  titleHtml: string;
  items?: Array<{
    icon: "stream" | "chat" | "provider" | "plugin" | "wifi" | "info" | string;
    title: string;
    desc: string;
  }>;
};

export type MobileConnectSection = SectionBase<"mobileConnect"> & {
  methods?: Array<{
    num: string;
    title: string;
    desc: string;
    code: string;
  }>;
};

export type MobileDownloadSection = SectionBase<"mobileDownload"> & {
  storeButtons?: StoreButton[];
  noteHtml?: string;
};

export type LegalContentSection = SectionBase<"legalContent"> & {
  label: string;
  meta: string;
  sections?: Array<{
    title: string;
    blocks?: Array<
      | { type: "paragraph"; html: string }
      | { type: "list"; items?: string[] }
    >;
  }>;
};

export type PageSection =
  | HeroSection
  | ProvidersSection
  | FeaturesSection
  | QuickstartSection
  | CtaSection
  | ActionGuideSection
  | FeatureMatrixSection
  | FeatureShowcaseSection
  | ProductWalkthroughSection
  | ProductOverviewSection
  | GettingStartedSection
  | FeatureCodeShowcaseSection
  | ScreenshotGallerySection
  | PromptBlockSection
  | CodeExampleSection
  | MobileHeroSection
  | MobileFeaturesSection
  | MobileConnectSection
  | MobileDownloadSection
  | LegalContentSection;

export type MarkdownDocument = {
  sourcePath: string;
  frontmatter: Record<string, unknown>;
  ast: Root;
};

export type SectionPrepareContext = {
  loadMarkdown: (source: string) => MarkdownDocument;
};

export type SectionDefinition = {
  type: PageSection["type"];
  Component: unknown;
  prepare?: (
    section: Record<string, unknown> & { type: string },
    context: SectionPrepareContext,
  ) => Record<string, unknown> & { type: string };
};

export type PageDocument = {
  seo?: {
    title?: string;
    description?: string;
  };
  nav?: Array<{
    label: string;
    href: string;
  }>;
  sections: PageSection[];
};
