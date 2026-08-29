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