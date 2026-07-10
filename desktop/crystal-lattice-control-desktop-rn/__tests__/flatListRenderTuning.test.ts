import { resolveFlatListRenderTuning } from '../src/ui/flatListRenderTuning';

const configuredTuning = {
  initialNumToRender: 12,
  maxToRenderPerBatch: 18,
  updateCellsBatchingPeriod: 40,
  removeClippedSubviews: true,
};

describe('resolveFlatListRenderTuning', () => {
  it.each([undefined, 0, -1, Number.NaN])(
    'keeps configured virtualization tuning when threshold is %s',
    (eagerRenderThreshold) => {
      expect(
        resolveFlatListRenderTuning({
          rowCount: 50,
          eagerRenderThreshold,
          ...configuredTuning,
        }),
      ).toEqual({
        eagerRenderAll: false,
        ...configuredTuning,
      });
    },
  );

  it('eagerly renders every transcript row at or below the threshold', () => {
    expect(
      resolveFlatListRenderTuning({
        rowCount: 100,
        eagerRenderThreshold: 100,
        ...configuredTuning,
      }),
    ).toEqual({
      eagerRenderAll: true,
      initialNumToRender: 100,
      maxToRenderPerBatch: 100,
      updateCellsBatchingPeriod: 0,
      removeClippedSubviews: false,
    });
  });

  it('keeps configured virtualization tuning above the threshold', () => {
    expect(
      resolveFlatListRenderTuning({
        rowCount: 101,
        eagerRenderThreshold: 100,
        ...configuredTuning,
      }),
    ).toEqual({
      eagerRenderAll: false,
      ...configuredTuning,
    });
  });

  it('keeps transient synthetic rows eager when the message count is at the threshold', () => {
    expect(
      resolveFlatListRenderTuning({
        rowCount: 101,
        eagerRenderEligibilityCount: 100,
        eagerRenderThreshold: 100,
        ...configuredTuning,
      }),
    ).toEqual({
      eagerRenderAll: true,
      initialNumToRender: 101,
      maxToRenderPerBatch: 101,
      updateCellsBatchingPeriod: 0,
      removeClippedSubviews: false,
    });
  });

  it('uses a valid minimum batch size for an empty transcript', () => {
    expect(
      resolveFlatListRenderTuning({
        rowCount: 0,
        eagerRenderThreshold: 100,
      }),
    ).toEqual({
      eagerRenderAll: true,
      initialNumToRender: 1,
      maxToRenderPerBatch: 1,
      updateCellsBatchingPeriod: 0,
      removeClippedSubviews: false,
    });
  });
});