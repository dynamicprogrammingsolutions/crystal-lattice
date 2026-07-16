import {
  deriveInvertedTranscriptScrollState,
  scrollInvertedTranscriptToBottom,
  scrollInvertedTranscriptToTop,
} from "../src/invertedTranscriptScroll";

describe("deriveInvertedTranscriptScrollState", () => {
  test("treats offset zero as the visual bottom", () => {
    expect(
      deriveInvertedTranscriptScrollState(
        {
          offsetY: 0,
          viewportHeight: 600,
          contentHeight: 1800,
        },
        40
      )
    ).toMatchObject({
      maxOffsetY: 1200,
      topGapPx: 1200,
      bottomGapPx: 0,
      canScrollToTop: true,
      canScrollToBottom: false,
      pinnedToBottom: true,
    });
  });

  test("treats maximum offset as the visual top", () => {
    expect(
      deriveInvertedTranscriptScrollState(
        {
          offsetY: 1200,
          viewportHeight: 600,
          contentHeight: 1800,
        },
        40
      )
    ).toMatchObject({
      topGapPx: 0,
      bottomGapPx: 1200,
      canScrollToTop: false,
      canScrollToBottom: true,
      pinnedToBottom: false,
    });
  });

  test("shows both edge actions in the middle", () => {
    expect(
      deriveInvertedTranscriptScrollState(
        {
          offsetY: 500,
          viewportHeight: 600,
          contentHeight: 1800,
        },
        40
      )
    ).toMatchObject({
      topGapPx: 700,
      bottomGapPx: 500,
      canScrollToTop: true,
      canScrollToBottom: true,
    });
  });

  test("shows no edge actions when content fits in the viewport", () => {
    expect(
      deriveInvertedTranscriptScrollState(
        {
          offsetY: 30,
          viewportHeight: 600,
          contentHeight: 400,
        },
        40
      )
    ).toMatchObject({
      offsetY: 0,
      maxOffsetY: 0,
      topGapPx: 0,
      bottomGapPx: 0,
      canScrollToTop: false,
      canScrollToBottom: false,
      pinnedToBottom: true,
    });
  });

  test("clamps overscroll and uses a strict threshold", () => {
    expect(
      deriveInvertedTranscriptScrollState(
        {
          offsetY: -20,
          viewportHeight: 100,
          contentHeight: 140,
        },
        40
      )
    ).toMatchObject({
      offsetY: 0,
      topGapPx: 40,
      canScrollToTop: false,
      canScrollToBottom: false,
    });

    expect(
      deriveInvertedTranscriptScrollState(
        {
          offsetY: 50,
          viewportHeight: 100,
          contentHeight: 140,
        },
        0
      )
    ).toMatchObject({
      offsetY: 40,
      topGapPx: 0,
      bottomGapPx: 40,
      canScrollToTop: false,
      canScrollToBottom: true,
    });
  });
});

describe("inverted transcript edge commands", () => {
  test("maps visual top to the inverted list end", () => {
    const list = {
      scrollToEnd: jest.fn(),
      scrollToOffset: jest.fn(),
    };

    scrollInvertedTranscriptToTop(list);

    expect(list.scrollToEnd).toHaveBeenCalledWith({ animated: true });
    expect(list.scrollToOffset).not.toHaveBeenCalled();
  });

  test("maps visual bottom to offset zero", () => {
    const list = {
      scrollToEnd: jest.fn(),
      scrollToOffset: jest.fn(),
    };

    scrollInvertedTranscriptToBottom(list, false);

    expect(list.scrollToOffset).toHaveBeenCalledWith({
      offset: 0,
      animated: false,
    });
    expect(list.scrollToEnd).not.toHaveBeenCalled();
  });
});
