import React from "react";
import { fireEvent, screen } from "@testing-library/react-native";

import { TranscriptEdgeButtons } from "../src/components/TranscriptEdgeButtons";
import { TranscriptRangeControls } from "../src/components/TranscriptRangeControls";
import { renderWithMobileProviders } from "../src/testUtils/renderWithMobileProviders";
import { DEFAULT_MOBILE_TRANSCRIPT_RANGE } from "../src/transcriptRange";

test("mobile transcript defaults to the same last-50 range as desktop", () => {
  expect(DEFAULT_MOBILE_TRANSCRIPT_RANGE).toEqual({
    startText: "-50",
    endText: "",
  });
});

describe("TranscriptRangeControls", () => {
  test("renders accessible range actions and dispatches their ids", () => {
    const onAction = jest.fn();
    renderWithMobileProviders(
      <TranscriptRangeControls
        buttons={[
          { id: "expandAbove", title: "Show 50 older messages" },
          { id: "showAll", title: "Show all" },
        ]}
        disabled={false}
        onAction={onAction}
        testID="range-top"
      />
    );

    fireEvent.press(screen.getByLabelText("Show 50 older messages"));
    fireEvent.press(screen.getByLabelText("Show all"));

    expect(onAction).toHaveBeenNthCalledWith(1, "expandAbove");
    expect(onAction).toHaveBeenNthCalledWith(2, "showAll");
  });

  test("does not dispatch disabled range actions", () => {
    const onAction = jest.fn();
    renderWithMobileProviders(
      <TranscriptRangeControls
        buttons={[{ id: "showLast", title: "Show last 50" }]}
        disabled
        onAction={onAction}
        testID="range-bottom"
      />
    );

    fireEvent.press(screen.getByLabelText("Show last 50"));

    expect(onAction).not.toHaveBeenCalled();
  });
});

describe("TranscriptEdgeButtons", () => {
  test("renders only requested edge actions with chevron icons", () => {
    renderWithMobileProviders(
      <TranscriptEdgeButtons
        canScrollToTop
        canScrollToBottom={false}
        onScrollToTop={jest.fn()}
        onScrollToBottom={jest.fn()}
      />
    );

    expect(screen.getByLabelText("Scroll to top")).toBeTruthy();
    expect(screen.queryByLabelText("Scroll to bottom")).toBeNull();
    expect(
      (screen.getByTestId("transcript-scroll-to-top") as any).findByType("Icon")
        .props.name
    ).toBe("chevron-up");
  });

  test("dispatches top and bottom navigation independently", () => {
    const onScrollToTop = jest.fn();
    const onScrollToBottom = jest.fn();
    renderWithMobileProviders(
      <TranscriptEdgeButtons
        canScrollToTop
        canScrollToBottom
        onScrollToTop={onScrollToTop}
        onScrollToBottom={onScrollToBottom}
      />
    );

    fireEvent.press(screen.getByLabelText("Scroll to top"));
    fireEvent.press(screen.getByLabelText("Scroll to bottom"));

    expect(onScrollToTop).toHaveBeenCalledTimes(1);
    expect(onScrollToBottom).toHaveBeenCalledTimes(1);
    expect(
      (screen.getByTestId("transcript-scroll-to-bottom") as any).findByType(
        "Icon"
      ).props.name
    ).toBe("chevron-down");
  });

  test("renders nothing when both edges are within threshold", () => {
    const { toJSON } = renderWithMobileProviders(
      <TranscriptEdgeButtons
        canScrollToTop={false}
        canScrollToBottom={false}
        onScrollToTop={jest.fn()}
        onScrollToBottom={jest.fn()}
      />
    );

    expect(toJSON()).toBeNull();
  });
});
