export type TranscriptRangeControlAction =
  | "expandAbove"
  | "expandBelow"
  | "showAll"
  | "showLast";

export type TranscriptRangeControlInput = {
  startText: string | null | undefined;
  endText: string | null | undefined;
  firstLoadedIndex: number | null;
  lastLoadedIndex: number | null;
  loadedCount: number;
  pageSize: number;
  maxRangeSize: number;
};

export type TranscriptRangePlan = {
  startText: string;
  endText: string;
};

export type TranscriptRangeControlButton = {
  id: TranscriptRangeControlAction;
  title: string;
};

export type TranscriptRangeControlPresentation = {
  topButtons: TranscriptRangeControlButton[];
  bottomButtons: TranscriptRangeControlButton[];
};

function parseIntegerText(value: string | null | undefined): number | null {
  const trimmed = (value ?? "").trim();
  if (!/^-?\d+$/.test(trimmed)) {
    return null;
  }
  const parsed = Number(trimmed);
  return Number.isSafeInteger(parsed) ? parsed : null;
}

function normalizeRangePart(value: string | null | undefined): string {
  return (value ?? "").trim();
}

function formatRangePart(value: number): string {
  return String(Math.trunc(value));
}

function resolvePageSize(pageSize: number): number {
  return Number.isFinite(pageSize) && pageSize > 0
    ? Math.max(1, Math.round(pageSize))
    : 50;
}

function resolveMaxRangeSize(maxRangeSize: number, pageSize: number): number {
  return Number.isFinite(maxRangeSize) && maxRangeSize > 0
    ? Math.max(pageSize, Math.round(maxRangeSize))
    : pageSize * 2;
}

function formatSuffixRange(count: number): TranscriptRangePlan {
  return {
    startText: formatRangePart(-Math.max(1, Math.round(count))),
    endText: "",
  };
}

export function planTranscriptRangeControlAction(
  input: TranscriptRangeControlInput,
  action: TranscriptRangeControlAction
): TranscriptRangePlan | null {
  const startText = normalizeRangePart(input.startText);
  const endText = normalizeRangePart(input.endText);
  const pageSize = resolvePageSize(input.pageSize);
  const maxRangeSize = resolveMaxRangeSize(input.maxRangeSize, pageSize);
  const loadedCount =
    Number.isFinite(input.loadedCount) && input.loadedCount > 0
      ? Math.round(input.loadedCount)
      : 0;

  const start = parseIntegerText(startText);
  const end = parseIntegerText(endText);

  if (action === "showAll") {
    if (startText === "" && endText === "") {
      return null;
    }
    return { startText: "", endText: "" };
  }

  if (action === "showLast") {
    if (start === -pageSize && endText === "") {
      return null;
    }
    return formatSuffixRange(pageSize);
  }

  if (action === "expandAbove") {
    if (start != null && start < 0 && endText === "") {
      const currentCount = Math.abs(start);
      if (currentCount < maxRangeSize) {
        return formatSuffixRange(
          Math.min(maxRangeSize, currentCount + pageSize)
        );
      }
      if (input.firstLoadedIndex == null || input.firstLoadedIndex <= 0) {
        return null;
      }
      const nextEnd = Math.max(pageSize, input.firstLoadedIndex + pageSize);
      const nextStart = Math.max(0, nextEnd - maxRangeSize);
      return {
        startText: formatRangePart(nextStart),
        endText: formatRangePart(nextEnd),
      };
    }
    if (start != null) {
      if (start <= 0) {
        return null;
      }
      if (end != null && end > start) {
        const currentCount = end - start;
        if (currentCount < maxRangeSize) {
          return {
            startText: formatRangePart(Math.max(0, start - pageSize)),
            endText,
          };
        }
        const nextStart = Math.max(0, start - pageSize);
        return {
          startText: formatRangePart(nextStart),
          endText: formatRangePart(nextStart + currentCount),
        };
      }
      return {
        startText: formatRangePart(Math.max(0, start - pageSize)),
        endText,
      };
    }
    if (input.firstLoadedIndex != null && input.firstLoadedIndex > 0) {
      return {
        startText: formatRangePart(
          Math.max(0, input.firstLoadedIndex - pageSize)
        ),
        endText:
          input.lastLoadedIndex != null
            ? formatRangePart(input.lastLoadedIndex + 1)
            : endText,
      };
    }
    return null;
  }

  if (end != null) {
    const requestedCount = start != null && end > start ? end - start : end;
    const reachedEnd =
      requestedCount > 0 &&
      loadedCount > 0 &&
      loadedCount < requestedCount &&
      (input.lastLoadedIndex == null || input.lastLoadedIndex + 1 < end);
    if (reachedEnd) {
      return formatSuffixRange(maxRangeSize);
    }
    if (start != null) {
      if (requestedCount > 0 && requestedCount < maxRangeSize) {
        return {
          startText,
          endText: formatRangePart(end + pageSize),
        };
      }
      return {
        startText: formatRangePart(start + pageSize),
        endText: formatRangePart(end + pageSize),
      };
    }
    return {
      startText,
      endText: formatRangePart(end + pageSize),
    };
  }
  return null;
}

export function getTranscriptRangeControlPresentation(
  input: TranscriptRangeControlInput
): TranscriptRangeControlPresentation {
  const firstLoadedIndex = input.firstLoadedIndex;
  const pageSize = resolvePageSize(input.pageSize);
  const topPlan = planTranscriptRangeControlAction(input, "expandAbove");
  const bottomPlan = planTranscriptRangeControlAction(input, "expandBelow");
  const showAllPlan = planTranscriptRangeControlAction(input, "showAll");
  const showLastPlan = planTranscriptRangeControlAction(input, "showLast");
  const hiddenAbove =
    firstLoadedIndex != null && firstLoadedIndex > 0
      ? firstLoadedIndex + 1
      : null;
  const topButtons: TranscriptRangeControlButton[] = [];
  const bottomButtons: TranscriptRangeControlButton[] = [];

  if (topPlan && hiddenAbove != null && hiddenAbove > 0) {
    topButtons.push({
      id: "expandAbove",
      title: `Show ${Math.min(pageSize, hiddenAbove)} older messages`,
    });
  }
  if (showAllPlan) {
    topButtons.push({ id: "showAll", title: "Show all" });
  }
  if (bottomPlan) {
    bottomButtons.push({
      id: "expandBelow",
      title: `Show ${pageSize} newer messages`,
    });
  }
  if (showLastPlan) {
    bottomButtons.push({
      id: "showLast",
      title: `Show last ${pageSize}`,
    });
  }

  return {
    topButtons,
    bottomButtons,
  };
}
