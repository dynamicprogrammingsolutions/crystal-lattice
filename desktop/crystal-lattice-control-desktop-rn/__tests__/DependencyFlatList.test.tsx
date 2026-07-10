import React from 'react';
import { FlatList, Text } from 'react-native';

import { render } from '@testing-library/react-native';

import { DependencyFlatList } from '../src/ui/DependencyFlatList';

function renderList(rowCount: number, eagerRenderThreshold: number) {
  return render(
    <DependencyFlatList
      data={Array.from({ length: rowCount }, (_, index) => index)}
      eagerRenderThreshold={eagerRenderThreshold}
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
});