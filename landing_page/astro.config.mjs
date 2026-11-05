import { defineConfig } from 'astro/config';
import {
  cpSync,
  createReadStream,
  existsSync,
  readdirSync,
  statSync,
} from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import tailwindcss from '@tailwindcss/vite';
import {
  sessionActionsPreviewEnabled,
  sessionActionsPreviewIntegration,
} from './scripts/visual-assets/session-actions-preview.mjs';
import {
  isStagingSite,
  siteOutputDirectory,
} from './site-variant.mjs';

const siteUrl =
  process.env.PUBLIC_CRYSTAL_LATTICE_SITE_URL ??
  (isStagingSite
    ? 'https://staging.crystallattice.dev'
    : 'https://crystallattice.dev');
const stagingPublicDirectory = path.resolve('./sites/staging/public');

function stagingPublicAssets() {
  return {
    name: 'crystal-lattice-staging-public-assets',
    hooks: {
      'astro:server:setup': ({ server }) => {
        if (!isStagingSite || !existsSync(stagingPublicDirectory)) return;
        server.middlewares.use((request, response, next) => {
          const pathname = decodeURIComponent(
            new URL(request.url ?? '/', 'http://localhost').pathname,
          );
          const candidate = path.resolve(
            stagingPublicDirectory,
            `.${pathname}`,
          );
          if (
            candidate !== stagingPublicDirectory &&
            !candidate.startsWith(`${stagingPublicDirectory}${path.sep}`)
          ) {
            next();
            return;
          }
          if (!existsSync(candidate) || !statSync(candidate).isFile()) {
            next();
            return;
          }
          if (candidate.endsWith('.webp')) {
            response.setHeader('Content-Type', 'image/webp');
          }
          createReadStream(candidate).pipe(response);
        });
      },
      'astro:build:done': ({ dir }) => {
        if (!isStagingSite || !existsSync(stagingPublicDirectory)) return;
        const outputDirectory = fileURLToPath(dir);
        for (const entry of readdirSync(stagingPublicDirectory)) {
          cpSync(
            path.join(stagingPublicDirectory, entry),
            path.join(outputDirectory, entry),
            { recursive: true },
          );
        }
      },
    },
  };
}

export default defineConfig({
  site: siteUrl,
  outDir: siteOutputDirectory(),
  ...(sessionActionsPreviewEnabled ? {
    outDir: './artifacts/plugin-session-actions-site/',
  } : {}),
  integrations: [
    stagingPublicAssets(),
    ...(sessionActionsPreviewEnabled ? [sessionActionsPreviewIntegration()] : []),
  ],

  vite: {
    plugins: [tailwindcss()],
  },
});