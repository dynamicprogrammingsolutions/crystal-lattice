import React from "react";
import { KeyboardAvoidingView, Platform, View } from "react-native";
import * as safeArea from "react-native-safe-area-context";
import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";
import { MobileRichSessionUiHarness } from "../src/testing/MobileRichSessionUiHarness";

afterEach(() => {
  jest.restoreAllMocks();
});

test.each([0, 44, 59])(
  "the inline iOS editor accounts for a %s-point safe area plus navigation padding",
  async (top) => {
    jest.replaceProperty(Platform, "OS", "ios");
    jest.spyOn(safeArea, "useSafeAreaInsets").mockReturnValue({
      top,
      bottom: 34,
      left: 0,
      right: 0,
    });

    const measuredY = top + 8;
    jest.spyOn(View.prototype, "measureInWindow").mockImplementation((callback) => {
      callback(16, measuredY, 343, 650);
    });
    render(<MobileRichSessionUiHarness />);
    await screen.findByTestId("message-composer-input");
    fireEvent(screen.getByTestId("chat-screen-viewport"), "layout", {
      nativeEvent: { layout: { x: 0, y: 0, width: 343, height: 650 } },
    });

    await waitFor(() => {
      const inlineAvoider = screen.UNSAFE_getAllByType(KeyboardAvoidingView)[0];
      expect(inlineAvoider.props.behavior).toBe("padding");
      expect(inlineAvoider.props.keyboardVerticalOffset).toBe(measuredY);
    });
  }
);

test("Android keeps its window-resize offset while using height avoidance", async () => {
  jest.replaceProperty(Platform, "OS", "android");
  jest.spyOn(safeArea, "useSafeAreaInsets").mockReturnValue({
    top: 24,
    bottom: 0,
    left: 0,
    right: 0,
  });

  render(<MobileRichSessionUiHarness />);
  await screen.findByTestId("message-composer-input");

  const inlineAvoider = screen.UNSAFE_getAllByType(KeyboardAvoidingView)[0];
  expect(inlineAvoider.props.behavior).toBe("height");
  expect(inlineAvoider.props.keyboardVerticalOffset).toBe(0);
});