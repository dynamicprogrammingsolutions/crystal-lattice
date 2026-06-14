import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://crystallattice.dev.dynamicprogrammingsolutions.com',

  vite: {
    plugins: [tailwindcss()],
  },
});