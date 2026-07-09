import {
  getTranscriptRangeControlPresentation,
  planTranscriptRangeControlAction,
} from '../src/chat/messageRangeControls';

describe('message range controls', () => {
  test('expands suffix ranges upward by page size', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '-50',
          endText: '',
          firstLoadedIndex: 175,
          lastLoadedIndex: 224,
          pageSize: 50,
        },
        'expandAbove',
      ),
    ).toEqual({ startText: '-100', endText: '' });
  });

  test('expands absolute range start upward without going below zero', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '25',
          endText: '75',
          firstLoadedIndex: 25,
          lastLoadedIndex: 74,
          pageSize: 50,
        },
        'expandAbove',
      ),
    ).toEqual({ startText: '0', endText: '75' });
  });

  test('expands absolute range end downward', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '125',
          endText: '175',
          firstLoadedIndex: 125,
          lastLoadedIndex: 174,
          pageSize: 50,
        },
        'expandBelow',
      ),
    ).toEqual({ startText: '125', endText: '225' });
  });

  test('expands prefix range end downward', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '',
          endText: '50',
          firstLoadedIndex: 0,
          lastLoadedIndex: 49,
          pageSize: 50,
        },
        'expandBelow',
      ),
    ).toEqual({ startText: '', endText: '100' });
  });

  test('show all clears both range fields', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '-50',
          endText: '',
          firstLoadedIndex: 175,
          lastLoadedIndex: 224,
          pageSize: 50,
        },
        'showAll',
      ),
    ).toEqual({ startText: '', endText: '' });
  });

  test('presentation uses loaded message index for hidden-above label', () => {
    expect(
      getTranscriptRangeControlPresentation({
        startText: '-50',
        endText: '',
        firstLoadedIndex: 175,
        lastLoadedIndex: 224,
        pageSize: 50,
      }).top,
    ).toEqual({ label: '176 messages above', action: 'expandAbove' });
  });

  test('presentation hides above control when loaded range starts at zero', () => {
    expect(
      getTranscriptRangeControlPresentation({
        startText: '0',
        endText: '50',
        firstLoadedIndex: 0,
        lastLoadedIndex: 49,
        pageSize: 50,
      }).top,
    ).toBeNull();
  });

  test('suffix ranges do not offer a newer-messages action', () => {
    expect(
      getTranscriptRangeControlPresentation({
        startText: '-50',
        endText: '',
        firstLoadedIndex: 175,
        lastLoadedIndex: 224,
        pageSize: 50,
      }).bottom,
    ).toBeNull();
  });
});