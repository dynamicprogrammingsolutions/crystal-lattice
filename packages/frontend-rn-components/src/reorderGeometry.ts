export interface ReorderItemFrame {
  x: number;
  y: number;
  width: number;
  height: number;
}

export type ReorderPreviewSlot<T> =
  | { kind: 'item'; item: T }
  | { kind: 'placeholder' };

export type ReorderRenderSlot<T> =
  | ReorderPreviewSlot<T>
  | { kind: 'dragged'; item: T };

export function moveReorderValues<T>(
  items: readonly T[],
  sourceIndex: number,
  targetIndex: number,
): T[] {
  if (
    sourceIndex < 0 ||
    sourceIndex >= items.length ||
    targetIndex < 0 ||
    targetIndex >= items.length ||
    sourceIndex === targetIndex
  ) {
    return [...items];
  }
  const moved = [...items];
  const [item] = moved.splice(sourceIndex, 1);
  moved.splice(targetIndex, 0, item);
  return moved;
}

export function applyReorderKeyOrder<T extends { key: string }>(
  items: readonly T[],
  orderedKeys: readonly string[],
): T[] {
  const itemsByKey = new Map(items.map(item => [item.key, item]));
  const ordered = orderedKeys.flatMap(key => {
    const item = itemsByKey.get(key);
    if (!item) return [];
    itemsByKey.delete(key);
    return [item];
  });
  return [...ordered, ...itemsByKey.values()];
}

export function resolveReorderDropTranslation(
  slotFrames: readonly ReorderItemFrame[],
  sourceIndex: number,
  targetIndex: number,
): { x: number; y: number } {
  const sourceFrame = slotFrames[sourceIndex];
  const targetFrame = slotFrames[targetIndex];
  if (!sourceFrame || !targetFrame) return { x: 0, y: 0 };
  return {
    x: targetFrame.x - sourceFrame.x,
    y: targetFrame.y - sourceFrame.y,
  };
}

function frameCenter(frame: ReorderItemFrame): { x: number; y: number } {
  return {
    x: frame.x + frame.width / 2,
    y: frame.y + frame.height / 2,
  };
}

export function resolveReorderDropTarget(
  slotFrames: readonly ReorderItemFrame[],
  sourceIndex: number,
  translationX: number,
  translationY: number,
): number {
  const sourceFrame = slotFrames[sourceIndex];
  if (!sourceFrame || slotFrames.length === 0) return sourceIndex;

  const sourceCenter = frameCenter(sourceFrame);
  const draggedCenter = {
    x: sourceCenter.x + translationX,
    y: sourceCenter.y + translationY,
  };
  let nearestIndex = sourceIndex;
  let nearestDistance = Number.POSITIVE_INFINITY;

  slotFrames.forEach((frame, index) => {
    const center = frameCenter(frame);
    const distance =
      (center.x - draggedCenter.x) ** 2 + (center.y - draggedCenter.y) ** 2;
    if (distance < nearestDistance) {
      nearestDistance = distance;
      nearestIndex = index;
    }
  });

  return nearestIndex;
}

export function buildReorderPreview<T>(
  items: readonly T[],
  sourceIndex: number,
  targetIndex: number,
): ReorderPreviewSlot<T>[] {
  if (
    sourceIndex < 0 ||
    sourceIndex >= items.length ||
    targetIndex < 0 ||
    targetIndex >= items.length
  ) {
    return items.map(item => ({ kind: 'item', item }));
  }

  const remaining = items.filter((_item, index) => index !== sourceIndex);
  const slots: ReorderPreviewSlot<T>[] = remaining.map(item => ({
    kind: 'item',
    item,
  }));
  slots.splice(targetIndex, 0, { kind: 'placeholder' });
  return slots;
}

export function buildReorderRenderSlots<T>(
  items: readonly T[],
  sourceIndex: number,
  targetIndex: number,
): ReorderRenderSlot<T>[] {
  const draggedItem = items[sourceIndex];
  if (!draggedItem) {
    return items.map(item => ({ kind: 'item', item }));
  }

  const preview = buildReorderPreview(items, sourceIndex, targetIndex);
  const rendered: ReorderRenderSlot<T>[] = [];
  let previewIndex = 0;
  for (let childIndex = 0; childIndex <= items.length; childIndex += 1) {
    if (childIndex === sourceIndex) {
      rendered.push({ kind: 'dragged', item: draggedItem });
    } else {
      const slot = preview[previewIndex];
      if (slot) rendered.push(slot);
      previewIndex += 1;
    }
  }
  return rendered;
}
