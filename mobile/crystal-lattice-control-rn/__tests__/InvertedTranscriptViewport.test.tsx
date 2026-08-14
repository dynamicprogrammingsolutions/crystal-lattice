import React from "react";
import { View } from "react-native";
import { act, fireEvent, screen } from "@testing-library/react-native";

import { InvertedTranscriptViewport } from "../src/components/InvertedTranscriptViewport";
import { renderWithMobileProviders } from "../src/testUtils/renderWithMobileProviders";

const mockScrollToIndex = jest.fn();
const mockScrollToOffset = jest.fn();

jest.mock("../src/components/DependencyFlatList", () => {
  const ReactModule = require("react");
  const { View: MockView } = require("react-native");
  return {
    DependencyFlatList: ReactModule.forwardRef((props: any, ref: any) => {
      ReactModule.useImperativeHandle(ref, () => ({
        scrollToIndex: mockScrollToIndex,
        scrollToOffset: mockScrollToOffset,
      }));
      return ReactModule.createElement(MockView, props);
    }),
  };
});

describe("InvertedTranscriptViewport", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    mockScrollToIndex.mockReset();
    mockScrollToOffset.mockReset();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  test("progressively retries a far top navigation and keeps bottom navigation independent", () => {
    const data = Array.from({ length: 300 }, (_, index) => index);
    const listRef = React.createRef<any>();
    renderWithMobileProviders(
      <InvertedTranscriptViewport
        listRef={listRef}
        data={data}
        testID="transcript-list"
        keyExtractor={String}
        getItemDependencies={() => []}
        renderItem={({ item }) => <View testID={`row-${item}`} />}
      />
    );

    const list = screen.getByTestId("transcript-list");
    act(() => {
      list.props.onLayout({ nativeEvent: { layout: { height: 500 } } });
      list.props.onContentSizeChange(100, 5000);
      list.props.onScroll({
        nativeEvent: {
          contentOffset: { y: 0 },
          layoutMeasurement: { height: 500 },
          contentSize: { height: 5000 },
        },
      });
    });

    fireEvent.press(screen.getByLabelText("Scroll to top"));
    expect(mockScrollToIndex).toHaveBeenCalledWith({
      index: 299,
      animated: true,
      viewPosition: 0,
    });

    act(() => {
      list.props.onScrollToIndexFailed({
        index: 299,
        highestMeasuredFrameIndex: 20,
        averageItemLength: 100,
      });
    });
    expect(mockScrollToOffset).toHaveBeenCalledWith({
      offset: 29900,
      animated: false,
    });

    act(() => {
      jest.advanceTimersByTime(100);
    });
    expect(mockScrollToOffset).toHaveBeenLastCalledWith({
      offset: 4500,
      animated: false,
    });

    act(() => {
      list.props.onScroll({
        nativeEvent: {
          contentOffset: { y: 1000 },
          layoutMeasurement: { height: 500 },
          contentSize: { height: 5000 },
        },
      });
    });
    fireEvent.press(screen.getByLabelText("Scroll to bottom"));
    expect(mockScrollToOffset).toHaveBeenLastCalledWith({
      offset: 0,
      animated: true,
    });

    const callCountAfterBottom = mockScrollToOffset.mock.calls.length;
    act(() => {
      jest.advanceTimersByTime(1000);
    });
    expect(mockScrollToOffset).toHaveBeenCalledTimes(callCountAfterBottom);
  });

  test("reports drag and edge navigation intents before issuing commands", () => {
    const onUserNavigationIntent = jest.fn();
    const listRef = React.createRef<any>();
    renderWithMobileProviders(
      <InvertedTranscriptViewport
        listRef={listRef}
        data={[0, 1, 2]}
        testID="transcript-list"
        keyExtractor={String}
        getItemDependencies={() => []}
        renderItem={({ item }) => <View testID={`row-${item}`} />}
        onUserNavigationIntent={onUserNavigationIntent}
      />
    );

    const list = screen.getByTestId("transcript-list");
    act(() => {
      list.props.onLayout({ nativeEvent: { layout: { height: 100 } } });
      list.props.onContentSizeChange(100, 500);
      list.props.onScroll({
        nativeEvent: {
          contentOffset: { y: 200 },
          layoutMeasurement: { height: 100 },
          contentSize: { height: 500 },
        },
      });
    });

    act(() => {
      list.props.onScrollBeginDrag();
    });
    fireEvent.press(screen.getByLabelText("Scroll to top"));
    fireEvent.press(screen.getByLabelText("Scroll to bottom"));

    expect(onUserNavigationIntent).toHaveBeenCalledTimes(3);
  });
});
