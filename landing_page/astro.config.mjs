import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

const siteUrl =
  process.env.PUBLIC_CRYSTAL_LATTICE_SITE_URL ?? 'https://crystallattice.dev';

export default defineConfig({
  site: siteUrl,

  vite: {
    plugins: [tailwindcss()],
  },
});