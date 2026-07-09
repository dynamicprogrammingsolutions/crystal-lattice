export type TranscriptRangeControlAction = 'expandAbove' | 'expandBelow' | 'showAll';

export type TranscriptRangeControlInput = {
  startText: string | null | undefined;
  endText: string | null | undefined;
  firstLoadedIndex: number | null;
  lastLoadedIndex: number | null;
  pageSize: number;
};

export type TranscriptRangePlan = {
  startText: string;
  endText: string;
};

export type TranscriptRangeControlPresentation = {
  top: { label: string; action: 'expandAbove' } | null;
  bottom: { label: string; action: 'expandBelow' } | null;
  showAll: { label: string; action: 'showAll' } | null;
};

function parseIntegerText(value: string | null | undefined): number | null {
  const trimmed = (value ?? '').trim();
  if (!/^-?\d+$/.test(trimmed)) {
    return null;
  }
  const parsed = Number(trimmed);
  return Number.isSafeInteger(parsed) ? parsed : null;
}

function normalizeRangePart(value: string | null | undefined): string {
  return (value ?? '').trim();
}

function formatRangePart(value: number): string {
  return String(Math.trunc(value));
}

function resolvePageSize(pageSize: number): number {
  return Number.isFinite(pageSize) && pageSize > 0 ? Math.max(1, Math.round(pageSize)) : 50;
}

export function planTranscriptRangeControlAction(
  input: TranscriptRangeControlInput,
  action: TranscriptRangeControlAction,
): TranscriptRangePlan | null {
  const startText = normalizeRangePart(input.startText);
  const endText = normalizeRangePart(input.endText);
  const pageSize = resolvePageSize(input.pageSize);

  if (action === 'showAll') {
    if (startText === '' && endText === '') {
      return null;
    }
    return { startText: '', endText: '' };
  }

  const start = parseIntegerText(startText);
  const end = parseIntegerText(endText);

  if (action === 'expandAbove') {
    if (start != null && start < 0 && endText === '') {
      return { startText: formatRangePart(start - pageSize), endText: '' };
    }
    if (start != null) {
      if (start <= 0) {
        return null;
      }
      return {
        startText: formatRangePart(Math.max(0, start - pageSize)),
        endText,
      };
    }
    if (input.firstLoadedIndex != null && input.firstLoadedIndex > 0) {
      return {
        startText: formatRangePart(Math.max(0, input.firstLoadedIndex - pageSize)),
        endText:
          input.lastLoadedIndex != null
            ? formatRangePart(input.lastLoadedIndex + 1)
            : endText,
      };
    }
    return null;
  }

  if (end != null) {
    return {
      startText,
      endText: formatRangePart(end + pageSize),
    };
  }
  return null;
}

export function getTranscriptRangeControlPresentation(
  input: TranscriptRangeControlInput,
): TranscriptRangeControlPresentation {
  const firstLoadedIndex = input.firstLoadedIndex;
  const startText = normalizeRangePart(input.startText);
  const endText = normalizeRangePart(input.endText);
  const topPlan = planTranscriptRangeControlAction(input, 'expandAbove');
  const bottomPlan = planTranscriptRangeControlAction(input, 'expandBelow');
  const showAllPlan = planTranscriptRangeControlAction(input, 'showAll');
  const hiddenAbove =
    firstLoadedIndex != null && firstLoadedIndex > 0 ? firstLoadedIndex + 1 : null;

  return {
    top:
      topPlan && hiddenAbove != null && hiddenAbove > 0
        ? { label: `${hiddenAbove} messages above`, action: 'expandAbove' }
        : null,
    bottom: bottomPlan
      ? {
          label: 'Show newer messages',
          action: 'expandBelow',
        }
      : null,
    showAll: showAllPlan ? { label: 'Show all', action: 'showAll' } : null,
  };
}