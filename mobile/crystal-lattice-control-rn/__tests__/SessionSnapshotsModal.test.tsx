import React from 'react';
import { fireEvent, screen } from '@testing-library/react-native';
import { StyleSheet } from 'react-native';

import SessionSnapshotsModal from '../src/components/SessionSnapshotsModal';
import { renderWithMobileProviders } from '../src/testUtils/renderWithMobileProviders';

const onRequestClose = jest.fn();
const onCreateSnapshot = jest.fn();
const onClearSelectedSnapshot = jest.fn();
const onSelectSnapshot = jest.fn();
const onRestoreSnapshot = jest.fn();
const onDeleteSnapshot = jest.fn();

const snapshotItems = [
  {
    snapshot_id: 'snap-1',
    created_at: '2026-06-17T12:00:00Z',
    reason: 'manual',
  },
  {
    snapshot_id: 'snap-2',
    created_at: '2026-06-17T13:00:00Z',
    reason: null,
  },
];

function renderModal(selectedSnapshotId: string | null = 'snap-1') {
  return renderWithMobileProviders(
    <SessionSnapshotsModal
      visible
      snapshotsLoading={false}
      snapshotItems={snapshotItems}
      selectedSnapshotId={selectedSnapshotId}
      onRequestClose={onRequestClose}
      onCreateSnapshot={onCreateSnapshot}
      onClearSelectedSnapshot={onClearSelectedSnapshot}
      onSelectSnapshot={onSelectSnapshot}
      onRestoreSnapshot={onRestoreSnapshot}
      onDeleteSnapshot={onDeleteSnapshot}
    />,
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

test('snapshot modal uses shared frame and renders snapshot actions', () => {
  renderModal();

  expect(screen.getByText('Snapshots')).toBeTruthy();
  expect(screen.getByText('Close')).toBeTruthy();
  expect(screen.getByText('Create')).toBeTruthy();
  expect(screen.getByText('Live session')).toBeTruthy();
  expect(screen.getByText('manual')).toBeTruthy();
  expect(screen.getByText('2026-06-17T12:00:00Z')).toBeTruthy();
  expect(screen.getByText('snap-1')).toBeTruthy();
  expect(screen.getByText('snapshot')).toBeTruthy();
  expect(screen.getByText('Selected')).toBeTruthy();
  expect(screen.getByText('Select')).toBeTruthy();
  expect(screen.getAllByText('Restore')).toHaveLength(2);
  expect(screen.getAllByText('Delete')).toHaveLength(2);

  fireEvent.press(screen.getByText('Close'));
  expect(onRequestClose).toHaveBeenCalledTimes(1);
});

test('snapshot modal hides live-session action when no snapshot is selected', () => {
  renderModal(null);

  expect(screen.queryByText('Live session')).toBeNull();
});

test('snapshot modal calls snapshot handlers with the selected snapshot id', () => {
  renderModal();

  fireEvent.press(screen.getByText('Create'));
  expect(onCreateSnapshot).toHaveBeenCalledTimes(1);

  fireEvent.press(screen.getByText('Live session'));
  expect(onClearSelectedSnapshot).toHaveBeenCalledTimes(1);

  fireEvent.press(screen.getByText('Selected'));
  expect(onSelectSnapshot).toHaveBeenCalledWith('snap-1');

  fireEvent.press(screen.getAllByText('Restore')[0]);
  expect(onRestoreSnapshot).toHaveBeenCalledWith('snap-1');

  fireEvent.press(screen.getAllByText('Delete')[0]);
  expect(onDeleteSnapshot).toHaveBeenCalledWith('snap-1');
});

test('snapshot item content is vertical while per-snapshot actions remain horizontal', () => {
  renderModal();

  const itemStyle = StyleSheet.flatten(screen.getByTestId('snapshot-item-snap-1').props.style);
  const actionStyle = StyleSheet.flatten(
    screen.getByTestId('snapshot-actions-snap-1').props.style,
  );

  expect(itemStyle.flexDirection).toBeUndefined();
  expect(actionStyle.flexDirection).toBe('row');
});