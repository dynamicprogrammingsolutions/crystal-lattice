import ScreenshotGallery from "../components/ScreenshotGallery.astro";

export const screenshotGallerySection = {
  type: "screenshotGallery",
  Component: ScreenshotGallery,
} as const;
