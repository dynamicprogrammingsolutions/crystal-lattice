import {
  applyWatchlistKeyOrder,
  buildWatchlistPreview,
  buildWatchlistRenderSlots,
  moveWatchlistValues,
  resolveWatchlistDropTranslation,
  resolveWatchlistDropTarget,
  type WatchlistTileFrame,
} from '../watchlistDrag';

describe('Watchlist drag geometry', () => {
  const frames: WatchlistTileFrame[] = [
    { x: 0, y: 0, width: 100, height: 120 },
    { x: 112, y: 0, width: 100, height: 150 },
    { x: 0, y: 162, width: 100, height: 180 },
    { x: 112, y: 162, width: 100, height: 100 },
  ];

  it('resolves horizontal and predominantly vertical movement from measured slots', () => {
    expect(resolveWatchlistDropTarget(frames, 0, 120, 5)).toBe(1);
    expect(resolveWatchlistDropTarget(frames, 0, 3, 190)).toBe(2);
  });

  it('places the empty slot at the prospective settled index', () => {
    expect(buildWatchlistPreview(['a', 'b', 'c', 'd'], 0, 2)).toEqual([
      { kind: 'item', item: 'b' },
      { kind: 'item', item: 'c' },
      { kind: 'placeholder' },
      { kind: 'item', item: 'd' },
    ]);
    expect(buildWatchlistPreview(['a', 'b', 'c', 'd'], 3, 0)).toEqual([
      { kind: 'placeholder' },
      { kind: 'item', item: 'a' },
      { kind: 'item', item: 'b' },
      { kind: 'item', item: 'c' },
    ]);
  });

  it('keeps the responder-owning child at its original render index', () => {
    expect(buildWatchlistRenderSlots(['a', 'b', 'c', 'd'], 0, 2)).toEqual([
      { kind: 'dragged', item: 'a' },
      { kind: 'item', item: 'b' },
      { kind: 'item', item: 'c' },
      { kind: 'placeholder' },
      { kind: 'item', item: 'd' },
    ]);
    expect(buildWatchlistRenderSlots(['a', 'b', 'c', 'd'], 2, 0)).toEqual([
      { kind: 'placeholder' },
      { kind: 'item', item: 'a' },
      { kind: 'dragged', item: 'c' },
      { kind: 'item', item: 'b' },
      { kind: 'item', item: 'd' },
    ]);
  });

  it('projects the settled order while the source still reports the old order', () => {
    const staleItems = [
      { key: 'a', value: 1 },
      { key: 'b', value: 2 },
      { key: 'c', value: 3 },
    ];
    const targetKeys = moveWatchlistValues(
      staleItems.map((item) => item.key),
      0,
      2,
    );

    expect(targetKeys).toEqual(['b', 'c', 'a']);
    expect(
      applyWatchlistKeyOrder(staleItems, targetKeys).map((item) => item.key),
    ).toEqual(['b', 'c', 'a']);
  });

  it('snaps the released overlay directly onto the measured placeholder', () => {
    expect(resolveWatchlistDropTranslation(frames, 0, 2)).toEqual({
      x: 0,
      y: 162,
    });
    expect(resolveWatchlistDropTranslation(frames, 1, 2)).toEqual({
      x: -112,
      y: 162,
    });
  });
});
