import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://crystallattice.dev',  // to be replaced with actual url

  vite: {
    plugins: [tailwindcss()],
  },
});