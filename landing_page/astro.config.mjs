import { defineConfig } from 'astro/config';

import tailwindcss from '@tailwindcss/vite';
import {
  sessionActionsPreviewEnabled,
  sessionActionsPreviewIntegration,
} from './scripts/visual-assets/session-actions-preview.mjs';

const siteUrl =
  process.env.PUBLIC_CRYSTAL_LATTICE_SITE_URL ?? 'https://crystallattice.dev';

export default defineConfig({
  site: siteUrl,
  ...(sessionActionsPreviewEnabled ? {
    outDir: './artifacts/plugin-session-actions-site/',
    integrations: [sessionActionsPreviewIntegration()],
  } : {}),

  vite: {
    plugins: [tailwindcss()],
  },
});