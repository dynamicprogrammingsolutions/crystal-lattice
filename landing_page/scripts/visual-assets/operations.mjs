import { definePipeline } from "./api.mjs";

function operation(id, getArguments) {
  return {
    id,
    getArguments,
  };
}

export function imageMagickArguments(id, getArguments) {
  return operation(id, getArguments);
}

export function trim() {
  return operation("trim", () => ["-trim", "+repage"]);
}

export function crop(geometry) {
  return operation("crop", () => ["-crop", String(geometry), "+repage"]);
}

export function resize(geometry) {
  return operation("resize", () => ["-resize", String(geometry)]);
}

export function centerExtent(geometry) {
  return operation("center-extent", () => [
    "-gravity",
    "center",
    "-extent",
    String(geometry),
  ]);
}

export function normalizeSrgb() {
  return operation("normalize-srgb", () => ["-colorspace", "sRGB"]);
}

export function stripMetadata() {
  return operation("strip-metadata", () => ["-strip"]);
}

export function encodeWebp({ quality = 80, method = 6 } = {}) {
  return operation("encode-webp", () => [
    "-quality",
    String(quality),
    "-define",
    `webp:method=${method}`,
  ]);
}

export function imageMagickPipeline({ id, operations }) {
  const activeOperations = operations.filter(Boolean);
  return definePipeline({
    id,
    async run(context) {
      const args = [context.sourcePath];
      for (const current of activeOperations) {
        const operationArguments = await current.getArguments(context);
        args.push(...operationArguments);
      }
      args.push(context.candidatePath);
      await context.run("magick", args, {
        cwd: context.landingRoot,
        stdio: "pipe",
      });
    },
  });
}

export function focusCalloutPipeline({
  id,
  canvas,
  original,
  callout,
  quality = 80,
  method = 6,
}) {
  const originalBorder =
    original.borderWidth > 0
      ? [
          "-bordercolor",
          String(original.borderColor),
          "-border",
          `${original.borderWidth}x${original.borderWidth}`,
        ]
      : [];
  const calloutBorder =
    callout.borderWidth > 0
      ? [
          "-bordercolor",
          String(callout.borderColor),
          "-border",
          `${callout.borderWidth}x${callout.borderWidth}`,
        ]
      : [];

  return definePipeline({
    id,
    async run(context) {
      const args = [
        "(",
        "-size",
        `${canvas.width}x${canvas.height}`,
        `xc:${canvas.background}`,
        ")",
        "(",
        context.sourcePath,
        "-gravity",
        "northwest",
        "-crop",
        String(original.crop),
        "+repage",
        "-resize",
        `${original.width}x${original.height}!`,
        "-fill",
        "#000000",
        "-colorize",
        `${original.dimPercent}%`,
        ...originalBorder,
        ")",
        "-gravity",
        String(original.gravity),
        "-geometry",
        String(original.geometry),
        "-compose",
        "over",
        "-composite",
        "(",
        context.sourcePath,
        "-gravity",
        "northwest",
        "-crop",
        String(callout.crop),
        "+repage",
        "-resize",
        `${callout.width}x${callout.height}!`,
        ...calloutBorder,
        "(",
        "+clone",
        "-background",
        String(callout.shadow.color),
        "-shadow",
        String(callout.shadow.geometry),
        ")",
        "+swap",
        "-background",
        "none",
        "-layers",
        "merge",
        "+repage",
        ")",
        "-gravity",
        String(callout.gravity),
        "-geometry",
        String(callout.geometry),
        "-compose",
        "over",
        "-composite",
        "-colorspace",
        "sRGB",
        "-strip",
        "-quality",
        String(quality),
        "-define",
        `webp:method=${method}`,
        context.candidatePath,
      ];
      await context.run("magick", args, {
        cwd: context.landingRoot,
        stdio: "pipe",
      });
    },
  });
}