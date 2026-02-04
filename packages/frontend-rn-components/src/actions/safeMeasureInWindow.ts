export function safeMeasureInWindow(
  current: any,
  cb: (layout: { x: number; y: number; width: number; height: number }) => void,
): boolean {
  if (!current || typeof current.measureInWindow !== 'function') {
    return false;
  }

  try {
    current.measureInWindow((x: number, y: number, width: number, height: number) => {
      cb({ x, y, width, height });
    });
    return true;
  } catch {
    return false;
  }
}
