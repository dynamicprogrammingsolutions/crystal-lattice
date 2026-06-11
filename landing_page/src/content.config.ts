import { defineCollection, z } from "astro:content";

const pages = defineCollection({
  type: "data",
  schema: z.any(),
});

const markdown = defineCollection({
  type: "content",
  schema: z.any(),
});

export const collections = { pages, markdown };
