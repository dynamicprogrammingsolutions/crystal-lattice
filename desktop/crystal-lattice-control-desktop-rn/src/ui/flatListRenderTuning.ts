export type FlatListRenderTuning = {
  eagerRenderAll: boolean;
  initialNumToRender?: number;
  maxToRenderPerBatch?: number;
  updateCellsBatchingPeriod?: number;
  removeClippedSubviews?: boolean;
};

export function resolveFlatListRenderTuning(params: {
  rowCount: number;
  eagerRenderEligibilityCount?: number;
  eagerRenderThreshold?: number;
  initialNumToRender?: number;
  maxToRenderPerBatch?: number;
  updateCellsBatchingPeriod?: number;
  removeClippedSubviews?: boolean;
}): FlatListRenderTuning {
  const rowCount = Number.isFinite(params.rowCount)
    ? Math.max(0, Math.floor(params.rowCount))
    : 0;
  const threshold =
    typeof params.eagerRenderThreshold === 'number' &&
    Number.isFinite(params.eagerRenderThreshold) &&
    params.eagerRenderThreshold > 0
      ? Math.floor(params.eagerRenderThreshold)
      : 0;
  const eligibilityCount =
    typeof params.eagerRenderEligibilityCount === 'number' &&
    Number.isFinite(params.eagerRenderEligibilityCount)
      ? Math.max(0, Math.floor(params.eagerRenderEligibilityCount))
      : rowCount;
  const eagerRenderAll = threshold > 0 && eligibilityCount <= threshold;

  if (!eagerRenderAll) {
    return {
      eagerRenderAll: false,
      initialNumToRender: params.initialNumToRender,
      maxToRenderPerBatch: params.maxToRenderPerBatch,
      updateCellsBatchingPeriod: params.updateCellsBatchingPeriod,
      removeClippedSubviews: params.removeClippedSubviews,
    };
  }

  const eagerBatchSize = Math.max(1, rowCount);
  return {
    eagerRenderAll: true,
    initialNumToRender: eagerBatchSize,
    maxToRenderPerBatch: eagerBatchSize,
    updateCellsBatchingPeriod: 0,
    removeClippedSubviews: false,
  };
}