import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import { validateContentBindings } from "../../scripts/visual-assets/validation.mjs";

test("a YAML media binding can target a section-owned image directly", () => {
  const landingRoot = fs.mkdtempSync(
    path.join(os.tmpdir(), "visual-assets-content-"),
  );
  const contentDirectory = path.join(landingRoot, "src", "content", "pages");
  fs.mkdirSync(contentDirectory, { recursive: true });
  fs.writeFileSync(
    path.join(contentDirectory, "mobile.yaml"),
    [
      "sections:",
      "  - type: mobileHero",
      "    id: mobile-hero",
      "    image:",
      "      src: /mobile-active-session.webp",
      "      srcDark: /mobile-active-session-dark.webp",
      "      alt: Active coding session",
      "      width: 1000",
      "      height: 2025",
      "",
    ].join("\n"),
  );

  assert.doesNotThrow(() =>
    validateContentBindings(
      {
        id: "mobile-active-session",
        presentation: {
          alt: "Active coding session",
          width: 1000,
          height: 2025,
        },
        contentBindings: [
          {
            kind: "yaml-media",
            file: "src/content/pages/mobile.yaml",
            sectionId: "mobile-hero",
            mediaField: "image",
            variantFields: {
              light: "src",
              dark: "srcDark",
            },
          },
        ],
        variants: {
          light: { output: "public/mobile-active-session.webp" },
          dark: { output: "public/mobile-active-session-dark.webp" },
        },
      },
      landingRoot,
      new Map(),
    ),
  );

  fs.rmSync(landingRoot, { recursive: true, force: true });
});