export type SectionDefinition = {
  type: string;
  Component: unknown;
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
  sections: Array<Record<string, unknown> & { type: string }>;
};
