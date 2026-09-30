import { defineCollection, z } from "astro:content";

const pages = defineCollection({
  type: "data",
  schema: z.object({
    seo: z.object({
      title: z.string().optional(),
      description: z.string().optional(),
    }).optional(),
    nav: z.array(z.object({
      label: z.string(),
      href: z.string(),
    })).optional(),
    sections: z.array(z.object({
      type: z.string(),
    }).passthrough()),
  }).passthrough(),
});

const markdown = defineCollection({
  type: "content",
  schema: z.object({}).passthrough(),
});

const releases = defineCollection({
  type: "data",
  schema: z.object({
    product: z.string(),
    version: z.string(),
    buildNumber: z.number().int().positive(),
    minimumMacos: z.string(),
    architectures: z.array(z.string()).min(1),
    dmg: z.object({
      filename: z.string(),
      url: z.string().url(),
      sha256: z.string().regex(/^[0-9a-f]{64}$/),
    }),
  }),
});

export const collections = { pages, markdown, releases };
