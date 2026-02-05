function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export interface Rgb {
  r: number;
  g: number;
  b: number;
}

export interface Rgba extends Rgb {
  a: number;
}

export function parseColorToRgb(color: string): Rgb | null {
  const trimmed = color.trim();

  if (trimmed.startsWith('#')) {
    const hex = trimmed.slice(1);
    if (hex.length === 3) {
      const r = parseInt(hex[0] + hex[0], 16);
      const g = parseInt(hex[1] + hex[1], 16);
      const b = parseInt(hex[2] + hex[2], 16);
      if ([r, g, b].some((value) => Number.isNaN(value))) return null;
      return { r, g, b };
    }
    if (hex.length === 6 || hex.length === 8) {
      const r = parseInt(hex.slice(0, 2), 16);
      const g = parseInt(hex.slice(2, 4), 16);
      const b = parseInt(hex.slice(4, 6), 16);
      if ([r, g, b].some((value) => Number.isNaN(value))) return null;
      return { r, g, b };
    }
    return null;
  }

  const rgbaMatch = trimmed.match(
    /^rgba\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)$/i,
  );
  if (rgbaMatch) {
    const r = Number(rgbaMatch[1]);
    const g = Number(rgbaMatch[2]);
    const b = Number(rgbaMatch[3]);
    if ([r, g, b].some((value) => !Number.isFinite(value))) return null;
    return { r, g, b };
  }

  const rgbMatch = trimmed.match(
    /^rgb\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)$/i,
  );
  if (rgbMatch) {
    const r = Number(rgbMatch[1]);
    const g = Number(rgbMatch[2]);
    const b = Number(rgbMatch[3]);
    if ([r, g, b].some((value) => !Number.isFinite(value))) return null;
    return { r, g, b };
  }

  return null;
}

export function parseColorToRgba(color: string): Rgba | null {
  const trimmed = color.trim();

  if (trimmed.startsWith('#')) {
    const rgb = parseColorToRgb(trimmed);
    if (!rgb) return null;
    return { ...rgb, a: 1 };
  }

  const rgbaMatch = trimmed.match(
    /^rgba\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)$/i,
  );
  if (rgbaMatch) {
    const r = Number(rgbaMatch[1]);
    const g = Number(rgbaMatch[2]);
    const b = Number(rgbaMatch[3]);
    const a = Number(rgbaMatch[4]);
    if ([r, g, b, a].some((value) => !Number.isFinite(value))) return null;
    return { r, g, b, a: clamp(a, 0, 1) };
  }

  const rgbMatch = trimmed.match(
    /^rgb\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)$/i,
  );
  if (rgbMatch) {
    const r = Number(rgbMatch[1]);
    const g = Number(rgbMatch[2]);
    const b = Number(rgbMatch[3]);
    if ([r, g, b].some((value) => !Number.isFinite(value))) return null;
    return { r, g, b, a: 1 };
  }

  return null;
}

export function scaleAlpha(color: string, multiplier: number): string {
  const rgba = parseColorToRgba(color);
  if (!rgba) return color;
  const nextAlpha = clamp(rgba.a * multiplier, 0, 1);
  return rgbaString(rgba, nextAlpha);
}

export function rgbaString(rgb: Rgb, alpha: number): string {
  const a = clamp(alpha, 0, 1);
  return `rgba(${Math.round(clamp(rgb.r, 0, 255))}, ${Math.round(clamp(rgb.g, 0, 255))}, ${Math.round(clamp(rgb.b, 0, 255))}, ${a})`;
}

export function withAlpha(color: string, alpha: number): string {
  const rgb = parseColorToRgb(color);
  if (!rgb) return color;
  return rgbaString(rgb, alpha);
}

export function mixColors(colorA: string, colorB: string, t: number): string {
  const rgbA = parseColorToRgb(colorA);
  const rgbB = parseColorToRgb(colorB);
  if (!rgbA || !rgbB) return colorA;

  const clampedT = clamp(t, 0, 1);
  const r = rgbA.r + (rgbB.r - rgbA.r) * clampedT;
  const g = rgbA.g + (rgbB.g - rgbA.g) * clampedT;
  const b = rgbA.b + (rgbB.b - rgbA.b) * clampedT;
  return `rgb(${Math.round(r)}, ${Math.round(g)}, ${Math.round(b)})`;
}

function channelToLinear(value: number): number {
  const normalized = value / 255;
  return normalized <= 0.04045
    ? normalized / 12.92
    : ((normalized + 0.055) / 1.055) ** 2.4;
}

export function relativeLuminance(color: string): number {
  const rgb = parseColorToRgb(color);
  if (!rgb) return 0;
  const r = channelToLinear(rgb.r);
  const g = channelToLinear(rgb.g);
  const b = channelToLinear(rgb.b);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrastRatio(colorA: string, colorB: string): number {
  const l1 = relativeLuminance(colorA);
  const l2 = relativeLuminance(colorB);
  const lighter = Math.max(l1, l2);
  const darker = Math.min(l1, l2);
  return (lighter + 0.05) / (darker + 0.05);
}

export function pickTextOnColor(background: string): string {
  const white = '#FFFFFF';
  const black = '#000000';
  const whiteContrast = contrastRatio(background, white);
  const blackContrast = contrastRatio(background, black);
  return whiteContrast >= blackContrast ? white : black;
}
