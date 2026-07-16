export type InvertedTranscriptScrollMetrics = {
  offsetY: number;
  viewportHeight: number;
  contentHeight: number;
};

export type InvertedTranscriptScrollState = {
  offsetY: number;
  viewportHeight: number;
  contentHeight: number;
  maxOffsetY: number;
  topGapPx: number;
  bottomGapPx: number;
  canScrollToTop: boolean;
  canScrollToBottom: boolean;
  pinnedToBottom: boolean;
};

export type InvertedTranscriptScrollable = {
  scrollToEnd: (options: { animated: boolean }) => void;
  scrollToOffset: (options: { offset: number; animated: boolean }) => void;
};

function finiteNonNegative(value: number): number {
  return Number.isFinite(value) ? Math.max(0, value) : 0;
}

export function deriveInvertedTranscriptScrollState(
  metrics: InvertedTranscriptScrollMetrics,
  thresholdPx: number
): InvertedTranscriptScrollState {
  const viewportHeight = finiteNonNegative(metrics.viewportHeight);
  const contentHeight = finiteNonNegative(metrics.contentHeight);
  const maxOffsetY = Math.max(0, contentHeight - viewportHeight);
  const offsetY = Math.min(maxOffsetY, finiteNonNegative(metrics.offsetY));
  const bottomGapPx = offsetY;
  const topGapPx = Math.max(0, maxOffsetY - offsetY);
  const threshold = finiteNonNegative(thresholdPx);
  const hasMeasuredViewport = viewportHeight > 0;

  return {
    offsetY,
    viewportHeight,
    contentHeight,
    maxOffsetY,
    topGapPx,
    bottomGapPx,
    canScrollToTop: hasMeasuredViewport && topGapPx > threshold,
    canScrollToBottom: hasMeasuredViewport && bottomGapPx > threshold,
    pinnedToBottom: bottomGapPx <= threshold,
  };
}

export function scrollInvertedTranscriptToTop(
  list: InvertedTranscriptScrollable | null | undefined,
  animated = true
): void {
  list?.scrollToEnd({ animated });
}

export function scrollInvertedTranscriptToBottom(
  list: InvertedTranscriptScrollable | null | undefined,
  animated = true
): void {
  list?.scrollToOffset({ offset: 0, animated });
}
