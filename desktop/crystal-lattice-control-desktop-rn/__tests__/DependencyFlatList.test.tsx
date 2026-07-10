import React from 'react';
import { FlatList, Text } from 'react-native';

import { act, render } from '@testing-library/react-native';

import { DependencyFlatList } from '../src/ui/DependencyFlatList';

function renderList(
  rowCount: number,
  eagerRenderThreshold: number,
  eagerRenderEligibilityCount?: number,
) {
  return render(
    <DependencyFlatList
      data={Array.from({ length: rowCount }, (_, index) => index)}
      eagerRenderThreshold={eagerRenderThreshold}
      eagerRenderEligibilityCount={eagerRenderEligibilityCount}
      initialNumToRender={2}
      maxToRenderPerBatch={3}
      updateCellsBatchingPeriod={40}
      removeClippedSubviews
      keyExtractor={(item) => String(item)}
      renderItem={({ item }) => <Text>{item}</Text>}
    />,
  ).UNSAFE_getByType(FlatList);
}

describe('DependencyFlatList eager rendering', () => {
  it('passes eager all-row tuning to FlatList at the threshold', () => {
    const list = renderList(5, 5);

    expect(list.props.initialNumToRender).toBe(5);
    expect(list.props.maxToRenderPerBatch).toBe(5);
    expect(list.props.updateCellsBatchingPeriod).toBe(0);
    expect(list.props.removeClippedSubviews).toBe(false);
  });

  it('preserves configured virtualization tuning above the threshold', () => {
    const list = renderList(6, 5);

    expect(list.props.initialNumToRender).toBe(2);
    expect(list.props.maxToRenderPerBatch).toBe(3);
    expect(list.props.updateCellsBatchingPeriod).toBe(40);
    expect(list.props.removeClippedSubviews).toBe(true);
  });

  it('uses a stable eligibility count for transient synthetic rows', () => {
    const list = renderList(6, 5, 5);

    expect(list.props.initialNumToRender).toBe(6);
    expect(list.props.maxToRenderPerBatch).toBe(6);
    expect(list.props.updateCellsBatchingPeriod).toBe(0);
    expect(list.props.removeClippedSubviews).toBe(false);
  });

  it('uses configured item-anchor limits and reports effective diagnostics', () => {
    const listRef = React.createRef<any>();
    const onScrollActionDiagnostic = jest.fn();
    const rendered = render(
      <DependencyFlatList
        data={[0, 1, 2]}
        listRef={listRef}
        itemAnchorTimeoutMs={15000}
        itemAnchorMaxAttempts={200}
        onScrollActionDiagnostic={onScrollActionDiagnostic}
        keyExtractor={(item) => `msg-${item}`}
        renderItem={({ item }) => <Text>{item}</Text>}
      />,
    );

    act(() => {
      listRef.current.scrollToItemAnchor({
        key: 'msg-2',
        offsetFromViewportTop: 40,
        animated: false,
      });
    });

    expect(onScrollActionDiagnostic).toHaveBeenCalledWith({
      event: 'listAnchorStarted',
      reason: 'scrollToItemAnchor',
      details: {
        key: 'msg-2',
        index: 2,
        requestedOffset: 40,
        timeoutMs: 15000,
        maxAttempts: 200,
      },
    });

    act(() => {
      listRef.current.scrollToOffset({ offset: 0, animated: false });
    });
    rendered.unmount();
  });
});