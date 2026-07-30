import { describe, expect, it } from "vitest";

import {
  getTranscriptRangeControlPresentation,
  planTranscriptRangeControlAction,
} from "../messageRangeControls";

describe("message range controls", () => {
  it("expands suffix ranges upward by page size", () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: "-50",
          endText: "",
          firstLoadedIndex: 175,
          lastLoadedIndex: 224,
          loadedCount: 50,
          pageSize: 50,
          maxRangeSize: 100,
        },
        "expandAbove"
      )
    ).toEqual({ startText: "-100", endText: "" });
  });

  it("converts a full suffix range to an absolute older window", () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: "-100",
          endText: "",
          firstLoadedIndex: 200,
          lastLoadedIndex: 299,
          loadedCount: 100,
          pageSize: 50,
          maxRangeSize: 100,
        },
        "expandAbove"
      )
    ).toEqual({ startText: "150", endText: "250" });
  });

  it("slides a capped absolute range toward older messages", () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: "150",
          endText: "250",
          firstLoadedIndex: 150,
          lastLoadedIndex: 249,
          loadedCount: 100,
          pageSize: 50,
          maxRangeSize: 100,
        },
        "expandAbove"
      )
    ).toEqual({ startText: "100", endText: "200" });
  });

  it("expands an absolute range toward newer messages", () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: "125",
          endText: "175",
          firstLoadedIndex: 125,
          lastLoadedIndex: 174,
          loadedCount: 50,
          pageSize: 50,
          maxRangeSize: 100,
        },
        "expandBelow"
      )
    ).toEqual({ startText: "125", endText: "225" });
  });

  it("returns to a suffix range after detecting the newest edge", () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: "200",
          endText: "300",
          firstLoadedIndex: 200,
          lastLoadedIndex: 279,
          loadedCount: 80,
          pageSize: 50,
          maxRangeSize: 100,
        },
        "expandBelow"
      )
    ).toEqual({ startText: "-100", endText: "" });
  });

  it("clears both fields for show all", () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: "-50",
          endText: "",
          firstLoadedIndex: 175,
          lastLoadedIndex: 224,
          loadedCount: 50,
          pageSize: 50,
          maxRangeSize: 100,
        },
        "showAll"
      )
    ).toEqual({ startText: "", endText: "" });
  });

  it("switches to the page-sized suffix for show last", () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: "150",
          endText: "250",
          firstLoadedIndex: 150,
          lastLoadedIndex: 249,
          loadedCount: 100,
          pageSize: 50,
          maxRangeSize: 100,
        },
        "showLast"
      )
    ).toEqual({ startText: "-50", endText: "" });
  });

  it("hides show last when the last page is already selected", () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: "-50",
          endText: "",
          firstLoadedIndex: 175,
          lastLoadedIndex: 224,
          loadedCount: 50,
          pageSize: 50,
          maxRangeSize: 100,
        },
        "showLast"
      )
    ).toBeNull();
  });

  it("presents older and all actions at the top", () => {
    expect(
      getTranscriptRangeControlPresentation({
        startText: "-50",
        endText: "",
        firstLoadedIndex: 175,
        lastLoadedIndex: 224,
        loadedCount: 50,
        pageSize: 50,
        maxRangeSize: 100,
      }).topButtons
    ).toEqual([
      { id: "expandAbove", title: "Show 50 older messages" },
      { id: "showAll", title: "Show all" },
    ]);
  });

  it("caps the older-message label at the page size", () => {
    expect(
      getTranscriptRangeControlPresentation({
        startText: "25",
        endText: "75",
        firstLoadedIndex: 25,
        lastLoadedIndex: 74,
        loadedCount: 50,
        pageSize: 50,
        maxRangeSize: 100,
      }).topButtons[0]
    ).toEqual({
      id: "expandAbove",
      title: "Show 26 older messages",
    });
  });

  it("presents newer and last actions at the bottom", () => {
    expect(
      getTranscriptRangeControlPresentation({
        startText: "150",
        endText: "250",
        firstLoadedIndex: 150,
        lastLoadedIndex: 249,
        loadedCount: 100,
        pageSize: 50,
        maxRangeSize: 100,
      }).bottomButtons
    ).toEqual([
      { id: "expandBelow", title: "Show 50 newer messages" },
      { id: "showLast", title: "Show last 50" },
    ]);
  });
});
