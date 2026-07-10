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
          loadedCount: 50,
          pageSize: 50,
          maxRangeSize: 100,
        },
        'expandAbove',
      ),
    ).toEqual({ startText: '-100', endText: '' });
  });

  test('converts suffix range to an absolute older window after max range is reached', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '-100',
          endText: '',
          firstLoadedIndex: 200,
          lastLoadedIndex: 299,
          loadedCount: 100,
          pageSize: 50,
          maxRangeSize: 100,
        },
        'expandAbove',
      ),
    ).toEqual({ startText: '150', endText: '250' });
  });

  test('expands absolute range start upward without going below zero', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '25',
          endText: '75',
          firstLoadedIndex: 25,
          lastLoadedIndex: 74,
          loadedCount: 50,
          pageSize: 50,
          maxRangeSize: 100,
        },
        'expandAbove',
      ),
    ).toEqual({ startText: '0', endText: '75' });
  });

  test('slides absolute older window after max range is reached', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '150',
          endText: '250',
          firstLoadedIndex: 150,
          lastLoadedIndex: 249,
          loadedCount: 100,
          pageSize: 50,
          maxRangeSize: 100,
        },
        'expandAbove',
      ),
    ).toEqual({ startText: '100', endText: '200' });
  });

  test('expands absolute range end downward', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '125',
          endText: '175',
          firstLoadedIndex: 125,
          lastLoadedIndex: 174,
          loadedCount: 50,
          pageSize: 50,
          maxRangeSize: 100,
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
          loadedCount: 50,
          pageSize: 50,
          maxRangeSize: 100,
        },
        'expandBelow',
      ),
    ).toEqual({ startText: '', endText: '100' });
  });

  test('converts absolute range back to suffix range after detecting the end', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '200',
          endText: '300',
          firstLoadedIndex: 200,
          lastLoadedIndex: 279,
          loadedCount: 80,
          pageSize: 50,
          maxRangeSize: 100,
        },
        'expandBelow',
      ),
    ).toEqual({ startText: '-100', endText: '' });
  });

  test('show all clears both range fields', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '-50',
          endText: '',
          firstLoadedIndex: 175,
          lastLoadedIndex: 224,
          loadedCount: 50,
          pageSize: 50,
          maxRangeSize: 100,
        },
        'showAll',
      ),
    ).toEqual({ startText: '', endText: '' });
  });

  test('show last switches back to the page-sized suffix range', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '150',
          endText: '250',
          firstLoadedIndex: 150,
          lastLoadedIndex: 249,
          loadedCount: 100,
          pageSize: 50,
          maxRangeSize: 100,
        },
        'showLast',
      ),
    ).toEqual({ startText: '-50', endText: '' });
  });

  test('show last is hidden when already showing the last page', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '-50',
          endText: '',
          firstLoadedIndex: 175,
          lastLoadedIndex: 224,
          loadedCount: 50,
          pageSize: 50,
          maxRangeSize: 100,
        },
        'showLast',
      ),
    ).toBeNull();
  });

  test('presentation labels older-message action using page size and hidden count', () => {
    expect(
      getTranscriptRangeControlPresentation({
        startText: '-50',
        endText: '',
        firstLoadedIndex: 175,
        lastLoadedIndex: 224,
        loadedCount: 50,
        pageSize: 50,
        maxRangeSize: 100,
      }).topButtons,
    ).toEqual([
      { id: 'expandAbove', title: 'Show 50 older messages' },
      { id: 'showAll', title: 'Show all' },
    ]);
  });

  test('presentation hides above control when loaded range starts at zero', () => {
    expect(
      getTranscriptRangeControlPresentation({
        startText: '0',
        endText: '50',
        firstLoadedIndex: 0,
        lastLoadedIndex: 49,
        loadedCount: 50,
        pageSize: 50,
        maxRangeSize: 100,
      }).topButtons.find((button) => button.id === 'expandAbove'),
    ).toBeUndefined();
  });

  test('suffix ranges do not offer a newer-messages action', () => {
    expect(
      getTranscriptRangeControlPresentation({
        startText: '-50',
        endText: '',
        firstLoadedIndex: 175,
        lastLoadedIndex: 224,
        loadedCount: 50,
        pageSize: 50,
        maxRangeSize: 100,
      }).bottomButtons.find((button) => button.id === 'expandBelow'),
    ).toBeUndefined();
  });

  test('open all-message range does not offer a newer-messages action', () => {
    expect(
      planTranscriptRangeControlAction(
        {
          startText: '',
          endText: '',
          firstLoadedIndex: 0,
          lastLoadedIndex: 99,
          loadedCount: 100,
          pageSize: 50,
          maxRangeSize: 100,
        },
        'expandBelow',
      ),
    ).toBeNull();
  });

  test('presentation offers show-last at the bottom when not already on the last page', () => {
    expect(
      getTranscriptRangeControlPresentation({
        startText: '150',
        endText: '250',
        firstLoadedIndex: 150,
        lastLoadedIndex: 249,
        loadedCount: 100,
        pageSize: 50,
        maxRangeSize: 100,
      }).bottomButtons,
    ).toEqual([
      { id: 'expandBelow', title: 'Show 50 newer messages' },
      { id: 'showLast', title: 'Show last 50' },
    ]);
  });
});
