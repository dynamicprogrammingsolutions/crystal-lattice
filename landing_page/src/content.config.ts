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

export const collections = { pages, markdown };
